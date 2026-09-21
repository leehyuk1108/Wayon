import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from openpilot.common.constants import CV
from opendbc.car.gm.values import get_traverse_stopping_accel_floor
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_longitudinal_coordinator import (
  LeadApproachController,
  LeadTrendAnticipator,
  LongitudinalResponseLearner,
  LowSpeedStopController,
  WayonCoastController,
  empty_response_profile,
  get_lead_accel_safety_cap,
  icbm_blocks_coast,
  learned_delay_for_speed,
  speed_bin_index,
)


def radar_lead(**overrides):
  values = {
    "status": True,
    "radar": True,
    "radarTrackId": 7,
    "dRel": 15.0,
    "vRel": 1.0,
    "vLeadK": 4.6,
    "aLeadK": 0.3,
  }
  values.update(overrides)
  return SimpleNamespace(**values)


def test_lead_trend_releases_throttle_before_relative_speed_turns_negative():
  anticipator = LeadTrendAnticipator()
  lead = radar_lead()

  results = [anticipator.update(True, 3.6, 1.4, 0.9, lead)
             for _ in range(LeadTrendAnticipator.ENTER_FRAMES)]

  assert not any(results[:-1])
  assert results[-1]
  assert lead.vRel > 0.0


def test_lead_trend_ignores_constant_opening_and_single_sample_noise():
  anticipator = LeadTrendAnticipator()
  lead = radar_lead(aLeadK=0.9)
  assert not any(anticipator.update(True, 3.6, 1.4, 0.9, lead) for _ in range(50))

  lead.aLeadK = 0.0
  assert not anticipator.update(True, 3.6, 1.4, 0.9, lead)
  lead.aLeadK = 0.9
  assert not any(anticipator.update(True, 3.6, 1.4, 0.9, lead) for _ in range(50))


def test_lead_trend_does_not_override_planned_braking_or_vision_lead():
  anticipator = LeadTrendAnticipator()
  lead = radar_lead()
  for _ in range(LeadTrendAnticipator.ENTER_FRAMES):
    anticipator.update(True, 3.6, 1.4, 0.9, lead)
  assert anticipator.state.active
  assert not anticipator.update(True, 3.6, -0.2, 0.9, lead)

  lead.radar = False
  assert not anticipator.update(True, 3.6, 1.4, 0.9, lead)


def test_lead_trend_ignores_distant_lead():
  anticipator = LeadTrendAnticipator()
  lead = radar_lead(dRel=80.0)
  assert not any(anticipator.update(True, 10.0, 1.0, 0.9, lead) for _ in range(50))
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
  closing_lead = lead(10.0, -2.0)
  lead_cap = get_lead_accel_safety_cap(20.0, closing_lead)
  assert lead_cap is not None
  assert not controller.update(True, 20.0, 20.2, -0.1, 0.0, False, closing_lead,
                               lead_accel_cap=lead_cap)


def test_icbm_restore_allows_coasting_only_without_active_slowdown():
  icbm = SimpleNamespace(automaticControlActive=True, controlSource="restore", sectionPhase="inactive",
                         automaticTargetSpeedKph=110.0, requiredAccel=0.0)
  v_ego = 85.0 * CV.KPH_TO_MS
  assert not icbm_blocks_coast(icbm, v_ego)

  controller = WayonCoastController()
  distant_lead = lead(d_rel=50.0, v_rel=-0.3)
  for _ in range(controller.ENTER_FRAMES - 1):
    assert not controller.update(True, v_ego, v_ego + 0.2, -0.1, 0.0,
                                 icbm_blocks_coast(icbm, v_ego), distant_lead)
  assert controller.update(True, v_ego, v_ego + 0.2, -0.1, 0.0,
                           icbm_blocks_coast(icbm, v_ego), distant_lead)

  close_lead = lead(d_rel=18.0, v_rel=-4.0)
  lead_cap = get_lead_accel_safety_cap(v_ego, close_lead)
  assert lead_cap is not None
  assert not controller.update(True, v_ego, v_ego + 0.2, -0.1, 0.0,
                               icbm_blocks_coast(icbm, v_ego), close_lead, lead_accel_cap=lead_cap)

  for source in ("camera", "curve", "section"):
    icbm.controlSource = source
    assert icbm_blocks_coast(icbm, v_ego)
  icbm.controlSource = "restore"
  icbm.sectionPhase = "active"
  assert icbm_blocks_coast(icbm, v_ego)
  icbm.sectionPhase = "inactive"
  icbm.automaticTargetSpeedKph = 80.0
  assert icbm_blocks_coast(icbm, v_ego)
  icbm.automaticTargetSpeedKph = 110.0
  icbm.requiredAccel = -0.2
  assert icbm_blocks_coast(icbm, v_ego)
  icbm.requiredAccel = 0.0
  icbm.automaticTargetSpeedKph = float("nan")
  assert icbm_blocks_coast(icbm, v_ego)


