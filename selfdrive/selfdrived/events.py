#!/usr/bin/env python3
import json
import math
import os
from pathlib import Path

from cereal import log, car
import cereal.messaging as messaging
from openpilot.common.constants import CV
from openpilot.common.git import get_short_branch
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.locationd.calibrationd import MIN_SPEED_FILTER
from openpilot.system.micd import SAMPLE_RATE, SAMPLE_BUFFER
from openpilot.selfdrive.ui.feedback.feedbackd import FEEDBACK_MAX_DURATION
from openpilot.system.hardware import HARDWARE

from openpilot.sunnypilot.selfdrive.selfdrived.events_base import EventsBase, Priority, ET, Alert, \
  NoEntryAlert, SoftDisableAlert, UserSoftDisableAlert, ImmediateDisableAlert, EngagementAlert, NormalPermanentAlert, \
  StartupAlert, AlertCallbackType, wrong_car_mode_alert


AlertSize = log.SelfdriveState.AlertSize
AlertStatus = log.SelfdriveState.AlertStatus
VisualAlert = car.CarControl.HUDControl.VisualAlert
AudibleAlert = car.CarControl.HUDControl.AudibleAlert
EventName = log.OnroadEvent.EventName


# get event name from enum
EVENT_NAME = {v: k for k, v in EventName.schema.enumerants.items()}
MICI_EVENT_ALERT_OVERRIDES_PATH = Path(__file__).resolve().parents[1] / "ui/mici/mici_event_alert_overrides.json"


class Events(EventsBase):
  def __init__(self):
    super().__init__()
    self.event_counters = dict.fromkeys(EVENTS.keys(), 0)

  def get_events_mapping(self) -> dict[int, dict[str, Alert | AlertCallbackType]]:
    return EVENTS

  def get_event_name(self, event: int):
    return EVENT_NAME[event]

  def get_event_msg_type(self):
    return log.OnroadEvent



# ********** helper functions **********
def get_display_speed(speed_ms: float, metric: bool) -> str:
  speed = int(round(speed_ms * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH)))
  unit = 'km/h' if metric else 'mph'
  return f"{speed} {unit}"


# ********** alert callback functions **********


