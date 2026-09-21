from types import SimpleNamespace

import pytest
from cereal import log, custom
from openpilot.common.params import Params

from openpilot.selfdrive.controls.lib.desire_helper import DesireHelper
from openpilot.sunnypilot.selfdrive.controls.lib.lane_turn_desire import LaneTurnController, LANE_CHANGE_SPEED_MIN
from openpilot.sunnypilot.selfdrive.controls.lib.auto_lane_change import AutoLaneChangeMode
from openpilot.sunnypilot.selfdrive.controls.lib.lane_change_safety import LaneBoundaryStateReader, LaneChangeSafetyGate

TurnDirection = custom.ModelDataV2SP.TurnDirection


@pytest.mark.parametrize("left_blinker,right_blinker,v_ego,blindspot_left,blindspot_right,expected", [
  (True, False, 5, False, False, TurnDirection.turnLeft),
  (False, True, 6, False, False, TurnDirection.turnRight),
  (True, False, 9, False, False, TurnDirection.none),
  (True, False, 7, True, False, TurnDirection.none),
  (False, True, 6, False, True, TurnDirection.none),
  (False, False, 5, False, False, TurnDirection.none),
  (True, True, 5, False, False, TurnDirection.none),
])
def test_lane_turn_desire_conditions(left_blinker, right_blinker, v_ego, blindspot_left, blindspot_right, expected):
  dh = DesireHelper()
  controller = LaneTurnController(dh)
  controller.enabled = True
  controller.lane_turn_value = LANE_CHANGE_SPEED_MIN
  controller.turn_direction = TurnDirection.none
  controller.update_lane_turn(blindspot_left, blindspot_right, left_blinker, right_blinker, v_ego)
  assert controller.get_turn_direction() == expected


def test_lane_turn_desire_disabled():
  dh = DesireHelper()
  controller = LaneTurnController(dh)
  controller.enabled = False
  controller.lane_turn_value = LANE_CHANGE_SPEED_MIN
  controller.turn_direction = TurnDirection.none
  controller.update_lane_turn(False, False, True, False, 7)
  assert controller.get_turn_direction() == TurnDirection.none


def test_lane_turn_overrides_lane_change():
  dh = DesireHelper()
  controller = LaneTurnController(dh)
  controller.enabled = True
  controller.lane_turn_value = LANE_CHANGE_SPEED_MIN
  controller.turn_direction = TurnDirection.none
  # left turn desire
  controller.update_lane_turn(False, False, True, False, 5)
  assert controller.get_turn_direction() == TurnDirection.turnLeft
  # right turn desire
  controller.update_lane_turn(False, False, False, True, 6)
  assert controller.get_turn_direction() == TurnDirection.turnRight
  # no turn
  controller.update_lane_turn(False, False, False, False, 7)
  assert controller.get_turn_direction() == TurnDirection.none


@pytest.mark.parametrize("v_ego,expected", [
  (8.93, TurnDirection.turnLeft),  # just below threshold
  (8.96, TurnDirection.none),  # above threshold
  (8.95, TurnDirection.none),  # just above threshold
])
def test_lane_turn_desire_speed_boundary(v_ego, expected):
  dh = DesireHelper()
  controller = LaneTurnController(dh)
  controller.enabled = True
  controller.lane_turn_value = LANE_CHANGE_SPEED_MIN
  controller.turn_direction = TurnDirection.none
  controller.update_lane_turn(False, True, True, False, v_ego)
  assert controller.get_turn_direction() == expected


class DummyCarState:
  def __init__(self, vEgo=0, leftBlinker=False, rightBlinker=False, leftBlindspot=False, rightBlindspot=False,
               steeringPressed=False, steeringTorque=0, brakePressed=False):
    self.vEgo = vEgo
    self.leftBlinker = leftBlinker
    self.rightBlinker = rightBlinker
    self.leftBlindspot = leftBlindspot
    self.rightBlindspot = rightBlindspot
    self.steeringPressed = steeringPressed
    self.steeringTorque = steeringTorque
    self.brakePressed = brakePressed


