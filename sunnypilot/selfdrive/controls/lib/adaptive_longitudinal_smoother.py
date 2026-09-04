import math
from typing import Any

import numpy as np

from openpilot.common.realtime import DT_CTRL


class AdaptiveLongitudinalSmoother:
  """Jerk-limited acceleration shaper with urgency-dependent response."""

  def __init__(self, dt: float = DT_CTRL):
    self.dt = dt
    self.output_accel = 0.0
    self.output_jerk = 0.0
    self.initialized = False

  def reset(self, accel: float = 0.0) -> None:
    self.output_accel = float(accel) if math.isfinite(accel) else 0.0
    self.output_jerk = 0.0
    self.initialized = True

  @staticmethod
  def _lead_urgency(lead: Any | None) -> float:
    if lead is None or not getattr(lead, "status", False):
      return 0.0

    d_rel = float(getattr(lead, "dRel", 0.0))
    v_rel = float(getattr(lead, "vRel", 0.0))
    if d_rel <= 0.0 or v_rel >= -0.1:
      return 0.0

    ttc = d_rel / max(-v_rel, 0.1)
    return float(np.interp(ttc, [1.5, 6.0], [1.0, 0.0]))

  @staticmethod
  def _cutin_urgency(cutin_risk: Any | None) -> float:
    if cutin_risk is None or not getattr(cutin_risk, "status", False):
      return 0.0
    return float(np.clip(getattr(cutin_risk, "score", 0.0), 0.0, 1.0))

  @staticmethod
  def _lead_departure_urgency(lead: Any | None, v_ego: float) -> float:
    if lead is None or not getattr(lead, "status", False) or not getattr(lead, "radar", False) or v_ego > 12.0:
      return 0.0

    d_rel = float(getattr(lead, "dRel", 0.0))
    v_rel = float(getattr(lead, "vRel", 0.0))
    a_lead = float(getattr(lead, "aLeadK", 0.0))
    j_lead = float(getattr(lead, "jLead", 0.0))
    safe_reserve = d_rel - max(6.0, v_ego * 1.2)
    if safe_reserve <= 0.0 or v_rel <= 0.2 or (a_lead <= 0.1 and j_lead <= 0.2):
      return 0.0

    opening = float(np.interp(v_rel, [0.2, 1.5], [0.0, 1.0]))
    lead_motion = max(float(np.interp(a_lead, [0.1, 1.2], [0.0, 1.0])),
                      float(np.interp(j_lead, [0.2, 1.5], [0.0, 1.0])))
    reserve = float(np.interp(safe_reserve, [0.0, 4.0], [0.0, 1.0]))
    return float(np.clip(max(opening, lead_motion) * reserve, 0.0, 1.0))

  def _urgency(self, target_accel: float, measured_accel: float, v_ego: float,
               v_target: float, planned_jerk: float, lead: Any | None,
               cutin_risk: Any | None) -> float:
    error = target_accel - self.output_accel
    demand = float(np.interp(abs(error), [0.05, 1.5], [0.0, 1.0]))
    plan = float(np.interp(abs(planned_jerk), [0.1, 2.0], [0.0, 1.0]))

    if error < 0.0:
      target_decel = float(np.interp(max(0.0, -target_accel), [0.2, 2.5], [0.0, 1.0]))
      speed_error = float(np.interp(max(0.0, v_ego - v_target), [0.2, 4.0], [0.0, 1.0]))
      tracking_error = float(np.interp(max(0.0, measured_accel - target_accel - 0.3), [0.0, 1.2], [0.0, 1.0]))
      return float(np.clip(max(demand, plan, target_decel, speed_error, tracking_error,
                               self._lead_urgency(lead), self._cutin_urgency(cutin_risk)), 0.0, 1.0))

    target_accel_demand = float(np.interp(max(0.0, target_accel), [0.1, 1.0], [0.0, 1.0]))
    speed_error = float(np.interp(max(0.0, v_target - v_ego), [0.2, 4.0], [0.0, 1.0]))
    tracking_error = float(np.interp(max(0.0, target_accel - measured_accel - 0.3), [0.0, 1.2], [0.0, 1.0]))
    return float(np.clip(max(demand, plan, target_accel_demand, speed_error, tracking_error,
                             self._lead_departure_urgency(lead, v_ego)), 0.0, 1.0))

  def update(self, target_accel: float, measured_accel: float, v_ego: float,
             v_target: float, planned_jerk: float = 0.0, lead: Any | None = None,
             cutin_risk: Any | None = None, accel_limits: tuple[float, float] | None = None,
             throttle_release: bool = False) -> float:
    if not math.isfinite(target_accel):
      target_accel = 0.0
    if not math.isfinite(measured_accel):
      measured_accel = self.output_accel
    if not math.isfinite(planned_jerk):
      planned_jerk = 0.0
    if throttle_release:
      target_accel = min(target_accel, 0.0)

    if accel_limits is not None:
      target_accel = float(np.clip(target_accel, accel_limits[0], accel_limits[1]))

    if not self.initialized:
      self.reset(measured_accel)

    error = target_accel - self.output_accel
    if abs(error) < 1e-4 and abs(self.output_jerk) < 1e-3:
      self.output_accel = target_accel
      self.output_jerk = 0.0
      return self.output_accel

    urgency = self._urgency(target_accel, measured_accel, v_ego, v_target,
                            planned_jerk, lead, cutin_risk)
    emergency_braking = error < 0.0 and (
      target_accel <= -2.0 or self._lead_urgency(lead) >= 0.9 or self._cutin_urgency(cutin_risk) >= 0.9)

    if throttle_release and error < 0.0 and self.output_accel > 0.0:
      # A release-only response may drop positive acceleration promptly, but
      # cannot cross through zero and turn into an unplanned brake request.
      natural_frequency = 8.0
      jerk_limit = 8.0
      snap_limit = 50.0
    elif emergency_braking:
      # Preserve a short reaction time for severe deceleration while retaining a continuous command.
      natural_frequency = 8.0
      jerk_limit = 8.0
      snap_limit = 50.0
    elif error < 0.0:
      # Releasing throttle or building brake pressure can respond quickly as risk rises.
      natural_frequency = 2.0 + 4.5 * urgency
      jerk_limit = 0.5 + 3.5 * urgency
      snap_limit = 2.0 + 18.0 * urgency
    elif self.output_accel < -0.05:
      # Release promptly enough to avoid undershooting while easing the final part of the ramp.
      natural_frequency = 2.2 + 2.8 * urgency
      jerk_limit = 0.6 + 2.0 * urgency
      snap_limit = 2.5 + 14.0 * urgency
    else:
      # Acceleration builds progressively, then eases as the speed target is approached.
      natural_frequency = 1.6 + 2.8 * urgency
      jerk_limit = 0.35 + 1.45 * urgency
      snap_limit = 1.5 + 11.0 * urgency

    desired_snap = natural_frequency * natural_frequency * error - \
                   2.0 * natural_frequency * self.output_jerk
    applied_snap = float(np.clip(desired_snap, -snap_limit, snap_limit))
    self.output_jerk = float(np.clip(self.output_jerk + applied_snap * self.dt,
                                     -jerk_limit, jerk_limit))

    next_accel = self.output_accel + self.output_jerk * self.dt
    if error * (target_accel - next_accel) <= 0.0:
      next_accel = target_accel
      self.output_jerk = 0.0

    if accel_limits is not None:
      clipped_accel = float(np.clip(next_accel, accel_limits[0], accel_limits[1]))
      if clipped_accel != next_accel:
        self.output_jerk = 0.0
      next_accel = clipped_accel

    self.output_accel = next_accel
    return self.output_accel