def test_coasting_and_lead_cap_share_the_same_urgency_decision():
  controller = WayonCoastController()
  closing_lead = lead(28.0, -4.0)
  lead_cap = get_lead_accel_safety_cap(12.0, closing_lead)
  assert lead_cap is not None

  for _ in range(controller.ENTER_FRAMES + 2):
    assert not controller.update(True, 12.0, 12.2, -0.05, 0.0, False, closing_lead,
                                 lead_accel_cap=lead_cap)
  assert not controller.state.active


def test_stationary_lead_extends_braking_horizon_only_after_stable_track():
  controller = LeadApproachController()
  stopped_lead = radar_lead(radarTrackId=41, dRel=72.0, vRel=-8.0, vLeadK=0.0)

  for _ in range(controller.STATIONARY_CONFIRM_FRAMES - 1):
    assert controller.update(True, 8.0, stopped_lead, response_delay=0.15) is None

  cap = controller.update(True, 8.0, stopped_lead, response_delay=0.15)
  assert cap is not None
  assert -0.5 < cap < 0.0


def test_stationary_lead_confirmation_resets_when_radar_track_changes():
  controller = LeadApproachController()
  stopped_lead = radar_lead(radarTrackId=41, dRel=72.0, vRel=-8.0, vLeadK=0.0)
  for _ in range(controller.STATIONARY_CONFIRM_FRAMES - 1):
    controller.update(True, 8.0, stopped_lead, response_delay=0.15)

  stopped_lead.radarTrackId = 42
  assert controller.update(True, 8.0, stopped_lead, response_delay=0.15) is None
  assert controller.stationary_frames == 1


def test_recorded_stationary_lead_route_never_coasts_or_drops_braking():
  fixture_path = Path(__file__).parent / "fixtures" / "traverse_stationary_lead_a5.json"
  fixture = json.loads(fixture_path.read_text())
  approach = LeadApproachController()
  coast = WayonCoastController()
  caps = []

  for sample in fixture["samples"]:
    v_ego = sample["speedKph"] * CV.KPH_TO_MS
    route_lead = radar_lead(
      radarTrackId=sample["trackId"], dRel=sample["dRel"], vRel=sample["vRel"],
      vLeadK=sample["vLeadK"],
    )
    cap = approach.update(True, v_ego, route_lead, fixture["responseDelay"])
    caps.append(cap)
    assert cap is not None
    assert not coast.update(
      True, v_ego, v_ego + 0.1, sample["requestedAccel"], 0.0, False, route_lead,
      measured_accel=sample["requestedAccel"], previous_accel=sample["requestedAccel"],
      lead_accel_cap=cap,
    )
    assert min(sample["requestedAccel"], cap) < 0.0

  # At first detection the recorded planner request was mild; the stopped-lead cap
  # must already request earlier braking rather than waiting for the gap to collapse.
  assert caps[0] < fixture["samples"][0]["requestedAccel"]


def test_low_speed_follow_coasts_only_with_stable_radar_lead():
  controller = WayonCoastController()
  stable_lead = lead(d_rel=8.0, v_rel=0.05, a_lead=0.1)
  for _ in range(controller.LOW_SPEED_ENTER_FRAMES - 1):
    assert not controller.update(True, 3.0, 3.1, -0.08, 0.0, False, stable_lead)
  assert controller.update(True, 3.0, 3.1, -0.08, 0.0, False, stable_lead)

  assert not controller.update(True, 3.0, 3.1, -0.25, 0.0, False, lead(8.0, -0.6))
  assert not controller.update(True, 3.0, 3.1, -0.08, 0.0, False,
                               lead(8.0, 0.0, radar=False))