def soft_disable_alert(alert_text_2: str) -> AlertCallbackType:
  def func(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
    if soft_disable_time < int(0.5 / DT_CTRL):
      return ImmediateDisableAlert(alert_text_2)
    return SoftDisableAlert(alert_text_2)
  return func

def user_soft_disable_alert(alert_text_2: str) -> AlertCallbackType:
  def func(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
    if soft_disable_time < int(0.5 / DT_CTRL):
      return ImmediateDisableAlert(alert_text_2)
    return UserSoftDisableAlert(alert_text_2)
  return func

def startup_master_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  branch = get_short_branch()  # Ensure get_short_branch is cached to avoid lags on startup
  if "REPLAY" in os.environ:
    branch = "replay"

  return StartupAlert("WARNING: This branch is not tested", branch, alert_status=AlertStatus.userPrompt)

def below_engage_speed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  return NoEntryAlert(f"Drive above {get_display_speed(CP.minEnableSpeed, metric)} to engage")


def below_steer_speed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  return Alert(
    f"Steer Assist Unavailable Below {get_display_speed(CP.minSteerSpeed, metric)}",
    "",
    AlertStatus.userPrompt, AlertSize.small,
    Priority.LOW, VisualAlert.none, AudibleAlert.prompt, 0.4)


def calibration_incomplete_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  first_word = 'Recalibrating' if sm['liveCalibration'].calStatus == log.LiveCalibrationData.Status.recalibrating else 'Calibrating'
  return Alert(
    f"{first_word}: {sm['liveCalibration'].calPerc:.0f}%",
    f"Drive Above {get_display_speed(MIN_SPEED_FILTER, metric)}",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2)


def audio_feedback_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  duration = FEEDBACK_MAX_DURATION - ((sm['audioFeedback'].blockNum + 1) * SAMPLE_BUFFER / SAMPLE_RATE)
  return NormalPermanentAlert(
    "Recording Audio Feedback",
    f"{round(duration)} second{'s' if round(duration) != 1 else ''} remaining. Press again to save early.",
    priority=Priority.LOW)


# *** debug alerts ***

def out_of_space_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  full_perc = round(100. - sm['deviceState'].freeSpacePercent)
  return NormalPermanentAlert("Out of Storage", f"{full_perc}% full")


def posenet_invalid_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  mdl = sm['modelV2'].velocity.x[0] if len(sm['modelV2'].velocity.x) else math.nan
  err = CS.vEgo - mdl
  msg = f"Speed Error: {err:.1f} m/s"
  return NoEntryAlert(msg, alert_text_1="Posenet Speed Invalid")


def process_not_running_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  not_running = [p.name for p in sm['managerState'].processes if not p.running and p.shouldBeRunning]
  msg = ', '.join(not_running)
  return NoEntryAlert(msg, alert_text_1="Process Not Running")


def comm_issue_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  bs = [s for s in sm.data.keys() if not sm.all_checks([s, ])]
  msg = ', '.join(bs[:4])  # can't fit too many on one line
  return NoEntryAlert(msg, alert_text_1="Communication Issue Between Processes")


def camera_malfunction_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  all_cams = ('roadCameraState', 'driverCameraState', 'wideRoadCameraState')
  bad_cams = [s.replace('State', '') for s in all_cams if s in sm.data.keys() and not sm.all_checks([s, ])]
  return NormalPermanentAlert("Camera Malfunction", ', '.join(bad_cams))


def calibration_invalid_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  rpy = sm['liveCalibration'].rpyCalib
  yaw = math.degrees(rpy[2] if len(rpy) == 3 else math.nan)
  pitch = math.degrees(rpy[1] if len(rpy) == 3 else math.nan)
  angles = f"Remount Device (Pitch: {pitch:.1f}°, Yaw: {yaw:.1f}°)"
  return NormalPermanentAlert("Calibration Invalid", angles)


def paramsd_invalid_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  if not sm['liveParameters'].angleOffsetValid:
    angle_offset_deg = sm['liveParameters'].angleOffsetDeg
    title = "Steering misalignment detected"
    text = f"Angle offset too high (Offset: {angle_offset_deg:.1f}°)"
  elif not sm['liveParameters'].steerRatioValid:
    steer_ratio = sm['liveParameters'].steerRatio
    title = "Steer ratio mismatch"
    text = f"Steering rack geometry may be off (Ratio: {steer_ratio:.1f})"
  elif not sm['liveParameters'].stiffnessFactorValid:
    stiffness_factor = sm['liveParameters'].stiffnessFactor
    title = "Abnormal tire stiffness"
    text = f"Check tires, pressure, or alignment (Factor: {stiffness_factor:.1f})"
  else:
    return NoEntryAlert("paramsd Temporary Error")

  return NoEntryAlert(alert_text_1=title, alert_text_2=text)

def overheat_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  cpu = max(sm['deviceState'].cpuTempC, default=0.)
  gpu = max(sm['deviceState'].gpuTempC, default=0.)
  temp = max((cpu, gpu, sm['deviceState'].memoryTempC))
  return NormalPermanentAlert("System Overheated", f"{temp:.0f} °C")


def low_memory_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  return NormalPermanentAlert("Low Memory", f"{sm['deviceState'].memoryUsagePercent}% used")


def high_cpu_usage_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  x = max(sm['deviceState'].cpuUsagePercent, default=0.)
  return NormalPermanentAlert("High CPU Usage", f"{x}% used")


def modeld_lagging_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  return NormalPermanentAlert("Driving Model Lagging", f"{sm['modelV2'].frameDropPerc:.1f}% frames dropped")


def joystick_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  gb = sm['carControl'].actuators.accel / 4.
  steer = sm['carControl'].actuators.torque
  vals = f"Gas: {round(gb * 100.)}%, Steer: {round(steer * 100.)}%"
  return NormalPermanentAlert("Joystick Mode", vals)


def longitudinal_maneuver_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  ad = sm['alertDebug']
  audible_alert = AudibleAlert.prompt if 'Active' in ad.alertText1 else AudibleAlert.none
  alert_status = AlertStatus.userPrompt if 'Active' in ad.alertText1 else AlertStatus.normal
  alert_size = AlertSize.mid if ad.alertText2 else AlertSize.small
  return Alert(ad.alertText1, ad.alertText2,
               alert_status, alert_size,
               Priority.LOW, VisualAlert.none, audible_alert, 0.2)


def personality_changed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  personality = str(personality).title()
  return NormalPermanentAlert(f"Driving Personality: {personality}", duration=1.5)


def invalid_lkas_setting_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality) -> Alert:
  text = "Toggle stock LKAS on or off to engage"
  if CP.brand == "tesla":
    text = "Switch to Traffic-Aware Cruise Control to engage"
  elif CP.brand == "mazda":
    text = "Enable your car's LKAS to engage"
  elif CP.brand == "nissan":
    text = "Disable your car's stock LKAS to engage"
  return NormalPermanentAlert("Invalid LKAS setting", text)



EVENTS: dict[int, dict[str, Alert | AlertCallbackType]] = {
  # ********** events with no alerts **********

  EventName.stockFcw: {},
  EventName.actuatorsApiUnavailable: {},

  # ********** events only containing alerts displayed in all states **********

  EventName.joystickDebug: {
    ET.WARNING: joystick_alert,
    ET.PERMANENT: NormalPermanentAlert("Joystick Mode"),
  },

  EventName.longitudinalManeuver: {
    ET.WARNING: longitudinal_maneuver_alert,
    ET.PERMANENT: NormalPermanentAlert("Longitudinal Maneuver Mode",
                                       "Ensure road ahead is clear"),
  },

  EventName.lateralManeuver: {
    ET.WARNING: longitudinal_maneuver_alert,
    ET.PERMANENT: NormalPermanentAlert("Lateral Maneuver Mode"),
  },

  EventName.selfdriveInitializing: {
    ET.NO_ENTRY: NoEntryAlert("System Initializing"),
  },

  EventName.startup: {
    ET.PERMANENT: StartupAlert("Be ready to take over at any time")
  },

  EventName.startupMaster: {
    ET.PERMANENT: startup_master_alert,
  },

  EventName.startupNoControl: {
    ET.PERMANENT: StartupAlert("Dashcam mode"),
    ET.NO_ENTRY: NoEntryAlert("Dashcam mode"),
  },

  EventName.startupNoCar: {
    ET.PERMANENT: StartupAlert("Dashcam mode for unsupported car"),
  },

  EventName.startupNoSecOcKey: {
    ET.PERMANENT: NormalPermanentAlert("Dashcam Mode",
                                       "Security Key Not Available",
                                       priority=Priority.HIGH),
  },

  EventName.dashcamMode: {
    ET.PERMANENT: NormalPermanentAlert("Dashcam Mode",
                                       priority=Priority.LOWEST),
  },

  EventName.invalidLkasSetting: {
    ET.PERMANENT: invalid_lkas_setting_alert,
    ET.NO_ENTRY: NoEntryAlert("Invalid LKAS setting"),
  },

  EventName.cruiseMismatch: {
    #ET.PERMANENT: ImmediateDisableAlert("openpilot failed to cancel cruise"),
  },

  # openpilot doesn't recognize the car. This switches openpilot into a
  # read-only mode. This can be solved by adding your fingerprint.
  # See https://github.com/commaai/openpilot/wiki/Fingerprinting for more information
  EventName.carUnrecognized: {
    ET.PERMANENT: NormalPermanentAlert("Dashcam Mode",
                                       "Car Unrecognized",
                                       priority=Priority.LOWEST),
  },

  EventName.aeb: {
    ET.PERMANENT: Alert(
      "BRAKE!",
      "Emergency Braking: Risk of Collision",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 2.),
    ET.NO_ENTRY: NoEntryAlert("AEB: Risk of Collision"),
  },

  EventName.stockAeb: {
    ET.PERMANENT: Alert(
      "BRAKE!",
      "Stock AEB: Risk of Collision",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 2.),
    ET.NO_ENTRY: NoEntryAlert("Stock AEB: Risk of Collision"),
  },

  EventName.stockLkas: {
    ET.NO_ENTRY: NoEntryAlert("Stock LKAS: Lane Departure Detected"),
  },

  EventName.fcw: {
    ET.PERMANENT: Alert(
      "BRAKE!",
      "Risk of Collision",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.warningSoft, 2.),
  },

  EventName.ldw: {
    ET.PERMANENT: Alert(
      "Lane Departure Detected",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.ldw, AudibleAlert.prompt, 3.),
  },

  # ********** events only containing alerts that display while engaged **********

  EventName.steerTempUnavailableSilent: {
    ET.WARNING: Alert(
      "Steering Assist Temporarily Unavailable",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.prompt, 1.8),
  },

  EventName.driverDistracted1: {
    ET.PERMANENT: Alert(
      "Pay Attention",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.driverDistracted2: {
    ET.PERMANENT: Alert(
      "Pay Attention",
      "Driver Distracted",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.promptDistracted, .1),
  },

  EventName.driverDistracted3: {
    ET.PERMANENT: Alert(
      "DISENGAGE IMMEDIATELY",
      "Driver Distracted",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.warningImmediate, .1),
  },

  EventName.driverUnresponsive1: {
    ET.PERMANENT: Alert(
      "Touch Steering Wheel: No Face Detected",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, .1),
  },

  EventName.driverUnresponsive2: {
    ET.PERMANENT: Alert(
      "Touch Steering Wheel",
      "Driver Unresponsive",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.promptDistracted, .1),
  },

  EventName.driverUnresponsive3: {
    ET.PERMANENT: Alert(
      "DISENGAGE IMMEDIATELY",
      "Driver Unresponsive",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.warningImmediate, .1),
  },

  EventName.manualRestart: {
    ET.WARNING: Alert(
      "TAKE CONTROL",
      "Resume Driving Manually",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .2),
  },

  EventName.resumeRequired: {
    ET.WARNING: Alert(
      "Press Resume to Exit Standstill",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .2),
  },

  EventName.belowSteerSpeed: {
    ET.WARNING: below_steer_speed_alert,
  },

  EventName.preLaneChangeLeft: {
    ET.WARNING: Alert(
      "Steer Left to Start Lane Change Once Safe",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.preLaneChangeRight: {
    ET.WARNING: Alert(
      "Steer Right to Start Lane Change Once Safe",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.laneChangeBlocked: {
    ET.WARNING: Alert(
      "Car Detected in Blindspot",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, .1),
  },

  EventName.laneChangeUnavailable: {
    ET.WARNING: Alert(
      "Lane Change Paused",
      "Lane Change Unavailable Area Detected",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.laneChange: {
    ET.WARNING: Alert(
      "Changing Lanes",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.steerSaturated: {
    ET.WARNING: Alert(
      "Take Control",
      "Turn Exceeds Steering Limit",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.promptRepeat, 2.),
  },

  # Thrown when the fan is driven at >50% but is not rotating
  EventName.fanMalfunction: {
    ET.PERMANENT: NormalPermanentAlert("Fan Malfunction", "Likely Hardware Issue"),
  },

  # Camera is not outputting frames
  EventName.cameraMalfunction: {
    ET.PERMANENT: camera_malfunction_alert,
    ET.SOFT_DISABLE: soft_disable_alert("Camera Malfunction"),
    ET.NO_ENTRY: NoEntryAlert("Camera Malfunction: Reboot Your Device"),
  },
  # Camera framerate too low
  EventName.cameraFrameRate: {
    ET.PERMANENT: NormalPermanentAlert("Camera Frame Rate Low", "Reboot your Device"),
    ET.SOFT_DISABLE: soft_disable_alert("Camera Frame Rate Low"),
    ET.NO_ENTRY: NoEntryAlert("Camera Frame Rate Low: Reboot Your Device"),
  },

  # Unused

  EventName.locationdTemporaryError: {
    ET.NO_ENTRY: NoEntryAlert("locationd Temporary Error"),
    ET.SOFT_DISABLE: soft_disable_alert("locationd Temporary Error"),
  },

  EventName.locationdPermanentError: {
    ET.NO_ENTRY: NoEntryAlert("locationd Permanent Error"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("locationd Permanent Error"),
    ET.PERMANENT: NormalPermanentAlert("locationd Permanent Error"),
  },

  # openpilot tries to learn certain parameters about your car by observing
  # how the car behaves to steering inputs from both human and openpilot driving.
  # This includes:
  # - steer ratio: gear ratio of the steering rack. Steering angle divided by tire angle
  # - tire stiffness: how much grip your tires have
  # - angle offset: most steering angle sensors are offset and measure a non zero angle when driving straight
  # This alert is thrown when any of these values exceed a sanity check. This can be caused by
  # bad alignment or bad sensor data. If this happens consistently consider creating an issue on GitHub
  EventName.paramsdTemporaryError: {
    ET.NO_ENTRY: paramsd_invalid_alert,
    ET.SOFT_DISABLE: soft_disable_alert("paramsd Temporary Error"),
  },

  EventName.paramsdPermanentError: {
    ET.NO_ENTRY: NoEntryAlert("paramsd Permanent Error"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("paramsd Permanent Error"),
    ET.PERMANENT: NormalPermanentAlert("paramsd Permanent Error"),
  },

  # ********** events that affect controls state transitions **********

  EventName.pcmEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.engage),
  },

  EventName.buttonEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.engage),
  },

  EventName.pcmDisable: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
  },

  EventName.buttonCancel: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("Cancel Pressed"),
  },

  EventName.brakeHold: {
    ET.WARNING: Alert(
      "Press Resume to Exit Brake Hold",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .2),
  },

  EventName.parkBrake: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("Parking Brake Engaged"),
  },

  EventName.pedalPressed: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("Pedal Pressed",
                              visual_alert=VisualAlert.brakePressed),
  },

  EventName.steerDisengage: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("Steering Pressed"),
  },

  EventName.preEnableStandstill: {
    ET.PRE_ENABLE: Alert(
      "Release Brake to Engage",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1, creation_delay=1.),
  },

  EventName.gasPressedOverride: {
    ET.OVERRIDE_LONGITUDINAL: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.steerOverride: {
    ET.OVERRIDE_LATERAL: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.wrongCarMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: wrong_car_mode_alert,
  },

  EventName.resumeBlocked: {
    ET.NO_ENTRY: NoEntryAlert("Press Set to Engage"),
  },

  EventName.wrongCruiseMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("Adaptive Cruise Disabled"),
  },

  EventName.steerTempUnavailable: {
    ET.SOFT_DISABLE: soft_disable_alert("Steering Assist Temporarily Unavailable"),
    ET.NO_ENTRY: NoEntryAlert("Steering Temporarily Unavailable"),
  },

  EventName.steerTimeLimit: {
    ET.SOFT_DISABLE: soft_disable_alert("Vehicle Steering Time Limit"),
    ET.NO_ENTRY: NoEntryAlert("Vehicle Steering Time Limit"),
  },

  EventName.outOfSpace: {
    ET.PERMANENT: out_of_space_alert,
    ET.NO_ENTRY: NoEntryAlert("Out of Storage"),
  },

  EventName.belowEngageSpeed: {
    ET.NO_ENTRY: below_engage_speed_alert,
  },

  EventName.sensorDataInvalid: {
    ET.PERMANENT: Alert(
      "Sensor Data Invalid",
      "Possible Hardware Issue",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, .2, creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("Sensor Data Invalid"),
    ET.SOFT_DISABLE: soft_disable_alert("Sensor Data Invalid"),
  },

  EventName.noGps: {
  },

  EventName.tooDistracted: {
    ET.NO_ENTRY: NoEntryAlert("Distraction Level Too High"),
  },

  EventName.excessiveActuation: {
    ET.SOFT_DISABLE: soft_disable_alert("Excessive Actuation"),
    ET.NO_ENTRY: NoEntryAlert("Excessive Actuation"),
  },

  EventName.overheat: {
    ET.PERMANENT: overheat_alert,
    ET.SOFT_DISABLE: soft_disable_alert("System Overheated"),
    ET.NO_ENTRY: NoEntryAlert("System Overheated"),
  },

  EventName.wrongGear: {
    ET.SOFT_DISABLE: user_soft_disable_alert("Gear not D"),
    ET.NO_ENTRY: NoEntryAlert("Gear not D"),
  },

  # This alert is thrown when the calibration angles are outside of the acceptable range.
  # For example if the device is pointed too much to the left or the right.
  # Usually this can only be solved by removing the mount from the windshield completely,
  # and attaching while making sure the device is pointed straight forward and is level.
  # See https://comma.ai/setup for more information
  EventName.calibrationInvalid: {
    ET.PERMANENT: calibration_invalid_alert,
    ET.SOFT_DISABLE: soft_disable_alert("Calibration Invalid: Remount Device & Recalibrate"),
    ET.NO_ENTRY: NoEntryAlert("Calibration Invalid: Remount Device & Recalibrate"),
  },

  EventName.calibrationIncomplete: {
    ET.PERMANENT: calibration_incomplete_alert,
    ET.SOFT_DISABLE: soft_disable_alert("Calibration Incomplete"),
    ET.NO_ENTRY: NoEntryAlert("Calibration in Progress"),
  },

  EventName.calibrationRecalibrating: {
    ET.PERMANENT: calibration_incomplete_alert,
    ET.SOFT_DISABLE: soft_disable_alert("Device Remount Detected: Recalibrating"),
    ET.NO_ENTRY: NoEntryAlert("Remount Detected: Recalibrating"),
  },

  EventName.doorOpen: {
    ET.SOFT_DISABLE: user_soft_disable_alert("Door Open"),
    ET.NO_ENTRY: NoEntryAlert("Door Open"),
  },

  EventName.seatbeltNotLatched: {
    ET.SOFT_DISABLE: user_soft_disable_alert("Seatbelt Unlatched"),
    ET.NO_ENTRY: NoEntryAlert("Seatbelt Unlatched"),
  },

  EventName.espDisabled: {
    ET.SOFT_DISABLE: soft_disable_alert("Electronic Stability Control Disabled"),
    ET.NO_ENTRY: NoEntryAlert("Electronic Stability Control Disabled"),
  },

  EventName.lowBattery: {
    ET.SOFT_DISABLE: soft_disable_alert("Low Battery"),
    ET.NO_ENTRY: NoEntryAlert("Low Battery"),
  },

  # Different openpilot services communicate between each other at a certain
  # interval. If communication does not follow the regular schedule this alert
  # is thrown. This can mean a service crashed, did not broadcast a message for
  # ten times the regular interval, or the average interval is more than 10% too high.
  EventName.commIssue: {
    ET.SOFT_DISABLE: soft_disable_alert("Communication Issue Between Processes"),
    ET.NO_ENTRY: comm_issue_alert,
  },
  EventName.commIssueAvgFreq: {
    ET.SOFT_DISABLE: soft_disable_alert("Low Communication Rate Between Processes"),
    ET.NO_ENTRY: NoEntryAlert("Low Communication Rate Between Processes"),
  },

  EventName.selfdrivedLagging: {
    ET.SOFT_DISABLE: soft_disable_alert("System Lagging"),
    ET.NO_ENTRY: NoEntryAlert("Selfdrive Process Lagging: Reboot Your Device"),
  },

  # Thrown when manager detects a service exited unexpectedly while driving
  EventName.processNotRunning: {
    ET.NO_ENTRY: process_not_running_alert,
    ET.SOFT_DISABLE: soft_disable_alert("Process Not Running"),
  },

  EventName.radarFault: {
    ET.SOFT_DISABLE: soft_disable_alert("Radar Error: Restart the Car"),
    ET.NO_ENTRY: NoEntryAlert("Radar Error: Restart the Car"),
  },

  EventName.radarTempUnavailable: {
    ET.SOFT_DISABLE: soft_disable_alert("Radar Temporarily Unavailable"),
    ET.NO_ENTRY: NoEntryAlert("Radar Temporarily Unavailable"),
  },

  # Every frame from the camera should be processed by the model. If modeld
  # is not processing frames fast enough they have to be dropped. This alert is
  # thrown when over 20% of frames are dropped.
  EventName.modeldLagging: {
    ET.SOFT_DISABLE: soft_disable_alert("Driving Model Lagging"),
    ET.NO_ENTRY: NoEntryAlert("Driving Model Lagging"),
    ET.PERMANENT: modeld_lagging_alert,
  },

  # Besides predicting the path, lane lines and lead car data the model also
  # predicts the current velocity and rotation speed of the car. If the model is
  # very uncertain about the current velocity while the car is moving, this
  # usually means the model has trouble understanding the scene. This is used
  # as a heuristic to warn the driver.
  EventName.posenetInvalid: {
    ET.SOFT_DISABLE: soft_disable_alert("Posenet Speed Invalid"),
    ET.NO_ENTRY: posenet_invalid_alert,
  },

  # When the localizer detects an acceleration of more than 40 m/s^2 (~4G) we
  # alert the driver the device might have fallen from the windshield.
  EventName.deviceFalling: {
    ET.SOFT_DISABLE: soft_disable_alert("Device Fell Off Mount"),
    ET.NO_ENTRY: NoEntryAlert("Device Fell Off Mount"),
  },

  EventName.lowMemory: {
    ET.SOFT_DISABLE: soft_disable_alert("Low Memory: Reboot Your Device"),
    ET.PERMANENT: low_memory_alert,
    ET.NO_ENTRY: NoEntryAlert("Low Memory: Reboot Your Device"),
  },

  EventName.accFaulted: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Cruise Fault: Restart the Car"),
    ET.PERMANENT: NormalPermanentAlert("Cruise Fault: Restart the car to engage"),
    ET.NO_ENTRY: NoEntryAlert("Cruise Fault: Restart the Car"),
  },

  EventName.espActive: {
    ET.SOFT_DISABLE: soft_disable_alert("Electronic Stability Control Active"),
    ET.NO_ENTRY: NoEntryAlert("Electronic Stability Control Active"),
  },

  EventName.controlsMismatch: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Controls Mismatch"),
    ET.NO_ENTRY: NoEntryAlert("Controls Mismatch"),
  },

  # Sometimes the USB stack on the device can get into a bad state
  # causing the connection to the panda to be lost
  EventName.usbError: {
    ET.SOFT_DISABLE: soft_disable_alert("USB Error: Reboot Your Device"),
    ET.PERMANENT: NormalPermanentAlert("USB Error: Reboot Your Device"),
    ET.NO_ENTRY: NoEntryAlert("USB Error: Reboot Your Device"),
  },

  # This alert can be thrown for the following reasons:
  # - No CAN data received at all
  # - CAN data is received, but some message are not received at the right frequency
  # If you're not writing a new car port, this is usually cause by faulty wiring
  EventName.canError: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Unknown Vehicle Variant"),
    ET.PERMANENT: Alert(
      "Unknown Vehicle Variant",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1., creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("Unknown Vehicle Variant"),
  },

  EventName.canBusMissing: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("CAN Bus Disconnected"),
    ET.PERMANENT: Alert(
      "CAN Bus Disconnected: Likely Faulty Cable",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1., creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("CAN Bus Disconnected: Check Connections"),
  },

  EventName.steerUnavailable: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("LKAS Fault: Restart the Car"),
    ET.PERMANENT: NormalPermanentAlert("LKAS Fault: Restart the car to engage"),
    ET.NO_ENTRY: NoEntryAlert("LKAS Fault: Restart the Car"),
  },

  EventName.reverseGear: {
    ET.PERMANENT: Alert(
      "Reverse\nGear",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2, creation_delay=0.5),
    ET.USER_DISABLE: ImmediateDisableAlert("Reverse Gear"),
    ET.NO_ENTRY: NoEntryAlert("Reverse Gear"),
  },

  # On cars that use stock ACC the car can decide to cancel ACC for various reasons.
  # When this happens we can no long control the car so the user needs to be warned immediately.
  EventName.cruiseDisabled: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Cruise Is Off"),
  },

  # When the relay in the harness box opens the CAN bus between the LKAS camera
  # and the rest of the car is separated. When messages from the LKAS camera
  # are received on the car side this usually means the relay hasn't opened correctly
  # and this alert is thrown.
  EventName.relayMalfunction: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Harness Relay Malfunction"),
    ET.PERMANENT: NormalPermanentAlert("Harness Relay Malfunction", "Check Hardware"),
    ET.NO_ENTRY: NoEntryAlert("Harness Relay Malfunction"),
  },

  EventName.speedTooLow: {
    ET.IMMEDIATE_DISABLE: Alert(
      "openpilot Canceled",
      "Speed too low",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, AudibleAlert.disengage, 3.),
  },

  # When the car is driving faster than most cars in the training data, the model outputs can be unpredictable.
  EventName.speedTooHigh: {
    ET.WARNING: Alert(
      "Speed Too High",
      "Model uncertain at this speed",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.promptRepeat, 4.),
    ET.NO_ENTRY: NoEntryAlert("Slow down to engage"),
  },

  EventName.vehicleSensorsInvalid: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("Vehicle Sensors Invalid"),
    ET.PERMANENT: NormalPermanentAlert("Vehicle Sensors Calibrating", "Drive to Calibrate"),
    ET.NO_ENTRY: NoEntryAlert("Vehicle Sensors Calibrating"),
  },

  EventName.personalityChanged: {
    ET.WARNING: personality_changed_alert,
  },

  EventName.userBookmark: {
    ET.PERMANENT: NormalPermanentAlert("Bookmark Saved", duration=1.5),
  },

  EventName.audioFeedback: {
    ET.PERMANENT: audio_feedback_alert,
  },
}


