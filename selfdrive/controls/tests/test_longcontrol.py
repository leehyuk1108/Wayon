from types import SimpleNamespace

from cereal import car, custom
from openpilot.selfdrive.controls.lib.longcontrol import (LongControl, LongCtrlState,
                                                          SOFT_HOLD_LEAD_CONFIRM_FRAMES,
                                                          long_control_state_trans)




class TestLongControlStateTransition:

  def test_stay_stopped(self):
    CP = car.CarParams.new_message()
    CP_SP = custom.CarParamsSP.new_message()
    active = True
    current_state = LongCtrlState.stopping
    next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=0.1,
                             should_stop=True, brake_pressed=False, cruise_standstill=False)
    assert next_state == LongCtrlState.stopping
    next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=0.1,
                             should_stop=False, brake_pressed=True, cruise_standstill=False)
    assert next_state == LongCtrlState.stopping
    next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=0.1,
                             should_stop=False, brake_pressed=False, cruise_standstill=True)
    assert next_state == LongCtrlState.stopping
    next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=1.0,
                             should_stop=False, brake_pressed=False, cruise_standstill=False)
    assert next_state == LongCtrlState.pid
    active = False
    next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=1.0,
                             should_stop=False, brake_pressed=False, cruise_standstill=False)
    assert next_state == LongCtrlState.off

def test_engage():
  CP = car.CarParams.new_message()
  CP_SP = custom.CarParamsSP.new_message()
  active = True
  current_state = LongCtrlState.off
  next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=0.1,
                             should_stop=True, brake_pressed=False, cruise_standstill=False)
  assert next_state == LongCtrlState.stopping
  next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=0.1,
                             should_stop=False, brake_pressed=True, cruise_standstill=False)
  assert next_state == LongCtrlState.stopping
  next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=0.1,
                             should_stop=False, brake_pressed=False, cruise_standstill=True)
  assert next_state == LongCtrlState.stopping
  next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=0.1,
                             should_stop=False, brake_pressed=False, cruise_standstill=False)
  assert next_state == LongCtrlState.pid

def test_starting():
  CP = car.CarParams.new_message(startingState=True, vEgoStarting=0.5)
  CP_SP = custom.CarParamsSP.new_message()
  active = True
  current_state = LongCtrlState.starting
  next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=0.1,
                             should_stop=False, brake_pressed=False, cruise_standstill=False)
  assert next_state == LongCtrlState.starting
  next_state = long_control_state_trans(CP, CP_SP, active, current_state, v_ego=1.0,
                             should_stop=False, brake_pressed=False, cruise_standstill=False)
  assert next_state == LongCtrlState.pid


def test_soft_hold_resume_bypasses_synthetic_cruise_standstill():
  CP = car.CarParams.new_message(startingState=True, vEgoStarting=0.5)
  CP_SP = custom.CarParamsSP.new_message()
  next_state = long_control_state_trans(CP, CP_SP, True, LongCtrlState.stopping, v_ego=0.0,
                                        should_stop=False, brake_pressed=False, cruise_standstill=True,
                                        soft_hold_resume=True)
  assert next_state == LongCtrlState.starting


def test_soft_hold_resume_requires_stable_departing_lead():
  controller = LongControl.__new__(LongControl)
  controller.wayon_carrot_profile = True
  controller.soft_hold_lead_frames = 0
  controller.soft_hold_resume_ready = False
  CS = SimpleNamespace(brakeHoldActive=True, brakePressed=False)
  plan = SimpleNamespace(shouldStop=False)
  radar = SimpleNamespace(leadOne=SimpleNamespace(status=True, dRel=6.0, vLead=1.0, vRel=0.8))

  for _ in range(SOFT_HOLD_LEAD_CONFIRM_FRAMES - 1):
    assert not controller.update_soft_hold_resume(CS, plan, radar)
  assert controller.update_soft_hold_resume(CS, plan, radar)

  radar.leadOne.vRel = 0.0
  assert not controller.update_soft_hold_resume(CS, plan, radar)
  assert controller.soft_hold_lead_frames == 0
