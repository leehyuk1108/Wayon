from types import SimpleNamespace

import pytest
from cereal import log, messaging

from openpilot.selfdrive.controls.lib.desire_helper import DesireHelper
from openpilot.selfdrive.modeld import lane_change_input_monitor as monitor_module
from openpilot.sunnypilot.selfdrive.controls.lib.auto_lane_change import AutoLaneChangeMode
from openpilot.sunnypilot.selfdrive.controls.lib.lane_change_safety import LaneBoundaryState, LaneChangeSafetyGate


class InputSubMaster(dict):
  def __init__(self, now, car_age, mirror_age, *, version=1, brake=False, steering=False, torque=0.0):
    super().__init__(
      carState=SimpleNamespace(vEgo=20.0, leftBlinker=False, rightBlinker=False,
                               leftBlindspot=False, rightBlindspot=False,
                               brakePressed=False, steeringPressed=False, steeringTorque=0.0),
      carStateSP=SimpleNamespace(navdyVEgo=19.0, navdyLeftBlinker=False, navdyRightBlinker=True,
                                 navdyLeftBlindspot=False, navdyRightBlindspot=False,
                                 laneChangeInputVersion=version, laneChangeBrakePressed=brake,
                                 laneChangeSteeringPressed=steering, laneChangeSteeringTorque=torque),
    )
    self.logMonoTime = {'carState': now - car_age, 'carStateSP': now - mirror_age}
    self.valid = {'carState': True, 'carStateSP': True}


def test_logs_each_new_signal_once(monkeypatch):
  events = []
  monkeypatch.setattr(monitor_module.cloudlog, 'event', lambda name, **data: events.append((name, data)))
  monitor = monitor_module.LaneChangeInputMonitor()
  car_state = SimpleNamespace(leftBlinker=False, rightBlinker=False, vEgo=20.0)
  navdy_state = SimpleNamespace(navdyLeftBlinker=False, navdyRightBlinker=False)
  class SubMasterStub(dict):
    logMonoTime = {'carState': 1, 'carStateSP': 2, 'carControl': 3}

  sm = SubMasterStub(carState=car_state, carStateSP=navdy_state, carControl=SimpleNamespace(latActive=True))
  desire_helper = SimpleNamespace(alc=SimpleNamespace(lane_change_set_timer=1), lane_change_state=0)

  monitor.update(sm, desire_helper)
  navdy_state.navdyLeftBlinker = True
  monitor.update(sm, desire_helper)
  monitor.update(sm, desire_helper)
  car_state.leftBlinker = True
  monitor.update(sm, desire_helper)

  assert [data['source'] for _, data in events] == ['carStateSP', 'carState']
  assert events[0][1]['car_signal'] == 0
  assert events[0][1]['navdy_signal'] == 1
  assert events[1][1]['car_signal'] == 1


def test_stale_car_state_uses_fresh_same_card_signal_without_arming_controls():
  now = 10_000_000_000
  car_state = SimpleNamespace(leftBlinker=False, rightBlinker=False)
  navdy_state = SimpleNamespace(navdyVEgo=19.0, navdyLeftBlinker=False, navdyRightBlinker=True,
                                navdyLeftBlindspot=False, navdyRightBlindspot=False)
  class SubMasterStub(dict):
    logMonoTime = {'carState': now - 3_200_000_000, 'carStateSP': now - 30_000_000}
    valid = {'carState': True, 'carStateSP': True}

  sm = SubMasterStub(carState=car_state, carStateSP=navdy_state)
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert stale
  assert selected.rightBlinker and selected.vEgo == 19.0
  assert selected.brakePressed and not selected.steeringPressed

  sm.logMonoTime = {'carState': now - 20_000_000, 'carStateSP': now - 30_000_000}
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert not stale and selected is car_state


def test_stale_car_state_without_fresh_backup_has_no_change_signal():
  now = 10_000_000_000
  class SubMasterStub(dict):
    logMonoTime = {'carState': now - 3_200_000_000, 'carStateSP': now - 2_000_000_000}
    valid = {'carState': True, 'carStateSP': True}

  sm = SubMasterStub(carState=SimpleNamespace(rightBlinker=True), carStateSP=SimpleNamespace(navdyRightBlinker=True))
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert stale and not selected.rightBlinker and selected.vEgo == 0.0


@pytest.mark.parametrize('car_age', [637_500_000, 1_684_900_000, 200_000_000])
def test_complete_newer_mirror_avoids_delayed_blinker_without_synthetic_brake(car_age):
  now = 10_000_000_000
  sm = InputSubMaster(now, car_age, 37_800_000)
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert not stale
  assert selected.rightBlinker and selected.vEgo == 19.0
  assert not selected.brakePressed and not selected.steeringPressed


