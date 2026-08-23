import pytest

from cereal import car
from openpilot.common.constants import CV
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_carrot_long_profile import (
  A_CHANGE_COST_STARTING,
  CURVE_SPEED_FLOOR,
  MAP_CURVE_FACTOR,
  MAX_ACCEL_V,
  PID_KF,
  PID_KI,
  PID_KP,
  V_EGO_STOPPING,
  VISION_CURVE_FACTOR,
  get_max_accel,
  is_enabled,
)


def make_cp(fingerprint="CHEVROLET_TRAVERSE", brand="gm", openpilot_long=True):
  cp = car.CarParams.new_message()
  cp.carFingerprint = fingerprint
  cp.brand = brand
  cp.openpilotLongitudinalControl = openpilot_long
  return cp


def test_profile_is_traverse_longitudinal_only():
  assert is_enabled(make_cp())
  assert not is_enabled(make_cp(fingerprint="CHEVROLET_BOLT_EUV"))
  assert not is_enabled(make_cp(brand="hyundai"))
  assert not is_enabled(make_cp(openpilot_long=False))


@pytest.mark.parametrize(("speed_kph", "expected"), [
  (0, 1.00),
  (10, 0.95),
  (40, 0.60),
  (60, 0.55),
  (80, 0.55),
  (110, 0.50),
  (140, 0.50),
])
def test_carrot_max_accel_curve(speed_kph, expected):
  assert get_max_accel(speed_kph * CV.KPH_TO_MS) == pytest.approx(expected)


def test_carrot_profile_scalars():
  assert (PID_KP, PID_KI, PID_KF) == (1.0, 0.0, 1.0)
  assert V_EGO_STOPPING == 0.5
  assert A_CHANGE_COST_STARTING == 10.0
  assert VISION_CURVE_FACTOR == 0.60
  assert CURVE_SPEED_FLOOR == pytest.approx(30 * CV.KPH_TO_MS)
  assert MAP_CURVE_FACTOR == 1.20
  assert MAX_ACCEL_V == [1.0, 0.95, 0.60, 0.55, 0.55, 0.50, 0.50]
