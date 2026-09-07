"""Shared ONNX lane-marking state produced and consumed on comma."""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from typing import Any


LANE_MARKING_STATE_PATH = "/dev/shm/onnx_lane_marking_state.json"
LANE_MARKING_MAX_AGE_SEC = 1.25
LANE_MARKING_READ_INTERVAL_SEC = 0.1
BLINDSPOT_STATE_PATH = "/dev/shm/onnx_blindspot_state.json"
BLINDSPOT_MAX_AGE_SEC = 1.5


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


@dataclass(frozen=True)
class BlindspotState:
  left: bool = False
  right: bool = False
  evaluated_side: str = ""


class BlindspotStateReader:
  def __init__(self, path: str = BLINDSPOT_STATE_PATH):
    self.path = path
    self.last_read_at = 0.0
    self.state = BlindspotState()

  def read(self, now: float | None = None) -> BlindspotState:
    now = time.monotonic() if now is None else now
    if now - self.last_read_at < LANE_MARKING_READ_INTERVAL_SEC:
      return self.state
    self.last_read_at = now
    try:
      with open(self.path, encoding="utf-8") as state_file:
        data = json.load(state_file)
      updated_at = _finite(data.get("updatedAtMonotonic"), -math.inf)
      side = str(data.get("evaluatedSide", ""))
      if (updated_at <= 0.0 or now < updated_at or now - updated_at > BLINDSPOT_MAX_AGE_SEC or
          side not in ("left", "right")):
        self.state = BlindspotState()
      else:
        self.state = BlindspotState(
          left=bool(data.get("left", False)) if side == "left" else False,
          right=bool(data.get("right", False)) if side == "right" else False,
          evaluated_side=side,
        )
    except (OSError, AttributeError, TypeError, ValueError, json.JSONDecodeError):
      self.state = BlindspotState()
    return self.state


def merge_visual_blindspot(car_state: Any, vision_state: BlindspotState) -> None:
  """Only add V-ASM detections; never clear the vehicle's OEM BSD state."""
  car_state.leftBlindspot = bool(car_state.leftBlindspot or vision_state.left)
  car_state.rightBlindspot = bool(car_state.rightBlindspot or vision_state.right)


def _atomic_json(path: str, payload: dict[str, Any]) -> None:
  temp_path = path + ".tmp"
  try:
    with open(temp_path, "w", encoding="utf-8") as state_file:
      json.dump(payload, state_file, separators=(",", ":"))
    os.replace(temp_path, path)
  except OSError:
    try:
      os.unlink(temp_path)
    except OSError:
      pass


def publish_lane_marking_state(markings: dict[str, str], updated_at: float,
                               duration_ms: float = 0.0, error: str = "",
                               path: str = LANE_MARKING_STATE_PATH) -> None:
  _atomic_json(path, {
    "version": 3,
    "source": "xiaoge",
    "leftType": str(markings.get("navLaneLeftType", "unknown")),
    "rightType": str(markings.get("navLaneRightType", "unknown")),
    "updatedAtMonotonic": float(updated_at),
    "inferenceMs": round(max(0.0, float(duration_ms)), 1),
    "error": str(error),
  })


def publish_blindspot_state(left: bool, right: bool, evaluated_side: str,
                            updated_at: float, confidence: float = 0.0,
                            path: str = BLINDSPOT_STATE_PATH) -> None:
  _atomic_json(path, {
    "version": 1,
    "source": "xiaoge-v-asm",
    "left": bool(left),
    "right": bool(right),
    "evaluatedSide": evaluated_side if evaluated_side in ("left", "right") else "",
    "updatedAtMonotonic": float(updated_at),
    "confidence": round(max(0.0, min(1.0, float(confidence))), 3),
  })
