from types import SimpleNamespace

import pytest

from openpilot.sunnypilot.selfdrive.controls.lib.wayon_carrot_long_profile import should_force_decel


@pytest.mark.parametrize("driver_unresponsive", [False, True])
@pytest.mark.parametrize("soft_disabling", [False, True])
@pytest.mark.parametrize("vehicle", ["traverse", "other_gm", "other_brand", "stock_long"])
def test_forced_decel_policy_preserves_driver_monitoring_and_other_vehicles(vehicle, driver_unresponsive, soft_disabling):
  cp = SimpleNamespace(brand="gm", carFingerprint="CHEVROLET_TRAVERSE", openpilotLongitudinalControl=True)
  if vehicle == "other_gm":
    cp.carFingerprint = "CHEVROLET_BOLT_EUV"
  elif vehicle == "other_brand":
    cp.brand = "hyundai"
  elif vehicle == "stock_long":
    cp.openpilotLongitudinalControl = False
  assert should_force_decel(cp, driver_unresponsive, soft_disabling) == (
    driver_unresponsive or (soft_disabling and vehicle != "traverse"))
