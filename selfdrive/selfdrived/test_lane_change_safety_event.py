from types import SimpleNamespace

from cereal import log

from openpilot.selfdrive.selfdrived.events import EVENTS, ET
from openpilot.selfdrive.selfdrived.selfdrived import lane_change_warning_event


LaneChangeState = log.LaneChangeState
LaneChangeDirection = log.LaneChangeDirection
EventName = log.OnroadEvent.EventName


def lane_meta(direction=LaneChangeDirection.left, blocked=False):
  return SimpleNamespace(
    laneChangeState=LaneChangeState.preLaneChange,
    laneChangeDirection=direction,
    laneChangeBlockedBySafety=blocked,
  )


def car_state(left_blindspot=False, right_blindspot=False):
  return SimpleNamespace(
    leftBlindspot=left_blindspot,
    rightBlindspot=right_blindspot,
  )


def test_safety_block_uses_unavailable_area_event():
  assert lane_change_warning_event(lane_meta(blocked=True), car_state()) == EventName.laneChangeUnavailable


def test_safety_block_uses_normal_alert_background():
  alert = EVENTS[EventName.laneChangeUnavailable][ET.WARNING]

  assert alert.alert_status == log.SelfdriveState.AlertStatus.normal


def test_blindspot_event_has_priority_over_safety_block():
  assert lane_change_warning_event(
    lane_meta(blocked=True),
    car_state(left_blindspot=True),
  ) == EventName.laneChangeBlocked


def test_clear_lane_keeps_directional_confirmation_event():
  assert lane_change_warning_event(lane_meta(), car_state()) == EventName.preLaneChangeLeft
  assert lane_change_warning_event(
    lane_meta(direction=LaneChangeDirection.right),
    car_state(),
  ) == EventName.preLaneChangeRight
