from pathlib import Path

from cereal import log
from openpilot.selfdrive.monitoring.remote_control import neutralize_driver_monitoring, remote_control_active


class FakeParams:
  def __init__(self, onroad: bool):
    self.onroad = onroad

  def get_bool(self, key: str) -> bool:
    return self.onroad if key == "IsOnroad" else False


def test_remote_control_active_requires_onroad_and_session(tmp_path: Path):
  session_path = tmp_path / "RemoteControlNextDrive"
  assert not remote_control_active(FakeParams(False), str(session_path))
  assert not remote_control_active(FakeParams(True), str(session_path))

  session_path.touch()
  assert not remote_control_active(FakeParams(False), str(session_path))
  assert remote_control_active(FakeParams(True), str(session_path))


def test_neutralize_driver_monitoring_preserves_metadata():
  dat = log.Event.new_message()
  state = dat.init("driverMonitoringState")
  state.lockout = True
  state.alertCountLockoutPercent = 100
  state.alertTimeLockoutPercent = 100
  state.alwaysOn = True
  state.alwaysOnLockout = True
  state.alertLevel = log.DriverMonitoringState.AlertLevel.three
  state.activePolicy = log.DriverMonitoringState.MonitoringPolicy.vision
  state.isRHD = True
  state.visionPolicyState.awarenessPercent = 0
  state.visionPolicyState.awarenessStep = -0.1
  state.visionPolicyState.isDistracted = True
  state.visionPolicyState.distractedTypes.pose = True
  state.visionPolicyState.distractedTypes.eye = True
  state.visionPolicyState.distractedTypes.phone = True
  state.visionPolicyState.faceDetected = True
  state.visionPolicyState.wheeltouchFallbackPercent = 100
  state.visionPolicyState.uncertainOffroadAlertPercent = 100
  state.wheeltouchPolicyState.awarenessPercent = 0
  state.wheeltouchPolicyState.awarenessStep = -0.1
  state.wheeltouchPolicyState.driverInteracting = True

  is_rhd = dat.driverMonitoringState.isRHD
  always_on = dat.driverMonitoringState.alwaysOn
  active_policy = dat.driverMonitoringState.activePolicy
  neutralize_driver_monitoring(dat)
  state = dat.driverMonitoringState

  assert not state.lockout
  assert state.alertCountLockoutPercent == 0
  assert state.alertTimeLockoutPercent == 0
  assert not state.alwaysOnLockout
  assert state.alertLevel == log.DriverMonitoringState.AlertLevel.none
  assert state.visionPolicyState.awarenessPercent == 100
  assert state.visionPolicyState.awarenessStep == 0.0
  assert not state.visionPolicyState.isDistracted
  assert not state.visionPolicyState.distractedTypes.pose
  assert not state.visionPolicyState.distractedTypes.eye
  assert not state.visionPolicyState.distractedTypes.phone
  assert not state.visionPolicyState.faceDetected
  assert state.visionPolicyState.wheeltouchFallbackPercent == 0
  assert state.visionPolicyState.uncertainOffroadAlertPercent == 0
  assert state.wheeltouchPolicyState.awarenessPercent == 100
  assert state.wheeltouchPolicyState.awarenessStep == 0.0
  assert not state.wheeltouchPolicyState.driverInteracting

  assert state.isRHD == is_rhd
  assert state.alwaysOn == always_on
  assert state.activePolicy == active_policy
