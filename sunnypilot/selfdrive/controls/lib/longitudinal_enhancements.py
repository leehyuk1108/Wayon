import math
from typing import Any

import numpy as np

from openpilot.common.realtime import DT_MDL
from openpilot.selfdrive.modeld.constants import ModelConstants


FUTURE_CURVATURE_LOOKAHEAD_S = 1.2
FUTURE_CURVATURE_MIN_SPEED = 2.0
CUTIN_MIN_SCORE = 0.15
CUTIN_URGENT_MIN_SCORE = 0.08
CUTIN_MIN_TTC_S = 2.5
CUTIN_MAX_TTC_S = 8.0
CUTIN_COAST_MAX_TTC_S = 13.0
CUTIN_MAX_CROSSING_TIME_S = 3.5
CUTIN_MIN_EGO_SPEED_MPS = 2.0
CUTIN_LATERAL_WINDOW_M = 0.90
CUTIN_EARLY_BRAKE_REL_SPEED_MPS = 3.0
CUTIN_FULL_BRAKE_REL_SPEED_MPS = 8.0
CUTIN_GAP_RECOVERY_MIN_T_FOLLOW = 0.80
CUTIN_GAP_RECOVERY_MIN_TTC_S = 6.0
CUTIN_GAP_RECOVERY_MAX_CLOSING_SPEED_MPS = 2.0
CUTIN_GAP_RECOVERY_MIN_DISTANCE_M = 9.0
CUTIN_GAP_RECOVERY_MIN_HEADWAY_S = 0.75
CUTIN_GAP_RECOVERY_STOP_DISTANCE_M = 6.0
CUTIN_GAP_RECOVERY_RATE_S_PER_S = 0.12
CUTIN_GAP_RECOVERY_MAX_DURATION_S = 7.0
CUTIN_GAP_RECOVERY_CANDIDATE_HOLD_S = 2.0
CUTIN_GAP_RECOVERY_MIN_SCORE = 0.10


def future_curvature(model_msg: Any, fallback_curvature: float,
                     lookahead_s: float = FUTURE_CURVATURE_LOOKAHEAD_S) -> float:
  if len(model_msg.orientationRate.z) != ModelConstants.IDX_N or \
     len(model_msg.velocity.x) != ModelConstants.IDX_N:
    return fallback_curvature

  yaw_rate = float(np.interp(lookahead_s, ModelConstants.T_IDXS, model_msg.orientationRate.z))
  velocity = float(np.interp(lookahead_s, ModelConstants.T_IDXS, model_msg.velocity.x))
  if not math.isfinite(yaw_rate) or not math.isfinite(velocity):
    return fallback_curvature
  return yaw_rate / max(abs(velocity), FUTURE_CURVATURE_MIN_SPEED)


def limit_accel_for_future_curve(v_ego: float, curvature: float, accel_limits: list[float],
                                 total_accel_limit: float, safety_ratio: float = 0.80) -> list[float]:
  if v_ego < FUTURE_CURVATURE_MIN_SPEED or total_accel_limit <= 0.0:
    return list(accel_limits)

  lateral_accel = abs(v_ego * v_ego * curvature)
  usable_total = max(0.0, total_accel_limit * safety_ratio)
  longitudinal_limit = math.sqrt(max(usable_total * usable_total - lateral_accel * lateral_accel, 0.0))
  return [accel_limits[0], min(accel_limits[1], longitudinal_limit)]


def lead_response_factor(lead: Any, cutin_risk: Any | None = None) -> float:
  factor = 0.0
  if getattr(lead, "status", False):
    negative_jerk = max(0.0, -float(getattr(lead, "jLead", 0.0)))
    factor = max(factor, float(np.interp(negative_jerk, [0.2, 2.0], [0.0, 1.0])))
    v_rel = float(getattr(lead, "vRel", 0.0))
    a_lead = float(getattr(lead, "aLeadK", 0.0))
    if getattr(lead, "radar", False) and v_rel > 0.2 and a_lead > 0.1:
      positive_jerk = max(0.0, float(getattr(lead, "jLead", 0.0)))
      departure_signal = max(positive_jerk, a_lead, v_rel)
      factor = max(factor, float(np.interp(departure_signal, [0.25, 1.5], [0.0, 0.75])))
  if cutin_risk is not None and getattr(cutin_risk, "status", False):
    factor = max(factor, float(np.clip(getattr(cutin_risk, "score", 0.0), 0.0, 1.0)))
  return float(np.clip(factor, 0.0, 1.0))