@pytest.mark.parametrize('brake,steering,torque,left_blindspot,right_blindspot', [
  (True, False, 0.0, False, False),
  (False, True, -1.5, False, False),
  (False, True, 1.5, True, False),
  (False, False, 0.0, False, True),
])
def test_mirror_preserves_actual_driver_inputs_and_blindspots(brake, steering, torque, left_blindspot, right_blindspot):
  now = 10_000_000_000
  sm = InputSubMaster(now, 650_000_000, 20_000_000, brake=brake, steering=steering, torque=torque)
  sm['carStateSP'].navdyLeftBlindspot = left_blindspot
  sm['carStateSP'].navdyRightBlindspot = right_blindspot
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert not stale
  assert (selected.brakePressed, selected.steeringPressed, selected.steeringTorque) == (brake, steering, torque)
  assert (selected.leftBlindspot, selected.rightBlindspot) == (left_blindspot, right_blindspot)


@pytest.mark.parametrize('mirror_age', [20_000_000, 300_000_000])
def test_newest_primary_packet_remains_selected(mirror_age):
  now = 10_000_000_000
  sm = InputSubMaster(now, 20_000_000, mirror_age)
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert not stale and selected is sm['carState']


@pytest.mark.parametrize('version', [0, 2])
@pytest.mark.parametrize('car_age', [50_000_000, 650_000_000])
def test_legacy_or_unknown_version_never_treated_as_complete_inputs(version, car_age):
  now = 10_000_000_000
  sm = InputSubMaster(now, car_age, 20_000_000, version=version)
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  if car_age <= monitor_module.LANE_CHANGE_INPUT_MAX_AGE_NS:
    assert not stale and selected is sm['carState']
  else:
    assert stale and selected.brakePressed and not selected.steeringPressed


@pytest.mark.parametrize('age,valid', [
  (300_000_001, True),
  (-1, True),
  (20_000_000, False),
])
def test_expired_future_or_invalid_mirror_does_not_authorize_lane_change(age, valid):
  now = 10_000_000_000
  sm = InputSubMaster(now, 650_000_000, age)
  sm.valid['carStateSP'] = valid
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert stale and selected.brakePressed and not selected.steeringPressed
  assert not selected.rightBlinker


def test_freshness_boundary_remains_300ms():
  now = 10_000_000_000
  sm = InputSubMaster(now, 650_000_000, 300_000_000)
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert not stale and selected.rightBlinker


@pytest.mark.parametrize('field,value', [
  ('navdyVEgo', float('nan')),
  ('navdyVEgo', float('inf')),
  ('navdyVEgo', -1.0),
  ('laneChangeSteeringTorque', float('nan')),
  ('laneChangeSteeringTorque', float('inf')),
])
def test_nonfinite_or_negative_mirror_inputs_remain_fail_closed(field, value):
  now = 10_000_000_000
  sm = InputSubMaster(now, 650_000_000, 20_000_000)
  setattr(sm['carStateSP'], field, value)
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert stale and selected.brakePressed and not selected.steeringPressed
  if field == 'navdyVEgo':
    assert selected.vEgo == 0.0 and not selected.rightBlinker


def test_mirror_packet_round_trip_preserves_complete_inputs_and_timestamp():
  now = 10_000_000_000
  sm = InputSubMaster(now, 650_000_000, 20_000_000, brake=True, steering=True, torque=-1.5)
  msg = messaging.new_message('carStateSP')
  msg.logMonoTime = sm.logMonoTime['carStateSP']
  msg.valid = True
  for field, value in vars(sm['carStateSP']).items():
    setattr(msg.carStateSP, field, value)
  parsed = messaging.log_from_bytes(msg.to_bytes())
  sm['carStateSP'] = parsed.carStateSP
  sm.logMonoTime['carStateSP'] = parsed.logMonoTime
  sm.valid['carStateSP'] = parsed.valid

  selected, stale = monitor_module.lane_change_car_state(sm, now)
  assert not stale and selected.rightBlinker
  assert selected.brakePressed and selected.steeringPressed and selected.steeringTorque == -1.5
  assert parsed.logMonoTime == now - 20_000_000


def make_desire_helper(boundary='dashed'):
  helper = DesireHelper()
  helper.alc.update_params = lambda: None
  helper.lane_turn_controller.update_params = lambda: None
  helper.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGELESS
  reader = SimpleNamespace(read=lambda: LaneBoundaryState(left_type=boundary, right_type=boundary))
  helper.lane_change_safety = LaneChangeSafetyGate(reader)
  return helper


def lane_model(edge_y=6.0):
  def line(y):
    return SimpleNamespace(x=[0.0, 8.0, 15.0, 25.0, 40.0], y=[y] * 5)

  return SimpleNamespace(laneLines=[line(-4.5), line(-1.5), line(1.5), line(4.5)],
                         laneLineProbs=[0.98] * 4, roadEdges=[line(-6.0), line(edge_y)], roadEdgeStds=[0.2] * 2)