MICI_EVENT_TYPE_BY_JSON_NAME = {
  "ENABLE": ET.ENABLE,
  "PRE_ENABLE": ET.PRE_ENABLE,
  "OVERRIDE_LATERAL": ET.OVERRIDE_LATERAL,
  "OVERRIDE_LONGITUDINAL": ET.OVERRIDE_LONGITUDINAL,
  "NO_ENTRY": ET.NO_ENTRY,
  "WARNING": ET.WARNING,
  "USER_DISABLE": ET.USER_DISABLE,
  "SOFT_DISABLE": ET.SOFT_DISABLE,
  "IMMEDIATE_DISABLE": ET.IMMEDIATE_DISABLE,
  "PERMANENT": ET.PERMANENT,
}


class _MiciFormatValues(dict):
  def __missing__(self, key: str) -> str:
    return "{" + key + "}"


class _MiciStaticSubMaster:
  data: dict = {}

  def __getitem__(self, key: str):
    raise KeyError(key)

  def all_checks(self, services) -> bool:
    return True


def _mici_alert_format_values(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster,
                              metric: bool) -> _MiciFormatValues:
  values = _MiciFormatValues()
  values["minSteerSpeed"] = get_display_speed(CP.minSteerSpeed, metric)
  values["minEnableSpeed"] = get_display_speed(CP.minEnableSpeed, metric)
  values["MIN_SPEED_FILTER"] = get_display_speed(MIN_SPEED_FILTER, metric)

  try:
    duration = FEEDBACK_MAX_DURATION - ((sm["audioFeedback"].blockNum + 1) * SAMPLE_BUFFER / SAMPLE_RATE)
    values["seconds"] = str(round(duration))
  except Exception:
    pass

  try:
    values["calPerc"] = f"{sm['liveCalibration'].calPerc:.0f}"
    rpy = sm["liveCalibration"].rpyCalib
    values["yaw"] = f"{math.degrees(rpy[2] if len(rpy) == 3 else math.nan):.1f}"
    values["pitch"] = f"{math.degrees(rpy[1] if len(rpy) == 3 else math.nan):.1f}"
  except Exception:
    pass

  try:
    all_cams = ("roadCameraState", "driverCameraState", "wideRoadCameraState")
    bad_cams = [s.replace("State", "") for s in all_cams if s in sm.data.keys() and not sm.all_checks([s, ])]
    values["bad camera list"] = ", ".join(bad_cams)
  except Exception:
    pass

  try:
    bad_services = [s for s in sm.data.keys() if not sm.all_checks([s, ])]
    values["service names"] = ", ".join(bad_services[:3])
  except Exception:
    pass

  try:
    values["accel"] = str(round(sm["carControl"].actuators.accel / 4. * 100.))
    values["steer"] = str(round(sm["carControl"].actuators.torque * 100.))
  except Exception:
    pass

  try:
    values["memoryUsagePercent"] = str(sm["deviceState"].memoryUsagePercent)
    cpu = max(sm["deviceState"].cpuTempC, default=0.)
    gpu = max(sm["deviceState"].gpuTempC, default=0.)
    values["temperature"] = f"{max((cpu, gpu, sm['deviceState'].memoryTempC)):.0f}"
  except Exception:
    pass

  try:
    values["frameDropPerc"] = f"{sm['modelV2'].frameDropPerc:.1f}"
  except Exception:
    pass

  try:
    values["offset"] = f"{sm['liveParameters'].angleOffsetDeg:.1f}"
  except Exception:
    pass

  return values


