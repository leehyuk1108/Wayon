"""Lane-boundary and target-space checks before starting a lane change."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from statistics import median
from typing import Any

from cereal import log


LaneChangeDirection = log.LaneChangeDirection

LANE_MARKING_STATE_PATH = "/dev/shm/navdy_lane_marking_state.json"
LANE_MARKING_MAX_AGE_SEC = 1.25
LANE_MARKING_READ_INTERVAL_SEC = 0.1
LANE_PROB_MIN = 0.55
ROAD_EDGE_STD_MAX = 0.65
TARGET_LANE_MIN_WIDTH_M = 1.00
TARGET_LANE_WIDTH_CONFIRM_FRAMES = 5
WIDTH_SAMPLE_DISTANCES_M = (8.0, 15.0, 25.0)
CENTERLINE_TYPES = frozenset(("centerSolid", "centerDashed"))


def _finite(value: Any, default: float = 0.0) -> float:
  try:
    value = float(value)
  except (TypeError, ValueError):
    return default
  return value if math.isfinite(value) else default


def _line_y_at(line: Any, distance_m: float) -> float | None:
  xs = list(getattr(line, "x", []))
  ys = list(getattr(line, "y", []))
  if len(xs) < 2 or len(xs) != len(ys):
    return None

  distance_m = _finite(distance_m)
  if distance_m <= _finite(xs[0]):
    return _finite(ys[0])
  for index in range(1, len(xs)):
    x0, x1 = _finite(xs[index - 1]), _finite(xs[index])
    if distance_m <= x1:
      if x1 <= x0:
        return _finite(ys[index])
      ratio = (distance_m - x0) / (x1 - x0)
      return _finite(ys[index - 1]) + ratio * (_finite(ys[index]) - _finite(ys[index - 1]))
  return _finite(ys[-1])


def _space_between(inner: Any, outer: Any) -> float | None:
  widths = []
  for distance_m in WIDTH_SAMPLE_DISTANCES_M:
    inner_y = _line_y_at(inner, distance_m)
    outer_y = _line_y_at(outer, distance_m)
    if inner_y is None or outer_y is None:
      continue
    width = abs(outer_y - inner_y)
    if 0.5 <= width <= 6.0:
      widths.append(width)
  return float(median(widths)) if widths else None


def target_lane_space_width(model_v2: Any, direction: Any) -> float | None:
  """Return a reliable adjacent-lane/edge space width, or None when unknown."""
  if model_v2 is None:
    return None
  lane_lines = list(getattr(model_v2, "laneLines", []))
  lane_probs = list(getattr(model_v2, "laneLineProbs", []))
  if len(lane_lines) < 4 or len(lane_probs) < 4:
    return None

  if direction == LaneChangeDirection.left:
    outer_index, inner_index, edge_index = 0, 1, 0
  elif direction == LaneChangeDirection.right:
    outer_index, inner_index, edge_index = 3, 2, 1
  else:
    return None

  inner_prob = _finite(lane_probs[inner_index])
  outer_prob = _finite(lane_probs[outer_index])
  if min(inner_prob, outer_prob) >= LANE_PROB_MIN:
    return _space_between(lane_lines[inner_index], lane_lines[outer_index])

  road_edges = list(getattr(model_v2, "roadEdges", []))
  road_edge_stds = list(getattr(model_v2, "roadEdgeStds", []))
  if inner_prob < LANE_PROB_MIN or len(road_edges) <= edge_index or len(road_edge_stds) <= edge_index:
    return None
  if _finite(road_edge_stds[edge_index], math.inf) > ROAD_EDGE_STD_MAX:
    return None
  return _space_between(lane_lines[inner_index], road_edges[edge_index])


@dataclass(frozen=True)
class LaneBoundaryState:
  left_type: str = "unknown"
  right_type: str = "unknown"

  def type_for_direction(self, direction: Any) -> str:
    if direction == LaneChangeDirection.left:
      return self.left_type
    if direction == LaneChangeDirection.right:
      return self.right_type
    return "unknown"


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


class LaneChangeSafetyGate:
  def __init__(self, boundary_reader: LaneBoundaryStateReader | None = None):
    self.boundary_reader = boundary_reader or LaneBoundaryStateReader()
    self.direction = LaneChangeDirection.none
    self.narrow_frames = 0
    self.blocked = False
    self.block_reason = ""
    self.target_width_m: float | None = None

  def reset(self) -> None:
    self.direction = LaneChangeDirection.none
    self.narrow_frames = 0
    self.blocked = False
    self.block_reason = ""
    self.target_width_m = None

  def update(self, direction: Any, model_v2: Any) -> bool:
    if direction == LaneChangeDirection.none:
      self.reset()
      return False
    if direction != self.direction:
      self.reset()
      self.direction = direction

    boundary_type = self.boundary_reader.read().type_for_direction(direction)
    if boundary_type in CENTERLINE_TYPES:
      self.blocked = True
      self.block_reason = "centerline"

    self.target_width_m = target_lane_space_width(model_v2, direction)
    narrow_now = self.target_width_m is not None and self.target_width_m < TARGET_LANE_MIN_WIDTH_M
    self.narrow_frames = self.narrow_frames + 1 if narrow_now else 0
    if self.narrow_frames >= TARGET_LANE_WIDTH_CONFIRM_FRAMES:
      self.blocked = True
      self.block_reason = "narrowTargetLane"

    return self.blocked
