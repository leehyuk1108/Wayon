import json
import time
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple
import pyray as rl
import random
import string
from dataclasses import dataclass
from cereal import messaging, log, car
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.common.filter_simple import BounceFilter, FirstOrderFilter
from openpilot.system.hardware import TICI
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.label import UnifiedLabel

from openpilot.selfdrive.ui.sunnypilot.onroad.speed_limit import SpeedLimitAlertRenderer
from openpilot.selfdrive.ui.sunnypilot.onroad.e2e_alerts import E2EAlertController
from openpilot.selfdrive.ui.mici.onroad.status_timers import (
  AUTO_HOLD_EVENT_NAMES,
  PARKING_BRAKE_EVENT_NAMES,
  format_mmss,
  should_show_auto_hold_timer,
  should_show_parking_brake_timer,
)

AlertSize = log.SelfdriveState.AlertSize
AlertStatus = log.SelfdriveState.AlertStatus

ALERT_MARGIN = 18

ALERT_FONT_SMALL = 66 - 50
ALERT_FONT_BIG = 88 - 40
AUTOHOLD_ICON_SIZE = 74
AUTOHOLD_TIMER_FONT_SIZE = 62
AUTOHOLD_TIMER_GAP = 18
AUTOHOLD_TIMER_BG_HEIGHT = 150
AUTOHOLD_TIMER_BG_ALPHA = 170

SELFDRIVE_STATE_TIMEOUT = 5  # Seconds
SELFDRIVE_UNRESPONSIVE_TIMEOUT = 10  # Seconds
MICI_EVENT_ALERT_OVERRIDES_PATH = Path(__file__).resolve().parents[1] / "mici_event_alert_overrides.json"

EVENT_TYPE_JSON_NAME = {
  "enable": "ENABLE",
  "preEnable": "PRE_ENABLE",
  "overrideLateral": "OVERRIDE_LATERAL",
  "overrideLongitudinal": "OVERRIDE_LONGITUDINAL",
  "noEntry": "NO_ENTRY",
  "warning": "WARNING",
  "userDisable": "USER_DISABLE",
  "softDisable": "SOFT_DISABLE",
  "immediateDisable": "IMMEDIATE_DISABLE",
  "permanent": "PERMANENT",
}

# Constants
ALERT_COLORS = {
  AlertStatus.normal: rl.Color(0, 0, 0, 255),
  AlertStatus.userPrompt: rl.Color(255, 115, 0, 255),
  AlertStatus.critical: rl.Color(255, 0, 21, 255),
}

TURN_SIGNAL_BLINK_PERIOD = 1 / (80 / 60)  # Mazda heartbeat turn signal BPM

DEBUG = False


class IconSide(StrEnum):
  left = 'left'
  right = 'right'


class IconLayout(NamedTuple):
  texture: rl.Texture
  side: IconSide
  margin_x: int
  margin_y: int
  alpha: float = 255.0


class AlertLayout(NamedTuple):
  text_rect: rl.Rectangle
  icon: IconLayout | None


@dataclass
class Alert:
  text1: str = ""
  text2: str = ""
  size: int = 0
  status: int = 0
  visual_alert: int = car.CarControl.HUDControl.VisualAlert.none
  alert_type: str = ""
  source: str = "EVENTS"
  title_font_px: int | None = None
  subtitle_font_px: int | None = None
  has_mici_override: bool = False


# Pre-defined alert instances
ALERT_STARTUP_PENDING = Alert(
  text1="sunnypilot Unavailable",
  text2="Waiting to start",
  size=AlertSize.mid,
  status=AlertStatus.normal,
)

ALERT_CRITICAL_TIMEOUT = Alert(
  text1="TAKE CONTROL IMMEDIATELY",
  text2="System Unresponsive",
  size=AlertSize.full,
  status=AlertStatus.critical,
)

ALERT_CRITICAL_REBOOT = Alert(
  text1="System Unresponsive",
  text2="Reboot Device",
  size=AlertSize.full,
  status=AlertStatus.critical,
)


