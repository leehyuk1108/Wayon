"""Parked, explicit Multipack door commands for the local Comma operator."""

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
import fcntl
from getpass import getpass
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import time
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


ENDPOINT = "https://mp.gmone.co.kr/api"
PRIVATE_DIR = Path("/data/wayon-door")
MAX_FILE_BYTES = 4096
SENSOR_MAX_AGE_NS = 1_000_000_000


class DoorCommand(Enum):
  LOCK = "DOOR_LOCK"
  UNLOCK = "DOOR_UNLOCK"


@dataclass(frozen=True, repr=False)
class Credentials:
  account: str
  key: str

  @classmethod
  def from_values(cls, account, key):
    if (not isinstance(account, str) or not re.fullmatch(r"[^\s@]{1,128}@[^\s@]{1,128}", account, re.ASCII)
        or not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_+/=-]{20,512}", key)):
      raise ValueError("invalid credential format")
    return cls(account, key)


def private_directory(path):
  info = path.lstat()
  if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
    raise ValueError("credential directory must be owned by the operator with mode 0700")


def read_credentials(directory):
  private_directory(directory)
  fd = os.open(directory / "multipack.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  with os.fdopen(fd, "rb") as stream:
    info = os.fstat(stream.fileno())
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
      raise ValueError("credential file must be owned by the operator with mode 0600")
    data = stream.read(MAX_FILE_BYTES + 1)
  if len(data) > MAX_FILE_BYTES:
    raise ValueError("credential file is too large")
  value = json.loads(data)
  if not isinstance(value, dict):
    raise ValueError("invalid credential file")
  return Credentials.from_values(value.get("account"), value.get("key"))


def provision(directory, credentials):
  directory.mkdir(mode=0o700, exist_ok=True)
  private_directory(directory)
  fd, path = tempfile.mkstemp(dir=directory, prefix=".multipack-")
  temporary = Path(path)
  try:
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
      json.dump({"account": credentials.account, "key": credentials.key}, stream)
      stream.flush()
      os.fsync(stream.fileno())
    os.replace(temporary, directory / "multipack.json")
  finally:
    temporary.unlink(missing_ok=True)


@contextmanager
def one_request(directory):
  private_directory(directory)
  fd = os.open(directory / "request.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
  try:
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
      raise ValueError("invalid request lock")
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    yield
  finally:
    os.close(fd)


class NoRedirect(HTTPRedirectHandler):
  def redirect_request(self, req, fp, code, msg, headers, newurl):
    return None


@dataclass(frozen=True)
class Result:
  state: str
  status: int | None = None


def send_command(command: DoorCommand, credentials: Credentials, *, opener=None) -> Result:
  if not isinstance(command, DoorCommand):
    raise ValueError("only lock and unlock are supported")
  if opener is None:
    opener = build_opener(ProxyHandler({}), NoRedirect())
  query = urlencode({"id": credentials.account, "key": credentials.key, "cmd": command.value})
  request = Request(f"{ENDPOINT}?{query}", method="GET",
                    headers={"Accept": "application/json", "Cache-Control": "no-store", "User-Agent": "WayonDoor/1.0"})
  try:
    with opener.open(request, timeout=8) as response:
      status = response.status
  except HTTPError as error:
    status = error.code
    error.close()
  except (OSError, URLError, HTTPException):
    # A timeout may occur after the service received the request. Never retry it here.
    return Result("unknown")
  if 200 <= status < 300:
    return Result("http_response", status)
  return Result("not_confirmed", status)


class DoorObservation:
  """Read-only 2022-23 Traverse BCM door switch state, never a command."""

  def __init__(self):
    self.sample_ns = None
    self.closed = None

  def update(self, event, now_ns):
    if not event.valid:
      self.closed = None
      return
    stamp = event.logMonoTime
    if not 0 <= now_ns - stamp <= SENSOR_MAX_AGE_NS or (self.sample_ns is not None and stamp < self.sample_ns):
      return
    for frame in event.can:
      if frame.src == 0 and frame.address == 0x12A:
        data = frame.dat
        self.sample_ns = stamp
        self.closed = None if len(data) != 8 else not (data[1] & 0x07 or data[2] & 0x80)

  def confirmed(self, now_ns):
    return self.closed is True and self.sample_ns is not None and 0 <= now_ns - self.sample_ns <= SENSOR_MAX_AGE_NS


def c4_panda_message(message):
  if message is None:
    return None
  # This tool targets one built-in C4 Panda, with two separate ignition signals.
  if len(message.pandaStates) == 1 and message.pandaStates[0].pandaType == "cuatro":
    return message
  return SimpleNamespace(valid=False)


def wait_for_vehicle(ignition, receive_can, clock_ns, monotonic=time.monotonic, sleep=time.sleep):
  doors = DoorObservation()
  deadline = monotonic() + 2
  while monotonic() < deadline:
    drained = True
    if receive_can is not None:
      for _ in range(24):
        message = receive_can()
        if message is None:
          break
        doors.update(message, clock_ns())
      else:
        drained = False
    parked = ignition()
    if ignition.reason in ("ignition_on", "not_offroad"):
      return "ignition_not_confirmed_off"
    if parked and drained and (receive_can is None or doors.confirmed(clock_ns())):
      return None
    sleep(.025)
  return "door_closed_not_confirmed" if ignition() else "ignition_not_confirmed_off"


def vehicle_check(command, *, require_closed=None):
  from comma_rssi_receiver import IgnitionGuard, boot_time_ns
  from openpilot.cereal import car, messaging

  try:
    with car.CarParams.from_bytes(Path("/data/params/d/CarParamsPersistent").read_bytes()) as params:
      if params.carFingerprint != "CHEVROLET_TRAVERSE":
        return "vehicle_not_confirmed"
  except Exception:
    return "vehicle_not_confirmed"
  panda = messaging.sub_sock("pandaStates", conflate=True)
  ignition = IgnitionGuard(lambda: c4_panda_message(messaging.recv_one_or_none(panda)))
  if require_closed is None:
    require_closed = command is DoorCommand.LOCK
  can = messaging.sub_sock("can", conflate=False) if require_closed else None
  return wait_for_vehicle(ignition, None if can is None else lambda: messaging.recv_one_or_none(can), boot_time_ns)


def run_command(command, execute, *, check, credentials, send):
  reason = check(command)
  if reason is not None:
    return Result(reason)
  if not execute:
    return Result("dry_run")
  secret = credentials()
  reason = check(command)
  if reason is not None:
    return Result(reason)
  return send(command, secret)


def main(argv=None):
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("action", choices=("lock", "unlock", "provision"))
  parser.add_argument("--execute", action="store_true", help="send one real command instead of a dry run")
  args = parser.parse_args(argv)
  if args.action == "provision":
    if args.execute or not sys.stdin.isatty():
      parser.error("provision requires a private interactive terminal")
    try:
      credentials = Credentials.from_values(getpass("Multipack account: "), getpass("New Multipack key: "))
      provision(PRIVATE_DIR, credentials)
    except (OSError, ValueError, EOFError):
      parser.exit(2, "credential setup failed\n")
    print("credential saved")
    return 0

  command = DoorCommand[args.action.upper()]
  try:
    if args.execute:
      with one_request(PRIVATE_DIR):
        result = run_command(command, True, check=vehicle_check,
                             credentials=lambda: read_credentials(PRIVATE_DIR), send=send_command)
    else:
      result = run_command(command, False, check=vehicle_check, credentials=None, send=None)
  except (OSError, ValueError, RuntimeError, ImportError):
    parser.exit(2, "door command unavailable; no retry performed\n")
  if result.status is None:
    print(result.state)
  else:
    print(f"{result.state}: HTTP {result.status}; physical door state not verified")
  return 0 if result.state in ("dry_run", "http_response") else 1


if __name__ == "__main__":
  sys.exit(main())
