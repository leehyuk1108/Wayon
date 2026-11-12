"""Authenticated proximity observations and fail-closed door transition policy."""

from dataclasses import dataclass
from hashlib import sha256
import hmac
import struct

from gmone_door_control import DoorCommand


SERVICE_UUID = "96d6e580-8c17-4c6e-bd09-44cc97e952c2"
SLOT_SECONDS = 4
PACKET_BYTES = 13
DOMAIN = b"wayon-door-ble-v1\0"
MIN_GAP_DB = 8
SAMPLE_GAP = 2.5
COOLDOWN = 12.0


@dataclass(frozen=True)
class Beacon:
  slot: int
  near: int
  far: int


def thresholds_valid(near, far):
  return -127 <= near <= -1 and -127 <= far <= -1 and near - far >= MIN_GAP_DB


def encode(key, beacon):
  if len(key) != 32 or beacon.slot < 0 or not thresholds_valid(beacon.near, beacon.far):
    raise ValueError("invalid beacon configuration")
  profile = struct.pack(">bbB", beacon.near, beacon.far, 0)
  mac = hmac.new(key, DOMAIN + struct.pack(">Q", beacon.slot) + profile, sha256).digest()[:8]
  return struct.pack(">H", beacon.slot & 0xFFFF) + profile + mac


def authenticate(key, packet, wall_seconds):
  if len(key) != 32 or len(packet) != PACKET_BYTES or wall_seconds < SLOT_SECONDS:
    return None
  low, near, far, flags = struct.unpack(">HbbB", packet[:5])
  if flags != 0 or not thresholds_valid(near, far):
    return None
  current = int(wall_seconds) // SLOT_SECONDS
  for slot in (current, current - 1):
    if slot & 0xFFFF == low:
      beacon = Beacon(slot, near, far)
      return beacon if hmac.compare_digest(packet, encode(key, beacon)) else None
  return None


class Policy:
  def __init__(self):
    self.profile = None
    self.last_at = None
    self.last_slot = -1
    self.stable = None
    self.candidate = None
    self.last_action = float("-inf")

  def invalidate(self):
    self.profile = None
    self.last_at = None
    self.stable = None
    self.candidate = None

  def expire(self, now, parked):
    if not parked or (self.last_at is not None and not 0 <= now - self.last_at <= SAMPLE_GAP):
      self.invalidate()

  def update(self, beacon, dbm, now, *, parked, closed, ready=True):
    self.expire(now, parked)
    if not parked or not -127 <= dbm <= -1 or beacon.slot < self.last_slot:
      return None
    if self.last_at is not None and now - self.last_at < .15:
      return None
    profile = (beacon.near, beacon.far)
    if self.profile != profile:
      self.invalidate()
      self.profile = profile
    self.last_at, self.last_slot = now, beacon.slot

    band = "near" if dbm >= beacon.near else "far" if dbm <= beacon.far else None
    if band is None or band == self.stable:
      self.candidate = None
      return None
    if self.candidate is None or self.candidate[0] != band:
      self.candidate = (band, now, beacon.slot, 1)
      return None
    _, started, first_slot, count = self.candidate
    self.candidate = (band, started, first_slot, count + 1)
    if count < 2 or beacon.slot == first_slot or now - started < (3 if band == "near" else 5):
      return None

    if self.stable is None:
      self.stable, self.candidate = band, None
      return None

    # Preserve a qualified departure through a busy sender, cooldown or an
    # open door, but only while the fresh far readings continue.
    if band == "far" and (not closed or not ready or now - self.last_action < COOLDOWN):
      return None
    self.stable, self.candidate = band, None
    if not closed or not ready or now - self.last_action < COOLDOWN:
      return None
    self.last_action = now
    return DoorCommand.LOCK if band == "far" else DoorCommand.UNLOCK
