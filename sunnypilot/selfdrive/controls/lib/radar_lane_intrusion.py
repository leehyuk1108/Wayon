from bisect import bisect_left
from dataclasses import dataclass
import math
from typing import Any


MIN_EGO_SPEED_MPS = 5.0
MIN_TRACK_DISTANCE_M = 4.0
MAX_TRACK_DISTANCE_M = 60.0
MIN_LANE_LINE_PROBABILITY = 0.45
ASSUMED_VEHICLE_HALF_WIDTH_M = 0.9
OUTSIDE_MARGIN_M = 0.25
INSIDE_MARGIN_M = 0.10
MIN_INWARD_SPEED_MPS = 0.25
REQUIRED_OUTSIDE_SAMPLES = 3
REQUIRED_INTRUSION_SAMPLES = 3
MAX_SAMPLE_GAP_S = 0.20
TRACK_STALE_S = 0.50
MAX_LATERAL_JUMP_M = 1.25


@dataclass(frozen=True)
class RadarLaneIntrusion:
  track_id: int
  side: str
  distance_m: float
  lateral_m: float
  inward_speed_mps: float


@dataclass
class _TrackState:
  side: str
  distance_m: float
  lateral_m: float
  penetration_m: float
  last_seen_s: float
  outside_samples: int
  intrusion_samples: int = 0
  inward_speed_mps: float = 0.0
  alerted: bool = False


def _finite_float(value: Any, default: float = 0.0) -> float:
  try:
    result = float(value)
  except (TypeError, ValueError):
    return default
  return result if math.isfinite(result) else default


def _line_y_at(line: Any, distance_m: float) -> float | None:
  x_values = list(getattr(line, "x", []))
  y_values = list(getattr(line, "y", []))
  size = min(len(x_values), len(y_values))
  if size < 2:
    return None

  x_values = x_values[:size]
  y_values = y_values[:size]
  if distance_m < x_values[0] or distance_m > x_values[-1]:
    return None

  index = bisect_left(x_values, distance_m)
  if index == 0:
    return _finite_float(y_values[0])
  if index >= size:
    return _finite_float(y_values[-1])

  x0 = _finite_float(x_values[index - 1])
  x1 = _finite_float(x_values[index])
  y0 = _finite_float(y_values[index - 1])
  y1 = _finite_float(y_values[index])
  if x1 <= x0:
    return None
  ratio = (distance_m - x0) / (x1 - x0)
  return y0 + ratio * (y1 - y0)


def ego_lane_bounds(model_v2: Any, distance_m: float) -> tuple[float, float] | None:
  lane_lines = list(getattr(model_v2, "laneLines", []))
  lane_probs = list(getattr(model_v2, "laneLineProbs", []))
  if len(lane_lines) < 3 or len(lane_probs) < 3:
    return None
  if min(_finite_float(lane_probs[1]), _finite_float(lane_probs[2])) < MIN_LANE_LINE_PROBABILITY:
    return None

  left = _line_y_at(lane_lines[1], distance_m)
  right = _line_y_at(lane_lines[2], distance_m)
  if left is None or right is None or left >= right:
    return None
  return left, right


def _side_for_lateral(lateral_m: float, left: float, right: float) -> str | None:
  if lateral_m < left:
    return "left"
  if lateral_m > right:
    return "right"
  return None


def _penetration_m(side: str, lateral_m: float, left: float, right: float) -> float:
  if side == "left":
    return lateral_m + ASSUMED_VEHICLE_HALF_WIDTH_M - left
  return right - (lateral_m - ASSUMED_VEHICLE_HALF_WIDTH_M)


