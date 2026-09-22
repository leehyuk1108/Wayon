"""Fresh, atomic ONNX observation state shared with the Navdy bridge."""

import json
import math
import os
import time
from pathlib import Path


STATE_PATH = Path("/dev/shm/wayon_onnx_vision.json")
LANE_MAX_AGE_SEC = 1.25
LANE_KEYS = ("navLaneLeftType", "navLaneRightType")
VALID_TYPES = frozenset(("solid", "dashed"))


def lane_markings(data: dict, now: float | None = None) -> dict[str, str]:
  now = time.monotonic() if now is None else now
  markings = dict.fromkeys(LANE_KEYS, "unknown")
  try:
    updated_at = float(data.get("laneUpdatedAtMonotonic", 0.0))
  except (TypeError, ValueError):
    return markings
  if not math.isfinite(updated_at) or updated_at <= 0.0 or now < updated_at or now - updated_at > LANE_MAX_AGE_SEC:
    return markings
  for key, source_key in (("navLaneLeftType", "leftType"), ("navLaneRightType", "rightType")):
    value = data.get(source_key)
    if value in VALID_TYPES:
      markings[key] = value
  return markings


def read_state(path: Path = STATE_PATH) -> dict:
  try:
    with path.open(encoding="utf-8") as state_file:
      data = json.load(state_file)
    return data if isinstance(data, dict) else {}
  except (OSError, ValueError):
    return {}


def write_state(data: dict, path: Path = STATE_PATH) -> None:
  temp_path = path.with_suffix(path.suffix + ".tmp")
  try:
    with temp_path.open("w", encoding="utf-8") as state_file:
      json.dump(data, state_file, separators=(",", ":"))
    os.replace(temp_path, path)
  except OSError:
    try:
      temp_path.unlink()
    except OSError:
      pass


class OnnxLaneMarkingReader:
  def __init__(self, path: Path = STATE_PATH):
    self.path = path
    self.active = False

  def is_alive(self) -> bool:
    return True

  def set_active(self, active: bool) -> None:
    self.active = active

  def submit(self, *_args) -> None:
    pass

  def snapshot(self, now: float | None = None) -> dict[str, str]:
    if not self.active:
      return lane_markings({}, now)
    return lane_markings(read_state(self.path), now)