class AlertRenderer(Widget, SpeedLimitAlertRenderer):
  def __init__(self):
    Widget.__init__(self)
    SpeedLimitAlertRenderer.__init__(self)

    self._alert_text1_label = UnifiedLabel(text="", font_size=ALERT_FONT_BIG, font_weight=FontWeight.DISPLAY, line_height=0.86,
                                           letter_spacing=-0.02)
    self._alert_text2_label = UnifiedLabel(text="", font_size=ALERT_FONT_SMALL, font_weight=FontWeight.ROMAN, line_height=0.86,
                                           letter_spacing=0.025)

    self._prev_alert: Alert | None = None
    self._text_gen_time = 0
    self._alert_text2_gen = ''
    self._resume_required_start_time: float | None = None
    self._parking_brake_start_time: float | None = None
    self._parking_brake_timer_visible = False
    self._last_started_frame = -1
    self._e2e_alerts = E2EAlertController()

    # animation filters
    # TODO: use 0.1 but with proper alert height calculation
    self._alert_y_filter = BounceFilter(0, 0.1, 1 / gui_app.target_fps)
    self._alpha_filter = FirstOrderFilter(0, 0.05, 1 / gui_app.target_fps)

    self._turn_signal_timer = 0.0
    self._turn_signal_alpha_filter = FirstOrderFilter(0.0, 0.3, 1 / gui_app.target_fps)
    self._last_icon_side: IconSide | None = None
    self._alert_override_mtime: float | None = None
    self._alert_overrides: dict[str, dict] = {}

    self._load_icons()
    ui_state.add_offroad_transition_callback(self._reset_timers)

  def _reset_timers(self) -> None:
    self._resume_required_start_time = None
    self._parking_brake_start_time = None
    self._parking_brake_timer_visible = False
    self._e2e_alerts.reset()

  def parking_brake_timer_visible(self) -> bool:
    return self._parking_brake_timer_visible

  def _load_icons(self):
    self._txt_turn_signal_left = gui_app.texture('icons_mici/onroad/turn_signal_left.png', 104, 96)
    self._txt_turn_signal_right = gui_app.texture('icons_mici/onroad/turn_signal_left.png', 104, 96, flip_x=True)
    self._txt_blind_spot_left = gui_app.texture('icons_mici/onroad/blind_spot_left.png', 134, 150)
    self._txt_blind_spot_right = gui_app.texture('icons_mici/onroad/blind_spot_left.png', 134, 150, flip_x=True)
    self._txt_autohold = gui_app.texture("icons/autohold.png", AUTOHOLD_ICON_SIZE, AUTOHOLD_ICON_SIZE, keep_aspect_ratio=True)
    self._txt_parking = gui_app.texture("icons/parking.png", AUTOHOLD_ICON_SIZE, AUTOHOLD_ICON_SIZE, keep_aspect_ratio=True)

  @staticmethod
  def _event_parts(alert: Alert) -> tuple[str, str]:
    if not alert.alert_type:
      return "", ""
    return (alert.alert_type.split("/", 1) + [""])[:2]

  def _load_alert_overrides(self) -> None:
    try:
      mtime = MICI_EVENT_ALERT_OVERRIDES_PATH.stat().st_mtime
    except OSError:
      self._alert_override_mtime = None
      self._alert_overrides = {}
      return

    if self._alert_override_mtime == mtime:
      return

    try:
      with open(MICI_EVENT_ALERT_OVERRIDES_PATH, encoding="utf-8") as f:
        self._alert_overrides = json.load(f).get("events", {})
      self._alert_override_mtime = mtime
    except (OSError, json.JSONDecodeError):
      self._alert_override_mtime = None
      self._alert_overrides = {}

  @staticmethod
  def _font_px(value) -> int | None:
    try:
      font_px = int(value)
    except (TypeError, ValueError):
      return None
    return font_px if font_px > 0 else None

  def _apply_render_overrides(self, alert: Alert) -> Alert:
    self._load_alert_overrides()
    event_name, event_type = self._event_parts(alert)
    json_event_type = EVENT_TYPE_JSON_NAME.get(event_type, event_type.upper())
    config = self._alert_overrides.get(f"{alert.source}.{event_name}.{json_event_type}")
    if config is None:
      return alert

    alert.has_mici_override = True
    alert.title_font_px = self._font_px(config.get("titleFontPx"))
    alert.subtitle_font_px = self._font_px(config.get("subtitleFontPx"))
    return alert

  def get_alert(self, sm: messaging.SubMaster) -> Alert | None:
    """Generate the current alert based on selfdrive state."""
    ss = sm['selfdriveState']
    e2e = sm['longitudinalPlanSP'].e2eAlerts
    gear = sm['carState'].gearShifter
    allowed = gear not in (
      car.CarState.GearShifter.neutral,
      car.CarState.GearShifter.park,
      car.CarState.GearShifter.reverse,
      car.CarState.GearShifter.unknown,
    )
    e2e_alert = self._e2e_alerts.update(
      e2e.greenLightAlert, e2e.leadDepartAlert, allowed=allowed)

    # Check if selfdriveState messages have stopped arriving
    if not sm.updated['selfdriveState']:
      recv_frame = sm.recv_frame['selfdriveState']
      time_since_onroad = time.monotonic() - ui_state.started_time

      # 1. Never received selfdriveState since going onroad
      waiting_for_startup = recv_frame < ui_state.started_frame
      if waiting_for_startup and time_since_onroad > 5:
        return ALERT_STARTUP_PENDING

      # 2. Lost communication with selfdriveState after receiving it
      if TICI and not waiting_for_startup:
        ss_missing = time.monotonic() - sm.recv_time['selfdriveState']
        if ss_missing > SELFDRIVE_STATE_TIMEOUT:
          if ss.enabled and (ss_missing - SELFDRIVE_STATE_TIMEOUT) < SELFDRIVE_UNRESPONSIVE_TIMEOUT:
            return ALERT_CRITICAL_TIMEOUT
          return ALERT_CRITICAL_REBOOT

    # No alert if size is none
    if ss.alertSize == 0:
      if e2e_alert is None:
        return None

      ret = Alert(text1=e2e_alert.text1, text2=e2e_alert.text2, size=AlertSize.mid, status=AlertStatus.normal,
                  alert_type=f"{e2e_alert.name}/permanent", source="E2E")
      self._prev_alert = ret
      return ret

    # Return current alert
    ret = Alert(text1=ss.alertText1, text2=ss.alertText2, size=ss.alertSize.raw, status=ss.alertStatus.raw,
                visual_alert=ss.alertHudVisual, alert_type=ss.alertType)
    ret = self._apply_render_overrides(ret)
    self._prev_alert = ret
    return ret

  def will_render(self) -> tuple[Alert | None, bool]:
    alert = self.get_alert(ui_state.sm)
    if alert is None and ui_state.sm['carState'].brakeHoldActive:
      return Alert(alert_type="silentBrakeHold/warning"), False
    return alert or self._prev_alert, alert is None

  def _icon_helper(self, alert: Alert) -> AlertLayout:
    icon_side = None
    txt_icon = None
    icon_alpha = 255.0
    icon_margin_x = 20
    icon_margin_y = 18

    # alert_type format is "EventName/eventType" (e.g., "preLaneChangeLeft/warning")
    event_name = alert.alert_type.split('/')[0] if alert.alert_type else ''

    if event_name == 'preLaneChangeLeft':
      icon_side = IconSide.left
      txt_icon = self._txt_turn_signal_left
      icon_margin_x = 2
      icon_margin_y = 5

    elif event_name == 'preLaneChangeRight':
      icon_side = IconSide.right
      txt_icon = self._txt_turn_signal_right
      icon_margin_x = 2
      icon_margin_y = 5

    elif event_name == 'laneChange':
      icon_side = self._last_icon_side
      txt_icon = self._txt_turn_signal_left if self._last_icon_side == 'left' else self._txt_turn_signal_right
      icon_margin_x = 2
      icon_margin_y = 5

    elif event_name == 'laneChangeBlocked':
      CS = ui_state.sm['carState']
      if CS.leftBlinker:
        icon_side = IconSide.left
      elif CS.rightBlinker:
        icon_side = IconSide.right
      else:
        icon_side = self._last_icon_side
      txt_icon = self._txt_blind_spot_left if icon_side == 'left' else self._txt_blind_spot_right
      icon_margin_x = 8
      icon_margin_y = 0

    elif event_name == 'speedLimitPreActive':
      icon_side, txt_icon, icon_alpha, icon_margin_x, icon_margin_y = SpeedLimitAlertRenderer.speed_limit_pre_active_icon_helper(self)

    else:
      self._turn_signal_timer = 0.0

    self._last_icon_side = icon_side

    # create text rect based on icon presence
    text_x = self._rect.x + ALERT_MARGIN
    text_width = self._rect.width - ALERT_MARGIN
    if icon_side == 'left':
      text_x = self._rect.x + self._txt_turn_signal_right.width
      text_width = self._rect.width - ALERT_MARGIN - self._txt_turn_signal_right.width
    elif icon_side == 'right':
      text_x = self._rect.x + ALERT_MARGIN
      text_width = self._rect.width - ALERT_MARGIN - self._txt_turn_signal_right.width

    text_rect = rl.Rectangle(
      text_x,
      self._alert_y_filter.x,
      text_width,
      self._rect.height,
    )
    icon_layout = IconLayout(txt_icon, icon_side, icon_margin_x, icon_margin_y, icon_alpha) if txt_icon is not None and icon_side is not None else None
    return AlertLayout(text_rect, icon_layout)

  def _render(self, rect: rl.Rectangle) -> bool:
    self._parking_brake_timer_visible = False

    if not ui_state.started:
      self._reset_timers()
      self._prev_alert = None
      self._alert_y_filter.update(self._rect.y - 50)
      self._alpha_filter.update(0)
      return False

    if self._last_started_frame != ui_state.started_frame:
      self._last_started_frame = ui_state.started_frame
      self._reset_timers()

    alert = self.get_alert(ui_state.sm)
    event_name = alert.alert_type.split('/')[0] if alert is not None and alert.alert_type else ''
    brake_hold_active = ui_state.sm["carState"].brakeHoldActive
    parking_brake_active = ui_state.sm["carState"].parkingBrake
    car_control = ui_state.sm["carControl"]
    long_auto_hold_active = bool(
      car_control.longActive and ui_state.sm["carState"].standstill and
      car_control.actuators.longControlState == car.CarControl.Actuators.LongControlState.stopping
    )
    auto_hold_active = brake_hold_active or long_auto_hold_active or event_name in AUTO_HOLD_EVENT_NAMES
    if auto_hold_active and self._resume_required_start_time is None:
      self._resume_required_start_time = time.monotonic()
    elif not auto_hold_active:
      self._resume_required_start_time = None
    if parking_brake_active and self._parking_brake_start_time is None:
      self._parking_brake_start_time = time.monotonic()
    elif not parking_brake_active:
      self._parking_brake_start_time = None
    draw_parking_timer = should_show_parking_brake_timer(parking_brake_active=parking_brake_active,
                                                         alert_event_name=event_name)
    draw_auto_hold_timer = should_show_auto_hold_timer(brake_hold_active=brake_hold_active,
                                                       alert_event_name=event_name,
                                                       has_alert=alert is not None)
    has_active_indicator = alert is not None or draw_auto_hold_timer or draw_parking_timer

    # Animate fade and slide in/out
    self._alert_y_filter.update(self._rect.y - 50 if not has_active_indicator else self._rect.y)
    self._alpha_filter.update(0 if not has_active_indicator else 1)

    if gui_app.sunnypilot_ui():
      ui_state.onroad_brightness_handle_alerts(ui_state, alert)

    active_alert = alert
    if alert is None:
      if draw_auto_hold_timer:
        self._prev_alert = None
        self._parking_brake_timer_visible = False
        self._draw_resume_required(True)
        return True

      if draw_parking_timer:
        self._prev_alert = None
        self._parking_brake_timer_visible = True
        self._draw_parking_brake_timer(True)
        return True

      # If still animating out, keep the previous alert
      if self._alpha_filter.x > 0.01 and self._prev_alert is not None:
        alert = self._prev_alert
      else:
        self._prev_alert = None
        return False

    self._draw_background(alert)

    # update speed limit UI states
    SpeedLimitAlertRenderer.update(self)

    alert_layout = self._icon_helper(alert)
    event_name = alert.alert_type.split('/')[0] if alert.alert_type else ''
    if event_name in AUTO_HOLD_EVENT_NAMES:
      self._draw_resume_required(active_alert is not None)
      return True
    if event_name in PARKING_BRAKE_EVENT_NAMES and parking_brake_active:
      self._parking_brake_timer_visible = True
      self._draw_parking_brake_timer(active_alert is not None)
      return True

    self._draw_text(alert, alert_layout)
    self._draw_icons(alert_layout)

    return True

  def _draw_resume_required(self, is_active: bool) -> None:
    if is_active and self._resume_required_start_time is None:
      self._resume_required_start_time = time.monotonic()
    elif self._resume_required_start_time is None:
      return

    elapsed = time.monotonic() - self._resume_required_start_time
    self._draw_center_timer(self._txt_autohold, format_mmss(elapsed), draw_gradient=True)

  def _draw_parking_brake_timer(self, is_active: bool) -> None:
    if is_active and self._parking_brake_start_time is None:
      self._parking_brake_start_time = time.monotonic()
    elif self._parking_brake_start_time is None:
      return

    elapsed = time.monotonic() - self._parking_brake_start_time
    self._draw_center_timer(self._txt_parking, format_mmss(elapsed))

  def _draw_center_timer(self, icon_texture: rl.Texture, timer_text: str, draw_gradient: bool = False) -> None:
    color = rl.Color(255, 255, 255, int(255 * 0.9 * self._alpha_filter.x))
    self._alert_text1_label.set_text(timer_text)
    self._alert_text1_label.set_text_color(color)
    self._alert_text1_label.set_font_size(AUTOHOLD_TIMER_FONT_SIZE)
    self._alert_text1_label.set_alignment(rl.GuiTextAlignment.TEXT_ALIGN_LEFT)

    timer_size = measure_text_cached(gui_app.font(FontWeight.DISPLAY), timer_text, AUTOHOLD_TIMER_FONT_SIZE,
                                     AUTOHOLD_TIMER_FONT_SIZE * -0.02)
    group_width = icon_texture.width + AUTOHOLD_TIMER_GAP + timer_size.x
    group_x = self._rect.x + (self._rect.width - group_width) / 2
    center_y = self._rect.y + self._rect.height / 2 + (self._alert_y_filter.x - self._rect.y)

    if draw_gradient:
      self._draw_center_timer_gradient(center_y)

    icon_x = group_x
    icon_y = center_y - icon_texture.height / 2
    rl.draw_texture_ex(icon_texture, rl.Vector2(icon_x, icon_y), 0.0, 1.0,
                       rl.Color(255, 255, 255, int(255 * self._alpha_filter.x)))

    timer_rect = rl.Rectangle(
      group_x + icon_texture.width + AUTOHOLD_TIMER_GAP,
      center_y - timer_size.y / 2,
      timer_size.x + 2,
      timer_size.y,
    )
    self._alert_text1_label.render(timer_rect)

  def _draw_center_timer_gradient(self, center_y: float) -> None:
    bg_alpha = int(AUTOHOLD_TIMER_BG_ALPHA * self._alpha_filter.x)
    center_color = rl.Color(0, 0, 0, bg_alpha)
    transparent = rl.Color(0, 0, 0, 0)
    half_height = AUTOHOLD_TIMER_BG_HEIGHT / 2
    bg_y = center_y - half_height

    rl.draw_rectangle_gradient_v(int(self._rect.x), int(bg_y), int(self._rect.width), int(half_height),
                                 transparent, center_color)
    rl.draw_rectangle_gradient_v(int(self._rect.x), int(bg_y + half_height), int(self._rect.width), int(half_height),
                                 center_color, transparent)

  def _draw_icons(self, alert_layout: AlertLayout) -> None:
    if alert_layout.icon is None:
      return

    if time.monotonic() - self._turn_signal_timer > TURN_SIGNAL_BLINK_PERIOD:
      self._turn_signal_timer = time.monotonic()
      self._turn_signal_alpha_filter.x = 255 * 2
    else:
      self._turn_signal_alpha_filter.update(255 * 0.2)

    if alert_layout.icon.side == 'left':
      pos_x = int(self._rect.x + alert_layout.icon.margin_x)
    else:
      pos_x = int(self._rect.x + self._rect.width - alert_layout.icon.margin_x - alert_layout.icon.texture.width)

    if alert_layout.icon.texture not in (self._txt_turn_signal_left, self._txt_turn_signal_right):
      icon_alpha = alert_layout.icon.alpha
    else:
      icon_alpha = int(min(self._turn_signal_alpha_filter.x, 255))

    rl.draw_texture_ex(alert_layout.icon.texture, rl.Vector2(pos_x, self._rect.y + alert_layout.icon.margin_y), 0.0, 1.0,
                       rl.Color(255, 255, 255, int(icon_alpha * self._alpha_filter.x)))

  def _draw_background(self, alert: Alert) -> None:
    # draw top gradient for alert text at top
    event_name = alert.alert_type.split('/')[0] if alert.alert_type else ''
    if event_name in AUTO_HOLD_EVENT_NAMES or event_name in PARKING_BRAKE_EVENT_NAMES:
      return

    color = ALERT_COLORS.get(alert.status, ALERT_COLORS[AlertStatus.normal])
    color = rl.Color(color.r, color.g, color.b, int(255 * 0.90 * self._alpha_filter.x))
    translucent_color = rl.Color(color.r, color.g, color.b, int(0 * self._alpha_filter.x))

    small_alert_height = round(self._rect.height * 0.583) # 140px at mici height
    medium_alert_height = round(self._rect.height * 0.833) # 200px at mici height

    # alert_type format is "EventName/eventType" (e.g., "preLaneChangeLeft/warning")
    if event_name == 'preLaneChangeLeft':
      bg_height = small_alert_height
    elif event_name == 'preLaneChangeRight':
      bg_height = small_alert_height
    elif event_name == 'laneChange':
      bg_height = small_alert_height
    elif event_name in ('laneChangeBlocked', 'laneChangeUnavailable'):
      bg_height = medium_alert_height
    else:
      bg_height = int(self._rect.height)

    solid_height = round(bg_height * 0.2)
    rl.draw_rectangle(int(self._rect.x), int(self._rect.y), int(self._rect.width), solid_height, color)
    rl.draw_rectangle_gradient_v(int(self._rect.x), int(self._rect.y + solid_height), int(self._rect.width),
                                 int(bg_height - solid_height),
                                 color, translucent_color)

  def _draw_text(self, alert: Alert, alert_layout: AlertLayout) -> None:
    icon_side = alert_layout.icon.side if alert_layout.icon is not None else None
    event_name = alert.alert_type.split('/')[0] if alert.alert_type else ''
    preserve_case = event_name == 'reverseGear' or alert.has_mici_override

    # TODO: hack
    alert_text1 = alert.text1 if preserve_case else alert.text1.lower().replace('calibrating: ', 'calibrating:\n')
    can_draw_second_line = False
    # TODO: there should be a common way to determine font size based on text length to maximize rect
    if alert.title_font_px is not None:
      can_draw_second_line = bool(alert.text2)
      font_size = alert.title_font_px
    elif len(alert_text1) <= 12:
      can_draw_second_line = True
      font_size = 92 - 10
    elif len(alert_text1) <= 16:
      can_draw_second_line = True
      font_size = 70
    else:
      font_size = 64 - 10

    if icon_side is not None and alert.title_font_px is None:
      font_size -= 10

    color = rl.Color(255, 255, 255, int(255 * 0.9 * self._alpha_filter.x))

    text1_y_offset = 11 if font_size >= 70 else 4
    text_rect1 = rl.Rectangle(
      alert_layout.text_rect.x,
      alert_layout.text_rect.y - text1_y_offset,
      alert_layout.text_rect.width,
      alert_layout.text_rect.height,
    )
    self._alert_text1_label.set_text(alert_text1)
    self._alert_text1_label.set_text_color(color)
    self._alert_text1_label.set_font_size(font_size)
    self._alert_text1_label.set_alignment(rl.GuiTextAlignment.TEXT_ALIGN_LEFT if icon_side != 'left' else rl.GuiTextAlignment.TEXT_ALIGN_RIGHT)
    self._alert_text1_label.render(text_rect1)

    alert_text2 = alert.text2 if preserve_case else alert.text2.lower()

    # randomize chars and length for testing
    if DEBUG:
      if time.monotonic() - self._text_gen_time > 0.5:
        self._alert_text2_gen = ''.join(random.choices(string.ascii_lowercase + ' ', k=random.randint(0, 40)))
        self._text_gen_time = time.monotonic()
      alert_text2 = self._alert_text2_gen or alert_text2

    if can_draw_second_line and alert_text2:
      last_line_h = self._alert_text1_label.rect.y + self._alert_text1_label.get_content_height(int(alert_layout.text_rect.width))
      last_line_h -= 4
      if alert.subtitle_font_px is not None:
        small_font_size = alert.subtitle_font_px
      elif len(alert_text2) > 18:
        small_font_size = 36
      elif len(alert_text2) > 24:
        small_font_size = 32
      else:
        small_font_size = 40
      text_rect2 = rl.Rectangle(
        alert_layout.text_rect.x,
        last_line_h,
        alert_layout.text_rect.width,
        alert_layout.text_rect.height - last_line_h
      )
      color = rl.Color(255, 255, 255, int(255 * 0.65 * self._alpha_filter.x))

      self._alert_text2_label.set_text(alert_text2)
      self._alert_text2_label.set_text_color(color)
      self._alert_text2_label.set_font_size(small_font_size)
      self._alert_text2_label.set_alignment(rl.GuiTextAlignment.TEXT_ALIGN_LEFT if icon_side != 'left' else rl.GuiTextAlignment.TEXT_ALIGN_RIGHT)
      self._alert_text2_label.render(text_rect2)