class DummyLaneChangeSafetyGate:
  def __init__(self, blocked):
    self.blocked = blocked
    self.update_calls = 0

  def update(self, direction, model_v2):
    self.update_calls += 1
    return self.blocked

  def reset(self):
    pass


def model_line(y):
  return SimpleNamespace(x=[0.0, 8.0, 15.0, 25.0, 40.0], y=[y] * 5)


def close_right_road_edge_model():
  return SimpleNamespace(
    laneLines=[model_line(-4.5), model_line(-1.5), model_line(1.5), model_line(4.5)],
    laneLineProbs=[0.01, 0.98, 0.98, 0.01],
    roadEdges=[model_line(-5.0), model_line(2.2)],
    roadEdgeStds=[0.4, 0.38],
  )


@pytest.fixture
def set_lane_turn_params():
  params = Params()
  params.put("LaneTurnDesire", True)
  params.put("LaneTurnValue", 20.0)


@pytest.mark.parametrize("carstate, lateral_active, lane_change_prob, expected_desire", [
  # Lane turn desire overrides lane change desire
  (DummyCarState(vEgo=5, leftBlinker=True, rightBlinker=False, leftBlindspot=False, rightBlindspot=False), True, 1.0,
   log.Desire.turnLeft),
  (DummyCarState(vEgo=7, leftBlinker=False, rightBlinker=True, leftBlindspot=False, rightBlindspot=False), True, 1.0,
   log.Desire.turnRight),
  # Lane change desire only (no turn desires)
  (DummyCarState(vEgo=9, leftBlinker=True, rightBlinker=False, leftBlindspot=False, rightBlindspot=False,
                 steeringPressed=True, steeringTorque=1), True, 1.0, log.Desire.laneChangeLeft),
  (DummyCarState(vEgo=9, leftBlinker=False, rightBlinker=True, leftBlindspot=False, rightBlindspot=False,
                 steeringPressed=True, steeringTorque=-1), True, 1.0, log.Desire.laneChangeRight),
  # No desire (inactive)
  (DummyCarState(vEgo=9, leftBlinker=False, rightBlinker=False), False, 1.0, log.Desire.none),
  (DummyCarState(vEgo=4, leftBlinker=False, rightBlinker=False), True, 1.0, log.Desire.none),  # No blinkers? no desire!
])
def test_desire_helper_integration(carstate, lateral_active, lane_change_prob, expected_desire, set_lane_turn_params):
  dh = DesireHelper()
  dh.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGE
  for _ in range(10):
    dh.update(carstate, lateral_active, lane_change_prob)
  assert dh.desire == expected_desire  # The first four tests were unit tests to test the controller, where this tests the integration in desire helpers


def test_lane_change_safety_gate_blocks_start_but_not_an_active_maneuver():
  dh = DesireHelper()
  dh.alc.update_params = lambda: None
  dh.lane_turn_controller.update_params = lambda: None
  dh.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGE
  gate = DummyLaneChangeSafetyGate(blocked=True)
  dh.lane_change_safety = gate
  carstate = DummyCarState(
    vEgo=15.0,
    leftBlinker=True,
    steeringPressed=True,
    steeringTorque=1.0,
  )

  dh.update(carstate, True, 1.0, object())
  assert dh.lane_change_state == log.LaneChangeState.preLaneChange

  dh.update(carstate, True, 1.0, object())
  assert gate.update_calls == 1
  assert dh.lane_change_state == log.LaneChangeState.preLaneChange

  gate.blocked = False
  dh.update(carstate, True, 1.0, object())
  assert dh.lane_change_state == log.LaneChangeState.laneChangeStarting

  gate.blocked = True
  dh.update(carstate, True, 1.0, object())
  assert dh.lane_change_state == log.LaneChangeState.laneChangeStarting