def _mici_format_alert_text(text: str, fallback: str, CP: car.CarParams, CS: car.CarState,
                            sm: messaging.SubMaster, metric: bool) -> str:
  try:
    return text.format_map(_mici_alert_format_values(CP, CS, sm, metric))
  except Exception:
    return fallback


def _mici_apply_alert_text_override(alert: Alert, config: dict, CP: car.CarParams, CS: car.CarState,
                                    sm: messaging.SubMaster, metric: bool) -> Alert:
  if "title" in config:
    alert.alert_text_1 = _mici_format_alert_text(config["title"], alert.alert_text_1, CP, CS, sm, metric)
  if "subtitle" in config:
    alert.alert_text_2 = _mici_format_alert_text(config["subtitle"], alert.alert_text_2, CP, CS, sm, metric)
  if alert.alert_size == AlertSize.small and alert.alert_text_2:
    alert.alert_size = AlertSize.mid
  return alert


def _mici_static_alert_args() -> tuple[car.CarParams, car.CarState, _MiciStaticSubMaster, bool]:
  return car.CarParams.new_message(), car.CarState.new_message(), _MiciStaticSubMaster(), True


def _mici_wrap_alert_callback(callback: AlertCallbackType, config: dict) -> AlertCallbackType:
  def wrapped(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool,
              soft_disable_time: int, personality) -> Alert:
    alert = callback(CP, CS, sm, metric, soft_disable_time, personality)
    return _mici_apply_alert_text_override(alert, config, CP, CS, sm, metric)
  return wrapped


