from types import SimpleNamespace

import pytest
from cereal import car, messaging
from opendbc.car import structs

from openpilot.selfdrive.car.card import Car
from openpilot.selfdrive.modeld.lane_change_input_monitor import lane_change_car_state


class CapturedPublisher:
  def __init__(self):
    self.messages = {}

  def send(self, service, message):
    self.messages[service] = messaging.log_from_bytes(message.to_bytes())


@pytest.mark.parametrize('can_valid,brake,steering,torque', [
  (True, False, False, 0.0),
  (True, True, True, -1.5),
  (False, False, False, 0.0),
])
def test_card_publishes_complete_same_can_inputs_without_changing_core_state(can_valid, brake, steering, torque):
  subject = Car.__new__(Car)
  subject.pm = CapturedPublisher()
  subject.sm = SimpleNamespace(frame=1, all_checks=lambda services: True)
  subject.last_actuators_output = structs.CarControl.Actuators()
  subject.can_rcv_cum_timeout_counter = 0
  subject.rk = SimpleNamespace(remaining=0.0)
  subject.CI = SimpleNamespace(CS=SimpleNamespace(gmEpbClosed=False))
  subject.gm_auto_hold_session = SimpleNamespace(
    active=False, elapsed_s=0.0, expected_progress=0.0, epb_transferred=False, epb_transition_age_s=0.0,
  )
  cs = car.CarState.new_message()
  cs.canValid = can_valid
  cs.vEgo = 19.0
  cs.rightBlinker = True
  cs.leftBlindspot = True
  cs.brakePressed = brake
  cs.steeringPressed = steering
  cs.steeringTorque = torque
  cs.cruiseState.speed = 0.0
  before = cs.to_dict()
  cs_sp = messaging.new_message('carStateSP').carStateSP

  subject.state_publish(cs, cs_sp, None)

  assert cs.to_dict() == before
  primary = subject.pm.messages['carState']
  mirror = subject.pm.messages['carStateSP']
  assert primary.carState.to_dict() == before
  assert primary.valid == mirror.valid == can_valid
  assert mirror.carStateSP.laneChangeInputVersion == 1
  assert mirror.carStateSP.laneChangeBrakePressed == brake
  assert mirror.carStateSP.laneChangeSteeringPressed == steering
  assert mirror.carStateSP.laneChangeSteeringTorque == torque
  assert mirror.carStateSP.navdyVEgo == primary.carState.vEgo
  assert mirror.carStateSP.navdyRightBlinker == primary.carState.rightBlinker
  assert mirror.carStateSP.navdyLeftBlindspot == primary.carState.leftBlindspot

  class SubMasterStub(dict):
    logMonoTime = {'carState': primary.logMonoTime - 650_000_000, 'carStateSP': mirror.logMonoTime}
    valid = {'carState': primary.valid, 'carStateSP': mirror.valid}

  selected, stale = lane_change_car_state(SubMasterStub(carState=primary.carState, carStateSP=mirror.carStateSP),
                                         mirror.logMonoTime + 20_000_000)
  assert stale == (not can_valid)
  if can_valid:
    assert selected.rightBlinker and selected.leftBlindspot
    assert (selected.brakePressed, selected.steeringPressed, selected.steeringTorque) == (brake, steering, torque)
  else:
    assert not selected.rightBlinker and selected.brakePressed
