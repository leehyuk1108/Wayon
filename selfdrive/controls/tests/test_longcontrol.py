from types import SimpleNamespace

from cereal import car, custom
from openpilot.selfdrive.controls.lib.longcontrol import (LongControl, LongCtrlState,
                                                          SNG_LEAD_CONFIRM_FRAMES, SNG_RESUME_TIMEOUT_FRAMES,
                                                          SNG_STOP_CONFIRM_FRAMES,
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


def test_sng_resume_releases_cruise_standstill():
  CP = car.CarParams.new_message(startingState=True, vEgoStarting=0.5)
  CP_SP = custom.CarParamsSP.new_message()
  next_state = long_control_state_trans(CP, CP_SP, True, LongCtrlState.stopping, v_ego=0.0,
                                        should_stop=False, brake_pressed=False, cruise_standstill=True,
                                        sng_resume=True)
  assert next_state == LongCtrlState.starting


def sng_controller():
  controller = LongControl.__new__(LongControl)
  controller.CP = SimpleNamespace(autoResumeSng=True, vEgoStarting=0.5)
  controller.long_control_state = LongCtrlState.stopping
  controller.sng_stop_frames = 0
  controller.sng_lead_frames = 0
  controller.sng_lead_baseline_m = None
  controller.sng_resume_ready = False
  controller.sng_resume_frames = 0
  controller.sng_resume_attempted = False
  return controller


def test_traverse_stopping_decel_rate_is_soft_until_standstill():
  controller = LongControl.__new__(LongControl)
  controller.CP = SimpleNamespace(stoppingDecelRate=2.0)
  controller.wayon_carrot_profile = True

  assert controller.get_stopping_decel_rate(False) == 0.8
  assert controller.get_stopping_decel_rate(True) == 2.0

  controller.wayon_carrot_profile = False
  assert controller.get_stopping_decel_rate(False) == 2.0


def test_sng_resume_requires_confirmed_stop_and_departing_lead():
  controller = sng_controller()
  CS = SimpleNamespace(vEgo=0.0, standstill=True, brakePressed=False, gasPressed=False,
                       cruiseState=SimpleNamespace(standstill=True))
  plan = SimpleNamespace(shouldStop=True)
  radar = SimpleNamespace(leadOne=SimpleNamespace(status=True, dRel=6.0, vLead=0.0, vRel=0.0))

  for _ in range(SNG_STOP_CONFIRM_FRAMES):
    assert not controller.update_sng_resume(True, CS, plan, radar)

  plan.shouldStop = False
  radar.leadOne.dRel = 6.6
  radar.leadOne.vRel = 0.8
  for _ in range(SNG_LEAD_CONFIRM_FRAMES - 1):
    assert not controller.update_sng_resume(True, CS, plan, radar)
  assert controller.update_sng_resume(True, CS, plan, radar)
  assert controller.sng_resume_attempted

  radar.leadOne.status = False
  assert not controller.update_sng_resume(True, CS, plan, radar)
  assert controller.sng_resume_attempted


def test_sng_resume_rejects_lead_loss_and_driver_input():
  controller = sng_controller()
  CS = SimpleNamespace(vEgo=0.0, standstill=True, brakePressed=False, gasPressed=False,
                       cruiseState=SimpleNamespace(standstill=True))
  plan = SimpleNamespace(shouldStop=True)
  radar = SimpleNamespace(leadOne=SimpleNamespace(status=True, dRel=6.0, vLead=0.0, vRel=0.0))

  for _ in range(SNG_STOP_CONFIRM_FRAMES):
    controller.update_sng_resume(True, CS, plan, radar)

  plan.shouldStop = False
  radar.leadOne.status = False
  assert not controller.update_sng_resume(True, CS, plan, radar)
  assert controller.sng_stop_frames == 0

  radar.leadOne.status = True
  CS.brakePressed = True
  assert not controller.update_sng_resume(True, CS, plan, radar)
  assert controller.sng_lead_baseline_m is None


def test_sng_resume_times_out_without_retrying_same_stop():
  controller = sng_controller()
  CS = SimpleNamespace(vEgo=0.0, standstill=True, brakePressed=False, gasPressed=False,
                       cruiseState=SimpleNamespace(standstill=True))
  plan = SimpleNamespace(shouldStop=True)
  radar = SimpleNamespace(leadOne=SimpleNamespace(status=True, dRel=6.0, vLead=0.0, vRel=0.0))

  for _ in range(SNG_STOP_CONFIRM_FRAMES):
    controller.update_sng_resume(True, CS, plan, radar)
  plan.shouldStop = False
  radar.leadOne.dRel = 6.6
  radar.leadOne.vRel = 0.8
  for _ in range(SNG_LEAD_CONFIRM_FRAMES):
    controller.update_sng_resume(True, CS, plan, radar)
  assert controller.sng_resume_ready

  controller.long_control_state = LongCtrlState.starting
  for _ in range(SNG_RESUME_TIMEOUT_FRAMES):
    controller.update_sng_resume(True, CS, plan, radar)
  assert not controller.sng_resume_ready
  assert controller.sng_resume_attempted

  controller.long_control_state = LongCtrlState.stopping
  for _ in range(SNG_STOP_CONFIRM_FRAMES + SNG_LEAD_CONFIRM_FRAMES):
    assert not controller.update_sng_resume(True, CS, plan, radar)

  CS.vEgo = 1.0
  assert not controller.update_sng_resume(True, CS, plan, radar)
  assert not controller.sng_resume_attempted
