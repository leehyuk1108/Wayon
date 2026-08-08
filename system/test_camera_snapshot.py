from types import SimpleNamespace

from openpilot.system.camerad.snapshot import exposure_near_target


def frame(measured, target):
  return SimpleNamespace(measuredGreyFraction=measured, targetGreyFraction=target)


def test_exposure_near_target_rejects_dark_startup_frame():
  assert not exposure_near_target(frame(0.07, 0.13), 0.78)


def test_exposure_near_target_accepts_converged_frame():
  assert exposure_near_target(frame(0.11, 0.13), 0.78)


def test_exposure_near_target_rejects_missing_measurement():
  assert not exposure_near_target(frame(0.0, 0.0), 0.78)