def dynamic_a_change_cost(base_cost: float, response_factor: float) -> float:
  return float(np.interp(np.clip(response_factor, 0.0, 1.0), [0.0, 1.0], [base_cost, 35.0]))


def dynamic_t_follow_target(base_t_follow: float, lead: Any, a_ego: float,
                            cutin_risk: Any | None = None) -> float:
  target = base_t_follow
  radar_lead = getattr(lead, "status", False) and getattr(lead, "radar", False)
  if radar_lead:
    jerk = float(np.clip(getattr(lead, "jLead", 0.0), -3.0, 2.0))
    v_rel = float(getattr(lead, "vRel", 0.0))
    a_lead = float(getattr(lead, "aLeadK", 0.0))
    if jerk < -0.3 and (a_lead < -0.05 or v_rel < -0.1):
      target += float(np.interp(jerk, [-3.0, -0.3], [0.45, 0.0]))
    elif v_rel > 0.2 and a_lead > 0.1:
      departure_signal = max(jerk, a_lead, v_rel)
      target -= float(np.interp(departure_signal, [0.25, 1.5], [0.0, 0.25]))
  if radar_lead and a_ego < -0.4:
    target += float(np.interp(a_ego, [-2.0, -0.4], [0.20, 0.0]))
  if cutin_risk is not None and getattr(cutin_risk, "status", False):
    target += 0.35 * float(np.clip(getattr(cutin_risk, "score", 0.0), 0.0, 1.0))
  return float(np.clip(target, 0.80, 2.10))


def ramp_t_follow(target: float, current: float, dt: float = DT_MDL,
                  rise_rate: float = 0.25) -> float:
  fall_rate = 0.50
  delta = np.clip(target - current, -fall_rate * dt, rise_rate * dt)
  return float(current + delta)


class CutInGapRecoveryController:
  """Restore the configured gap gradually after a non-urgent cut-in."""

  def __init__(self):
    self.reset()

  def reset(self) -> None:
    self.active_track_id = -1
    self.elapsed = 0.0
    self.t_follow_cap = math.inf
    self.pending_track_id = -1
    self.pending_elapsed = 0.0

  @staticmethod
  def _track_id(lead: Any) -> int:
    return int(getattr(lead, "radarTrackId", -1))

  @staticmethod
  def _is_nonurgent(v_ego: float, lead: Any) -> bool:
    if not getattr(lead, "status", False) or not getattr(lead, "radar", False):
      return False

    d_rel = float(getattr(lead, "dRel", 0.0))
    v_rel = float(getattr(lead, "vRel", 0.0))
    closing_speed = max(0.0, -v_rel)
    ttc = d_rel / max(closing_speed, 0.1)
    minimum_distance = max(CUTIN_GAP_RECOVERY_MIN_DISTANCE_M,
                           v_ego * CUTIN_GAP_RECOVERY_MIN_HEADWAY_S)
    return (
      v_ego >= CUTIN_MIN_EGO_SPEED_MPS and d_rel >= minimum_distance and
      0.1 <= closing_speed < CUTIN_GAP_RECOVERY_MAX_CLOSING_SPEED_MPS and
      ttc > CUTIN_GAP_RECOVERY_MIN_TTC_S and
      float(getattr(lead, "aLeadK", 0.0)) > -0.7 and
      float(getattr(lead, "jLead", 0.0)) > -1.5
    )

  def update(self, nominal_t_follow: float, v_ego: float, lead: Any,
             cutin_candidate: Any | None, dt: float = DT_MDL) -> float:
    track_id = self._track_id(lead)
    candidate_valid = (
      cutin_candidate is not None and getattr(cutin_candidate, "status", False) and
      getattr(cutin_candidate, "radar", False) and
      float(getattr(cutin_candidate, "score", 0.0)) >= CUTIN_GAP_RECOVERY_MIN_SCORE
    )
    if candidate_valid:
      self.pending_track_id = self._track_id(cutin_candidate)
      self.pending_elapsed = 0.0
    elif self.pending_track_id >= 0:
      self.pending_elapsed += dt
      if self.pending_elapsed > CUTIN_GAP_RECOVERY_CANDIDATE_HOLD_S:
        self.pending_track_id = -1
        self.pending_elapsed = 0.0

    if self.pending_track_id == track_id and track_id >= 0:
      if self._is_nonurgent(v_ego, lead):
        implied_t_follow = (
          float(getattr(lead, "dRel", 0.0)) - CUTIN_GAP_RECOVERY_STOP_DISTANCE_M
        ) / max(v_ego, 1.0)
        if implied_t_follow < nominal_t_follow:
          self.active_track_id = track_id
          self.elapsed = 0.0
          self.t_follow_cap = float(np.clip(
            implied_t_follow,
            CUTIN_GAP_RECOVERY_MIN_T_FOLLOW,
            nominal_t_follow,
          ))
      self.pending_track_id = -1
      self.pending_elapsed = 0.0

    if self.active_track_id < 0:
      return nominal_t_follow

    if track_id != self.active_track_id or not self._is_nonurgent(v_ego, lead):
      self.reset()
      return nominal_t_follow

    self.elapsed += dt
    self.t_follow_cap = min(
      nominal_t_follow,
      self.t_follow_cap + CUTIN_GAP_RECOVERY_RATE_S_PER_S * dt,
    )
    result = min(nominal_t_follow, self.t_follow_cap)
    if self.elapsed >= CUTIN_GAP_RECOVERY_MAX_DURATION_S or result >= nominal_t_follow - 1e-3:
      self.reset()
    return result


