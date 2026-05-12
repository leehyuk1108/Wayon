import time
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple
import pyray as rl
import random
import string
from dataclasses import dataclass
from cereal import messaging, log, car, custom
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.common.filter_simple import BounceFilter, FirstOrderFilter
from openpilot.system.hardware import TICI
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.label import UnifiedLabel

AlertSize = log.SelfdriveState.AlertSize
AlertStatus = log.SelfdriveState.AlertStatus
StarPilotAlertStatus = custom.StarPilotSelfdriveState.AlertStatus

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
ERROR_LOG_PATH = Path("/data/error_logs/error.txt")

# Constants
ALERT_COLORS = {
  AlertStatus.normal: rl.Color(0, 0, 0, 255),
  AlertStatus.userPrompt: rl.Color(255, 115, 0, 255),
  AlertStatus.critical: rl.Color(255, 0, 21, 255),
}
GREEN_PROMPT_EVENT_TYPE = 'greenPrompt'
GREEN_PROMPT_COLOR = rl.Color(0, 175, 95, 255)
E2E_PROMPT_EVENT_NAMES = ('greenLightAlert', 'leadDepartAlert', 'greenLight', 'leadDeparting')
PARKING_BRAKE_EVENT_NAMES = ('parkBrake', 'silentParkBrake')
STARPILOT_ALERT_STATUS = int(StarPilotAlertStatus.starpilot)

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


