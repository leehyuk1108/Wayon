"""Receive Galaxy BLE RSSI on Comma. Temporary, parked-only diagnostics."""

import argparse
import asyncio
from collections import deque
from contextlib import contextmanager, suppress
import fcntl
from hashlib import sha256
import hmac
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import signal
import ssl
from statistics import median
import subprocess
import tempfile
import time
from uuid import UUID

from aiohttp import ClientError, ClientSession, ClientTimeout, WSMsgType, web
from jeepney import DBusAddress, HeaderFields, MatchRule, new_method_call
from jeepney.io.asyncio import open_dbus_router
from jeepney.wrappers import unwrap_msg

STAGES = ("INSIDE", "DOOR", "AWAY")
CAPTURE_MS = 18_000
SAMPLE_MS = 125
WIRE_BUCKET_MS = 250
REACQUIRE_MS = 1_050
REACQUIRE_MAX = 12
DEVICE = "org.bluez.Device1"
ADAPTER = "org.bluez.Adapter1"
PROPS = "org.freedesktop.DBus.Properties"
OBJECTS = "org.freedesktop.DBus.ObjectManager"
DBUS = DBusAddress("/org/freedesktop/DBus", bus_name="org.freedesktop.DBus", interface="org.freedesktop.DBus")
ONROAD = Path("/data/params/d/IsOnroad")
OFFROAD = Path("/data/params/d/IsOffroad")
DIAGNOSTIC_RADIO = Path("/data/wayon-door/rssi-diagnostic.lock")
SYSTEM_PHONE = Path("/data/wayon-door/system-phone.address")
WAYON_WS = "wss://wayon-ble-rssi.hyuklee.workers.dev/api/diagnostics/ble-rssi/device"


def parked():
  try:
    return ONROAD.read_bytes() == b"0"
  except OSError:
    return False


@contextmanager
def diagnostic_priority(path=DIAGNOSTIC_RADIO):
  try:
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
  except FileNotFoundError:
    yield False
    return
  try:
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    yield True
  finally:
    os.close(fd)


def diagnostic_waiting(path=DIAGNOSTIC_RADIO):
  try:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  except FileNotFoundError:
    return False
  try:
    fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
    return False
  except BlockingIOError:
    return True
  finally:
    os.close(fd)


def boot_time_ns():
  return time.clock_gettime_ns(time.CLOCK_BOOTTIME) if hasattr(time, "CLOCK_BOOTTIME") else time.monotonic_ns()


class IgnitionGuard:
  def __init__(self, receive, clock=boot_time_ns, is_offroad=None):
    self.receive, self.clock, self.last = receive, clock, None
    self.is_offroad = is_offroad or (lambda: parked() and OFFROAD.read_bytes() == b"1")
    self.reason = "waiting"

  def __call__(self):
    try:
      msg = self.receive()
      if msg is not None:
        self.last = msg
      msg = self.last
      if not self.is_offroad():
        self.reason = "not_offroad"
      elif msg is None:
        self.reason = "missing_panda"
      elif not msg.valid or not 0 <= self.clock() - msg.logMonoTime <= 1_000_000_000:
        self.reason = "stale_or_invalid_panda"
      elif not len(msg.pandaStates) or any(p.pandaType == "unknown" for p in msg.pandaStates):
        self.reason = "unknown_panda"
      elif any(p.ignitionLine or p.ignitionCan for p in msg.pandaStates):
        self.reason = "ignition_on"
      else:
        self.reason = "off"
    except Exception:
      self.reason = "unavailable"
    return self.reason == "off"

  async def watch(self):
    while True:
      self()
      await asyncio.sleep(.25)


def adapter_path(objects):
  paths = [path for path, ifaces in objects.items()
           if ifaces.get(ADAPTER, {}).get("Powered") == ("b", True)]
  if len(paths) != 1:
    raise RuntimeError("Expected one powered Bluetooth adapter")
  return paths[0]


async def call(router, address, method, signature=None, args=()):
  msg = new_method_call(address, method, signature, args)
  return unwrap_msg(await asyncio.wait_for(router.send_and_get_reply(msg), 2.5))