def test_close_road_edge_blocks_before_nudgeless_timer(tmp_path):
  dh = DesireHelper()
  dh.alc.update_params = lambda: None
  dh.lane_turn_controller.update_params = lambda: None
  dh.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGELESS
  dh.lane_change_safety = LaneChangeSafetyGate(LaneBoundaryStateReader(str(tmp_path / "missing.json")))
  carstate = DummyCarState(
    vEgo=15.0,
    rightBlinker=True,
    steeringPressed=True,
    steeringTorque=-1.0,
  )
  model_v2 = close_right_road_edge_model()

  dh.update(carstate, True, 1.0, model_v2)
  assert dh.lane_change_state == log.LaneChangeState.preLaneChange
  dh.update(carstate, True, 1.0, model_v2)
  assert dh.lane_change_state == log.LaneChangeState.preLaneChange
  dh.update(carstate, True, 1.0, model_v2)

  assert dh.lane_change_safety.blocked
  assert dh.lane_change_safety.block_reason == "narrowTargetLane"
  assert dh.lane_change_state == log.LaneChangeState.preLaneChange


def test_fresh_signal_still_starts_nudgeless_lane_change():
  dh = DesireHelper()
  dh.alc.update_params = lambda: None
  dh.lane_turn_controller.update_params = lambda: None
  dh.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGELESS
  carstate = DummyCarState(vEgo=15.0, leftBlinker=True)

  dh.update(carstate, True, 1.0)
  assert dh.lane_change_state == log.LaneChangeState.preLaneChange
  for _ in range(4):
    dh.update(carstate, True, 1.0)
  assert dh.lane_change_state == log.LaneChangeState.laneChangeStarting


def test_held_signal_recovers_with_nudge_without_repeating_auto_change():
  dh = DesireHelper()
  dh.alc.update_params = lambda: None
  dh.lane_turn_controller.update_params = lambda: None
  dh.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGELESS
  carstate = DummyCarState(vEgo=15.0, leftBlinker=True)

  dh.update(carstate, True, 1.0)
  for _ in range(4):
    dh.update(carstate, True, 1.0)
  assert dh.lane_change_state == log.LaneChangeState.laneChangeStarting

  dh.lane_change_state = log.LaneChangeState.off
  dh.update(carstate, True, 1.0)
  assert dh.lane_change_state == log.LaneChangeState.off

  carstate.steeringPressed = True
  carstate.steeringTorque = 1.0
  dh.update(carstate, True, 1.0)
  assert dh.lane_change_state == log.LaneChangeState.preLaneChange
  dh.update(carstate, True, 1.0)
  assert dh.lane_change_state == log.LaneChangeState.laneChangeStarting


def test_signal_held_before_engagement_needs_nudge():
  dh = DesireHelper()
  dh.alc.update_params = lambda: None
  dh.lane_turn_controller.update_params = lambda: None
  dh.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGELESS
  carstate = DummyCarState(vEgo=15.0, rightBlinker=True)

  dh.update(carstate, False, 1.0)
  assert dh.lane_change_state == log.LaneChangeState.off
  for _ in range(5):
    dh.update(carstate, True, 1.0)
  assert dh.lane_change_state == log.LaneChangeState.preLaneChange

  carstate.steeringPressed = True
  carstate.steeringTorque = -1.0
  dh.update(carstate, True, 1.0)
  assert dh.lane_change_state == log.LaneChangeState.laneChangeStarting


def test_missed_signal_edge_enters_prompt_but_road_edge_still_blocks(tmp_path):
  dh = DesireHelper()
  dh.alc.update_params = lambda: None
  dh.lane_turn_controller.update_params = lambda: None
  dh.alc.lane_change_set_timer = AutoLaneChangeMode.NUDGELESS
  dh.lane_change_safety = LaneChangeSafetyGate(LaneBoundaryStateReader(str(tmp_path / "missing.json")))
  dh.prev_blinker_direction = log.LaneChangeDirection.right
  carstate = DummyCarState(vEgo=15.0, rightBlinker=True, steeringPressed=True, steeringTorque=-1.0)
  model_v2 = close_right_road_edge_model()

  dh.update(carstate, True, 1.0, model_v2)
  assert dh.lane_change_state == log.LaneChangeState.preLaneChange
  for _ in range(5):
    dh.update(carstate, True, 1.0, model_v2)
  assert dh.lane_change_safety.blocked
  assert dh.lane_change_state == log.LaneChangeState.preLaneChange
