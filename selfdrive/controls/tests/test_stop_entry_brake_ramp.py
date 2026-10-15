from types import SimpleNamespace

import numpy as np
import pytest

from cereal import car
from opendbc.car.gm.carcontroller import get_gas_brake_commands, limit_traverse_stopping_brake
from opendbc.car.gm.values import CarControllerParams, get_traverse_stopping_accel_floor
from openpilot.selfdrive.controls.tests.test_longcontrol import high_speed_controller  # noqa: F401
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_longitudinal_coordinator import StopEntryBrakeRamp


def lead(**kwargs):
  return SimpleNamespace(**dict(status=True, radar=True, radarTrackId=10, dRel=6.0, vRel=-0.1, vLeadK=0.0) | kwargs)


@pytest.mark.parametrize("speed,initial,accel", [(0.0499, 0.0, -0.44), (0.494, -0.1833, -0.2), (0.1, 0.0, -0.1)])
def test_ramp_builds_monotonically_and_finishes_within_200ms(speed, initial, accel):
  ramp = StopEntryBrakeRamp()
  values = [initial]
  for _ in range(21):
    output = ramp.update(True, values[-1], -0.12, speed, speed, accel, lead())
    if output is None:
      break
    values.append(output)
  else:
    pytest.fail("handoff did not finish")
  assert len(values) <= 21
  assert values[-1] == pytest.approx(get_traverse_stopping_accel_floor(speed))
  assert np.max(np.abs(np.diff(values))) <= 0.1
  assert np.all(np.diff(values) <= 0)


@pytest.mark.parametrize("change", [
  {"enabled": False}, {"previous_accel": 0.1}, {"requested_accel": -1.0},
  {"v_ego": 0.0}, {"v_ego_raw": 0.0}, {"v_ego_raw": 1.0},
  {"a_ego": 0.2}, {"a_ego": -1.1}, {"lead": None},
  {"lead": lead(dRel=3.4)}, {"lead": lead(vRel=-0.71)},
  {"lead": lead(radar=False)}, {"lead": lead(radarTrackId=-1)},
  {"lead": lead(dRel=float("nan"))}, {"requested_accel": float("nan")},
  {"previous_accel": float("nan")}, {"v_ego": float("inf")},
])
def test_unverified_or_urgent_stop_never_uses_handoff(change):
  args = dict(enabled=True, previous_accel=0.0, requested_accel=-0.1,
              v_ego=0.05, v_ego_raw=0.05, a_ego=-0.2, lead=lead()) | change
  assert StopEntryBrakeRamp().update(**args) is None


def test_track_change_and_already_sufficient_braking_bypass_ramp():
  ramp = StopEntryBrakeRamp()
  assert ramp.update(True, 0.0, -0.1, 0.1, 0.1, -0.1, lead()) is not None
  assert ramp.update(True, -0.025, -0.1, 0.1, 0.1, -0.1, lead(radarTrackId=20)) is None
  assert StopEntryBrakeRamp().update(True, -0.5, -0.1, 0.1, 0.1, -0.1, lead()) is None


def inputs(controller, speed=0.0499, initial=0.0):
  controller.long_control_state = car.CarControl.Actuators.LongControlState.pid
  controller.last_output_accel = initial
  controller.accel_smoother.reset(initial)
  controller.queue_creep_controller.stopped_latched = True
  cs = car.CarState.new_message(vEgo=speed, vEgoRaw=speed, aEgo=-0.44, canValid=True, gearShifter="drive")
  cs.cruiseState.enabled = True
  plan = SimpleNamespace(aTarget=-0.12, speeds=[speed], shouldStop=True, jTargetNow=0.0, fcw=False,
                         longitudinalPlanSource="lead0")
  radar = SimpleNamespace(leadOne=lead(), leadTwo=SimpleNamespace(status=False))
  return cs, plan, radar


@pytest.mark.parametrize("speed,initial", [(0.0499, 0.0), (0.494, -0.1833)])
def test_longcontrol_and_gm_mapping_have_no_floor_step(high_speed_controller, speed, initial):  # noqa: F811
  ctrl = high_speed_controller
  cs, plan, radar = inputs(ctrl, speed, initial)
  params = CarControllerParams(ctrl.CP)
  values, brakes, states = [initial], [], []
  for _ in range(24):
    value = float(ctrl.update(True, cs, plan, (-4.0, 2.0), radar, manual_resume_sensors_valid=True))
    stopping = ctrl.long_control_state == car.CarControl.Actuators.LongControlState.stopping
    gas, brake = get_gas_brake_commands(params, value)
    brakes.append(limit_traverse_stopping_brake(ctrl.CP, stopping, speed, brake))
    states.append(stopping)
    values.append(value)
    assert gas <= 0
  assert not states[0] and states[-1]
  assert np.max(np.abs(np.diff(values))) <= 0.1
  assert np.max(np.abs(np.diff(brakes))) <= 10
  initial_brake = get_gas_brake_commands(params, initial)[1]
  for phase in range(4):
    # GM transmits brake commands at 25 Hz, not at the controller's 100 Hz.
    assert np.max(np.abs(np.diff([initial_brake, *brakes[phase::4]]))) <= 25
  assert values[-1] <= get_traverse_stopping_accel_floor(speed)


