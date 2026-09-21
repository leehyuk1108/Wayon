import math

import pytest

from openpilot.selfdrive.controls.lib.drive_helpers import clip_curvature, get_curvature_from_path_poly, guard_model_curvature


def test_curvature_from_straight_path_poly():
  assert get_curvature_from_path_poly([0.0, 8.0, 0.0], [0.0, 0.0, 0.0]) == 0.0


def test_curvature_from_path_poly_rejects_invalid_path():
  assert math.isnan(get_curvature_from_path_poly([0.0, 0.0], [0.0, 0.0]))
  assert math.isnan(get_curvature_from_path_poly([0.0, 0.0, 0.0], [0.0, 0.0, 0.0]))


def test_model_curvature_guard_preserves_normal_curve():
  guarded, active = guard_model_curvature(8.0, 0.012, 0.006)
  assert not active
  assert guarded == 0.012


def test_model_curvature_guard_limits_recorded_action_spike():
  speed = 7.75867
  path_curvature = -0.00031
  guarded, active = guard_model_curvature(speed, 0.05135, path_curvature)
  assert active
  assert abs(guarded - path_curvature) * speed ** 2 == pytest.approx(1.25)


def test_model_curvature_guard_ignores_low_speed_turn():
  guarded, active = guard_model_curvature(4.0, 0.08, 0.0)
  assert not active
  assert guarded == 0.08


def test_guarded_curvature_uses_lower_lateral_jerk_limit():
  speed = 8.0
  curvature, _ = clip_curvature(speed, 0.0, 0.05, 0.0, max_lateral_jerk=2.0)
  assert curvature == pytest.approx(2.0 / speed ** 2 * 0.01)
