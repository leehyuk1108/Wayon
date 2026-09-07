import numpy as np


REMOTE_MAX_SPEED_MPS = 50.0 / 3.6
REMOTE_MIN_STEER_SPEED_MPS = 10.0 / 3.6
REMOTE_FULL_STEER_SPEED_MPS = 15.0 / 3.6
REMOTE_MAX_ACCEL = 0.8
REMOTE_MAX_BRAKE = 1.5
REMOTE_MAX_STEER = 0.25


def remote_control_limits(long_axis: float, steer_axis: float, v_ego: float) -> tuple[float, float]:
  long_axis = float(np.clip(long_axis, -1.0, 1.0))
  steer_axis = float(np.clip(steer_axis, -1.0, 1.0))
  requested_accel = long_axis * (REMOTE_MAX_ACCEL if long_axis >= 0.0 else REMOTE_MAX_BRAKE)
  speed_governor = float(np.clip((REMOTE_MAX_SPEED_MPS - max(v_ego, 0.0)) * 1.5,
                                 -REMOTE_MAX_BRAKE, REMOTE_MAX_ACCEL))
  steer_speed_scale = float(np.interp(max(v_ego, 0.0),
                                      [REMOTE_MIN_STEER_SPEED_MPS, REMOTE_FULL_STEER_SPEED_MPS],
                                      [0.0, 1.0]))
  return min(requested_accel, speed_governor), steer_axis * REMOTE_MAX_STEER * steer_speed_scale
