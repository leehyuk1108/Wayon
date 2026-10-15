"""Exercise the actual controlsd call/publication path without sockets or actuators."""
from types import SimpleNamespace

import pytest

from cereal import car, custom, log
import cereal.messaging as messaging
from openpilot.selfdrive.controls.controlsd import Controls

State = log.SelfdriveState.OpenpilotState


class FakeSubMaster(dict):
  def __init__(self):
    services = ("selfdriveState", "driverMonitoringState", "longitudinalPlan", "liveParameters", "modelV2", "liveDelay")
    super().__init__({name: getattr(messaging.new_message(name), name) for name in services})
    self["carState"] = car.CarState.new_message(vEgo=20.0, vEgoRaw=20.0, canValid=True, gearShifter="drive")
    self["selfdriveState"].enabled = True
    self["selfdriveStateSP"] = SimpleNamespace(intelligentCruiseButtonManagement=None)
    self["drivingModelData"] = SimpleNamespace(frameId=0)
    self["onroadEvents"] = []
    self.valid = {"driverAssistance": False, "lateralManeuverPlan": False, "drivingModelData": False}
    self.alive = {"drivingModelData": False}
    self.logMonoTime = {"longitudinalPlan": 1, "modelV2": 1}

  def all_checks(self, services):
    return True


def fake_controls(fingerprint="CHEVROLET_TRAVERSE"):
  controls = Controls.__new__(Controls)
  controls.CP = car.CarParams.new_message(brand="gm", carFingerprint=fingerprint,
                                         openpilotLongitudinalControl=True)
  controls.CP.lateralTuning.init("pid")
  controls.CP_SP = custom.CarParamsSP.new_message()
  controls.sm = FakeSubMaster()
  controls.curvature = controls.desired_curvature = 0.0
  controls.calibrated_pose = None
  controls.steer_limited_by_safety = controls.model_curvature_guard_active = False
  controls.gm_manual_resume_receiver = None
  controls.get_lat_active = lambda sm: False
  controls.CI = SimpleNamespace(get_pid_accel_limits=lambda *args: (-3.5, 2.0))
  controls.VM = SimpleNamespace(update_params=lambda *args: None, calc_curvature=lambda *args: 0.0)
  lateral_log = log.ControlsState.new_message().lateralControlState.init("pidState")
  controls.LaC = SimpleNamespace(reset=lambda: None, update=lambda *args: (0.0, 0.0, lateral_log))
  captured = {}

  def update(*args, **kwargs):
    captured.update(kwargs)
    return 0.0

  controls.LoC = SimpleNamespace(long_control_state=car.CarControl.Actuators.LongControlState.pid,
                                pid=SimpleNamespace(p=0.0, i=0.0, f=0.0), reset=lambda: None,
                                update=update, get_resume_request=lambda *args: False)
  sent = {}
  controls.pm = SimpleNamespace(send=lambda name, message: sent.update({name: message.to_dict()}))
  return controls, captured, sent, lateral_log


@pytest.mark.parametrize("state", [State.enabled, State.softDisabling])
def test_actual_controlsd_passes_takeover_state_to_long_control(state):
  controls, captured, _, _ = fake_controls()
  controls.sm["selfdriveState"].state = state
  controls.sm["radarState"] = SimpleNamespace(leadOne=SimpleNamespace(status=False), leadTwo=SimpleNamespace(status=False))
  controls.state_control()
  assert captured["soft_disabling"] == (state == State.softDisabling)


@pytest.mark.parametrize("state", [State.enabled, State.softDisabling, State.disabled])
@pytest.mark.parametrize("driver_unresponsive", [False, True])
@pytest.mark.parametrize("fingerprint", ["CHEVROLET_TRAVERSE", "CHEVROLET_BOLT_EUV"])
def test_actual_publication_preserves_driver_monitoring_but_not_traverse_soft_disable_decel(
    state, driver_unresponsive, fingerprint):
  controls, _, sent, lateral_log = fake_controls(fingerprint)
  controls.sm["selfdriveState"].state = state
  controls.sm["driverMonitoringState"].alertLevel = "three" if driver_unresponsive else "none"
  cc = car.CarControl.new_message(enabled=True, longActive=True)
  controls.publish(cc, lateral_log)
  expected = driver_unresponsive or (state == State.softDisabling and fingerprint != "CHEVROLET_TRAVERSE")
  assert sent["controlsState"]["controlsState"]["forceDecel"] == expected
