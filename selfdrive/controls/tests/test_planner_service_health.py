import cereal.messaging as messaging

from openpilot.selfdrive.controls.lib.longitudinal_planner import PLAN_REQUIRED_SERVICES
from openpilot.selfdrive.controls.plannerd import PLANNER_IGNORE_AVG_FREQ


PLAN_SERVICES = list(PLAN_REQUIRED_SERVICES)


def make_submaster_health():
  sm = messaging.SubMaster.__new__(messaging.SubMaster)
  sm.services = PLAN_SERVICES
  sm.alive = dict.fromkeys(PLAN_SERVICES, True)
  sm.freq_ok = dict.fromkeys(PLAN_SERVICES, True)
  sm.valid = dict.fromkeys(PLAN_SERVICES, True)
  sm.ignore_alive = []
  sm.ignore_average_freq = PLANNER_IGNORE_AVG_FREQ
  sm.ignore_valid = []
  return sm


def test_local_high_rate_jitter_does_not_invalidate_plan():
  sm = make_submaster_health()
  sm.freq_ok['carState'] = False
  sm.freq_ok['controlsState'] = False
  sm.freq_ok['selfdriveState'] = False

  assert sm.all_checks(PLAN_SERVICES)


def test_radar_rate_failure_still_invalidates_plan():
  sm = make_submaster_health()
  sm.freq_ok['radarState'] = False

  assert not sm.all_checks(PLAN_SERVICES)


def test_dead_or_invalid_input_still_invalidates_plan():
  sm = make_submaster_health()
  sm.alive['selfdriveState'] = False
  assert not sm.all_checks(PLAN_SERVICES)

  sm = make_submaster_health()
  sm.valid['controlsState'] = False
  assert not sm.all_checks(PLAN_SERVICES)