@pytest.mark.parametrize("gate", ["stale", "standstill", "canInvalid", "fault", "brakePressed", "gasPressed",
                                 "regenBraking", "parkingBrake", "reverse", "fcw", "secondary", "takeover", "off", "resume"])
def test_integration_gates_never_delay_stopping(high_speed_controller, gate):  # noqa: F811
  ctrl = high_speed_controller
  cs, plan, radar = inputs(ctrl)
  if gate in ("standstill", "brakePressed", "gasPressed", "regenBraking", "parkingBrake"):
    setattr(cs, gate, True)
  elif gate == "canInvalid":
    cs.canValid = False
  elif gate == "fault":
    cs.accFaulted = True
  elif gate == "reverse":
    cs.gearShifter = "reverse"
  elif gate == "fcw":
    plan.fcw = True
  elif gate == "secondary":
    radar.leadTwo.status = True
  elif gate == "off":
    ctrl.long_control_state = car.CarControl.Actuators.LongControlState.off
  elif gate == "resume":
    ctrl.CP.autoResumeSng = True
    ctrl.sng_resume_attempted = True
    ctrl.sng_resume_failed = True
  ctrl.update(True, cs, plan, (-4.0, 2.0), radar, manual_resume_sensors_valid=gate != "stale",
              soft_disabling=gate == "takeover")
  assert ctrl.stop_entry_ramp.frames == 0
  assert ctrl.long_control_state == car.CarControl.Actuators.LongControlState.stopping


def test_normal_pid_clears_old_stop_output(high_speed_controller):  # noqa: F811
  ctrl = high_speed_controller
  cs, plan, radar = inputs(ctrl, speed=1.0, initial=-0.1)
  ctrl.stop_controller.output_accel = -1.5
  ctrl.stop_controller.phase = "taper"
  plan.shouldStop = False
  ctrl.update(True, cs, plan, (-4.0, 2.0), radar, manual_resume_sensors_valid=True)
  assert ctrl.stop_controller.output_accel is None
  assert ctrl.stop_controller.phase == "inactive"


def test_real_standstill_interrupts_handoff_and_keeps_floor(high_speed_controller):  # noqa: F811
  ctrl = high_speed_controller
  cs, plan, radar = inputs(ctrl)
  assert ctrl.update(True, cs, plan, (-4.0, 2.0), radar, manual_resume_sensors_valid=True) > -0.3
  cs.standstill = True
  cs.vEgo = cs.vEgoRaw = 0.0
  value = ctrl.update(True, cs, plan, (-4.0, 2.0), radar, manual_resume_sensors_valid=True)
  assert ctrl.long_control_state == car.CarControl.Actuators.LongControlState.stopping
  assert value <= -0.3


@pytest.mark.parametrize("reason", ["stale", "close", "fastClosing", "track", "strongDemand", "fcw", "secondary"])
def test_changed_risk_interrupts_in_progress_handoff(high_speed_controller, reason):  # noqa: F811
  ctrl = high_speed_controller
  cs, plan, radar = inputs(ctrl, speed=0.2)
  ctrl.update(True, cs, plan, (-4.0, 2.0), radar, manual_resume_sensors_valid=True)
  assert ctrl.stop_entry_ramp.frames == 1
  if reason == "close":
    radar.leadOne.dRel = 3.0
  elif reason == "fastClosing":
    radar.leadOne.vRel = -1.0
  elif reason == "track":
    radar.leadOne.radarTrackId = 20
  elif reason == "strongDemand":
    plan.aTarget = -2.0
  elif reason == "fcw":
    plan.fcw = True
  elif reason == "secondary":
    radar.leadTwo.status = True
  ctrl.update(True, cs, plan, (-4.0, 2.0), radar, manual_resume_sensors_valid=reason != "stale")
  assert ctrl.long_control_state == car.CarControl.Actuators.LongControlState.stopping


def test_stop_request_clearing_cancels_ramp_without_carrying_state(high_speed_controller):  # noqa: F811
  ctrl = high_speed_controller
  cs, plan, radar = inputs(ctrl, speed=0.2)
  previous = ctrl.update(True, cs, plan, (-4.0, 2.0), radar, manual_resume_sensors_valid=True)
  plan.shouldStop = False
  plan.aTarget = 0.0
  value = ctrl.update(True, cs, plan, (-4.0, 2.0), radar, manual_resume_sensors_valid=True)
  assert ctrl.stop_entry_ramp.frames == 0
  assert ctrl.stop_controller.output_accel is None
  assert abs(value - previous) <= 0.03
