"""Observe or execute authenticated parked door proximity transitions on Comma."""

import argparse
import asyncio
from contextlib import suppress
import os
from pathlib import Path
import secrets
import stat
import sys
import time

from jeepney import DBusAddress, HeaderFields, MatchRule
from jeepney.io.asyncio import open_dbus_router
from jeepney.wrappers import DBusErrorResponse

from comma_rssi_receiver import (
  ADAPTER, DBUS, DEVICE, OBJECTS, PROPS, IgnitionGuard, adapter_path, boot_time_ns, call, diagnostic_waiting,
)
from door_proximity import SERVICE_UUID, Policy, authenticate
from gmone_door_control import (
  PRIVATE_DIR, DoorObservation, c4_panda_message, one_request, private_directory, read_credentials,
  run_command, send_command, vehicle_check,
)


def read_sample(key, properties, wall):
  if "RSSI" not in properties or "ServiceData" not in properties:
    return None
  rssi_type, dbm = properties["RSSI"]
  data_type, data = properties["ServiceData"]
  if rssi_type != "n" or type(dbm) is not int or not -127 <= dbm <= -1 or data_type != "a{sv}":
    return None
  variant = data.get(SERVICE_UUID)
  if variant is None or variant[0] != "ay":
    return None
  beacon = authenticate(key, bytes(variant[1]), wall)
  return (beacon, dbm) if beacon is not None else None


def properties_for(message, owner, adapter):
  header = message.header.fields
  if header.get(HeaderFields.sender) != owner:
    return None
  interface = header.get(HeaderFields.interface)
  member = header.get(HeaderFields.member)
  if interface == OBJECTS and member == "InterfacesAdded":
    path, interfaces = message.body
    props = interfaces.get(DEVICE, {})
  elif interface == PROPS and member == "PropertiesChanged" and message.body[0] == DEVICE:
    path, props = header[HeaderFields.path], message.body[1]
  else:
    return None
  return props if path.startswith(adapter + "/dev_") else None


def pair_file():
  PRIVATE_DIR.mkdir(mode=0o700, exist_ok=True)
  private_directory(PRIVATE_DIR)
  path = PRIVATE_DIR / "proximity.key"
  if not sys.stdin.isatty() or not sys.stdout.isatty():
    raise ValueError("pairing requires a private terminal")
  fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
  with os.fdopen(fd, "w", encoding="ascii") as stream:
    key = secrets.token_hex(32)
    stream.write(key + "\n")
    stream.flush()
    os.fsync(stream.fileno())
  print(key)