def test_downhill_low_speed_follow_can_coast_instead_of_gas_brake_hunting():
  controller = WayonCoastController()
  stable_lead = lead(d_rel=17.0, v_rel=0.6, a_lead=0.1)
  pitch = -1.7 * CV.DEG_TO_RAD
  results = [controller.update(True, 3.9, 4.2, 0.24, pitch, False, stable_lead,
                               measured_accel=0.05, previous_accel=0.0)
             for _ in range(controller.LOW_SPEED_ENTER_FRAMES)]

  assert results[-1]
  assert controller.natural_accel_initialized
  assert not controller.update(True, 3.9, 4.2, -0.5, pitch, False,
                               lead(d_rel=6.5, v_rel=-1.2),
                               measured_accel=0.1, previous_accel=0.0)


def test_meaningful_uphill_exits_coasting_before_speed_drops():
  controller = WayonCoastController()
  for _ in range(controller.ENTER_FRAMES):
    controller.update(True, 20.0, 20.2, -0.1, 0.0, False)
  assert controller.state.active

  assert not controller.update(True, 20.0, 20.2, -0.1, 1.0 * CV.DEG_TO_RAD, False)
  assert not controller.state.active


def test_low_speed_stop_only_tapers_final_stop_with_verified_lead():
  controller = LowSpeedStopController()
  assert controller.update(-0.4, 2.6 * CV.KPH_TO_MS, -0.2, False, True, lead(8.0)) == -0.4
  assert controller.phase == "approach"

  tapered = -0.4
  for _ in range(30):
    tapered = controller.update(tapered, 0.7 * CV.KPH_TO_MS, -0.2, False, True, lead(8.0))
  assert controller.phase == "taper"
  assert tapered == pytest.approx(get_traverse_stopping_accel_floor(0.7 * CV.KPH_TO_MS))

  for _ in range(controller.HOLD_CONFIRM_FRAMES - 1):
    assert controller.update(-0.2, 0.0, 0.0, True, True, lead(8.0)) <= -0.2
    assert controller.phase == "settle"
  assert controller.update(-0.2, 0.0, 0.0, True, True, lead(8.0)) == pytest.approx(-0.3)
  assert controller.phase == "hold"


def test_low_speed_stop_avoids_recorded_stopping_transition_brake_pulse():
  controller = LowSpeedStopController()
  # The recorded stop entered stopping at 2.08 km/h with 5.88 m to the lead.
  # The old 1.5 km/h taper threshold let the stopping ramp reach 96 raw brake.
  samples = [
    (2.08, -0.55, 5.88, -0.62),
    (1.99, -0.63, 5.75, -0.50),
    (1.84, -0.71, 5.75, -0.50),
    (1.70, -0.79, 5.62, -0.50),
    (1.70, -0.87, 5.62, -0.50),
    (1.51, -0.95, 5.62, -0.50),
    (1.32, -1.03, 5.50, -0.38),
  ]
  outputs = [controller.update(requested, speed * CV.KPH_TO_MS, -0.3, False, True,
                               lead(distance, relative_speed))
             for speed, requested, distance, relative_speed in samples]

  assert controller.phase == "taper"
  assert min(outputs) >= -0.55
  assert outputs[-1] == pytest.approx(get_traverse_stopping_accel_floor(1.32 * CV.KPH_TO_MS))


def test_low_speed_stop_preserves_braking_when_closing_quickly_above_old_threshold():
  controller = LowSpeedStopController()
  assert controller.update(-0.9, 2.1 * CV.KPH_TO_MS, -0.3, False, True,
                           lead(3.2, -0.9)) == -0.9
  assert controller.phase == "safety"


def test_low_speed_stop_relaxes_strong_request_with_verified_reserve():
  controller = LowSpeedStopController()
  speed = 0.7 * CV.KPH_TO_MS
  output = -1.1
  for _ in range(20):
    output = controller.update(-1.1, speed, -0.5, False, True, lead(5.0, -0.2))
  assert controller.phase == "taper"
  assert output == pytest.approx(get_traverse_stopping_accel_floor(speed))


def test_low_speed_stop_returns_the_same_floor_as_the_gm_output_layer():
  controller = LowSpeedStopController()
  speed = 0.7 * CV.KPH_TO_MS

  output = controller.update(-0.2, speed, -0.1, False, True, lead(5.0, -0.2))

  assert output == pytest.approx(get_traverse_stopping_accel_floor(speed))