class RadarLaneIntrusionDetector:
  def __init__(self) -> None:
    self._tracks: dict[int, _TrackState] = {}

  def reset(self) -> None:
    self._tracks.clear()

  def _new_state(self, side: str, distance_m: float, lateral_m: float,
                 penetration_m: float, now_s: float) -> _TrackState:
    return _TrackState(
      side=side,
      distance_m=distance_m,
      lateral_m=lateral_m,
      penetration_m=penetration_m,
      last_seen_s=now_s,
      outside_samples=1 if penetration_m <= -OUTSIDE_MARGIN_M else 0,
    )

  def update(self, v_ego: float, radar_points: list[Any], model_v2: Any, now_s: float,
             lane_change_active: bool = False) -> RadarLaneIntrusion | None:
    if v_ego < MIN_EGO_SPEED_MPS or lane_change_active:
      self.reset()
      return None

    seen_tracks: set[int] = set()
    intrusions: list[RadarLaneIntrusion] = []
    for point in radar_points:
      track_id = int(_finite_float(getattr(point, "trackId", -1), -1.0))
      distance_m = _finite_float(getattr(point, "dRel", 0.0))
      if track_id < 0 or not MIN_TRACK_DISTANCE_M <= distance_m <= MAX_TRACK_DISTANCE_M:
        continue

      bounds = ego_lane_bounds(model_v2, distance_m)
      if bounds is None:
        continue
      left, right = bounds

      # GM radar yRel is positive to vehicle-left; modelV2 y is positive to vehicle-right.
      lateral_m = -_finite_float(getattr(point, "yRel", 0.0))
      state = self._tracks.get(track_id)
      side = state.side if state is not None else _side_for_lateral(lateral_m, left, right)
      if side is None:
        continue

      penetration_m = _penetration_m(side, lateral_m, left, right)
      seen_tracks.add(track_id)
      if state is None:
        self._tracks[track_id] = self._new_state(side, distance_m, lateral_m, penetration_m, now_s)
        continue

      sample_gap_s = now_s - state.last_seen_s
      distance_jump_limit = max(6.0, distance_m * 0.30)
      if sample_gap_s <= 0.0 or sample_gap_s > MAX_SAMPLE_GAP_S or \
         abs(distance_m - state.distance_m) > distance_jump_limit or \
         abs(lateral_m - state.lateral_m) > MAX_LATERAL_JUMP_M:
        current_side = _side_for_lateral(lateral_m, left, right)
        if current_side is None:
          del self._tracks[track_id]
        else:
          self._tracks[track_id] = self._new_state(
            current_side, distance_m, lateral_m,
            _penetration_m(current_side, lateral_m, left, right), now_s)
        continue

      raw_inward_speed = (penetration_m - state.penetration_m) / sample_gap_s
      state.inward_speed_mps = 0.55 * state.inward_speed_mps + 0.45 * raw_inward_speed
      state.distance_m = distance_m
      state.lateral_m = lateral_m
      state.penetration_m = penetration_m
      state.last_seen_s = now_s

      if penetration_m <= -OUTSIDE_MARGIN_M:
        state.outside_samples += 1
        state.intrusion_samples = 0
        if state.outside_samples >= REQUIRED_OUTSIDE_SAMPLES:
          state.alerted = False
      elif penetration_m >= INSIDE_MARGIN_M and \
           state.outside_samples >= REQUIRED_OUTSIDE_SAMPLES and \
           state.inward_speed_mps >= MIN_INWARD_SPEED_MPS:
        state.intrusion_samples += 1
      else:
        state.intrusion_samples = 0

      if state.intrusion_samples >= REQUIRED_INTRUSION_SAMPLES and not state.alerted:
        state.alerted = True
        intrusions.append(RadarLaneIntrusion(
          track_id=track_id,
          side=state.side,
          distance_m=distance_m,
          lateral_m=lateral_m,
          inward_speed_mps=state.inward_speed_mps,
        ))

    for track_id, state in list(self._tracks.items()):
      if track_id not in seen_tracks and now_s - state.last_seen_s > TRACK_STALE_S:
        del self._tracks[track_id]

    return min(intrusions, key=lambda intrusion: intrusion.distance_m, default=None)