MICI_ALERT_TEXT_TRANSLATIONS = {
  "System Initializing": "시스템 시작 중",
  "openpilot Unavailable": "오픈파일럿 사용 불가",
  "Be ready to take over at any time": "언제든지 운전대를 잡을 준비를 하세요",
  "WARNING: This branch is not tested": "경고: 테스트되지 않은 브랜치입니다",
  "Dashcam mode": "블랙박스 모드",
  "Dashcam Mode": "블랙박스 모드",
  "Dashcam mode for unsupported car": "지원되지 않는 차량: 블랙박스 모드",
  "Security Key Not Available": "보안 키를 사용할 수 없습니다",
  "BRAKE!": "브레이크!",
  "Emergency Braking: Risk of Collision": "긴급 제동: 충돌 위험",
  "Stock LKAS: Lane Departure Detected": "순정 LKAS: 차선 이탈 감지됨",
  "DISENGAGE IMMEDIATELY": "즉시 제어하세요",
  "Driver Distracted": "운전자 부주의 감지됨",
  "Touch Steering Wheel: No Face Detected": "스티어링 휠을 잡아주세요: 운전자 감지 안됨",
  "Touch Steering Wheel": "스티어링 휠을 잡아주세요",
  "Driver Unresponsive": "운전자 응답 없음",
  "Cancel Pressed": "취소 버튼 눌림",
  "Press Resume to Exit Brake Hold": "브레이크 홀드를 해제하려면 Resume 버튼을 누르세요",
  "Parking Brake Engaged": "주차 브레이크 체결됨",
  "Pedal Pressed": "페달 눌림",
  "Steering Pressed": "스티어링 조작됨",
  "Enable Adaptive Cruise to Engage": "활성화하려면 어댑티브 크루즈를 켜세요",
  "Press Set to Engage": "활성화하려면 SET 버튼을 누르세요",
  "Adaptive Cruise Disabled": "어댑티브 크루즈 꺼짐",
  "TAKE CONTROL IMMEDIATELY": "즉시 제어하세요",
  "Vehicle Steering Time Limit": "차량 조향 시간 제한",
  "Sensor Data Invalid": "센서 데이터 이상",
  "Possible Hardware Issue": "하드웨어 문제가 있을 수 있습니다",
  "openpilot will disengage": "오픈파일럿이 곧 비활성화됩니다",
  "Gear not D": "기어가 D가 아닙니다",
  "Seatbelt Unlatched": "안전벨트가 체결되지 않았습니다",
  "System Lagging": "시스템 지연",
  "Selfdrive Process Lagging: Reboot Your Device": "selfdrive 지연: 기기를 재부팅하세요",
  "Process Not Running": "외부 프로그램 비정상",
  "Radar Error: Restart the Car": "레이더 오류: 차량을 재시동하세요",
  "Radar Temporarily Unavailable": "레이더 일시 사용 불가",
  "Posenet Speed Invalid": "포즈넷 속도 이상",
  "USB Error: Reboot Your Device": "USB 오류: 기기를 재부팅하세요",
  "Camera Malfunction": "카메라 이상",
  "Calibration Invalid": "캘리브레이션 오류",
  "Steering misalignment detected": "조향 정렬 이상 감지됨",
  "Steer ratio mismatch": "조향비 불일치",
  "Abnormal tire stiffness": "타이어 강성 이상",
  "paramsd Temporary Error": "차량 파라미터 일시 오류",
  "System Overheated": "기기 온도 높음",
  "Low Memory": "메모리 부족",
  "High CPU Usage": "CPU 사용량 높음",
  "Driving Model Lagging": "주행 모델 지연",
  "Joystick Mode": "조이스틱 모드",
  "Longitudinal Maneuver Mode": "종방향 테스트 모드",
  "Lateral Maneuver Mode": "횡방향 테스트 모드",
  "Ensure road ahead is clear": "전방 도로가 안전한지 확인하세요",
  "Speed Too High": "속도가 너무 높습니다",
  "Model uncertain at this speed": "현재 속도에서 모델 예측이 불안정합니다",
  "Slow down to engage": "속도를 낮추면 활성화할 수 있습니다",
  "Vehicle Sensors Invalid": "차량 센서 이상",
  "Vehicle Sensors Calibrating": "차량 센서 캘리브레이션 중",
  "Drive to Calibrate": "캘리브레이션을 위해 주행하세요",
  "Bookmark Saved": "북마크 저장됨",
  "Recording Audio Feedback": "음성 피드백 녹음 중",
  "Harness Relay Malfunction": "하네스 릴레이 이상",
  "Check Hardware": "하드웨어 점검 필요",
  "openpilot Canceled": "오픈파일럿 취소됨",
  "Speed too low": "속도가 너무 낮습니다",
}


