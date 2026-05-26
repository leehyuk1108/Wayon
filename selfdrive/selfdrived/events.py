#!/usr/bin/env python3
import bisect
import json
import math
import os
from enum import IntEnum
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

from cereal import log, car, custom
import cereal.messaging as messaging
from openpilot.common.constants import CV
from openpilot.common.git import get_short_branch
from openpilot.common.params import Params
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.controls.lib.desire_helper import LaneChangeDirection
from openpilot.selfdrive.locationd.calibrationd import MIN_SPEED_FILTER
from openpilot.system.micd import SAMPLE_RATE, SAMPLE_BUFFER
from openpilot.selfdrive.ui.feedback.feedbackd import FEEDBACK_MAX_DURATION
from openpilot.system.hardware import HARDWARE

AlertSize = log.SelfdriveState.AlertSize
AlertStatus = log.SelfdriveState.AlertStatus
VisualAlert = car.CarControl.HUDControl.VisualAlert
AudibleAlert = car.CarControl.HUDControl.AudibleAlert
EventName = log.OnroadEvent.EventName

StarPilotAlertStatus = custom.StarPilotSelfdriveState.AlertStatus
StarPilotAudibleAlert = custom.StarPilotCarControl.HUDControl.AudibleAlert
StarPilotEventName = custom.StarPilotOnroadEvent.EventName


# Alert priorities
class Priority(IntEnum):
  LOWEST = 0
  LOWER = 1
  LOW = 2
  MID = 3
  HIGH = 4
  HIGHEST = 5


# Event types
class ET:
  ENABLE = 'enable'
  PRE_ENABLE = 'preEnable'
  OVERRIDE_LATERAL = 'overrideLateral'
  OVERRIDE_LONGITUDINAL = 'overrideLongitudinal'
  NO_ENTRY = 'noEntry'
  WARNING = 'warning'
  USER_DISABLE = 'userDisable'
  SOFT_DISABLE = 'softDisable'
  IMMEDIATE_DISABLE = 'immediateDisable'
  PERMANENT = 'permanent'


# get event name from enum
EVENT_NAME = {v: k for k, v in EventName.schema.enumerants.items()}

STARPILOT_EVENT_NAME = {v: k for k, v in StarPilotEventName.schema.enumerants.items()}

MICI_EVENT_ALERT_OVERRIDES_PATH = Path(__file__).resolve().parents[1] / "ui/mici/mici_event_alert_overrides.json"


class Events:
  def __init__(self, starpilot=False):
    self.events: list[int] = []
    self.static_events: list[int] = []
    self.event_counters = dict.fromkeys((STARPILOT_EVENTS if starpilot else EVENTS).keys(), 0)

    self.starpilot = starpilot

  @property
  def names(self) -> list[int]:
    return self.events

  def __len__(self) -> int:
    return len(self.events)

  def add(self, event_name: int, static: bool=False) -> None:
    if static:
      bisect.insort(self.static_events, event_name)
    bisect.insort(self.events, event_name)

  def clear(self) -> None:
    self.event_counters = {k: (v + 1 if k in self.events else 0) for k, v in self.event_counters.items()}
    self.events = self.static_events.copy()

  def contains(self, event_type: str) -> bool:
    return any(event_type in (STARPILOT_EVENTS if self.starpilot else EVENTS).get(e, {}) for e in self.events)

  def create_alerts(self, event_types: list[str], callback_args=None):
    if callback_args is None:
      callback_args = []

    ret = []
    for e in self.events:
      types = (STARPILOT_EVENTS if self.starpilot else EVENTS)[e].keys()
      for et in event_types:
        if et in types:
          alert = (STARPILOT_EVENTS if self.starpilot else EVENTS)[e][et]
          if not isinstance(alert, Alert):
            alert = alert(*callback_args)

          if DT_CTRL * (self.event_counters[e] + 1) >= alert.creation_delay:
            alert.alert_type = f"{(STARPILOT_EVENT_NAME if self.starpilot else EVENT_NAME)[e]}/{et}"
            alert.event_type = et
            ret.append(alert)
    return ret

  def add_from_msg(self, events):
    for e in events:
      bisect.insort(self.events, e.name.raw)

  def to_msg(self):
    ret = []
    for event_name in self.events:
      event = (custom.StarPilotOnroadEvent if self.starpilot else log.OnroadEvent).new_message()
      event.name = event_name
      for event_type in (STARPILOT_EVENTS if self.starpilot else EVENTS).get(event_name, {}):
        setattr(event, event_type, True)
      ret.append(event)
    return ret


class Alert:
  def __init__(self,
               alert_text_1: str,
               alert_text_2: str,
               alert_status: log.SelfdriveState.AlertStatus,
               alert_size: log.SelfdriveState.AlertSize,
               priority: Priority,
               visual_alert: car.CarControl.HUDControl.VisualAlert,
               audible_alert: car.CarControl.HUDControl.AudibleAlert,
               duration: float,
               creation_delay: float = 0.):

    self.alert_text_1 = alert_text_1
    self.alert_text_2 = alert_text_2
    self.alert_status = alert_status
    self.alert_size = alert_size
    self.priority = priority
    self.visual_alert = visual_alert
    self.audible_alert = audible_alert

    self.duration = int(duration / DT_CTRL)

    self.creation_delay = creation_delay

    self.alert_type = ""
    self.event_type: str | None = None

  def __str__(self) -> str:
    return f"{self.alert_text_1}/{self.alert_text_2} {self.priority} {self.visual_alert} {self.audible_alert}"

  def __gt__(self, alert2) -> bool:
    if not isinstance(alert2, Alert):
      return False
    return self.priority > alert2.priority

EmptyAlert = Alert("" , "", AlertStatus.normal, AlertSize.none, Priority.LOWEST,
                   VisualAlert.none, AudibleAlert.none, 0)

class NoEntryAlert(Alert):
  def __init__(self, alert_text_2: str,
               alert_text_1: str = "오픈파일럿 사용 불가",
               visual_alert: car.CarControl.HUDControl.VisualAlert=VisualAlert.none):
    if HARDWARE.get_device_type() == 'mici':
      alert_text_1, alert_text_2 = alert_text_2, alert_text_1
    super().__init__(alert_text_1, alert_text_2, AlertStatus.normal,
                     AlertSize.mid, Priority.LOW, visual_alert,
                     AudibleAlert.refuse, 3.)


class SoftDisableAlert(Alert):
  def __init__(self, alert_text_2: str):
    super().__init__("직접 운전을 진행해주세요", alert_text_2,
                     AlertStatus.userPrompt, AlertSize.full,
                     Priority.MID, VisualAlert.steerRequired,
                     AudibleAlert.warningSoft, 2.),


