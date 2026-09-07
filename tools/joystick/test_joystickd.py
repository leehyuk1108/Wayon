import pytest

from openpilot.tools.joystick.remote_control_limits import (
  REMOTE_MAX_ACCEL,
  REMOTE_MAX_BRAKE,
  REMOTE_MAX_SPEED_MPS,
  REMOTE_MAX_STEER,
  REMOTE_MIN_STEER_SPEED_MPS,
  REMOTE_FULL_STEER_SPEED_MPS,
  remote_control_limits,
)


def test_remote_control_limits_bound_actuation():
  accel, steer = remote_control_limits(1.0, 1.0, REMOTE_FULL_STEER_SPEED_MPS)
  assert accel == REMOTE_MAX_ACCEL
  assert steer == REMOTE_MAX_STEER

  brake, steer = remote_control_limits(-1.0, -1.0, REMOTE_FULL_STEER_SPEED_MPS)
  assert brake == -REMOTE_MAX_BRAKE
  assert steer == -REMOTE_MAX_STEER


def test_remote_speed_governor_removes_accel_at_limit():
  accel, _ = remote_control_limits(1.0, 0.0, REMOTE_MAX_SPEED_MPS)
  assert accel == 0.0

  overspeed_accel, _ = remote_control_limits(0.0, 0.0, REMOTE_MAX_SPEED_MPS + 0.2)
  assert overspeed_accel == pytest.approx(-0.3)


def test_remote_steering_ramps_in_above_ten_kph():
  _, below = remote_control_limits(0.0, 1.0, REMOTE_MIN_STEER_SPEED_MPS - 0.1)
  _, halfway = remote_control_limits(0.0, 1.0, (REMOTE_MIN_STEER_SPEED_MPS + REMOTE_FULL_STEER_SPEED_MPS) / 2)
  _, full = remote_control_limits(0.0, 1.0, REMOTE_FULL_STEER_SPEED_MPS)
  assert below == 0.0
  assert halfway == pytest.approx(REMOTE_MAX_STEER / 2)
  assert full == REMOTE_MAX_STEER
