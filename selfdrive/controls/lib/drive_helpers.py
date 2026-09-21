import math

import numpy as np
from openpilot.common.constants import ACCELERATION_DUE_TO_GRAVITY
from openpilot.common.realtime import DT_CTRL, DT_MDL

MIN_SPEED = 1.0
CONTROL_N = 17
CAR_ROTATION_RADIUS = 0.0
# This is a turn radius smaller than most cars can achieve
MAX_CURVATURE = 0.2
MAX_VEL_ERR = 5.0  # m/s
MIN_STABLE_DELAY = 0.3

# EU guidelines
MAX_LATERAL_JERK = 5.0  # m/s^3
MAX_LATERAL_ACCEL_NO_ROLL = 3.0  # m/s^2
MODEL_CURVATURE_GUARD_MIN_SPEED = 5.0  # m/s
MODEL_CURVATURE_GUARD_MAX_LAT_ACCEL_DELTA = 1.25  # m/s^2
MODEL_CURVATURE_GUARD_MAX_LATERAL_JERK = 2.0  # m/s^3
MODEL_CURVATURE_GUARD_PATH_TIME = 0.3  # seconds


def clamp(val, min_val, max_val):
  clamped_val = float(np.clip(val, min_val, max_val))
  return clamped_val, clamped_val != val

def smooth_value(val, prev_val, tau, dt=DT_MDL):
  alpha = 1 - np.exp(-dt/tau) if tau > 0 else 1
  return alpha * val + (1 - alpha) * prev_val

def clip_curvature(v_ego, prev_curvature, new_curvature, roll, max_lateral_jerk=MAX_LATERAL_JERK) -> tuple[float, bool]:
  # This function respects ISO lateral jerk and acceleration limits + a max curvature
  v_ego = max(v_ego, MIN_SPEED)
  max_curvature_rate = max_lateral_jerk / (v_ego ** 2)  # inexact calculation, check https://github.com/commaai/openpilot/pull/24755
  new_curvature = np.clip(new_curvature,
                          prev_curvature - max_curvature_rate * DT_CTRL,
                          prev_curvature + max_curvature_rate * DT_CTRL)

  roll_compensation = roll * ACCELERATION_DUE_TO_GRAVITY
  max_lat_accel = MAX_LATERAL_ACCEL_NO_ROLL + roll_compensation
  min_lat_accel = -MAX_LATERAL_ACCEL_NO_ROLL + roll_compensation
  new_curvature, limited_accel = clamp(new_curvature, min_lat_accel / v_ego ** 2, max_lat_accel / v_ego ** 2)

  new_curvature, limited_max_curv = clamp(new_curvature, -MAX_CURVATURE, MAX_CURVATURE)
  return float(new_curvature), limited_accel or limited_max_curv


def get_curvature_from_path_poly(x_coeffs, y_coeffs, t=MODEL_CURVATURE_GUARD_PATH_TIME) -> float:
  if len(x_coeffs) < 3 or len(y_coeffs) < 3:
    return math.nan

  x_coeffs = np.asarray(x_coeffs, dtype=float)
  y_coeffs = np.asarray(y_coeffs, dtype=float)
  x_rate = np.polynomial.polynomial.polyval(t, np.polynomial.polynomial.polyder(x_coeffs))
  y_rate = np.polynomial.polynomial.polyval(t, np.polynomial.polynomial.polyder(y_coeffs))
  x_accel = np.polynomial.polynomial.polyval(t, np.polynomial.polynomial.polyder(x_coeffs, 2))
  y_accel = np.polynomial.polynomial.polyval(t, np.polynomial.polynomial.polyder(y_coeffs, 2))
  denominator = (x_rate ** 2 + y_rate ** 2) ** 1.5
  if not np.isfinite(denominator) or denominator < 1e-6:
    return math.nan

  return float((x_rate * y_accel - y_rate * x_accel) / denominator)


def guard_model_curvature(v_ego, model_curvature, path_curvature) -> tuple[float, bool]:
  if v_ego < MODEL_CURVATURE_GUARD_MIN_SPEED or not np.isfinite(model_curvature) or not np.isfinite(path_curvature):
    return float(model_curvature), False

  speed_squared = v_ego ** 2
  model_lat_accel = abs(model_curvature) * speed_squared
  lat_accel_delta = abs(model_curvature - path_curvature) * speed_squared
  if model_lat_accel <= MODEL_CURVATURE_GUARD_MAX_LAT_ACCEL_DELTA or lat_accel_delta <= MODEL_CURVATURE_GUARD_MAX_LAT_ACCEL_DELTA:
    return float(model_curvature), False

  max_curvature_delta = MODEL_CURVATURE_GUARD_MAX_LAT_ACCEL_DELTA / speed_squared
  guarded_curvature = np.clip(model_curvature,
                              path_curvature - max_curvature_delta,
                              path_curvature + max_curvature_delta)
  return float(guarded_curvature), True


def get_accel_from_plan(speeds, accels, t_idxs, action_t=DT_MDL, vEgoStopping=0.3):
  if len(speeds) == len(t_idxs):
    v_now = speeds[0]
    a_now = accels[0]
    if action_t < MIN_STABLE_DELAY:
      v_target = v_now + (action_t / MIN_STABLE_DELAY) * (np.interp(MIN_STABLE_DELAY, t_idxs, speeds) - v_now)
    else:
      v_target = np.interp(action_t, t_idxs, speeds)
    a_target = 2 * (v_target - v_now) / (action_t) - a_now
  else:
    v_now = 0.0
    v_target = 0.0
    a_target = 0.0
  should_stop = (v_now < vEgoStopping and a_target < 0.1)
  return a_target, should_stop

def curv_from_psis(psi_target, psi_rate, vego, action_t):
  vego = np.clip(vego, MIN_SPEED, np.inf)
  curv_from_psi = psi_target / (vego * action_t)
  return 2*curv_from_psi - psi_rate / vego

def get_curvature_from_plan(yaws, yaw_rates, t_idxs, vego, action_t):
  if action_t < MIN_STABLE_DELAY:
    psi_target = (action_t / MIN_STABLE_DELAY) * np.interp(MIN_STABLE_DELAY, t_idxs, yaws)
  else:
    psi_target = np.interp(action_t, t_idxs, yaws)
  psi_rate = yaw_rates[0]
  return curv_from_psis(psi_target, psi_rate, vego, action_t)