def update_with_mirror(helper, sm, model, now, *, lateral_active=True):
  sm.logMonoTime['carStateSP'] = now - 20_000_000
  selected, stale = monitor_module.lane_change_car_state(sm, now)
  helper.update(selected, lateral_active, 1.0, model, input_stale=stale)


def test_delayed_primary_no_longer_cancels_original_nudgeless_timer():
  now = 10_000_000_000
  sm = InputSubMaster(now, 637_500_000, 37_800_000)
  helper = make_desire_helper()
  for frame in range(4):
    update_with_mirror(helper, sm, lane_model(), now + frame * 50_000_000)
  assert helper.lane_change_state == log.LaneChangeState.laneChangeStarting
  assert not helper.alc.prev_brake_pressed


@pytest.mark.parametrize('hazard', ['solid', 'centerSolid', 'roadEdge', 'blindspot', 'brake', 'stale'])
def test_complete_mirror_does_not_bypass_existing_safety_checks(hazard):
  now = 10_000_000_000
  sm = InputSubMaster(now, 650_000_000, 20_000_000, brake=hazard == 'brake')
  sm['carStateSP'].navdyRightBlindspot = hazard == 'blindspot'
  sm.valid['carStateSP'] = hazard != 'stale'
  helper = make_desire_helper(hazard if hazard in ('solid', 'centerSolid') else 'dashed')
  model = lane_model(2.2 if hazard == 'roadEdge' else 6.0)
  for frame in range(6):
    update_with_mirror(helper, sm, model, now + frame * 50_000_000)
    assert helper.lane_change_state != log.LaneChangeState.laneChangeStarting
  if hazard in ('solid', 'centerSolid'):
    assert helper.lane_change_safety.block_reason == 'solidLine'
  elif hazard == 'roadEdge':
    assert helper.lane_change_safety.block_reason == 'narrowTargetLane'
  elif hazard == 'brake':
    assert helper.alc.prev_brake_pressed


def test_fresh_mirror_with_signal_held_before_engagement_still_requires_nudge():
  now = 10_000_000_000
  sm = InputSubMaster(now, 650_000_000, 20_000_000)
  helper = make_desire_helper()
  update_with_mirror(helper, sm, lane_model(), now, lateral_active=False)
  for frame in range(6):
    update_with_mirror(helper, sm, lane_model(), now + (frame + 1) * 50_000_000)
  assert helper.lane_change_state == log.LaneChangeState.preLaneChange

  sm['carStateSP'].laneChangeSteeringPressed = True
  sm['carStateSP'].laneChangeSteeringTorque = -1.5
  update_with_mirror(helper, sm, lane_model(), now + 400_000_000)
  assert helper.lane_change_state == log.LaneChangeState.laneChangeStarting


def test_mirror_receives_blinker_release_while_primary_is_still_cached():
  now = 10_000_000_000
  sm = InputSubMaster(now, 650_000_000, 20_000_000)
  sm['carState'].rightBlinker = True
  helper = make_desire_helper()
  update_with_mirror(helper, sm, lane_model(), now)
  sm['carStateSP'].navdyRightBlinker = False
  update_with_mirror(helper, sm, lane_model(), now + 50_000_000)
  assert helper.lane_change_state == log.LaneChangeState.off
  assert not helper.lane_change_auto_armed


@pytest.mark.parametrize('mode', [AutoLaneChangeMode.OFF, AutoLaneChangeMode.NUDGE, AutoLaneChangeMode.ONE_SECOND])
def test_mirror_keeps_disabled_nudge_and_configured_delay_modes(mode):
  now = 10_000_000_000
  sm = InputSubMaster(now, 650_000_000, 20_000_000)
  helper = make_desire_helper()
  helper.alc.lane_change_set_timer = mode
  for frame in range(11):
    update_with_mirror(helper, sm, lane_model(), now + frame * 50_000_000)
  assert helper.lane_change_state == (log.LaneChangeState.off if mode == AutoLaneChangeMode.OFF
                                      else log.LaneChangeState.preLaneChange)
  if mode == AutoLaneChangeMode.ONE_SECOND:
    for frame in range(11, 25):
      update_with_mirror(helper, sm, lane_model(), now + frame * 50_000_000)
    assert helper.lane_change_state == log.LaneChangeState.laneChangeStarting
  else:
    sm['carStateSP'].laneChangeSteeringPressed = True
    sm['carStateSP'].laneChangeSteeringTorque = -1.5
    update_with_mirror(helper, sm, lane_model(), now + 600_000_000)
    assert helper.lane_change_state == (log.LaneChangeState.off if mode == AutoLaneChangeMode.OFF
                                        else log.LaneChangeState.laneChangeStarting)
