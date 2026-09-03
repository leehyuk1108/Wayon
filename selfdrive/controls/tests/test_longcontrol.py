from types import SimpleNamespace

from cereal import car, custom
from openpilot.selfdrive.controls.lib.longcontrol import (LongControl, LongCtrlState,
                                                          SNG_LEAD_CONFIRM_FRAMES, SNG_RESUME_TIMEOUT_FRAMES,
                                                          SNG_PRESTOP_TRACK_SPEED, SNG_STOP_CONFIRM_FRAMES,
                                                          long_control_state_trans, use_gm_auto_hold_sng)
from openpilot.sunnypilot.selfdrive.controls.lib.adaptive_longitudinal_smoother import AdaptiveLongitudinalSmoother




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


def test_gm_hold_blocks_launch_without_confirmed_lead_departure():
  CP = car.CarParams.new_message(brand="gm", autoResumeSng=True, startingState=True,
                                 vEgoStopping=0.5, vEgoStarting=0.5)
  CP_SP = custom.CarParamsSP.new_message()
  assert use_gm_auto_hold_sng(CP)

  next_state = long_control_state_trans(CP, CP_SP, True, LongCtrlState.stopping, v_ego=0.0,
                                        should_stop=False, brake_pressed=False, cruise_standstill=False,
                                        sng_resume=False)
  assert next_state == LongCtrlState.stopping

  next_state = long_control_state_trans(CP, CP_SP, True, LongCtrlState.stopping, v_ego=0.0,
                                        should_stop=False, brake_pressed=False, cruise_standstill=False,
                                        sng_resume=True)
  assert next_state == LongCtrlState.starting


def sng_controller():
  controller = LongControl.__new__(LongControl)
  controller.CP = SimpleNamespace(brand="gm", autoResumeSng=True, vEgoStarting=0.5)
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
                       cruiseState=SimpleNamespace(standstill=False))
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


def test_sng_resume_tracks_lead_before_full_stop():
  controller = sng_controller()
  CS = SimpleNamespace(vEgo=SNG_PRESTOP_TRACK_SPEED, standstill=False, brakePressed=False, gasPressed=False,
                       cruiseState=SimpleNamespace(standstill=False))
  plan = SimpleNamespace(shouldStop=True)
  radar = SimpleNamespace(leadOne=SimpleNamespace(status=True, dRel=5.5, vLead=0.0, vRel=0.0))

  for _ in range(SNG_STOP_CONFIRM_FRAMES):
    assert not controller.update_sng_resume(True, CS, plan, radar)

  CS.vEgo = 0.35
  plan.shouldStop = False
  radar.leadOne.dRel = 6.1
  radar.leadOne.vRel = 0.8
  for _ in range(SNG_LEAD_CONFIRM_FRAMES - 1):
    assert not controller.update_sng_resume(True, CS, plan, radar)
  assert controller.update_sng_resume(True, CS, plan, radar)


def test_sng_resume_rejects_lead_loss_and_driver_input():
  controller = sng_controller()
  CS = SimpleNamespace(vEgo=0.0, standstill=True, brakePressed=False, gasPressed=False,
                       cruiseState=SimpleNamespace(standstill=False))
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

  CS.vEgo = SNG_PRESTOP_TRACK_SPEED + 0.1
  assert not controller.update_sng_resume(True, CS, plan, radar)
  assert not controller.sng_resume_attempted


def run_smoother(target, seconds=4.0, **kwargs):
  smoother = AdaptiveLongitudinalSmoother(dt=0.01)
  smoother.reset(0.0)
  outputs = []
  for _ in range(round(seconds / smoother.dt)):
    outputs.append(smoother.update(target, measured_accel=outputs[-1] if outputs else 0.0,
                                   v_ego=20.0, v_target=20.0, **kwargs))
  return outputs


def test_adaptive_smoother_builds_and_releases_brake_without_overshoot():
  outputs = run_smoother(-1.0)
  slopes = [(outputs[i] - outputs[i - 1]) / 0.01 for i in range(1, len(outputs))]

  assert min(outputs) >= -1.0
  assert abs(outputs[-1] + 1.0) < 0.01
  assert abs(slopes[2]) < max(abs(s) for s in slopes)
  assert abs(slopes[-2]) < max(abs(s) for s in slopes)


def test_adaptive_smoother_compresses_curve_for_stronger_braking():
  mild = run_smoother(-0.4, seconds=1.0)
  strong = run_smoother(-2.0, seconds=1.0)

  assert abs(strong[-1]) > abs(mild[-1]) * 2.0
  assert strong[-1] < -1.0


def test_adaptive_smoother_responds_faster_to_closing_lead():
  calm = run_smoother(-0.6, seconds=0.5)
  lead = SimpleNamespace(status=True, dRel=10.0, vRel=-6.0)
  urgent = run_smoother(-0.6, seconds=0.5, lead=lead)

  assert urgent[-1] < calm[-1]


def test_adaptive_smoother_releases_brake_faster_for_departing_radar_lead():
  calm_smoother = AdaptiveLongitudinalSmoother(dt=0.01)
  calm_smoother.reset(-0.6)
  calm = [calm_smoother.update(0.3, measured_accel=-0.4, v_ego=3.0, v_target=3.5)
          for _ in range(50)]

  departing_smoother = AdaptiveLongitudinalSmoother(dt=0.01)
  departing_smoother.reset(-0.6)
  departing_lead = SimpleNamespace(status=True, radar=True, dRel=12.0, vRel=1.0,
                                   aLeadK=0.7, jLead=0.8)
  departing = [departing_smoother.update(0.3, measured_accel=-0.4, v_ego=3.0, v_target=3.5,
                                         lead=departing_lead) for _ in range(50)]

  assert departing[-1] > calm[-1]


def test_adaptive_smoother_preserves_emergency_brake_response():
  outputs = run_smoother(-3.0, seconds=0.5)

  assert outputs[-1] < -2.0
  assert min(outputs) >= -3.0


def test_adaptive_smoother_releases_brake_without_lingering_or_overshoot():
  smoother = AdaptiveLongitudinalSmoother(dt=0.01)
  smoother.reset(-1.0)
  outputs = [smoother.update(0.0, measured_accel=smoother.output_accel,
                             v_ego=18.0, v_target=18.0) for _ in range(150)]

  assert outputs[49] < -0.3
  assert outputs[99] > -0.15
  assert outputs[-1] > -0.05
  assert max(outputs) <= 0.0


def test_adaptive_smoother_acceleration_is_smooth_and_bounded():
  outputs = run_smoother(0.8)
  slopes = [(outputs[i] - outputs[i - 1]) / 0.01 for i in range(1, len(outputs))]

  assert max(outputs) <= 0.8
  assert abs(outputs[-1] - 0.8) < 0.01
  assert slopes[2] < max(slopes)
  assert slopes[-2] < max(slopes)
