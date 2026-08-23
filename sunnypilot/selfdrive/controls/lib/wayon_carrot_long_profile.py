"""Traverse-only Wayon longitudinal values derived from the Carrot profile."""

import numpy as np

from openpilot.common.constants import CV


TRAVERSE_FINGERPRINT = "CHEVROLET_TRAVERSE"

PID_KP = 1.0
PID_KI = 0.0
PID_KF = 1.0
V_EGO_STOPPING = 0.5
A_CHANGE_COST_STARTING = 10.0

MAX_ACCEL_BP = [
  0.0,
  10.0 * CV.KPH_TO_MS,
  40.0 * CV.KPH_TO_MS,
  60.0 * CV.KPH_TO_MS,
  80.0 * CV.KPH_TO_MS,
  110.0 * CV.KPH_TO_MS,
  140.0 * CV.KPH_TO_MS,
]
MAX_ACCEL_V = [1.0, 0.95, 0.60, 0.55, 0.55, 0.50, 0.50]

VISION_CURVE_FACTOR = 0.60
VISION_TARGET_LAT_ACCEL = 1.90
CURVE_SPEED_FLOOR = 30.0 * CV.KPH_TO_MS
MAP_CURVE_FACTOR = 1.20


def is_enabled(CP) -> bool:
  return bool(
    CP.brand == "gm" and
    str(CP.carFingerprint) == TRAVERSE_FINGERPRINT and
    CP.openpilotLongitudinalControl
  )


def get_max_accel(v_ego: float) -> float:
  return float(np.interp(v_ego, MAX_ACCEL_BP, MAX_ACCEL_V))
