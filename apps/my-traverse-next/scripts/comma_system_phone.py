"""Read the configured phone's Bluetooth Classic link RSSI, not a door command."""

import asyncio
from contextlib import suppress
import os
import re
import socket
import stat
from statistics import median


class PhoneNotSeen(Exception):
  pass


def configured_address(path):
  fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  with os.fdopen(fd, "rb") as f:
    info = os.fstat(f.fileno())
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o600:
      raise ValueError("invalid system phone configuration")
    address = f.read(32).strip().decode("ascii")
  if not re.fullmatch(r"[0-9A-F]{2}(?::[0-9A-F]{2}){5}", address) or address in (
      "00:00:00:00:00:00", "02:00:00:00:00:00", "FF:FF:FF:FF:FF:FF"):
    raise ValueError("invalid system phone address")
  return address


def parse_link_rssi(output):
  match = re.fullmatch(rb"RSSI return value:\s*(-?\d+)\s*", output)
  if match:
    value = int(match[1])
    if -128 <= value <= 126:
      return value
  return None


async def read_link_rssi(address):
  proc = await asyncio.create_subprocess_exec("/usr/bin/hcitool", "rssi", address,
                                              stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
  try:
    output, _ = await asyncio.wait_for(proc.communicate(), 1)
    return parse_link_rssi(output) if proc.returncode == 0 else None
  finally:
    if proc.returncode is None:
      with suppress(ProcessLookupError):
        proc.kill()
      await proc.wait()


async def phone_rssi(path, is_parked):
  address = configured_address(path)
  if not is_parked():
    raise RuntimeError("ignition off not confirmed")
  with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP) as link:
    link.setblocking(False)
    try:
      await asyncio.wait_for(asyncio.get_running_loop().sock_connect(link, (address, 1)), 4)
    except (OSError, TimeoutError) as exc:
      raise PhoneNotSeen() from exc
    samples = []
    for attempt in range(3):
      if not is_parked():
        raise RuntimeError("ignition off not confirmed")
      try:
        value = await read_link_rssi(address)
      except TimeoutError:
        value = None
      if value is not None:
        samples.append(value)
      if attempt < 2:
        await asyncio.sleep(.25)
    if not is_parked():
      raise RuntimeError("ignition off not confirmed")
  if not samples:
    raise PhoneNotSeen()
  return int(median(samples))
