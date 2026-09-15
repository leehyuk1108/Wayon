"""Read a fresh TMAP road limit relayed by Navdy's existing road preview."""

import json
import math
import os
import time


PREVIEW_PATH = "/dev/shm/wayon_tmap_road_limit.json"


def set_target_kph(current_kph: float, road_limit_kph: int) -> float:
  if current_kph >= road_limit_kph:
    return current_kph
  return 35 if road_limit_kph == 30 else road_limit_kph + 10


class RoadLimitFeedback:
  def __init__(self, path: str = PREVIEW_PATH):
    self.path = path
    self.last_identity: tuple[str, int] | None = None

  def clear(self) -> None:
    try:
      os.unlink(self.path)
    except OSError:
      pass

  def accept(self, feedback: object, onroad: bool, now: float | None = None) -> bool:
    if not onroad or not isinstance(feedback, dict):
      self.clear()
      return False
    packet = feedback.get("roadPreview")
    if not isinstance(packet, dict) or packet.get("version") != 1:
      self.clear()
      return False
    session = packet.get("session")
    sequence = packet.get("sequence")
    age = packet.get("ageMs")
    limit = packet.get("roadLimitKph")
    if (not isinstance(session, str) or len(session) != 36 or
        not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0 or
        not isinstance(age, (int, float)) or isinstance(age, bool) or
        not math.isfinite(age) or not 0 <= age <= 4000 or
        not isinstance(limit, int) or isinstance(limit, bool) or
        not 10 <= limit <= 200 or limit % 10 != 0):
      self.clear()
      return False
    identity = (session, sequence)
    if self.last_identity is not None and session == self.last_identity[0] and sequence <= self.last_identity[1]:
      return False
    now = time.monotonic() if now is None else now
    state = {"onroad": True, "monotonic": now,
             "packetAgeMs": age, "roadLimitKph": limit}
    try:
      temporary = self.path + ".tmp"
      with open(temporary, "w", encoding="utf-8") as stream:
        json.dump(state, stream, separators=(",", ":"), allow_nan=False)
      os.replace(temporary, self.path)
    except OSError:
      return False
    self.last_identity = identity
    return True


def read_road_limit_kph(path: str = PREVIEW_PATH, now: float | None = None) -> int | None:
  now = time.monotonic() if now is None else now
  try:
    with open(path, encoding="utf-8") as stream:
      preview = json.load(stream)
  except (OSError, ValueError, TypeError):
    return None

  if not isinstance(preview, dict) or preview.get("onroad") is not True:
    return None
  received_at = preview.get("monotonic")
  packet_age_ms = preview.get("packetAgeMs")
  limit = preview.get("roadLimitKph")
  if (not isinstance(received_at, (int, float)) or isinstance(received_at, bool) or
      not math.isfinite(received_at) or not 0 <= now - received_at <= 2.0 or
      not isinstance(packet_age_ms, (int, float)) or isinstance(packet_age_ms, bool) or
      not math.isfinite(packet_age_ms) or not 0 <= packet_age_ms or
      packet_age_ms + (now - received_at) * 1000 > 4000 or
      not isinstance(limit, int) or isinstance(limit, bool) or
      not 10 <= limit <= 200 or limit % 10 != 0):
    return None
  return limit
