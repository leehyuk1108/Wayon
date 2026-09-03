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


def lead(d_rel=20.0, v_rel=0.0, radar=True, a_lead=0.0):
  return SimpleNamespace(status=True, radar=radar, dRel=d_rel, vRel=v_rel, aLeadK=a_lead)


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


def test_low_speed_follow_coasts_only_with_stable_radar_lead():
  controller = WayonCoastController()
  stable_lead = lead(d_rel=8.0, v_rel=0.05, a_lead=0.1)
  for _ in range(controller.LOW_SPEED_ENTER_FRAMES - 1):
    assert not controller.update(True, 3.0, 3.1, -0.08, 0.0, False, stable_lead)
  assert controller.update(True, 3.0, 3.1, -0.08, 0.0, False, stable_lead)

  assert not controller.update(True, 3.0, 3.1, -0.25, 0.0, False, lead(8.0, -0.6))
  assert not controller.update(True, 3.0, 3.1, -0.08, 0.0, False,
                               lead(8.0, 0.0, radar=False))


def test_low_speed_stop_only_tapers_final_stop_with_verified_lead():
  controller = LowSpeedStopController()
  assert controller.update(-0.4, 1.0 * CV.KPH_TO_MS, -0.2, False, True, lead(8.0)) == -0.4
  assert controller.phase == "approach"

  tapered = -0.4
  for _ in range(30):
    tapered = controller.update(tapered, 0.5 * CV.KPH_TO_MS, -0.2, False, True, lead(8.0))
  assert controller.phase == "taper"
  assert -0.4 < tapered < 0.0

  assert controller.update(-0.2, 0.0, 0.0, True, True, lead(8.0)) == -0.2
  assert controller.phase == "hold"


def test_low_speed_stop_never_relaxes_close_or_unverified_stop():
  controller = LowSpeedStopController()
  speed = 0.5 * CV.KPH_TO_MS
  assert controller.update(-0.8, speed, -0.5, False, True, lead(8.0)) == -0.8
  assert controller.phase == "safety"
  assert controller.update(-0.4, speed, -0.2, False, True, lead(3.2)) == -0.4
  assert controller.phase == "safety"
  assert controller.update(-0.4, speed, -0.2, False, True, None) == -0.4
  assert controller.phase == "unverified"


def test_response_learning_stays_shadow_until_confident_then_is_bounded(tmp_path):
  learner = LongitudinalResponseLearner(0.5, str(tmp_path / "profile.json"))
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


def test_response_delay_is_observed_from_command_to_accel_change(monkeypatch, tmp_path):
  clock = SimpleNamespace(now=0.0)
  monkeypatch.setattr(coordinator_module.time, "monotonic", lambda: clock.now)
  learner = LongitudinalResponseLearner(0.5, str(tmp_path / "profile.json"))
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


def test_response_profile_save_is_atomic_and_reloadable(tmp_path):
  profile_path = str(tmp_path / "profile" / "response.json")
  learner = LongitudinalResponseLearner(0.5, profile_path)
  learner.profile["bins"][1]["samples"] = 321
  learner.save()

  reloaded = LongitudinalResponseLearner(0.5, profile_path)
  assert reloaded.profile["bins"][1]["samples"] == 321
  assert not (tmp_path / "profile" / "response.json.tmp").exists()