# Pre-defined alert instances
ALERT_STARTUP_PENDING = Alert(
  text1="openpilot Unavailable",
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

ALERT_OPENPILOT_CRASHED = Alert(
  text1="openpilot crashed",
  text2="오류 로그를 확인해주세요",
  size=AlertSize.mid,
  status=AlertStatus.critical,
  alert_type="openpilotCrashed",
)


class AlertRenderer(Widget):
  def __init__(self):
    super().__init__()

    self._alert_text1_label = UnifiedLabel(text="", font_size=ALERT_FONT_BIG, font_weight=FontWeight.DISPLAY, line_height=0.86,
                                           letter_spacing=-0.02)
    self._alert_text2_label = UnifiedLabel(text="", font_size=ALERT_FONT_SMALL, font_weight=FontWeight.ROMAN, line_height=0.86,
                                           letter_spacing=0.025)

    self._prev_alert: Alert | None = None
    self._text_gen_time = 0
    self._alert_text2_gen = ''
    self._resume_required_start_time: float | None = None
    self._parking_brake_start_time: float | None = None
    self._last_started_frame = -1

    # animation filters
    # TODO: use 0.1 but with proper alert height calculation
    self._alert_y_filter = BounceFilter(0, 0.1, 1 / gui_app.target_fps)
    self._alpha_filter = FirstOrderFilter(0, 0.05, 1 / gui_app.target_fps)

    self._turn_signal_timer = 0.0
    self._turn_signal_alpha_filter = FirstOrderFilter(0.0, 0.3, 1 / gui_app.target_fps)
    self._last_icon_side: IconSide | None = None

    self._load_icons()
    ui_state.add_offroad_transition_callback(self._reset_timers)

  def _reset_timers(self) -> None:
    self._resume_required_start_time = None
    self._parking_brake_start_time = None

  def _load_icons(self):
    self._txt_turn_signal_left = gui_app.texture('icons_mici/onroad/turn_signal_left.png', 104, 96)
    self._txt_turn_signal_right = gui_app.texture('icons_mici/onroad/turn_signal_left.png', 104, 96, flip_x=True)
    self._txt_autohold = gui_app.texture("icons/autohold.png", AUTOHOLD_ICON_SIZE, AUTOHOLD_ICON_SIZE, keep_aspect_ratio=True)
    self._txt_parking = gui_app.texture("icons/parking.png", AUTOHOLD_ICON_SIZE, AUTOHOLD_ICON_SIZE, keep_aspect_ratio=True)

  @staticmethod
  def _enum_raw(value) -> int:
    return int(getattr(value, "raw", value))

  @staticmethod
  def _event_parts(alert: Alert) -> tuple[str, str]:
    if not alert.alert_type:
      return "", ""
    return (alert.alert_type.split("/", 1) + [""])[:2]

  @staticmethod
  def _is_green_prompt(alert: Alert) -> bool:
    event_name, event_type = AlertRenderer._event_parts(alert)
    return event_type == GREEN_PROMPT_EVENT_TYPE or event_name in E2E_PROMPT_EVENT_NAMES or alert.status == STARPILOT_ALERT_STATUS

  def _get_starpilot_alert(self, sm: messaging.SubMaster) -> Alert | None:
    if sm.recv_frame.get("starpilotSelfdriveState", -1) < ui_state.started_frame:
      return None

    ss = sm["starpilotSelfdriveState"]
    if self._enum_raw(ss.alertSize) == 0:
      return None

    return Alert(
      text1=ss.alertText1,
      text2=ss.alertText2,
      size=self._enum_raw(ss.alertSize),
      status=self._enum_raw(ss.alertStatus),
      visual_alert=car.CarControl.HUDControl.VisualAlert.none,
      alert_type=ss.alertType,
    )

  def get_alert(self, sm: messaging.SubMaster) -> Alert | None:
    """Generate the current alert based on selfdrive state."""
    ss = sm['selfdriveState']

    if ERROR_LOG_PATH.is_file():
      self._prev_alert = ALERT_OPENPILOT_CRASHED
      return ALERT_OPENPILOT_CRASHED

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
      if starpilot_alert := self._get_starpilot_alert(sm):
        self._prev_alert = starpilot_alert
        return starpilot_alert
      return None

    # Return current alert
    ret = Alert(text1=ss.alertText1, text2=ss.alertText2, size=ss.alertSize.raw, status=ss.alertStatus.raw,
                visual_alert=ss.alertHudVisual, alert_type=ss.alertType)
    self._prev_alert = ret
    return ret

  def will_render(self) -> tuple[Alert | None, bool]:
    alert = self.get_alert(ui_state.sm)
    return alert or self._prev_alert, alert is None

  def _icon_helper(self, alert: Alert) -> AlertLayout:
    icon_side = None
    txt_icon = None
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
      self._turn_signal_timer = 0.0

    elif event_name == 'laneChangeBlocked':
      self._turn_signal_timer = 0.0

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
    icon_layout = IconLayout(txt_icon, icon_side, icon_margin_x, icon_margin_y) if txt_icon is not None and icon_side is not None else None
    return AlertLayout(text_rect, icon_layout)

  def _render(self, rect: rl.Rectangle) -> bool:
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
    parking_brake_active = ui_state.sm['carState'].parkingBrake
    if parking_brake_active and self._parking_brake_start_time is None:
      self._parking_brake_start_time = time.monotonic()
    elif not parking_brake_active:
      self._parking_brake_start_time = None
    draw_parking_timer = parking_brake_active and (alert is None or event_name in PARKING_BRAKE_EVENT_NAMES)
    has_active_indicator = alert is not None or draw_parking_timer

    # Animate fade and slide in/out
    self._alert_y_filter.update(self._rect.y - 50 if not has_active_indicator else self._rect.y)
    self._alpha_filter.update(0 if not has_active_indicator else 1)

    active_alert = alert
    if alert is None:
      if draw_parking_timer:
        self._prev_alert = None
        self._resume_required_start_time = None
        self._draw_parking_brake_timer(True)
        return True

      # If still animating out, keep the previous alert
      if self._alpha_filter.x > 0.01 and self._prev_alert is not None:
        alert = self._prev_alert
      else:
        self._prev_alert = None
        self._resume_required_start_time = None
        return False

    self._draw_background(alert)

    alert_layout = self._icon_helper(alert)
    event_name = alert.alert_type.split('/')[0] if alert.alert_type else ''
    if event_name == 'resumeRequired':
      self._draw_resume_required(active_alert is not None)
      return True
    if event_name in PARKING_BRAKE_EVENT_NAMES and parking_brake_active:
      self._resume_required_start_time = None
      self._draw_parking_brake_timer(active_alert is not None)
      return True

    if event_name not in E2E_PROMPT_EVENT_NAMES:
      self._resume_required_start_time = None
    self._draw_text(alert, alert_layout)
    self._draw_icons(alert_layout)

    return True

  def _draw_resume_required(self, is_active: bool) -> None:
    if is_active and self._resume_required_start_time is None:
      self._resume_required_start_time = time.monotonic()
    elif self._resume_required_start_time is None:
      return

    elapsed = max(0, int(time.monotonic() - self._resume_required_start_time))
    timer_text = f"{elapsed // 60:02d}:{elapsed % 60:02d}"

    self._draw_center_timer(self._txt_autohold, timer_text, draw_gradient=True)

  def _draw_parking_brake_timer(self, is_active: bool) -> None:
    if is_active and self._parking_brake_start_time is None:
      self._parking_brake_start_time = time.monotonic()
    elif self._parking_brake_start_time is None:
      return

    elapsed = max(0, int(time.monotonic() - self._parking_brake_start_time))
    timer_text = f"{elapsed // 60:02d}:{elapsed % 60:02d}"

    self._draw_center_timer(self._txt_parking, timer_text)

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

    rl.draw_rectangle_gradient_v(
      int(self._rect.x),
      int(bg_y),
      int(self._rect.width),
      int(half_height),
      transparent,
      center_color,
    )
    rl.draw_rectangle_gradient_v(
      int(self._rect.x),
      int(bg_y + half_height),
      int(self._rect.width),
      int(half_height),
      center_color,
      transparent,
    )

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
    if alert.alert_type:
      event_name, event_type = (alert.alert_type.split('/', 1) + [''])[:2]
    else:
      event_name, event_type = '', ''
    color = ALERT_COLORS.get(alert.status, ALERT_COLORS[AlertStatus.normal])
    if event_type == GREEN_PROMPT_EVENT_TYPE or self._is_green_prompt(alert):
      color = GREEN_PROMPT_COLOR
    color = rl.Color(color.r, color.g, color.b, int(255 * 0.90 * self._alpha_filter.x))
    translucent_color = rl.Color(color.r, color.g, color.b, int(0 * self._alpha_filter.x))

    small_alert_height = round(self._rect.height * 0.583) # 140px at mici height
    medium_alert_height = round(self._rect.height * 0.833) # 200px at mici height

    if event_name == 'resumeRequired' or event_name in PARKING_BRAKE_EVENT_NAMES:
      return

    if event_type == GREEN_PROMPT_EVENT_TYPE or event_name in E2E_PROMPT_EVENT_NAMES:
      bg_height = small_alert_height
    elif event_name == 'preLaneChangeLeft':
      bg_height = small_alert_height
    elif event_name == 'preLaneChangeRight':
      bg_height = small_alert_height
    elif event_name == 'laneChange':
      bg_height = small_alert_height
    elif event_name == 'laneChangeBlocked':
      bg_height = medium_alert_height
    else:
      bg_height = int(self._rect.height)

    solid_height = round(bg_height * 0.2)
    bg_y = self._alert_y_filter.x
    rl.draw_rectangle(int(self._rect.x), int(bg_y), int(self._rect.width), solid_height, color)
    rl.draw_rectangle_gradient_v(int(self._rect.x), int(bg_y + solid_height), int(self._rect.width),
                                 int(bg_height - solid_height),
                                 color, translucent_color)

  def _draw_text(self, alert: Alert, alert_layout: AlertLayout) -> None:
    icon_side = alert_layout.icon.side if alert_layout.icon is not None else None
    event_name = alert.alert_type.split('/')[0] if alert.alert_type else ''
    preserve_case = event_name == 'reverseGear'

    # TODO: hack
    alert_text1 = alert.text1 if preserve_case else alert.text1.lower().replace('calibrating: ', 'calibrating:\n')
    can_draw_second_line = False
    # TODO: there should be a common way to determine font size based on text length to maximize rect
    if len(alert_text1) <= 12:
      can_draw_second_line = True
      font_size = 92 - 10
    elif len(alert_text1) <= 16:
      can_draw_second_line = True
      font_size = 70
    else:
      font_size = 64 - 10

    if icon_side is not None:
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
      if len(alert_text2) > 18:
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
