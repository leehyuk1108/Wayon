import os

from cereal import log


REMOTE_CONTROL_SESSION = "/data/RemoteControlNextDrive"


def remote_control_active(params, session_path: str = REMOTE_CONTROL_SESSION) -> bool:
  """True only during the onroad cycle selected for remote control."""
  return params.get_bool("IsOnroad") and os.path.isfile(session_path)


def neutralize_driver_monitoring(dat):
  """Keep driverMonitoringState alive without alerts or forced deceleration."""
  dm = dat.driverMonitoringState
  dm.lockout = False
  dm.alertCountLockoutPercent = 0
  dm.alertTimeLockoutPercent = 0
  dm.alwaysOnLockout = False
  dm.alertLevel = log.DriverMonitoringState.AlertLevel.none

  dm.visionPolicyState.awarenessPercent = 100
  dm.visionPolicyState.awarenessStep = 0.0
  dm.visionPolicyState.isDistracted = False
  dm.visionPolicyState.distractedTypes.pose = False
  dm.visionPolicyState.distractedTypes.eye = False
  dm.visionPolicyState.distractedTypes.phone = False
  dm.visionPolicyState.faceDetected = False
  dm.visionPolicyState.wheeltouchFallbackPercent = 0
  dm.visionPolicyState.uncertainOffroadAlertPercent = 0

  dm.wheeltouchPolicyState.awarenessPercent = 100
  dm.wheeltouchPolicyState.awarenessStep = 0.0
  dm.wheeltouchPolicyState.driverInteracting = False
  return dat
