from types import SimpleNamespace

import pytest

from openpilot.common.constants import CV
from openpilot.sunnypilot.selfdrive.controls.lib.longitudinal_planner import apply_icbm_accel_target, apply_icbm_target


def icbm_target(speed_kph: float, active: bool = True):
  return SimpleNamespace(automaticControlActive=active, automaticTargetSpeedKph=speed_kph)


def test_active_icbm_target_caps_openpilot_long_cruise():
  assert apply_icbm_target(icbm_target(50), 100 * CV.KPH_TO_MS) == pytest.approx(50 * CV.KPH_TO_MS)


def test_inactive_icbm_target_does_not_change_cruise():
  cruise = 100 * CV.KPH_TO_MS
  assert apply_icbm_target(icbm_target(50, active=False), cruise) == cruise


@pytest.mark.parametrize("target", [0, 19, 141, float("inf"), float("nan")])
def test_invalid_icbm_target_is_ignored(target):
  cruise = 100 * CV.KPH_TO_MS
  assert apply_icbm_target(icbm_target(target), cruise) == cruise


def test_icbm_never_raises_driver_cruise_target():
  cruise = 80 * CV.KPH_TO_MS
  assert apply_icbm_target(icbm_target(100), cruise) == cruise


def test_icbm_releases_propulsion_instead_of_requesting_early_braking():
  accel = apply_icbm_accel_target(icbm_target(65), 67 * CV.KPH_TO_MS, 0.3, 80 * CV.KPH_TO_MS)
  assert accel == 0.0


def test_icbm_large_speed_error_still_starts_from_coast_target():
  accel = apply_icbm_accel_target(icbm_target(50), 80 * CV.KPH_TO_MS, 0.3, 100 * CV.KPH_TO_MS)
  assert accel == 0.0


def test_icbm_does_not_brake_below_target():
  assert apply_icbm_accel_target(icbm_target(60), 55 * CV.KPH_TO_MS, 0.4, 80 * CV.KPH_TO_MS) == 0.4


def test_icbm_starts_coasting_when_target_is_near_current_speed():
  accel = apply_icbm_accel_target(icbm_target(60), 58 * CV.KPH_TO_MS, 0.4, 80 * CV.KPH_TO_MS)
  assert accel == 0.0


def test_inactive_icbm_does_not_change_accel():
  assert apply_icbm_accel_target(icbm_target(50, active=False), 80 * CV.KPH_TO_MS, 0.4, 100 * CV.KPH_TO_MS) == 0.4