def _mici_translate_text(text: str) -> str:
  if text.startswith("Driving Personality: "):
    return "주행 성향: " + text.removeprefix("Driving Personality: ")
  return MICI_ALERT_TEXT_TRANSLATIONS.get(text, text)


def _mici_translate_alert_text(alert: Alert) -> Alert:
  alert.alert_text_1 = _mici_translate_text(alert.alert_text_1)
  alert.alert_text_2 = _mici_translate_text(alert.alert_text_2)
  if alert.alert_size == AlertSize.small and alert.alert_text_2:
    alert.alert_size = AlertSize.mid
  return alert


def _mici_wrap_alert_translation(callback: AlertCallbackType) -> AlertCallbackType:
  def wrapped(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool,
              soft_disable_time: int, personality) -> Alert:
    return _mici_translate_alert_text(callback(CP, CS, sm, metric, soft_disable_time, personality))
  return wrapped


def _apply_mici_alert_text_translations() -> None:
  for event_alerts in EVENTS.values():
    for event_type, alert in list(event_alerts.items()):
      if isinstance(alert, Alert):
        _mici_translate_alert_text(alert)
      else:
        event_alerts[event_type] = _mici_wrap_alert_translation(alert)


def _apply_mici_event_alert_overrides() -> None:
  if not MICI_EVENT_ALERT_OVERRIDES_PATH.is_file():
    return

  with open(MICI_EVENT_ALERT_OVERRIDES_PATH, encoding="utf-8") as f:
    configs = json.load(f).get("events", {})

  static_CP, static_CS, static_sm, static_metric = _mici_static_alert_args()

  for config in configs.values():
    if config.get("source") != "EVENTS":
      continue

    event_name = config.get("eventName")
    event_type = MICI_EVENT_TYPE_BY_JSON_NAME.get(config.get("eventType", ""))
    if event_name is None or event_type is None:
      continue

    event_id = EventName.schema.enumerants.get(event_name)
    if event_id is None or event_id not in EVENTS or event_type not in EVENTS[event_id]:
      continue

    alert = EVENTS[event_id][event_type]
    if isinstance(alert, Alert):
      _mici_apply_alert_text_override(alert, config, static_CP, static_CS, static_sm, static_metric)
    else:
      EVENTS[event_id][event_type] = _mici_wrap_alert_callback(alert, config)