def read_key():
  private_directory(PRIVATE_DIR)
  fd = os.open(PRIVATE_DIR / "proximity.key", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  with os.fdopen(fd, "rb") as stream:
    info = os.fstat(stream.fileno())
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
      raise ValueError("invalid proximity key file")
    raw = stream.read(66)
  if len(raw) != 65 or not raw.endswith(b"\n"):
    raise ValueError("invalid proximity key")
  value = bytes.fromhex(raw[:-1].decode("ascii"))
  if len(value) != 32:
    raise ValueError("invalid proximity key")
  return value


class CarObservations:
  def __init__(self, messaging):
    self.messaging = messaging
    self.panda = messaging.sub_sock("pandaStates", conflate=True)
    self.ignition = IgnitionGuard(lambda: c4_panda_message(messaging.recv_one_or_none(self.panda)))
    self.can = None
    self.doors = DoorObservation()

  def parked(self):
    ok = self.ignition()
    if not ok and self.can is not None:
      self.can = None
      self.doors = DoorObservation()
    return ok

  def doors_closed(self):
    if self.can is None:
      self.can = self.messaging.sub_sock("can", conflate=False)
    for _ in range(48):
      event = self.messaging.recv_one_or_none(self.can)
      if event is None:
        return self.doors.confirmed(boot_time_ns())
      self.doors.update(event, boot_time_ns())
    return False


def dispatch(command, live, deadline):
  if not live:
    return "dry_run"
  def check(action):
    if time.monotonic() >= deadline or diagnostic_waiting():
      return "observation_expired"
    reason = vehicle_check(action, require_closed=True)
    return "observation_expired" if time.monotonic() >= deadline or diagnostic_waiting() else reason

  try:
    with one_request(PRIVATE_DIR):
      return run_command(command, True, check=check,
                         credentials=lambda: read_credentials(PRIVATE_DIR), send=send_command).state
  except (OSError, ValueError, RuntimeError):
    return "command_unavailable"


async def scan_session(car, key, policy, live):
  if not car.parked() or diagnostic_waiting():
    return
  async with open_dbus_router("SYSTEM") as router:
    owner, = await call(router, DBUS, "GetNameOwner", "s", ("org.bluez",))
    objects, = await call(router, DBusAddress("/", bus_name=owner, interface=OBJECTS), "GetManagedObjects")
    path = adapter_path(objects)
    if objects[path][ADAPTER].get("Discovering") == ("b", True):
      return
    adapter = DBusAddress(path, bus_name=owner, interface=ADAPTER)
    for interface, member in ((PROPS, "PropertiesChanged"), (OBJECTS, "InterfacesAdded")):
      match = MatchRule(type="signal", sender=owner, interface=interface, member=member)
      await call(router, DBUS, "AddMatch", "s", (match.serialise(),))
    with router.filter(MatchRule(type="signal", sender=owner), bufsize=128) as queue:
      await call(router, adapter, "SetDiscoveryFilter", "a{sv}",
                 ({"Transport": ("s", "le"), "UUIDs": ("as", [SERVICE_UUID]), "DuplicateData": ("b", True)},))
      if not car.parked() or diagnostic_waiting():
        return
      command_task = None
      try:
        await call(router, adapter, "StartDiscovery")
        while car.parked() and not diagnostic_waiting():
          now = time.monotonic()
          policy.expire(now, True)
          closed = car.doors_closed()
          if command_task is not None and command_task.done():
            print("door proximity command:", command_task.result(), flush=True)
            command_task = None
          try:
            message = await asyncio.wait_for(queue.get(), .2)
          except asyncio.TimeoutError:
            continue
          if not car.parked() or diagnostic_waiting():
            break
          data = properties_for(message, owner, path)
          if data is None:
            continue
          sample = read_sample(key, data, time.time())
          if sample is None:
            continue
          beacon, dbm = sample
          command = policy.update(beacon, dbm, time.monotonic(), parked=True, closed=closed, ready=command_task is None)
          if command is not None:
            print("door proximity transition:", command.name, flush=True)
            command_task = asyncio.create_task(asyncio.to_thread(dispatch, command, live, time.monotonic() + 2.5))
      finally:
        policy.invalidate()
        with suppress(Exception):
          await call(router, adapter, "StopDiscovery")
        if command_task is not None:
          print("door proximity command:", await command_task, flush=True)


async def monitor(key, live):
  from openpilot.cereal import car, messaging

  with car.CarParams.from_bytes(Path("/data/params/d/CarParamsPersistent").read_bytes()) as params:
    if params.carFingerprint != "CHEVROLET_TRAVERSE":
      raise ValueError("unsupported vehicle")
  observed = CarObservations(messaging)
  policy = Policy()
  while True:
    try:
      await scan_session(observed, key, policy, live)
    except (OSError, RuntimeError, asyncio.TimeoutError, DBusErrorResponse) as error:
      print("proximity scanner unavailable:", type(error).__name__, flush=True)
    await asyncio.sleep(2)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("mode", choices=("pair", "monitor"))
  parser.add_argument("--execute", action="store_true", help="allow guarded real door requests; default is dry-run")
  args = parser.parse_args()
  try:
    if args.mode == "pair":
      if args.execute:
        parser.error("execution is not a pairing option")
      pair_file()
    else:
      asyncio.run(monitor(read_key(), args.execute))
  except (ValueError, OSError, RuntimeError, ImportError):
    parser.exit(2, "proximity monitor unavailable\n")
  except KeyboardInterrupt:
    pass


if __name__ == "__main__":
  main()