# less harsh version of SoftDisable, where the condition is user-triggered
class UserSoftDisableAlert(SoftDisableAlert):
  def __init__(self, alert_text_2: str):
    super().__init__(alert_text_2),
    self.alert_text_1 = "오픈파일럿이 곧 비활성화됩니다"


class ImmediateDisableAlert(Alert):
  def __init__(self, alert_text_2: str):
    super().__init__("직접 운전을 진행해주세요", alert_text_2,
                     AlertStatus.critical, AlertSize.full,
                     Priority.HIGHEST, VisualAlert.steerRequired,
                     AudibleAlert.warningImmediate, 4.),


class EngagementAlert(Alert):
  def __init__(self, audible_alert: car.CarControl.HUDControl.AudibleAlert):
    super().__init__("", "",
                     AlertStatus.normal, AlertSize.none,
                     Priority.MID, VisualAlert.none,
                     audible_alert, .2),


class NormalPermanentAlert(Alert):
  def __init__(self, alert_text_1: str, alert_text_2: str = "", duration: float = 0.2, priority: Priority = Priority.LOWER, creation_delay: float = 0.):
    super().__init__(alert_text_1, alert_text_2,
                     AlertStatus.normal, AlertSize.mid if len(alert_text_2) else AlertSize.small,
                     priority, VisualAlert.none, AudibleAlert.none, duration, creation_delay=creation_delay),


class StartupAlert(Alert):
  def __init__(self, alert_text_1: str, alert_text_2: str = "항시 전방을 주시하고 교통 상황에 유의하세요", alert_status=AlertStatus.normal):
    alert_size = AlertSize.mid
    if HARDWARE.get_device_type() == 'mici':
      if alert_text_2 == "항시 전방을 주시하고 교통 상황에 유의하세요":
        alert_text_2 = ""
      alert_size = AlertSize.small
    super().__init__(alert_text_1, alert_text_2,
                     alert_status, alert_size,
                     Priority.LOWER, VisualAlert.none, AudibleAlert.none, 5.),



# ********** helper functions **********
def get_display_speed(speed_ms: float, metric: bool) -> str:
  speed = int(round(speed_ms * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH)))
  unit = 'km/h' if metric else 'mph'
  return f"{speed} {unit}"


# ********** alert callback functions **********

AlertCallbackType = Callable[[car.CarParams, car.CarState, messaging.SubMaster, bool, int, log.ControlsState], Alert]