if HARDWARE.get_device_type() == 'mici':
  EVENTS.update({
    EventName.driverDistracted1: {
      ET.PERMANENT: Alert(
        "운전에 집중하세요",
        "",
        AlertStatus.normal, AlertSize.small,
        Priority.LOW, VisualAlert.none, AudibleAlert.none, 2),
    },
    EventName.driverDistracted2: {
      ET.PERMANENT: Alert(
        "운전에 집중하세요",
        "운전자 부주의 감지됨",
        AlertStatus.userPrompt, AlertSize.mid,
        Priority.MID, VisualAlert.steerRequired, AudibleAlert.promptDistracted, 1),
    },
    EventName.resumeRequired: {
      ET.WARNING: Alert(
        "Resume 버튼을 누르세요",
        "",
        AlertStatus.userPrompt, AlertSize.small,
        Priority.LOW, VisualAlert.none, AudibleAlert.none, .2),
    },
    EventName.preLaneChangeLeft: {
      ET.WARNING: Alert(
        "왼쪽 조향",
        "차선 변경 확인",
        AlertStatus.normal, AlertSize.mid,
        Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
    },
    EventName.preLaneChangeRight: {
      ET.WARNING: Alert(
        "오른쪽 조향",
        "차선 변경 확인",
        AlertStatus.normal, AlertSize.mid,
        Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
    },
    EventName.laneChangeBlocked: {
      ET.WARNING: Alert(
        "사각지대 차량",
        "",
        AlertStatus.userPrompt, AlertSize.small,
        Priority.LOW, VisualAlert.none, AudibleAlert.prompt, .1),
    },
    EventName.laneChangeUnavailable: {
      ET.WARNING: Alert(
        "차선 변경 일시정지",
        "차선 변경 불가 구역 감지됨",
        AlertStatus.userPrompt, AlertSize.mid,
        Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
    },
    EventName.steerSaturated: {
      ET.WARNING: Alert(
        "직접 운전하세요",
        "조향 한계 초과",
        AlertStatus.userPrompt, AlertSize.mid,
        Priority.LOW, VisualAlert.steerRequired, AudibleAlert.promptRepeat, 2.),
    },
    EventName.calibrationIncomplete: {
      ET.PERMANENT: calibration_incomplete_alert,
      ET.SOFT_DISABLE: soft_disable_alert("캘리브레이션이 완료되지 않았습니다"),
      ET.NO_ENTRY: NoEntryAlert("캘리브레이션 중"),
    },
    EventName.reverseGear: {
      ET.PERMANENT: Alert(
        "후진",
        "",
        AlertStatus.normal, AlertSize.full,
        Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2, creation_delay=0.5),
      ET.USER_DISABLE: ImmediateDisableAlert("후진"),
      ET.NO_ENTRY: NoEntryAlert("후진"),
    },
  })
  _apply_mici_alert_text_translations()
  _apply_mici_event_alert_overrides()


if __name__ == '__main__':
  # print all alerts by type and priority
  from cereal.services import SERVICE_LIST
  from collections import defaultdict

  event_names = {v: k for k, v in EventName.schema.enumerants.items()}
  alerts_by_type: dict[str, dict[Priority, list[str]]] = defaultdict(lambda: defaultdict(list))

  CP = car.CarParams.new_message()
  CS = car.CarState.new_message()
  sm = messaging.SubMaster(list(SERVICE_LIST.keys()))

  for i, alerts in EVENTS.items():
    for et, alert in alerts.items():
      if not isinstance(alert, Alert):
        alert = alert(CP, CS, sm, False, 1, log.LongitudinalPersonality.standard)
      alerts_by_type[et][alert.priority].append(event_names[i])

  all_alerts: dict[str, list[tuple[Priority, list[str]]]] = {}
  for et, priority_alerts in alerts_by_type.items():
    all_alerts[et] = sorted(priority_alerts.items(), key=lambda x: x[0], reverse=True)

  for status, evs in sorted(all_alerts.items(), key=lambda x: x[0]):
    print(f"**** {status} ****")
    for p, alert_list in evs:
      print(f"  {repr(p)}:")
      print("   ", ', '.join(alert_list), "\n")
