"""Shared ONNX lane-marking state produced and consumed on comma."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass


LANE_MARKING_STATE_PATH = "/dev/shm/onnx_lane_marking_state.json"
LANE_MARKING_MAX_AGE_SEC = 1.25
LANE_MARKING_READ_INTERVAL_SEC = 0.1


def _finite(value: object, default: float = 0.0) -> float:
  try:
    value = float(value)  # type: ignore[arg-type]
  except (TypeError, ValueError):
    return default
  return value if math.isfinite(value) else default


@dataclass(frozen=True)
class LaneBoundaryState:
  left_type: str = "unknown"
  right_type: str = "unknown"


class LaneBoundaryStateReader:
  def __init__(self, path: str = LANE_MARKING_STATE_PATH):
    self.path = path
    self.last_read_at = 0.0
    self.state = LaneBoundaryState()

  def read(self, now: float | None = None) -> LaneBoundaryState:
    now = time.monotonic() if now is None else now
    if now - self.last_read_at < LANE_MARKING_READ_INTERVAL_SEC:
      return self.state
    self.last_read_at = now

    try:
      with open(self.path, encoding="utf-8") as state_file:
        data = json.load(state_file)
      updated_at = _finite(data.get("updatedAtMonotonic"), -math.inf)
      if updated_at <= 0.0 or now < updated_at or now - updated_at > LANE_MARKING_MAX_AGE_SEC:
        self.state = LaneBoundaryState()
        return self.state
      self.state = LaneBoundaryState(
        left_type=str(data.get("leftType", "unknown")),
        right_type=str(data.get("rightType", "unknown")),
      )
    except (OSError, AttributeError, TypeError, ValueError, json.JSONDecodeError):
      self.state = LaneBoundaryState()
    return self.state
