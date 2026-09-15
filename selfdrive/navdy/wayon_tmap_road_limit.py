"""Read a fresh TMAP road limit relayed by Navdy's existing road preview."""

import json
import math
import time


PREVIEW_PATH = "/dev/shm/wayon_tmap_preview.json"


def set_target_kph(current_kph: float, road_limit_kph: int) -> float:
  if current_kph >= road_limit_kph:
    return current_kph
  return 35 if road_limit_kph == 30 else road_limit_kph + 10


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
