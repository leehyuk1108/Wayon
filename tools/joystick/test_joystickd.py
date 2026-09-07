import pytest

from openpilot.tools.joystick.remote_control_limits import (
  REMOTE_MAX_ACCEL,
  REMOTE_MAX_BRAKE,
  REMOTE_MAX_SPEED_MPS,
  REMOTE_MAX_STEER,
  REMOTE_MIN_STEER_SPEED_MPS,
  REMOTE_FULL_STEER_SPEED_MPS,
  REMOTE_INITIAL_CRUISE_KPH,
  REMOTE_MAX_SPEED_KPH,
  joystick_cc_enabled,
  remote_hud_set_speed_kph,
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


@pytest.mark.parametrize("v_cruise_cluster, expected", [
  (float("nan"), REMOTE_INITIAL_CRUISE_KPH),
  (0.0, REMOTE_INITIAL_CRUISE_KPH),
  (255.0, REMOTE_INITIAL_CRUISE_KPH),
  (40.0, 40.0),
  (80.0, REMOTE_MAX_SPEED_KPH),
])
def test_remote_hud_set_speed_is_valid_and_capped(v_cruise_cluster, expected):
  assert remote_hud_set_speed_kph(v_cruise_cluster) == expected


def test_remote_cc_stays_synchronized_when_web_input_drops():
  assert joystick_cc_enabled(True, True, True, True)
  assert joystick_cc_enabled(True, True, False, True)
  assert joystick_cc_enabled(True, True, False, False)
  assert not joystick_cc_enabled(False, True, True, True)


def test_debug_joystick_still_requires_live_ready_input():
  assert joystick_cc_enabled(True, False, True, True)
  assert not joystick_cc_enabled(True, False, False, True)
  assert not joystick_cc_enabled(True, False, True, False)
