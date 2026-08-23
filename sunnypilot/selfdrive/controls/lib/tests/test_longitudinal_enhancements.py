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
    "score": 0.0,
    "dRel": 30.0,
    "vRel": -5.0,
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


def test_t_follow_ramp_is_bounded():
  assert ramp_t_follow(2.0, 1.4, 0.05) == pytest.approx(1.4125)
  assert ramp_t_follow(0.8, 1.4, 0.05) == pytest.approx(1.375)


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
