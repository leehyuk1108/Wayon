"""Traverse-only Wayon longitudinal values derived from the Carrot profile."""

import math
import numpy as np

from openpilot.common.constants import ACCELERATION_DUE_TO_GRAVITY, CV


TRAVERSE_FINGERPRINT = "CHEVROLET_TRAVERSE"

PID_KP = 1.0
PID_KI = 0.0
PID_KF = 1.0
V_EGO_STOPPING = 0.5
A_CHANGE_COST_STARTING = 10.0
MOVING_STOPPING_DECEL_RATE = 0.8

MAX_ACCEL_BP = [
  0.0,
  10.0 * CV.KPH_TO_MS,
  20.0 * CV.KPH_TO_MS,
  30.0 * CV.KPH_TO_MS,
  40.0 * CV.KPH_TO_MS,
  60.0 * CV.KPH_TO_MS,
  80.0 * CV.KPH_TO_MS,
  110.0 * CV.KPH_TO_MS,
  140.0 * CV.KPH_TO_MS,
]
MAX_ACCEL_V = [1.80, 1.70, 1.55, 1.20, 0.90, 0.65, 0.55, 0.50, 0.50]

# Keep the tuned flat-road curve unchanged. Grade compensation only provides
# bounded headroom above it when calibrated pitch shows a real uphill.
UPHILL_COMPENSATION_DEADBAND = 0.25 * CV.DEG_TO_RAD
UPHILL_COMPENSATION_MAX = 0.35
UPHILL_COMPENSATION_ACCEL_MAX = 2.0
UPHILL_COMPENSATION_MIN_SPEED = 5.0 * CV.KPH_TO_MS
UPHILL_TARGET_SPEED_MARGIN = 0.3 * CV.KPH_TO_MS

VISION_CURVE_FACTOR = 0.60
VISION_TARGET_LAT_ACCEL = 1.90
CURVE_SPEED_FLOOR = 30.0 * CV.KPH_TO_MS
MAP_CURVE_FACTOR = 1.20


def is_enabled(CP) -> bool:
  return bool(
    getattr(CP, "brand", "") == "gm" and
    str(getattr(CP, "carFingerprint", "")) == TRAVERSE_FINGERPRINT and
    bool(getattr(CP, "openpilotLongitudinalControl", False))
  )


def get_max_accel(v_ego: float) -> float:
  return float(np.interp(v_ego, MAX_ACCEL_BP, MAX_ACCEL_V))


def get_uphill_accel_compensation(pitch: float) -> float:
  if not math.isfinite(pitch) or pitch <= UPHILL_COMPENSATION_DEADBAND:
    return 0.0

  gravity_delta = ACCELERATION_DUE_TO_GRAVITY * (
    math.sin(pitch) - math.sin(UPHILL_COMPENSATION_DEADBAND)
  )
  return float(np.clip(gravity_delta, 0.0, UPHILL_COMPENSATION_MAX))


def get_grade_adjusted_max_accel(v_ego: float, pitch: float) -> float:
  return min(UPHILL_COMPENSATION_ACCEL_MAX,
             get_max_accel(v_ego) + get_uphill_accel_compensation(pitch))


def apply_uphill_accel_compensation(command: float, v_ego: float, v_target: float,
                                    pitch: float) -> float:
  if (v_ego < UPHILL_COMPENSATION_MIN_SPEED or
      v_target < v_ego - UPHILL_TARGET_SPEED_MARGIN or
      command < -0.05):
    return command
  return command + get_uphill_accel_compensation(pitch)
