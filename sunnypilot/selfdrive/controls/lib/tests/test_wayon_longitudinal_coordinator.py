from types import SimpleNamespace

import pytest

from openpilot.common.constants import CV
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_longitudinal_coordinator import (
  LongitudinalResponseLearner,
  LowSpeedStopController,
  WayonCoastController,
  empty_response_profile,
  learned_delay_for_speed,
  speed_bin_index,
)
from openpilot.sunnypilot.selfdrive.controls.lib import wayon_longitudinal_coordinator as coordinator_module


class FakeParams:
  def __init__(self, enabled=True):
    self.values = {"WayonLongitudinalLearning": b"1" if enabled else b"0"}

  def get(self, key):
    return self.values.get(key)

  def get_bool(self, key):
    return self.values.get(key) == b"1"

  def put(self, key, value):
    self.values[key] = value


def lead(d_rel=20.0, v_rel=0.0):
  return SimpleNamespace(status=True, dRel=d_rel, vRel=v_rel)


def test_speed_bins_cover_traverse_learning_ranges():
  assert speed_bin_index(5.0 * CV.KPH_TO_MS) == 0
  assert speed_bin_index(20.0 * CV.KPH_TO_MS) == 1
  assert speed_bin_index(45.0 * CV.KPH_TO_MS) == 2
  assert speed_bin_index(80.0 * CV.KPH_TO_MS) == 3


def test_coasting_requires_stability_and_exits_for_camera_or_closing_lead():
  controller = WayonCoastController()
  for _ in range(controller.ENTER_FRAMES - 1):
    assert not controller.update(True, 20.0, 20.2, -0.1, 0.0, False)
  assert controller.update(True, 20.0, 20.2, -0.1, 0.0, False)
  assert not controller.update(True, 20.0, 20.2, -0.1, 0.0, True)

  for _ in range(controller.ENTER_FRAMES):
    controller.update(True, 20.0, 20.2, -0.1, 0.0, False)
  assert controller.state.active
  assert not controller.update(True, 20.0, 20.2, -0.1, 0.0, False, lead(10.0, -2.0))


def test_low_speed_stop_releases_then_recaptures_with_verified_lead():
  controller = LowSpeedStopController()
  for _ in range(100):
    release = controller.update(-0.8, 2.0 * CV.KPH_TO_MS, -0.5, False, True, lead(8.0))
  assert controller.phase == "release"
  assert -0.8 < release < -0.2

  for _ in range(100):
    capture = controller.update(-0.8, 0.5 * CV.KPH_TO_MS, -0.2, False, True, lead(8.0))
  assert controller.phase == "capture"
  assert capture < release
  assert capture <= -0.25


def test_low_speed_stop_never_relaxes_close_or_unverified_stop():
  controller = LowSpeedStopController()
  assert controller.update(-0.8, 2.0 * CV.KPH_TO_MS, -0.5, False, True, lead(3.2)) == -0.8
  assert controller.phase == "safety"
  assert controller.update(-0.8, 2.0 * CV.KPH_TO_MS, -0.5, False, True, None) == -0.8
  assert controller.phase == "unverified"


def test_response_learning_stays_shadow_until_confident_then_is_bounded():
  learner = LongitudinalResponseLearner(0.5, FakeParams())
  learned = learner.profile["bins"][2]
  learned["samples"] = 299
  learned["brakeGain"] = 0.5
  assert learner.correction(-1.0, 45.0 * CV.KPH_TO_MS) == -1.0

  learned["samples"] = 300
  assert learner.correction(-1.0, 45.0 * CV.KPH_TO_MS) == pytest.approx(-1.15)
  learned["gasGain"] = 1.5
  assert learner.correction(1.0, 45.0 * CV.KPH_TO_MS) == pytest.approx(0.85)


def test_learned_delay_requires_multiple_observations():
  profile = empty_response_profile(0.5)
  learned = profile["bins"][3]
  learned["delay"] = 0.25
  learned["delaySamples"] = 5
  assert learned_delay_for_speed(profile, 80.0 * CV.KPH_TO_MS, 0.5) == 0.5
  learned["delaySamples"] = 6
  assert learned_delay_for_speed(profile, 80.0 * CV.KPH_TO_MS, 0.5) == 0.25


def test_response_delay_is_observed_from_command_to_accel_change(monkeypatch):
  clock = SimpleNamespace(now=0.0)
  monkeypatch.setattr(coordinator_module.time, "monotonic", lambda: clock.now)
  learner = LongitudinalResponseLearner(0.5, FakeParams())
  speed = 45.0 * CV.KPH_TO_MS

  for _ in range(10):
    learner.update(0.0, 0.0, speed, True, 0.0, False, False, False)
    clock.now += 0.01
  for _ in range(10):
    learner.update(0.25, 0.0, speed, True, 0.0, False, False, False)
    clock.now += 0.01
  for _ in range(10):
    learner.update(0.25, 0.0, speed, True, 0.0, False, False, False)
    clock.now += 0.01
  learner.update(0.25, 0.1, speed, True, 0.0, False, False, False)

  assert learner.profile["bins"][2]["delaySamples"] == 1