class Capture:
  def __init__(self, stage, service, started=None, wall=None):
    self.stage, self.service = stage, service
    self.started = time.monotonic() if started is None else started
    self.wall = int(time.time() * 1000) if wall is None else wall
    self.path = None
    self.samples = []
    self.last_seen_ms = 0

  def elapsed(self, now=None):
    return int(1000 * ((time.monotonic() if now is None else now) - self.started))

  def receive(self, path, props, now=None):
    uuids = props.get("UUIDs", ("as", []))[1]
    if self.service in uuids and self.path is None:
      self.path = path
    if path != self.path or "RSSI" not in props:
      return
    dbm = props["RSSI"][1]
    elapsed = self.elapsed(now)
    if not (type(dbm) is int and -127 <= dbm <= -1 and 0 <= elapsed < CAPTURE_MS):
      return
    self.last_seen_ms = elapsed
    if not self.samples or elapsed // SAMPLE_MS > self.samples[-1][0] // SAMPLE_MS:
      self.samples.append([elapsed, dbm])

  def series(self):
    # Keep existing clients and stored rows at up to four points per second,
    # while letting both radio samples in a bucket contribute.
    buckets = {}
    for elapsed, dbm in self.samples:
      buckets.setdefault(elapsed // WIRE_BUCKET_MS, []).append((elapsed, dbm))
    return [[bucket[-1][0], int(median(dbm for _, dbm in bucket))] for bucket in buckets.values()]

  def row(self):
    return [self.stage, self.wall, self.series()]


def consume(message, owner, adapter, capture):
  header = message.header.fields
  if header.get(HeaderFields.sender) != owner:
    return
  interface = header.get(HeaderFields.interface)
  member = header.get(HeaderFields.member)
  if interface == OBJECTS and member == "InterfacesAdded":
    path, ifaces = message.body
    props = ifaces.get(DEVICE, {})
  elif interface == PROPS and member == "PropertiesChanged" and message.body[0] == DEVICE:
    path = header[HeaderFields.path]
    props = message.body[1]
  else:
    return
  if path.startswith(adapter + "/dev_"):
    capture.receive(path, props)


async def scan(capture, is_parked, ready):
  async with open_dbus_router("SYSTEM") as router:
    owner, = await call(router, DBUS, "GetNameOwner", "s", ("org.bluez",))
    objects, = await call(router, DBusAddress("/", bus_name=owner, interface=OBJECTS), "GetManagedObjects")
    path = adapter_path(objects)
    if objects[path][ADAPTER].get("Discovering") == ("b", True):
      raise RuntimeError("Another Bluetooth discovery is already running")
    adapter = DBusAddress(path, bus_name=owner, interface=ADAPTER)
    rule = MatchRule(type="signal", sender=owner)
    for interface, member in ((PROPS, "PropertiesChanged"), (OBJECTS, "InterfacesAdded")):
      match = MatchRule(type="signal", sender=owner, interface=interface, member=member)
      await call(router, DBUS, "AddMatch", "s", (match.serialise(),))
    if not is_parked():
      raise RuntimeError("Vehicle is not offroad")
    with router.filter(rule, bufsize=128) as queue:
      await call(router, adapter, "SetDiscoveryFilter", "a{sv}",
                 ({"Transport": ("s", "le"), "UUIDs": ("as", [capture.service]), "DuplicateData": ("b", True)},))
      owned = False
      restarts = last_restart_ms = 0
      try:
        await call(router, adapter, "StartDiscovery")
        owned = True
        if not is_parked():
          raise RuntimeError("Ignition off was not confirmed")
        capture.started = time.monotonic()
        ready.set_result(None)
        while capture.elapsed() < CAPTURE_MS:
          if not is_parked():
            raise RuntimeError("Vehicle left offroad")
          elapsed = capture.elapsed()
          if (restarts < REACQUIRE_MAX and elapsed < CAPTURE_MS - REACQUIRE_MS and
              elapsed - max(last_restart_ms, capture.last_seen_ms) >= REACQUIRE_MS):
            # BlueZ duplicate data is separate from the controller duplicate
            # filter. Reacquire only our scan when real RSSI stops arriving.
            await call(router, adapter, "StopDiscovery")
            owned = False
            props = DBusAddress(path, bus_name=owner, interface=PROPS)
            discovering, = await call(router, props, "Get", "ss", (ADAPTER, "Discovering"))
            if discovering == ("b", True):
              # Do not disrupt another client's discovery.
              break
            if not is_parked():
              raise RuntimeError("Vehicle left offroad")
            await call(router, adapter, "StartDiscovery")
            owned = True
            restarts += 1
            last_restart_ms = capture.elapsed()
          try:
            event = await asyncio.wait_for(queue.get(), min(.25, max(.001, (CAPTURE_MS - capture.elapsed()) / 1000)))
          except asyncio.TimeoutError:
            continue
          consume(event, owner, path, capture)
      finally:
        if owned:
          with suppress(Exception):
            await call(router, adapter, "StopDiscovery")


def load_runs(path):
  if path is None:
    return []
  try:
    with path.open("rb") as f:
      data = json.loads(f.read(32_769))
    rows = data.get("runs") if isinstance(data, dict) else None
    if not isinstance(rows, list) or len(rows) > 3 * len(STAGES):
      return []
    runs = []
    for row in rows:
      if not isinstance(row, list) or len(row) != 3:
        return []
      stage, wall, samples = row
      if (stage not in STAGES or type(wall) is not int or not isinstance(samples, list) or
          len(samples) > CAPTURE_MS // WIRE_BUCKET_MS):
        return []
      if not all(isinstance(p, list) and len(p) == 2 and all(type(x) is int for x in p) and
                 0 <= p[0] < CAPTURE_MS and -127 <= p[1] <= -1 for p in samples):
        return []
      runs.append(row)
    return runs
  except (OSError, ValueError):
    return []


class Receiver:
  def __init__(self, token, log_path, is_parked=parked, scanner=scan, *, limited=False, clock=time.monotonic):
    self.token, self.log_path, self.is_parked, self.scanner = token, log_path, is_parked, scanner
    self.runs = load_runs(log_path)
    self.active = self.task = None
    self.error = None
    self.limited, self.clock = limited, clock
    self.starts = deque()
    self.system_probe_at = float("-inf")
    self.system_probe_active = False

  def save(self):
    if self.log_path is None:
      return
    # Preserve the history even when the phone leaves Wi-Fi range.
    fd, temp = tempfile.mkstemp(dir=self.log_path.parent, prefix=".rssi-")
    try:
      with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"source": "comma", "runs": self.runs}, f)
      os.replace(temp, self.log_path)
    finally:
      with suppress(FileNotFoundError):
        os.unlink(temp)

  async def capture(self, current, ready):
    try:
      with diagnostic_priority() as requested:
        if requested:
          await asyncio.sleep(.6)
        await self.scanner(current, self.is_parked, ready)
      self.runs.append(current.row())
      self.runs = [row for i, row in enumerate(self.runs)
                   if sum(future[0] == row[0] for future in self.runs[i:]) <= 3]
      self.save()
    except Exception:
      self.error = "capture_failed"
      if not ready.done():
        ready.set_result(False)
    finally:
      self.active = None
      if not ready.done():
        ready.set_result(False)

  def authorize(self, request):
    supplied = request.headers.get("Authorization", "")
    if not supplied.isascii() or not hmac.compare_digest(supplied, "Bearer " + self.token):
      raise web.HTTPUnauthorized()

  async def start(self, request):
    self.authorize(request)
    body, status = await self.begin(request.match_info["stage"], request.match_info["service"])
    return web.json_response(body, status=status)

  async def begin(self, stage, service):
    if not self.is_parked():
      if isinstance(self.is_parked, IgnitionGuard):
        print(f"Wayon RSSI capture refused ({self.is_parked.reason})", flush=True)
      return {"error": "ignition_not_confirmed_off"}, 409
    if self.active is not None or self.system_probe_active:
      return {"error": "busy"}, 409
    try:
      if stage not in STAGES or not isinstance(service, str) or str(UUID(service, version=4)) != service:
        raise ValueError()
    except ValueError:
      return {"error": "invalid_capture"}, 400
    if self.limited:
      now = self.clock()
      while self.starts and now - self.starts[0] >= 300:
        self.starts.popleft()
      if len(self.starts) >= 6 or (self.starts and now - self.starts[-1] < 2):
        return {"error": "rate_limited"}, 429
      self.starts.append(now)
    self.error = None
    current = Capture(stage, service)
    self.active = current
    ready = asyncio.get_running_loop().create_future()
    self.task = asyncio.create_task(self.capture(current, ready))
    try:
      started = await asyncio.wait_for(asyncio.shield(ready), 6)
    except asyncio.TimeoutError:
      await self.close(None)
      started = False
    if started is False:
      return {"error": "scan_unavailable"}, 503
    return {"source": "comma"}, 200

  async def system_phone(self):
    if not self.is_parked():
      return {"error": "ignition_not_confirmed_off"}, 409
    if self.active is not None or self.system_probe_active:
      return {"error": "busy"}, 409
    if self.clock() - self.system_probe_at < 6:
      return {"error": "rate_limited"}, 429
    try:
      from comma_system_phone import PhoneNotSeen, phone_rssi
    except ImportError:
      return {"error": "receiver_unavailable"}, 503
    self.system_probe_active = True
    self.system_probe_at = self.clock()
    try:
      with diagnostic_priority() as owned:
        if not owned:
          return {"error": "busy"}, 409
        value = await phone_rssi(SYSTEM_PHONE, self.is_parked)
    except PhoneNotSeen:
      return {"error": "phone_not_seen"}, 409
    except (OSError, ValueError, RuntimeError, TimeoutError):
      return {"error": "receiver_unavailable"}, 503
    finally:
      self.system_probe_active = False
    return {"source": "comma", "linkRssi": value}, 200

  async def snapshot(self, request):
    self.authorize(request)
    return web.json_response(self.snapshot_data(), headers={"Cache-Control": "no-store"})

  def snapshot_data(self):
    active = self.active
    return {
      "source": "comma", "runs": self.runs, "error": self.error,
      "active": None if active is None else {
        "stage": active.stage, "elapsed": active.elapsed(), "samples": active.series(), "received": len(active.samples),
      },
    }

  async def close(self, _app):
    if self.task is not None and not self.task.done():
      self.error = "capture_cancelled"
      self.task.cancel()
      with suppress(asyncio.CancelledError):
        await self.task

  def app(self):
    app = web.Application(client_max_size=1024)
    app.router.add_get("/snapshot", self.snapshot, allow_head=False)
    app.router.add_post("/capture/{stage}/{service}", self.start)
    app.on_cleanup.append(self.close)
    return app