def soft_disable_alert(alert_text_2: str) -> AlertCallbackType:
  def func(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
    if soft_disable_time < int(0.5 / DT_CTRL):
      return ImmediateDisableAlert(alert_text_2)
    return SoftDisableAlert(alert_text_2)
  return func

def user_soft_disable_alert(alert_text_2: str) -> AlertCallbackType:
  def func(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
    if soft_disable_time < int(0.5 / DT_CTRL):
      return ImmediateDisableAlert(alert_text_2)
    return UserSoftDisableAlert(alert_text_2)
  return func

def startup_master_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  branch = get_short_branch()  # Ensure get_short_branch is cached to avoid lags on startup
  if "REPLAY" in os.environ:
    branch = "replay"

  return StartupAlert("경고: 테스트되지 않은 브랜치입니다", branch, alert_status=AlertStatus.userPrompt)

def below_engage_speed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  return NoEntryAlert(f"활성화하려면 {get_display_speed(CP.minEnableSpeed, metric)} 이상으로 주행하세요")


def below_steer_speed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  return Alert(
    "조향 보조 꺼짐",
    f"최소 속도 {get_display_speed(CP.minSteerSpeed, metric)}",
    AlertStatus.normal, AlertSize.small,
    Priority.LOW, VisualAlert.none, AudibleAlert.none, 0.4)


def speed_limit_changed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  return Alert(
    "제한 속도가 변경되었습니다",
    "",
    StarPilotAlertStatus.starpilot, AlertSize.small,
    Priority.LOW, VisualAlert.none, AudibleAlert.prompt, 3.0)


def calibration_incomplete_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  first_word = '재보정 진행중' if sm['liveCalibration'].calStatus == log.LiveCalibrationData.Status.recalibrating else '캘리브레이션이 진행중입니다'
  return Alert(
    f"{first_word}: {sm['liveCalibration'].calPerc:.0f}%",
    f"{get_display_speed(MIN_SPEED_FILTER, metric)} 이상으로 주행하세요",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2)


def audio_feedback_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  duration = FEEDBACK_MAX_DURATION - ((sm['audioFeedback'].blockNum + 1) * SAMPLE_BUFFER / SAMPLE_RATE)
  return NormalPermanentAlert(
    "음성 피드백 녹음 중",
    f"{round(duration)}초 남음. 다시 누르면 바로 저장됩니다.",
    priority=Priority.LOW)


# *** debug alerts ***

def out_of_space_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  full_perc = round(100. - sm['deviceState'].freeSpacePercent)
  return NormalPermanentAlert("용량 부족", f"{full_perc}%")


def posenet_invalid_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  mdl = sm['modelV2'].velocity.x[0] if len(sm['modelV2'].velocity.x) else math.nan
  err = CS.vEgo - mdl
  msg = f"속도 오류: {err:.1f} m/s"
  return NoEntryAlert(msg, alert_text_1="포즈넷 속도 이상")


def process_not_running_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  not_running = [p.name for p in sm['managerState'].processes if not p.running and p.shouldBeRunning]
  msg = ', '.join(not_running)
  return NoEntryAlert(msg, alert_text_1="외부 프로그램 비정상")


def comm_issue_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  bs = [s for s in sm.data.keys() if not sm.all_checks([s, ])]
  msg = ', '.join(bs[:4])  # can't fit too many on one line
  return NoEntryAlert(msg, alert_text_1="차량과의 통신 오류")


def camera_malfunction_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  all_cams = ('roadCameraState', 'driverCameraState', 'wideRoadCameraState')
  bad_cams = [s.replace('State', '') for s in all_cams if s in sm.data.keys() and not sm.all_checks([s, ])]
  return NormalPermanentAlert("카메라 이상", ', '.join(bad_cams))


def calibration_invalid_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  rpy = sm['liveCalibration'].rpyCalib
  yaw = math.degrees(rpy[2] if len(rpy) == 3 else math.nan)
  pitch = math.degrees(rpy[1] if len(rpy) == 3 else math.nan)
  angles = f"기기의 각도를 조정해주세요 (Pitch: {pitch:.1f}°, Yaw: {yaw:.1f}°)"
  return NormalPermanentAlert("캘리브레이션이 필요합니다", angles)


def paramsd_invalid_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  if not sm['liveParameters'].angleOffsetValid:
    angle_offset_deg = sm['liveParameters'].angleOffsetDeg
    title = "조향 정렬 이상 감지됨"
    text = f"각도 오프셋이 너무 큽니다 (Offset: {angle_offset_deg:.1f}°)"
  elif not sm['liveParameters'].steerRatioValid:
    steer_ratio = sm['liveParameters'].steerRatio
    title = "조향비 불일치"
    text = f"조향 장치 설정이 맞지 않을 수 있습니다 (Ratio: {steer_ratio:.1f})"
  elif not sm['liveParameters'].stiffnessFactorValid:
    stiffness_factor = sm['liveParameters'].stiffnessFactor
    title = "타이어 강성 이상"
    text = f"타이어, 공기압, 얼라인먼트를 확인하세요 (Factor: {stiffness_factor:.1f})"
  else:
    return NoEntryAlert("차량 파라미터 일시 오류")

  return NoEntryAlert(alert_text_1=title, alert_text_2=text)

def overheat_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  cpu = max(sm['deviceState'].cpuTempC, default=0.)
  gpu = max(sm['deviceState'].gpuTempC, default=0.)
  temp = max((cpu, gpu, sm['deviceState'].memoryTempC))
  return NormalPermanentAlert("기기의 온도가 높습니다", f"{temp:.0f} °C")


def low_memory_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  return NormalPermanentAlert("메모리 부족", f"{sm['deviceState'].memoryUsagePercent}% 사용됨")


def high_cpu_usage_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  x = max(sm['deviceState'].cpuUsagePercent, default=0.)
  return NormalPermanentAlert("CPU 사용량이 높습니다", f"{x}% 사용됨")


def modeld_lagging_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  return NormalPermanentAlert("오픈파일럿이 불안정합니다", f"{sm['modelV2'].frameDropPerc:.1f}% 프레임 하락")


def wrong_car_mode_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  if starpilot_toggles.has_cc_long:
    text = "활성화하려면 크루즈 컨트롤을 켜주세요"
  elif CP.brand == "honda":
    text = "활성화하려면 메인 스위치를 켜주세요"
  else:
    text = "활성화하려면 어댑티브 크루즈를 켜주세요"
  return NoEntryAlert(text)


def joystick_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  gb = sm['carControl'].actuators.accel / 4.
  steer = sm['carControl'].actuators.torque
  vals = f"가속: {round(gb * 100.)}%, 조향: {round(steer * 100.)}%"
  return NormalPermanentAlert("원격 제어 중", vals)


def longitudinal_maneuver_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  ad = sm['alertDebug']
  audible_alert = AudibleAlert.prompt if 'Active' in ad.alertText1 else AudibleAlert.none
  alert_status = AlertStatus.userPrompt if 'Active' in ad.alertText1 else AlertStatus.normal
  alert_size = AlertSize.mid if ad.alertText2 else AlertSize.small
  return Alert(ad.alertText1, ad.alertText2,
               alert_status, alert_size,
               Priority.LOW, VisualAlert.none, audible_alert, 0.2)


def personality_changed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  personality = str(personality).title()
  return NormalPermanentAlert(f"주행 성향: {personality}", duration=1.5)


def invalid_lkas_setting_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  text = "활성화하려면 순정 LKAS 설정을 전환하세요"
  if CP.brand == "tesla" and CP.carFingerprint == "TESLA_MODEL_S_PREAP":
    return NormalPermanentAlert("EPAS 펌웨어 필요", "조향을 사용하려면 Pre-AP EPAS 펌웨어를 플래시하세요")
  if CP.brand == "tesla":
    text = "활성화하려면 트래픽 어웨어 크루즈 컨트롤로 전환하세요"
  elif CP.brand == "mazda":
    text = "활성화하려면 차량의 LKAS를 켜주세요"
  elif CP.brand == "nissan":
    text = "활성화하려면 차량의 순정 LKAS를 꺼주세요"
  return NormalPermanentAlert("LKAS 설정 오류", text)


def custom_startup_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  return StartupAlert(starpilot_toggles.startup_alert_top, starpilot_toggles.startup_alert_bottom, alert_status=StarPilotAlertStatus.starpilot)


def forcing_stop_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  if CS.standstill:
    return Alert(
      "정차 상태를 유지 중입니다",
      "해제하려면 가속 페달 또는 Resume 버튼을 누르세요",
      StarPilotAlertStatus.starpilot, AlertSize.mid,
      Priority.MID, VisualAlert.none, AudibleAlert.prompt, 1.)

  model_length = sm["starpilotPlan"].forcingStopLength
  model_length_msg = f"{model_length:.1f}미터" if metric else f"{model_length * CV.METER_TO_FOOT:.1f}피트"

  return Alert(
    f"{model_length_msg} 앞에서 차량을 정지시킵니다",
    "해제하려면 가속 페달 또는 Resume 버튼을 누르세요",
    StarPilotAlertStatus.starpilot, AlertSize.mid,
    Priority.MID, VisualAlert.none, AudibleAlert.prompt, 1.)


def holiday_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  holiday_messages = {
    "new_years": "새해 복 많이 받으세요! 🎉",
    "valentines": "해피 밸런타인데이! ❤️",
    "st_patricks": "해피 세인트 패트릭스 데이! 🍀",
    "world_frog_day": "세계 개구리의 날입니다! 🐸",
    "april_fools": "만우절입니다! 🤡",
    "easter_week": "해피 이스터! 🐰",
    "may_the_fourth": "포스가 함께하길! 🚀",
    "cinco_de_mayo": "신코 데 마요입니다! 🌮",
    "stitch_day": "스티치 데이입니다! 💙",
    "fourth_of_july": "미국 독립기념일입니다! 🎆",
    "halloween_week": "해피 핼러윈! 🎃",
    "thanksgiving_week": "해피 추수감사절! 🦃",
    "christmas_week": "메리 크리스마스! 🎄",
  }

  return Alert(
    holiday_messages.get(starpilot_toggles.current_holiday_theme, ""),
    "",
    AlertStatus.normal, AlertSize.small,
    Priority.LOWEST, VisualAlert.none, StarPilotAudibleAlert.startup, 5.)


def nnff_loaded_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  model_name = Params().get("NNFFModelName")
  if model_name is None:
    return Alert(
      "NNFF 토크 컨트롤러를 사용할 수 없습니다",
      "차량 지원을 위해 Twilsonco에게 로그를 공유해주세요",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, 10.0)
  else:
    return Alert(
      "NNFF 토크 컨트롤러 로드됨:",
      model_name,
      StarPilotAlertStatus.starpilot, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.engage, 5.0)


def no_lane_available_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
  lane_width = sm["starpilotPlan"].laneWidthLeft if sm["modelV2"].meta.laneChangeDirection == LaneChangeDirection.left else sm["starpilotPlan"].laneWidthRight
  lane_width_msg = f"{lane_width:.1f}미터" if metric else f"{lane_width * CV.METER_TO_FOOT:.1f}피트"

  return Alert(
    "사용 가능한 차선 없음",
    f"감지된 차선 폭이 {lane_width_msg}뿐입니다",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2)



EVENTS: dict[int, dict[str, Alert | AlertCallbackType]] = {
  # ********** events with no alerts **********

  EventName.stockFcw: {},
  EventName.actuatorsApiUnavailable: {},

  # ********** events only containing alerts displayed in all states **********

  EventName.joystickDebug: {
    ET.WARNING: joystick_alert,
    ET.PERMANENT: NormalPermanentAlert("원격 제어 중"),
  },

  EventName.longitudinalManeuver: {
    ET.WARNING: longitudinal_maneuver_alert,
    ET.PERMANENT: NormalPermanentAlert("가감속 테스트 모드",
                                       "전방 도로가 비어있는지 확인하세요"),
  },

  EventName.lateralManeuver: {
    ET.WARNING: longitudinal_maneuver_alert,
    ET.PERMANENT: NormalPermanentAlert("조향 테스트 모드",
                                       "전방 도로가 비어있는지 확인하세요"),
  },

  EventName.selfdriveInitializing: {
    ET.NO_ENTRY: NoEntryAlert("시스템 시작중"),
  },

  EventName.startup: {
    ET.PERMANENT: StartupAlert("언제든지 운전대를 잡을 준비를 하세요")
  },

  EventName.startupMaster: {
    ET.PERMANENT: startup_master_alert,
  },

  EventName.startupNoControl: {
    ET.PERMANENT: StartupAlert("블랙박스 모드"),
    ET.NO_ENTRY: NoEntryAlert("블랙박스 모드"),
  },

  EventName.startupNoCar: {
    ET.PERMANENT: StartupAlert("지원되지 않는 차량: 블랙박스 모드"),
  },

  EventName.startupNoSecOcKey: {
    ET.PERMANENT: NormalPermanentAlert("블랙박스 모드",
                                       "보안 키를 사용할 수 없습니다",
                                       priority=Priority.HIGH),
  },

  EventName.dashcamMode: {
    ET.PERMANENT: NormalPermanentAlert("블랙박스 모드",
                                       priority=Priority.LOWEST),
  },

  EventName.invalidLkasSetting: {
    ET.PERMANENT: invalid_lkas_setting_alert,
    ET.NO_ENTRY: NoEntryAlert("LKAS 설정 오류"),
  },

  EventName.cruiseMismatch: {
    #ET.PERMANENT: ImmediateDisableAlert("openpilot failed to cancel cruise"),
  },

  # openpilot doesn't recognize the car. This switches openpilot into a
  # read-only mode. This can be solved by adding your fingerprint.
  # See https://github.com/commaai/openpilot/wiki/Fingerprinting for more information
  EventName.carUnrecognized: {
    ET.PERMANENT: NormalPermanentAlert("블랙박스 모드",
                                       "인식되지 않은 차량입니다",
                                       priority=Priority.LOWEST),
  },

  EventName.aeb: {
    ET.PERMANENT: Alert(
      "브레이크!",
      "긴급 제동: 충돌 위험",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 2.),
    ET.NO_ENTRY: NoEntryAlert("AEB: 충돌 위험"),
  },

  EventName.stockAeb: {
    ET.PERMANENT: Alert(
      "AEB 작동",
      "충돌의 위험이 있어 차량의 순정 AEB가 작동했습니다",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 2.),
    ET.NO_ENTRY: NoEntryAlert("충돌의 위험이 있어 차량의 순정 AEB가 작동했습니다"),
  },

  EventName.fcw: {
    ET.PERMANENT: Alert(
      "전방 추돌 주의",
      "전방 차량과 추돌 위험이 있습니다",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.warningSoft, 2.),
  },

  EventName.ldw: {
    ET.PERMANENT: Alert(
      "차선 이탈 감지됨",
      "운전에 주의하세요",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.ldw, AudibleAlert.prompt, 3.),
  },

  # ********** events only containing alerts that display while engaged **********

  EventName.steerTempUnavailableSilent: {
    ET.WARNING: Alert(
      "조향 제어 불안정",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.prompt, 1.8),
  },

  EventName.preDriverDistracted: {
    ET.PERMANENT: Alert(
      "운전에 집중하세요",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.promptDriverDistracted: {
    ET.PERMANENT: Alert(
      "운전에 집중하세요",
      "운전자 부주의 감지됨",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.promptDistracted, .1),
  },

  EventName.driverDistracted: {
    ET.PERMANENT: Alert(
      "오픈파일럿 비활성화",
      "운전자 부주의 감지됨",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.warningImmediate, .1),
  },

  EventName.preDriverUnresponsive: {
    ET.PERMANENT: Alert(
      "스티어링 휠을 잡아주세요 (운전자 감지 안됨)",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, .1),
  },

  EventName.promptDriverUnresponsive: {
    ET.PERMANENT: Alert(
      "스티어링 휠을 잡아주세요",
      "운전자 응답 없음",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.promptDistracted, .1),
  },

  EventName.driverUnresponsive: {
    ET.PERMANENT: Alert(
      "오픈파일럿 비활성화",
      "운전자 응답 없음",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.warningImmediate, .1),
  },

  EventName.manualRestart: {
    ET.WARNING: Alert(
      "수동 운전 요구됨",
      "직접 운전을 진행하세요",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .2),
  },

  EventName.resumeRequired: {
    ET.WARNING: Alert(
      "오토 홀드",
      "해제하려면 악셀을 밟거나 RES버튼을 누르세요",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .2),
  },

  EventName.belowSteerSpeed: {
    ET.WARNING: below_steer_speed_alert,
  },

  EventName.preLaneChangeLeft: {
    ET.WARNING: Alert(
      "좌측 차선 변경 승인 대기중",
      "핸들을 돌려 차선 변경을 승인해주세요",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.preLaneChangeRight: {
    ET.WARNING: Alert(
      "우측 차선 변경 승인 대기중",
      "핸들을 돌려 차선 변경을 승인해주세요",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.laneChangeBlocked: {
    ET.WARNING: Alert(
      "차선 변경 대기중",
      "사각지대에 차량이 감지되었습니다",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, .1),
  },

  EventName.laneChange: {
    ET.WARNING: Alert(
      "차선 변경 중",
      "전후방 및 측면에 유의하세요",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.steerSaturated: {
    ET.WARNING: Alert(
      "핸들을 조작해주세요",
      "조향각 한계에 도달했습니다",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.promptRepeat, 2.),
  },

  # Thrown when the fan is driven at >50% but is not rotating
  EventName.fanMalfunction: {
    ET.PERMANENT: NormalPermanentAlert("쿨링팬 이상 감지됨", "하드웨어를 점검해주세요"),
  },

  # Camera is not outputting frames
  EventName.cameraMalfunction: {
    ET.PERMANENT: camera_malfunction_alert,
    ET.SOFT_DISABLE: soft_disable_alert("카메라 이상 감지됨"),
    ET.NO_ENTRY: NoEntryAlert("기기를 재부팅해주세요"),
  },
  # Camera framerate too low
  EventName.cameraFrameRate: {
    ET.PERMANENT: NormalPermanentAlert("카메라의 프레임이 낮습니다", "기기를 재부팅하세요"),
    ET.SOFT_DISABLE: soft_disable_alert("카메라의 프레임이 낮습니다"),
    ET.NO_ENTRY: NoEntryAlert("카메라의 프레임이 낮습니다: 기기를 재부팅하세요"),
  },

  # Unused

  EventName.locationdTemporaryError: {
    ET.NO_ENTRY: NoEntryAlert("위치 서비스 일시 오류"),
    ET.SOFT_DISABLE: soft_disable_alert("위치 서비스 일시 오류"),
  },

  EventName.locationdPermanentError: {
    ET.NO_ENTRY: NoEntryAlert("위치 서비스 영구 오류"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("위치 서비스 영구 오류"),
    ET.PERMANENT: NormalPermanentAlert("위치 서비스 영구 오류"),
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
    ET.SOFT_DISABLE: soft_disable_alert("차량 파라미터 일시 오류"),
  },

  EventName.paramsdPermanentError: {
    ET.NO_ENTRY: NoEntryAlert("차량 파라미터 영구 오류"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("차량 파라미터 영구 오류"),
    ET.PERMANENT: NormalPermanentAlert("차량 파라미터 영구 오류"),
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
    ET.NO_ENTRY: NoEntryAlert("취소 버튼이 눌렸습니다"),
  },

  EventName.brakeHold: {
    ET.WARNING: Alert(
      "브레이크 홀드",
      "해제하려면 Resume 버튼을 누르세요",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .2),
  },

  EventName.parkBrake: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("주차 브레이크가 체결되었습니다"),
  },

  EventName.pedalPressed: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("페달이 눌렸습니다",
                              visual_alert=VisualAlert.brakePressed),
  },

  EventName.steerDisengage: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("핸들이 조작되었습니다"),
  },

  EventName.preEnableStandstill: {
    ET.PRE_ENABLE: Alert(
      "활성화하려면 브레이크를 놓으세요",
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
    ET.NO_ENTRY: NoEntryAlert("활성화하려면 SET 버튼을 누르세요"),
  },

  EventName.wrongCruiseMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("어댑티브 크루즈가 꺼져 있습니다"),
  },

  EventName.steerTempUnavailable: {
    ET.SOFT_DISABLE: soft_disable_alert("조향 제어를 일시적으로 사용할 수 없습니다"),
    ET.NO_ENTRY: NoEntryAlert("조향 제어를 일시적으로 사용할 수 없습니다"),
  },

  EventName.steerTimeLimit: {
    ET.SOFT_DISABLE: soft_disable_alert("차량 조향 시간 제한"),
    ET.NO_ENTRY: NoEntryAlert("차량 조향 시간 제한"),
  },

  EventName.outOfSpace: {
    ET.PERMANENT: out_of_space_alert,
    ET.NO_ENTRY: NoEntryAlert("저장 공간 부족"),
  },

  EventName.belowEngageSpeed: {
    ET.NO_ENTRY: below_engage_speed_alert,
  },

  EventName.sensorDataInvalid: {
    ET.PERMANENT: Alert(
      "센서 데이터 이상",
      "하드웨어 문제가 있을 수 있습니다",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, .2, creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("센서 데이터 이상"),
    ET.SOFT_DISABLE: soft_disable_alert("센서 데이터 이상"),
  },

  EventName.noGps: {
  },

  EventName.tooDistracted: {
    ET.NO_ENTRY: NoEntryAlert("운전자 부주의 수준이 너무 높습니다"),
  },

  EventName.excessiveActuation: {
    ET.SOFT_DISABLE: soft_disable_alert("제어 입력이 과도합니다"),
    ET.NO_ENTRY: NoEntryAlert("제어 입력이 과도합니다"),
  },

  EventName.overheat: {
    ET.PERMANENT: overheat_alert,
    ET.SOFT_DISABLE: soft_disable_alert("기기의 온도가 높습니다"),
    ET.NO_ENTRY: NoEntryAlert("기기의 온도가 높습니다"),
  },

  EventName.wrongGear: {
    ET.SOFT_DISABLE: user_soft_disable_alert("기어가 D가 아닙니다"),
    ET.NO_ENTRY: NoEntryAlert("기어가 D가 아닙니다"),
  },

  # This alert is thrown when the calibration angles are outside of the acceptable range.
  # For example if the device is pointed too much to the left or the right.
  # Usually this can only be solved by removing the mount from the windshield completely,
  # and attaching while making sure the device is pointed straight forward and is level.
  # See https://comma.ai/setup for more information
  EventName.calibrationInvalid: {
    ET.PERMANENT: calibration_invalid_alert,
    ET.SOFT_DISABLE: soft_disable_alert("캘리브레이션 오류: 기기를 다시 장착하고 재보정하세요"),
    ET.NO_ENTRY: NoEntryAlert("캘리브레이션 오류: 기기를 다시 장착하고 재보정하세요"),
  },

  EventName.calibrationIncomplete: {
    ET.PERMANENT: calibration_incomplete_alert,
    ET.SOFT_DISABLE: soft_disable_alert("캘리브레이션이 완료되지 않았습니다"),
    ET.NO_ENTRY: NoEntryAlert("캘리브레이션이 진행중입니다"),
  },

  EventName.calibrationRecalibrating: {
    ET.PERMANENT: calibration_incomplete_alert,
    ET.SOFT_DISABLE: soft_disable_alert("기기 재장착 감지됨: 재보정 중"),
    ET.NO_ENTRY: NoEntryAlert("기기 재장착 감지됨: 재보정 중"),
  },

  EventName.doorOpen: {
    ET.SOFT_DISABLE: user_soft_disable_alert("문이 열려 있습니다"),
    ET.NO_ENTRY: NoEntryAlert("문이 열려 있습니다"),
  },

  EventName.seatbeltNotLatched: {
    ET.SOFT_DISABLE: user_soft_disable_alert("안전벨트가 체결되지 않았습니다"),
    ET.NO_ENTRY: NoEntryAlert("안전벨트가 체결되지 않았습니다"),
  },

  EventName.espDisabled: {
    ET.SOFT_DISABLE: soft_disable_alert("차체 자세 제어 장치가 꺼져 있습니다"),
    ET.NO_ENTRY: NoEntryAlert("차체 자세 제어 장치가 꺼져 있습니다"),
  },

  EventName.lowBattery: {
    ET.SOFT_DISABLE: soft_disable_alert("배터리 전압이 낮습니다"),
    ET.NO_ENTRY: NoEntryAlert("배터리 전압이 낮습니다"),
  },

  # Different openpilot services communicate between each other at a certain
  # interval. If communication does not follow the regular schedule this alert
  # is thrown. This can mean a service crashed, did not broadcast a message for
  # ten times the regular interval, or the average interval is more than 10% too high.
  EventName.commIssue: {
    ET.SOFT_DISABLE: soft_disable_alert("프로세스 간 통신 오류"),
    ET.NO_ENTRY: comm_issue_alert,
  },
  EventName.commIssueAvgFreq: {
    ET.SOFT_DISABLE: soft_disable_alert("프로세스 간 통신 속도 낮음"),
    ET.NO_ENTRY: NoEntryAlert("프로세스 간 통신 속도 낮음"),
  },

  EventName.selfdrivedLagging: {
    ET.SOFT_DISABLE: soft_disable_alert("시스템이 지연되고 있습니다"),
    ET.NO_ENTRY: NoEntryAlert("Selfdrive 프로세스 지연: 기기를 재부팅하세요"),
  },

  # Thrown when manager detects a service exited unexpectedly while driving
  EventName.processNotRunning: {
    ET.NO_ENTRY: process_not_running_alert,
    ET.SOFT_DISABLE: soft_disable_alert("외부 프로그램 비정상"),
  },

  EventName.radarFault: {
    ET.SOFT_DISABLE: soft_disable_alert("레이더 오류: 차량을 재시동하세요"),
    ET.NO_ENTRY: NoEntryAlert("레이더 오류: 차량을 재시동하세요"),
  },

  EventName.radarTempUnavailable: {
    ET.SOFT_DISABLE: soft_disable_alert("레이더를 일시적으로 사용할 수 없습니다"),
    ET.NO_ENTRY: NoEntryAlert("레이더를 일시적으로 사용할 수 없습니다"),
  },

  # Every frame from the camera should be processed by the model. If modeld
  # is not processing frames fast enough they have to be dropped. This alert is
  # thrown when over 20% of frames are dropped.
  EventName.modeldLagging: {
    ET.SOFT_DISABLE: soft_disable_alert("주행 모델이 지연되고 있습니다"),
    ET.NO_ENTRY: NoEntryAlert("주행 모델이 지연되고 있습니다"),
    ET.PERMANENT: modeld_lagging_alert,
  },

  # Besides predicting the path, lane lines and lead car data the model also
  # predicts the current velocity and rotation speed of the car. If the model is
  # very uncertain about the current velocity while the car is moving, this
  # usually means the model has trouble understanding the scene. This is used
  # as a heuristic to warn the driver.
  EventName.posenetInvalid: {
    ET.SOFT_DISABLE: soft_disable_alert("포즈넷 속도 이상"),
    ET.NO_ENTRY: posenet_invalid_alert,
  },

  # When the localizer detects an acceleration of more than 40 m/s^2 (~4G) we
  # alert the driver the device might have fallen from the windshield.
  EventName.deviceFalling: {
    ET.SOFT_DISABLE: soft_disable_alert("기기가 거치대에서 떨어졌습니다"),
    ET.NO_ENTRY: NoEntryAlert("기기가 거치대에서 떨어졌습니다"),
  },

  EventName.lowMemory: {
    ET.SOFT_DISABLE: soft_disable_alert("메모리 부족: 기기를 재부팅하세요"),
    ET.PERMANENT: low_memory_alert,
    ET.NO_ENTRY: NoEntryAlert("메모리 부족: 기기를 재부팅하세요"),
  },

  EventName.accFaulted: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("크루즈 오류: 차량을 재시동하세요"),
    ET.PERMANENT: NormalPermanentAlert("크루즈 오류: 활성화하려면 차량을 재시동하세요"),
    ET.NO_ENTRY: NoEntryAlert("크루즈 오류: 차량을 재시동하세요"),
  },

  EventName.espActive: {
    ET.SOFT_DISABLE: soft_disable_alert("차체 자세 제어 장치가 작동 중입니다"),
    ET.NO_ENTRY: NoEntryAlert("차체 자세 제어 장치가 작동 중입니다"),
  },

  EventName.controlsMismatch: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("제어 상태 불일치"),
    ET.NO_ENTRY: NoEntryAlert("제어 상태 불일치"),
  },

  # Sometimes the USB stack on the device can get into a bad state
  # causing the connection to the panda to be lost
  EventName.usbError: {
    ET.SOFT_DISABLE: soft_disable_alert("USB 오류: 기기를 재부팅하세요"),
    ET.PERMANENT: NormalPermanentAlert("USB 오류: 기기를 재부팅하세요"),
    ET.NO_ENTRY: NoEntryAlert("USB 오류: 기기를 재부팅하세요"),
  },

  # This alert can be thrown for the following reasons:
  # - No CAN data received at all
  # - CAN data is received, but some message are not received at the right frequency
  # If you're not writing a new car port, this is usually cause by faulty wiring
  EventName.canError: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("알 수 없는 차량 사양"),
    ET.PERMANENT: Alert(
      "알 수 없는 차량 사양",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1., creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("알 수 없는 차량 사양"),
  },

  EventName.canBusMissing: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("CAN 버스 연결이 끊겼습니다"),
    ET.PERMANENT: Alert(
      "CAN 버스 연결 끊김: 케이블 문제일 수 있습니다",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1., creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("CAN 버스 연결 끊김: 연결 상태를 확인하세요"),
  },

  EventName.steerUnavailable: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("LKAS 오류: 차량을 재시동하세요"),
    ET.PERMANENT: NormalPermanentAlert("LKAS 오류: 활성화하려면 차량을 재시동하세요"),
    ET.NO_ENTRY: NoEntryAlert("LKAS 오류: 차량을 재시동하세요"),
  },

  EventName.reverseGear: {
    ET.PERMANENT: Alert(
      "후진\n기어",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2, creation_delay=0.5),
    ET.USER_DISABLE: ImmediateDisableAlert("후진 기어"),
    ET.NO_ENTRY: NoEntryAlert("후진 기어"),
  },

  # On cars that use stock ACC the car can decide to cancel ACC for various reasons.
  # When this happens we can no long control the car so the user needs to be warned immediately.
  EventName.cruiseDisabled: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("크루즈가 꺼져 있습니다"),
  },

  # When the relay in the harness box opens the CAN bus between the LKAS camera
  # and the rest of the car is separated. When messages from the LKAS camera
  # are received on the car side this usually means the relay hasn't opened correctly
  # and this alert is thrown.
  EventName.relayMalfunction: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("하네스 릴레이 이상"),
    ET.PERMANENT: NormalPermanentAlert("하네스 릴레이 이상", "하드웨어를 확인하세요"),
    ET.NO_ENTRY: NoEntryAlert("하네스 릴레이 이상"),
  },

  EventName.speedTooLow: {
    ET.IMMEDIATE_DISABLE: Alert(
      "오픈파일럿 해제됨",
      "속도가 너무 낮습니다",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, AudibleAlert.disengage, 3.),
  },

  # When the car is driving faster than most cars in the training data, the model outputs can be unpredictable.
  EventName.speedTooHigh: {
    ET.WARNING: Alert(
      "속도가 너무 높습니다",
      "이 속도에서는 모델 예측이 불안정합니다",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.promptRepeat, 4.),
    ET.NO_ENTRY: NoEntryAlert("활성화하려면 속도를 줄이세요"),
  },

  EventName.vehicleSensorsInvalid: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("차량 센서 이상"),
    ET.PERMANENT: NormalPermanentAlert("차량 센서 보정 중", "보정을 위해 주행하세요"),
    ET.NO_ENTRY: NoEntryAlert("차량 센서 보정 중"),
  },

  EventName.personalityChanged: {
    ET.WARNING: personality_changed_alert,
  },

  EventName.userBookmark: {
    ET.PERMANENT: NormalPermanentAlert("북마크 저장됨", duration=1.5),
  },

  EventName.audioFeedback: {
    ET.PERMANENT: audio_feedback_alert,
  },
}

STARPILOT_EVENTS: dict[int, dict[str, Alert | AlertCallbackType]] = {
  StarPilotEventName.blockUser: {
    ET.PERMANENT: Alert(
      "Development 브랜치는 사용하지 마세요!",
      "안전을 위해 블랙박스 모드로 전환합니다...",
      AlertStatus.critical, AlertSize.mid,
      Priority.HIGHEST, VisualAlert.none, AudibleAlert.warningImmediate, 1.),
  },

  StarPilotEventName.customStartupAlert: {
    ET.PERMANENT: custom_startup_alert,
  },

  StarPilotEventName.forcingStop: {
    ET.WARNING: forcing_stop_alert,
  },

  StarPilotEventName.goatSteerSaturated: {
    ET.WARNING: Alert(
      "조향 한계 초과!",
      "조향각 한계에 도달했습니다",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, StarPilotAudibleAlert.goat, 2.),
  },

  StarPilotEventName.greenLight: {
    ET.PERMANENT: Alert(
      "신호가 초록불로 바뀌었습니다",
      "",
      StarPilotAlertStatus.starpilot, AlertSize.small,
      Priority.MID, VisualAlert.none, AudibleAlert.prompt, 3.),
  },

  StarPilotEventName.holidayActive: {
    ET.PERMANENT: holiday_alert,
  },

  StarPilotEventName.laneChangeBlockedLoud: {
    ET.WARNING: Alert(
      "사각지대에 차량이 감지되었습니다",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.warningSoft, .1),
  },

  StarPilotEventName.leadDeparting: {
    ET.PERMANENT: Alert(
      "앞차가 출발했습니다",
      "",
      StarPilotAlertStatus.starpilot, AlertSize.small,
      Priority.MID, VisualAlert.none, AudibleAlert.prompt, 3.),
  },

  StarPilotEventName.phoneLeadClosing: {
    ET.WARNING: Alert(
      "전방 주의",
      "전방 차량과 접근중",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.none, AudibleAlert.warningSoft, 2.),
  },

  StarPilotEventName.phoneLaneIntrusion: {
    ET.WARNING: Alert(
      "전방 차량 주의",
      "전방 차량 차선 침범함",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.none, AudibleAlert.warningSoft, 2.),
  },

  StarPilotEventName.nnffLoaded: {
    ET.PERMANENT: nnff_loaded_alert,
  },

  StarPilotEventName.noLaneAvailable: {
    ET.WARNING: no_lane_available_alert,
  },

  StarPilotEventName.openpilotCrashed: {
    ET.IMMEDIATE_DISABLE: Alert(
      "오픈파일럿 오류 발생",
      "StarPilot Discord에 오류 로그를 올려주세요",
      AlertStatus.critical, AlertSize.mid,
      Priority.HIGHEST, VisualAlert.none, AudibleAlert.prompt, .1),

    ET.NO_ENTRY: Alert(
      "오픈파일럿 오류 발생",
      "StarPilot Discord에 오류 로그를 올려주세요",
      AlertStatus.critical, AlertSize.mid,
      Priority.HIGHEST, VisualAlert.none, AudibleAlert.prompt, .1),
  },

  StarPilotEventName.speedLimitChanged: {
    ET.PERMANENT: speed_limit_changed_alert,
  },

  StarPilotEventName.trafficModeActive: {
    ET.WARNING: Alert(
      "트래픽 모드 켜짐",
      "",
      StarPilotAlertStatus.starpilot, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, 3.),
  },

  StarPilotEventName.trafficModeInactive: {
    ET.WARNING: Alert(
      "트래픽 모드 꺼짐",
      "",
      StarPilotAlertStatus.starpilot, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, 3.),
  },

  StarPilotEventName.switchbackModeActive: {
    ET.WARNING: Alert(
      "스위치백 모드",
      "",
      StarPilotAlertStatus.starpilot, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, 3.),
  },

  StarPilotEventName.switchbackModeInactive: {
    ET.WARNING: Alert(
      "스위치백 모드 꺼짐",
      "",
      StarPilotAlertStatus.starpilot, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, 3.),
  },

  StarPilotEventName.lkasEnable: {
    ET.WARNING: EngagementAlert(AudibleAlert.engage),
  },

  StarPilotEventName.lkasDisable: {
    ET.PERMANENT: EngagementAlert(AudibleAlert.disengage),
  },

  StarPilotEventName.turningLeft: {
    ET.WARNING: Alert(
      "좌회전 중",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1),
  },

  StarPilotEventName.turningRight: {
    ET.WARNING: Alert(
      "우회전 중",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1),
  },

  # Random Events
  StarPilotEventName.accel30: {
    ET.WARNING: Alert(
      "조금 빠른데요!",
      "(⁄ ⁄•⁄ω⁄•⁄ ⁄)",
      StarPilotAlertStatus.starpilot, AlertSize.mid,
      Priority.LOW, VisualAlert.none, StarPilotAudibleAlert.uwu, 4.),
  },

  StarPilotEventName.accel35: {
    ET.WARNING: Alert(
      "그 정도는 못 드립니다",
      "속도를 조금 줄여주세요!",
      StarPilotAlertStatus.starpilot, AlertSize.mid,
      Priority.LOW, VisualAlert.none, StarPilotAudibleAlert.nessie, 4.),
  },

  StarPilotEventName.accel40: {
    ET.WARNING: Alert(
      "이런 세상에!",
      "🚗💨",
      StarPilotAlertStatus.starpilot, AlertSize.mid,
      Priority.LOW, VisualAlert.none, StarPilotAudibleAlert.doc, 4.),
  },

  StarPilotEventName.dejaVuCurve: {
    ET.PERMANENT: Alert(
      "♬♪ Deja vu! ᕕ(⌐■_■)ᕗ ♪♬",
      "🏎️",
      StarPilotAlertStatus.starpilot, AlertSize.mid,
      Priority.LOW, VisualAlert.none, StarPilotAudibleAlert.dejaVu, 4.),
  },

  StarPilotEventName.firefoxSteerSaturated: {
    ET.WARNING: Alert(
      "IE가 응답하지 않습니다...",
      "조향각 한계에 도달했습니다",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, StarPilotAudibleAlert.firefox, 4.),
  },

  StarPilotEventName.hal9000: {
    ET.WARNING: Alert(
      "미안해요 Dave",
      "그건 할 수 없어요...",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, StarPilotAudibleAlert.hal9000, 4.),
  },

  StarPilotEventName.openpilotCrashedRandomEvent: {
    ET.IMMEDIATE_DISABLE: Alert(
      "오픈파일럿 오류 발생 💩",
      "StarPilot Discord에 오류 로그를 올려주세요",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGHEST, VisualAlert.none, StarPilotAudibleAlert.fart, 10.),

    ET.NO_ENTRY: Alert(
      "오픈파일럿 오류 발생 💩",
      "StarPilot Discord에 오류 로그를 올려주세요",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGHEST, VisualAlert.none, StarPilotAudibleAlert.fart, 10.),
  },

  StarPilotEventName.thisIsFineSteerSaturated: {
    ET.WARNING: Alert(
      "괜찮아 보이네요 ☕",
      "조향각 한계에 도달했습니다",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, StarPilotAudibleAlert.thisIsFine, 2.),
  },

  StarPilotEventName.toBeContinued: {
    ET.PERMANENT: Alert(
      "다음 편에 계속...",
      "⬅️",
      StarPilotAlertStatus.starpilot, AlertSize.mid,
      Priority.MID, VisualAlert.none, StarPilotAudibleAlert.continued, 7.),
  },

  StarPilotEventName.vCruise69: {
    ET.WARNING: Alert(
      "좋은 숫자네요 69",
      "",
      StarPilotAlertStatus.starpilot, AlertSize.small,
      Priority.LOW, VisualAlert.none, StarPilotAudibleAlert.noice, 2.),
  },

  StarPilotEventName.yourFrogTriedToKillMe: {
    ET.PERMANENT: Alert(
      "이 녀석이 저를 죽일 뻔했어요...",
      "👺",
      StarPilotAlertStatus.starpilot, AlertSize.mid,
      Priority.MID, VisualAlert.none, StarPilotAudibleAlert.angry, 5.),
  },

  StarPilotEventName.youveGotMail: {
    ET.WARNING: Alert(
      "메일이 도착했습니다! 📧",
      "",
      StarPilotAlertStatus.starpilot, AlertSize.small,
      Priority.LOW, VisualAlert.none, StarPilotAudibleAlert.mail, 3.),
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
    values["service names"] = ", ".join(bad_services[:4])
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
  return alert


def _mici_static_alert_args() -> tuple[car.CarParams, car.CarState, _MiciStaticSubMaster, bool]:
  return car.CarParams.new_message(), car.CarState.new_message(), _MiciStaticSubMaster(), True


def _mici_wrap_alert_callback(callback: AlertCallbackType, config: dict) -> AlertCallbackType:
  def wrapped(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool,
              soft_disable_time: int, personality, starpilot_toggles: SimpleNamespace) -> Alert:
    alert = callback(CP, CS, sm, metric, soft_disable_time, personality, starpilot_toggles)
    return _mici_apply_alert_text_override(alert, config, CP, CS, sm, metric)
  return wrapped


def _apply_mici_event_alert_overrides() -> None:
  if not MICI_EVENT_ALERT_OVERRIDES_PATH.is_file():
    return

  with open(MICI_EVENT_ALERT_OVERRIDES_PATH, encoding="utf-8") as f:
    configs = json.load(f).get("events", {})

  sources = {
    "EVENTS": (EVENTS, EventName.schema.enumerants),
    "STARPILOT_EVENTS": (STARPILOT_EVENTS, StarPilotEventName.schema.enumerants),
  }
  static_CP, static_CS, static_sm, static_metric = _mici_static_alert_args()

  for config in configs.values():
    source = config.get("source")
    event_name = config.get("eventName")
    event_type = MICI_EVENT_TYPE_BY_JSON_NAME.get(config.get("eventType", ""))
    if source not in sources or event_name is None or event_type is None:
      continue

    alerts, enumerants = sources[source]
    event_id = enumerants.get(event_name)
    if event_id is None or event_id not in alerts or event_type not in alerts[event_id]:
      continue

    alert = alerts[event_id][event_type]
    if isinstance(alert, Alert):
      _mici_apply_alert_text_override(alert, config, static_CP, static_CS, static_sm, static_metric)
    else:
      alerts[event_id][event_type] = _mici_wrap_alert_callback(alert, config)


if HARDWARE.get_device_type() == 'mici':
  EVENTS.update({
    EventName.preDriverDistracted: {
      ET.PERMANENT: Alert(
        "운전에 집중하세요",
        "",
        AlertStatus.normal, AlertSize.small,
        Priority.LOW, VisualAlert.none, AudibleAlert.none, 2),
    },
    EventName.promptDriverDistracted: {
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
      if callable(alert):
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