def cutin_predecel_accel(cutin_risk: Any, v_ego: float) -> float | None:
  if not getattr(cutin_risk, "status", False) or not getattr(cutin_risk, "radar", False):
    return None

  score = float(np.clip(getattr(cutin_risk, "score", 0.0), 0.0, 1.0))
  d_rel = float(getattr(cutin_risk, "dRel", 0.0))
  v_rel = float(getattr(cutin_risk, "vRel", 0.0))
  inward_speed = max(0.0, float(getattr(cutin_risk, "vLat", 0.0)))
  if d_rel <= 0.0 or v_rel >= -0.1 or v_ego < CUTIN_MIN_EGO_SPEED_MPS:
    return None

  ttc = d_rel / max(-v_rel, 0.1)
  required_score = float(np.interp(
    ttc, [CUTIN_MIN_TTC_S, CUTIN_MAX_TTC_S], [CUTIN_URGENT_MIN_SCORE, CUTIN_MIN_SCORE]))
  if score < required_score:
    return None
  boundary_gap = max(0.0, (1.0 - score) * CUTIN_LATERAL_WINDOW_M)
  crossing_time = boundary_gap / max(inward_speed, 0.05)
  if ttc > CUTIN_COAST_MAX_TTC_S or crossing_time > CUTIN_MAX_CROSSING_TIME_S:
    return None

  if ttc > CUTIN_MAX_TTC_S:
    closing_speed = -v_rel
    if closing_speed <= CUTIN_EARLY_BRAKE_REL_SPEED_MPS:
      return 0.0
    # A fast-closing adjacent vehicle needs braking before it becomes the
    # selected lead. Keep this mild while TTC is still above the urgent range.
    closing_urgency = float(np.interp(
      closing_speed, [CUTIN_EARLY_BRAKE_REL_SPEED_MPS, CUTIN_FULL_BRAKE_REL_SPEED_MPS], [0.0, 1.0]))
    return float(np.interp(closing_urgency, [0.0, 1.0], [-0.12, -0.35]))

  ttc_urgency = float(np.interp(ttc, [CUTIN_MIN_TTC_S, CUTIN_MAX_TTC_S], [1.0, 0.0]))
  crossing_urgency = float(np.interp(crossing_time, [0.5, CUTIN_MAX_CROSSING_TIME_S], [1.0, 0.0]))
  closing_urgency = float(np.interp(
    -v_rel, [1.0, CUTIN_FULL_BRAKE_REL_SPEED_MPS], [0.0, 1.0]))
  urgency = max(score, ttc_urgency, crossing_urgency, closing_urgency)
  return float(np.interp(urgency, [0.0, 1.0], [-0.25, -0.65]))