def tls(ip, directory):
  cert, key, config = (directory / name for name in ("cert.pem", "key.pem", "openssl.cnf"))
  config.write_text(
    "[req]\nprompt=no\ndistinguished_name=dn\nx509_extensions=ext\n"
    f"[dn]\nCN=Comma RSSI calibration\n[ext]\nsubjectAltName=IP:{ip}\n",
    encoding="ascii",
  )
  subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                  "-config", str(config), "-out", str(cert), "-keyout", str(key)],
                 check=True, capture_output=True, timeout=15)
  context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
  context.minimum_version = ssl.TLSVersion.TLSv1_2
  context.load_cert_chain(cert, key)
  return context, sha256(ssl.PEM_cert_to_DER_cert(cert.read_text(encoding="ascii"))).hexdigest()


async def run(args):
  if not parked():
    raise RuntimeError("Vehicle is not offroad")
  token = secrets.token_urlsafe(18)
  receiver = Receiver(token, args.log)
  with tempfile.TemporaryDirectory(prefix="comma-rssi-") as temp:
    context, pin = tls(args.bind, Path(temp))
    runner = web.AppRunner(receiver.app(), access_log=None, handle_signals=True)
    await runner.setup()
    try:
      await web.TCPSite(runner, args.bind, args.port, ssl_context=context).start()
      print(f"{args.bind}:{args.port}|{pin}|{token}", flush=True)
      await asyncio.sleep(args.seconds)
    finally:
      await runner.cleanup()


