"""Warning-only crossing confirmation; does not alter longitudinal candidates."""
from dataclasses import dataclass
import math
from typing import Any

from openpilot.sunnypilot.selfdrive.controls.lib.radar_lane_intrusion import MAX_LATERAL_JUMP_M, ego_lane_bounds

OUTSIDE_MARGIN_M = 0.20
OUTSIDE_DURATION_S = 0.15
ENTRY_DURATION_S = 0.10
OUTSIDE_HISTORY_S = 3.0
TRACK_GAP_S = 0.75
OWN_LANE_CHANGE_SETTLE_S = 1.0
MIN_INWARD_TRAVEL_M = 0.35
MIN_SELECTED_PROBABILITY = 0.50


def value(message: Any, name: str, default: Any = None) -> Any:
  return message.get(name, default) if isinstance(message, dict) else getattr(message, name, default)


@dataclass
class _Crossing:
  side: str
  last_seen: float
  last_y: float
  last_distance: float
  origin_y: float
  origin_penetration: float
  outside_since: float | None
  last_outside: float
  armed: bool = False
  entry_since: float | None = None
  warned: bool = False


@dataclass(frozen=True)
class CutInWarning:
  lead: Any
  track_id: int
  side: str
  inward_travel: float
  outside_age: float
  selected_by_vision: bool


class CutInWarningTracker:
  def __init__(self):
    self._tracks: dict[int, _Crossing] = {}
    self._last_own_lane_change: float | None = None

  def reset(self):
    self._tracks.clear()
    self._last_own_lane_change = None

  @staticmethod
  def _selected(candidate, leads) -> tuple[bool, bool]:
    for lead in leads:
      probability = value(lead, "modelProb", 0.0)
      if not value(lead, "status", False) or not math.isfinite(probability) or probability < MIN_SELECTED_PROBABILITY:
        continue
      if value(lead, "radar", False):
        if value(lead, "radarTrackId", -1) == value(candidate, "radarTrackId", -1):
          return True, False
      else:
        # Fusion can temporarily fall back to vision without changing the car.
        deltas = [abs(value(lead, k, math.inf) - value(candidate, k, -math.inf)) for k in ("dRel", "yRel", "vRel")]
        if all(math.isfinite(delta) for delta in deltas) and \
           deltas[0] <= max(3.0, value(candidate, "dRel", 0.0) * 0.10) and deltas[1] <= 0.70 and deltas[2] <= 2.0:
          return True, True
    return False, False

  def update(self, radar_state, model, v_ego: float, now: float, lane_change_active: bool = False) -> CutInWarning | None:
    if not math.isfinite(now) or not math.isfinite(v_ego) or v_ego < 2.0:
      self.reset()
      return None
    if lane_change_active:
      self._last_own_lane_change = now
    own_movement = lane_change_active or (self._last_own_lane_change is not None and
                                         now - self._last_own_lane_change < OWN_LANE_CHANGE_SETTLE_S)
    leads = [value(radar_state, name) for name in ("leadOne", "leadTwo")]
    observations = {}
    for lead in [value(radar_state, "leadCutInRisk"), *leads]:
      track_id = value(lead, "radarTrackId", -1)
      if value(lead, "status", False) and value(lead, "radar", False) and track_id >= 0:
        observations[track_id] = lead
    warnings = []
    for track_id, lead in observations.items():
      state = self._tracks.get(track_id)
      distance, y_rel, v_rel = (value(lead, k, math.nan) for k in ("dRel", "yRel", "vRel"))
      if not all(math.isfinite(x) for x in (distance, y_rel, v_rel)) or not 4.0 <= distance <= 60.0:
        if state is not None:
          state.entry_since = None
        continue
      lateral = -y_rel
      if state is not None and (now <= state.last_seen or now - state.last_seen > TRACK_GAP_S or
                                abs(lateral - state.last_y) > MAX_LATERAL_JUMP_M or
                                abs(distance - state.last_distance) > max(6.0, distance * 0.30)):
        del self._tracks[track_id]
        state = None
      bounds = ego_lane_bounds(model, distance)
      reliable_lane = bounds is not None and all(math.isfinite(x) for x in bounds) and 2.4 <= bounds[1] - bounds[0] <= 5.0
      if own_movement and state is None:
        state = _Crossing("left" if lateral < 0.0 else "right", now, lateral, distance, lateral, 0.0,
                          None, -math.inf, warned=True)
        self._tracks[track_id] = state
      if state is not None:
        state.last_seen = now
        state.last_y = lateral
        state.last_distance = distance
      if own_movement or not reliable_lane:
        if state is not None:
          state.entry_since = None
          if own_movement:
            state.armed = False
            state.outside_since = None
            state.last_outside = -math.inf
            state.warned = True
          elif not state.armed or now - state.last_outside > OUTSIDE_HISTORY_S:
            state.armed = False
            state.outside_since = None
        continue
      left, right = bounds
      outside_side = "left" if lateral < left - OUTSIDE_MARGIN_M else "right" if lateral > right + OUTSIDE_MARGIN_M else None
      if state is None:
        side = outside_side or ("left" if lateral < (left + right) / 2.0 else "right")
        penetration = lateral + 0.9 - left if side == "left" else right - lateral + 0.9
        self._tracks[track_id] = _Crossing(side, now, lateral, distance, lateral, penetration,
                                         now if outside_side else None, now if outside_side else -math.inf,
                                         warned=outside_side is None)
        continue

      penetration = lateral + 0.9 - left if state.side == "left" else right - lateral + 0.9
      outside_penetration = lateral + 0.9 - left if outside_side == "left" else right - lateral + 0.9
      # An established lead must leave the lane with its whole body before rearming.
      can_arm = outside_side is not None and (not state.warned or outside_penetration <= -OUTSIDE_MARGIN_M)
      if can_arm:
        if state.outside_since is None or outside_side != state.side:
          state.side = outside_side
          penetration = outside_penetration
          state.outside_since = now
          state.origin_y = lateral
          state.origin_penetration = penetration
          state.armed = False
          state.entry_since = None
        state.last_outside = now
        if now - state.outside_since >= OUTSIDE_DURATION_S and not state.armed:
          state.armed = True
          state.warned = False
      else:
        state.outside_since = None
      outside_age = now - state.last_outside
      if outside_age > OUTSIDE_HISTORY_S:
        state.armed = False

      radar_travel = lateral - state.origin_y if state.side == "left" else state.origin_y - lateral
      inward_travel = min(radar_travel, penetration - state.origin_penetration)
      selected, selected_by_vision = self._selected(lead, leads)
      entering = state.armed and penetration >= 0.10 and inward_travel >= MIN_INWARD_TRAVEL_M and selected
      if not entering:
        state.entry_since = None
      elif state.entry_since is None:
        state.entry_since = now
      elif now - state.entry_since >= ENTRY_DURATION_S and not state.warned:
        state.warned = True
        warnings.append(CutInWarning(lead, track_id, state.side, inward_travel, outside_age, selected_by_vision))
    for track_id, state in list(self._tracks.items()):
      if now - state.last_seen > TRACK_GAP_S:
        del self._tracks[track_id]
    return min(warnings, key=lambda w: value(w.lead, "dRel"), default=None)