def test_low_speed_stop_tapers_recorded_close_stable_lead():
  controller = LowSpeedStopController()
  output = -1.67
  recorded_lead = lead(3.8, -0.62)

  for _ in range(30):
    output = controller.update(-1.67, 1.44 * CV.KPH_TO_MS, -0.95, False, True, recorded_lead)

  assert controller.phase == "taper"
  assert output == pytest.approx(get_traverse_stopping_accel_floor(1.44 * CV.KPH_TO_MS))


def test_low_speed_stop_close_taper_has_distance_and_closing_hysteresis():
  controller = LowSpeedStopController()
  output = controller.update(-1.4, 1.0 * CV.KPH_TO_MS, -0.6, False, True, lead(3.6, -0.65))
  assert controller.phase == "taper"
  assert output > -1.4

  output = controller.update(-1.4, 0.8 * CV.KPH_TO_MS, -0.5, False, True, lead(3.3, -0.75))
  assert controller.phase == "taper"
  assert output > -1.4

  assert controller.update(-1.4, 0.8 * CV.KPH_TO_MS, -0.5, False, True, lead(3.15, -0.75)) == -1.4
  assert controller.phase == "safety"


def test_low_speed_stop_does_not_taper_fast_closing_close_lead():
  controller = LowSpeedStopController()
  speed = 1.0 * CV.KPH_TO_MS

  assert controller.update(-1.4, speed, -0.6, False, True, lead(3.8, -0.85)) == -1.4
  assert controller.phase == "safety"


def test_low_speed_stop_does_not_raise_hold_pressure_on_premature_standstill():
  controller = LowSpeedStopController()
  safe_lead = lead(5.0, -0.25)
  output = -1.2
  for _ in range(25):
    output = controller.update(-1.2, 0.2, -0.4, False, True, safe_lead)
  assert output == pytest.approx(get_traverse_stopping_accel_floor(0.2))

  output = controller.update(-1.2, 0.03, -1.4, True, True, safe_lead)

  assert output <= get_traverse_stopping_accel_floor(0.03)
  assert controller.phase == "taper"


def test_low_speed_stop_never_relaxes_close_or_unverified_stop():
  controller = LowSpeedStopController()
  speed = 0.5 * CV.KPH_TO_MS
  assert controller.update(-0.4, speed, -0.2, False, True, lead(3.2)) == -0.4
  assert controller.phase == "safety"
  assert controller.update(-0.4, speed, -0.2, False, True, None) == -0.4
  assert controller.phase == "unverified"


def test_response_learning_stays_shadow_until_confident_then_is_bounded(tmp_path):
  learner = LongitudinalResponseLearner(0.5, str(tmp_path / "profile.json"))
  learned = learner.profile["bins"][2]
  learned["brakeSamples"] = 99
  learned["brakeGain"] = 0.5
  assert learner.correction(-1.0, 45.0 * CV.KPH_TO_MS) == -1.0

  learned["brakeSamples"] = 550
  assert learner.correction(-1.0, 45.0 * CV.KPH_TO_MS) == pytest.approx(-1.075)
  learned["brakeSamples"] = 1000
  assert learner.correction(-1.0, 45.0 * CV.KPH_TO_MS) == pytest.approx(-1.15)
  learned["gasGain"] = 1.5
  learned["gasSamples"] = 1000
  assert learner.correction(1.0, 45.0 * CV.KPH_TO_MS) == pytest.approx(0.85)


def test_response_learning_uses_direction_specific_confidence(tmp_path):
  learner = LongitudinalResponseLearner(0.5, str(tmp_path / "profile.json"))
  learned = learner.profile["bins"][1]
  learned.update({"gasSamples": 1000, "brakeSamples": 20, "gasGain": 0.5, "brakeGain": 0.5})

  assert learner.correction(1.0, 20.0 * CV.KPH_TO_MS) == pytest.approx(1.15)
  assert learner.correction(-1.0, 20.0 * CV.KPH_TO_MS) == -1.0


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
  learner.profile["bins"][1]["gasSamples"] = 123
  learner.profile["bins"][1]["brakeSamples"] = 198
  learner.save()

  reloaded = LongitudinalResponseLearner(0.5, profile_path)
  assert reloaded.profile["bins"][1]["samples"] == 321
  assert reloaded.profile["bins"][1]["gasSamples"] == 123
  assert reloaded.profile["bins"][1]["brakeSamples"] == 198
  assert not (tmp_path / "profile" / "response.json.tmp").exists()
