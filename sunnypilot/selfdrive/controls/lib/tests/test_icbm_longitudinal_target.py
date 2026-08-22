from types import SimpleNamespace

import pytest

from openpilot.common.constants import CV
from openpilot.sunnypilot.selfdrive.controls.lib.longitudinal_planner import apply_icbm_target


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