async def pair_wayon(receiver, command, directory=None):
  if not receiver.is_parked():
    return {"error": "ignition_on"}, 409
  try:
    from wayon_door_pair import PAIR_DIRECTORY, InvalidSignature, authorize, enroll
  except ImportError:
    return {"error": "receiver_unavailable"}, 503
  directory = PAIR_DIRECTORY if directory is None else directory
  try:
    key = await asyncio.to_thread(authorize, directory, command)
  except InvalidSignature:
    return {"error": "phone_not_approved"}, 403
  except (ValueError, OSError):
    return {"error": "receiver_unavailable"}, 503
  if not receiver.is_parked():
    return {"error": "ignition_on"}, 409
  try:
    if not enroll(directory, key):
      return {"error": "phone_already_registered"}, 409
  except (ValueError, OSError):
    return {"error": "receiver_unavailable"}, 503
  return {"source": "comma"}, 200


async def reply_wayon(ws, receiver, command):
  if not isinstance(command, dict):
    return
  try:
    request_id = command["id"]
    if not isinstance(request_id, str) or str(UUID(request_id, version=4)) != request_id:
      return
  except (KeyError, ValueError):
    return
  if command.get("op") == "capture":
    body, status = await receiver.begin(command.get("stage"), command.get("service"))
  elif command.get("op") == "snapshot":
    body, status = receiver.snapshot_data(), 200
  elif command.get("op") == "pair":
    body, status = await pair_wayon(receiver, command)
  elif command.get("op") == "system_phone":
    body, status = await receiver.system_phone()
  elif command.get("op") in ("link", "link_thresholds"):
    try:
      import system_phone_settings as settings
      if command["op"] == "link":
        body, status = settings.snapshot(parked=receiver.is_parked()), 200
      else:
        body, status = settings.update(command, receiver.is_parked)
    except (ImportError, OSError, ValueError):
      body, status = {"error": "receiver_unavailable"}, 503
  else:
    return
  await ws.send_json({"id": request_id, "status": status, "body": body})


