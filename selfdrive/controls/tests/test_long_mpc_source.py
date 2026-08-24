import numpy as np

from cereal import log
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import get_mpc_source


LongitudinalPlanSource = log.LongitudinalPlan.LongitudinalPlanSource


def test_mpc_source_reports_lead_that_constrains_future_horizon():
  obstacles = np.array([
    [80.0, 90.0, 50.0],
    [75.0, 90.0, 60.0],
    [68.0, 90.0, 72.0],
  ])

  assert get_mpc_source(obstacles, (True, False)) == LongitudinalPlanSource.lead0


def test_mpc_source_ignores_invalid_lead_obstacle():
  obstacles = np.array([
    [40.0, 90.0, 50.0],
    [38.0, 90.0, 55.0],
  ])

  assert get_mpc_source(obstacles, (False, False)) == LongitudinalPlanSource.cruise


def test_mpc_source_chooses_earliest_constraining_valid_lead():
  obstacles = np.array([
    [80.0, 45.0, 50.0],
    [40.0, 60.0, 55.0],
  ])

  assert get_mpc_source(obstacles, (True, True)) == LongitudinalPlanSource.lead1


def test_mpc_source_ignores_lead_outside_display_lookahead():
  obstacles = np.full((13, 3), 100.0)
  obstacles[:, 2] = 50.0
  obstacles[9:, 0] = 40.0

  assert get_mpc_source(obstacles, (True, False)) == LongitudinalPlanSource.cruise
