from types import SimpleNamespace

import pytest

from openpilot.selfdrive.modeld.constants import ModelConstants
from openpilot.sunnypilot.selfdrive.controls.lib.longitudinal_enhancements import (
  cutin_predecel_accel,
  dynamic_a_change_cost,
  dynamic_t_follow_target,
  future_curvature,
  lead_response_factor,
  limit_accel_for_future_curve,
  ramp_t_follow,
)


def lead(**kwargs):
  values = {
    "status": True,
    "radar": True,
    "jLead": 0.0,
    "aLeadK": 0.0,
    "score": 0.0,
    "dRel": 30.0,
    "vRel": -5.0,
    "vLat": 0.5,
  }
  values.update(kwargs)
  return SimpleNamespace(**values)


def model(curvature=0.0, velocity=20.0):
  return SimpleNamespace(
    orientationRate=SimpleNamespace(z=[curvature * velocity] * ModelConstants.IDX_N),
    velocity=SimpleNamespace(x=[velocity] * ModelConstants.IDX_N),
  )


def test_future_curvature_uses_model_yaw_rate():
  assert future_curvature(model(curvature=0.012), 0.0) == pytest.approx(0.012)


def test_future_curve_only_reduces_positive_accel_limit():
  straight = limit_accel_for_future_curve(20.0, 0.0, [-3.5, 1.2], 2.5)
  curve = limit_accel_for_future_curve(20.0, 0.005, [-3.5, 1.2], 2.5)
  assert straight == [-3.5, 1.2]
  assert curve[0] == -3.5
  assert 0.0 <= curve[1] < straight[1]


def test_lead_braking_jerk_increases_response_and_follow_distance():
  braking_lead = lead(jLead=-2.0)
  response = lead_response_factor(braking_lead)
  assert response > 0.5
  assert dynamic_a_change_cost(200.0, response) < 120.0
  assert dynamic_t_follow_target(1.45, braking_lead, -0.8) > 1.45


def test_departing_radar_lead_increases_response_and_temporarily_closes_follow_gap():
  departing_lead = lead(jLead=1.5, aLeadK=0.4, vRel=0.8)
  response = lead_response_factor(departing_lead)
  assert response > 0.4
  assert dynamic_a_change_cost(200.0, response) < 140.0
  assert dynamic_t_follow_target(1.45, departing_lead, 0.0) < 1.30


def test_positive_jerk_without_opening_gap_does_not_trigger_departure_response():
  ambiguous_lead = lead(jLead=1.5, vRel=-0.1)
  assert lead_response_factor(ambiguous_lead) == 0.0
  assert dynamic_t_follow_target(1.45, ambiguous_lead, 0.0) == 1.45


def test_departure_response_persists_after_initial_jerk_fades():
  moving_away = lead(jLead=0.0, aLeadK=0.5, vRel=0.8)
  assert lead_response_factor(moving_away) > 0.2
  assert dynamic_t_follow_target(1.45, moving_away, 0.0) < 1.40


def test_opening_accelerating_lead_is_not_treated_as_braking_when_jerk_falls():
  moving_away = lead(jLead=-0.5, aLeadK=0.3, vRel=0.9)
  assert dynamic_t_follow_target(1.45, moving_away, 0.0) < 1.45


def test_t_follow_ramp_is_bounded():
  assert ramp_t_follow(2.0, 1.4, 0.05) == pytest.approx(1.4125)
  assert ramp_t_follow(0.8, 1.4, 0.05) == pytest.approx(1.375)


def test_t_follow_ramp_can_raise_faster_for_active_cutin():
  assert ramp_t_follow(2.0, 1.4, 0.05, rise_rate=0.75) == pytest.approx(1.4375)


def test_vision_only_lead_does_not_change_dynamic_follow():
  assert dynamic_t_follow_target(1.45, lead(radar=False, jLead=-2.0), -1.0) == 1.45


def test_radar_cutin_predecel_is_bounded():
  risk = lead(score=0.7, dRel=30.0, vRel=-5.0)
  accel = cutin_predecel_accel(risk, 20.0)
  assert accel is not None
  assert -0.65 <= accel <= -0.25


def test_nonclosing_or_vision_cutin_does_not_predecelerate():
  assert cutin_predecel_accel(lead(vRel=1.0), 20.0) is None
  assert cutin_predecel_accel(lead(radar=False), 20.0) is None


def test_early_cutin_releases_throttle_before_braking_is_needed():
  risk = lead(score=0.3, dRel=24.5, vRel=-2.0, vLat=0.6)
  assert cutin_predecel_accel(risk, 15.0) == 0.0


def test_early_fast_closing_cutin_applies_mild_braking():
  risk = lead(score=0.3, dRel=49.0, vRel=-4.0, vLat=0.6)
  accel = cutin_predecel_accel(risk, 15.0)
  assert accel is not None
  assert -0.35 <= accel < 0.0


def test_urgent_cutin_does_not_drop_out_below_old_minimum_ttc():
  risk = lead(score=0.8, dRel=8.0, vRel=-5.0, vLat=0.7)
  accel = cutin_predecel_accel(risk, 15.0)
  assert accel is not None
  assert accel <= -0.6


def test_fast_closing_cutin_uses_lower_score_threshold():
  risk = lead(score=0.12, dRel=38.9, vRel=-8.2, vLat=1.68)
  assert cutin_predecel_accel(risk, 8.2) is not None


def test_distant_low_score_cutin_does_not_trigger():
  risk = lead(score=0.12, dRel=44.0, vRel=-4.0, vLat=0.5)
  assert cutin_predecel_accel(risk, 15.0) is None


def test_slow_lateral_motion_does_not_trigger_cutin_predecel():
  risk = lead(score=0.2, dRel=25.0, vRel=-4.0, vLat=0.05)
  assert cutin_predecel_accel(risk, 15.0) is None


def test_cutin_predecel_operates_in_low_speed_traffic():
  risk = lead(score=0.7, dRel=7.0, vRel=-1.0, vLat=0.4)
  assert cutin_predecel_accel(risk, 3.0) is not None