async def connected_wayon(ws, receiver):
  tasks = set()

  async def reply(command):
    with suppress(ConnectionError, RuntimeError):
      await reply_wayon(ws, receiver, command)

  try:
    async for message in ws:
      if message.type != WSMsgType.TEXT or len(tasks) >= 8:
        continue
      try:
        command = json.loads(message.data)
      except ValueError:
        continue
      task = asyncio.create_task(reply(command))
      tasks.add(task)
      task.add_done_callback(tasks.discard)
  finally:
    for task in tasks:
      task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await receiver.close(None)


async def run_wayon(token, log_path):
  from openpilot.cereal import messaging

  asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, asyncio.current_task().cancel)
  sock = messaging.sub_sock("pandaStates", conflate=True)
  guard = IgnitionGuard(lambda: messaging.recv_one_or_none(sock))
  receiver = Receiver(token, log_path, guard, limited=True)
  watcher = asyncio.create_task(guard.watch())
  try:
    async with ClientSession(timeout=ClientTimeout(total=12, connect=8)) as session:
      backoff = 5
      while True:
        try:
          async with session.ws_connect(WAYON_WS, headers={"Authorization": "Bearer " + token},
                                        heartbeat=30, max_msg_size=1024) as ws:
            backoff = 5
            await connected_wayon(ws, receiver)
        except (ClientError, OSError, asyncio.TimeoutError) as error:
          print(f"Wayon RSSI relay disconnected ({type(error).__name__})", flush=True)
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, 60)
  finally:
    watcher.cancel()
    await asyncio.gather(watcher, return_exceptions=True)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  mode = parser.add_mutually_exclusive_group(required=True)
  mode.add_argument("--bind", help="exact private IPv4 address of Comma for a temporary receiver")
  mode.add_argument("--wayon-token-file", type=Path, help="private credential for the outbound Wayon relay")
  parser.add_argument("--port", type=int, default=8765)
  parser.add_argument("--seconds", type=int, default=600)
  parser.add_argument("--log", type=Path)
  args = parser.parse_args()
  if args.wayon_token_file is not None:
    try:
      if args.wayon_token_file.stat().st_mode & 0o077:
        raise ValueError()
      token = args.wayon_token_file.read_text(encoding="ascii").strip()
      if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        raise ValueError()
    except (OSError, ValueError):
      parser.error("Use a private Wayon receiver credential file")
    with suppress(asyncio.CancelledError):
      asyncio.run(run_wayon(token, args.log))
    return
  try:
    ip = ipaddress.IPv4Address(args.bind)
    private = any(ip in ipaddress.ip_network(net) for net in
                  ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10"))
    if not private or not (1024 <= args.port <= 65535 and 60 <= args.seconds <= 900):
      raise ValueError()
  except ValueError:
    parser.error("Use a private IPv4 bind address, port 1024-65535 and duration 60-900 seconds")
  if args.log is None or args.log.exists() or not args.log.parent.is_dir():
    parser.error("Use a new log file inside an existing private directory")
  asyncio.run(run(args))


if __name__ == "__main__":
  main()
