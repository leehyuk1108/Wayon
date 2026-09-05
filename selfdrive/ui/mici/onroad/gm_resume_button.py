from time import monotonic

import pyray as rl

from cereal import car
from openpilot.sunnypilot.selfdrive.controls.lib.gm_manual_resume import manual_resume_eligible, request_manual_resume
from openpilot.system.ui.lib.application import FontWeight, gui_app
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.label import gui_label


RESUME_SERVICES = ("carState", "carControl", "selfdriveState", "longitudinalPlan")
RESUME_CLICK_INTERVAL = 2.5
RESUME_LABEL = "오토리슘"
RESUME_SUBTITLE = "앞차 없이 수동 시험"
REQUEST_QUEUED = "요청 보냄"
REQUEST_UNAVAILABLE = "제어 연결 대기"


def show_manual_resume_button(state) -> bool:
  if not state.started or state.CP is None or not state.sm.all_checks(RESUME_SERVICES):
    return False
  sm = state.sm
  control = sm["carControl"]
  if control.actuators.longControlState != car.CarControl.Actuators.LongControlState.stopping:
    return False
  return manual_resume_eligible(state.CP, sm["carState"], sm["selfdriveState"].enabled,
                                control.longActive, sm["longitudinalPlan"].shouldStop)


class GMResumeButton(Widget):
  """A stationary, explicit test request; controlsd owns all resulting control."""

  def __init__(self, state=None, request=request_manual_resume, clock=monotonic):
    super().__init__()
    if state is None:
      from openpilot.selfdrive.ui.ui_state import ui_state
      state = ui_state
    self._state = state
    self._request = request
    self._clock = clock
    self._eligible = False
    self._press_armed = False
    self._touch_capture = False
    self._capture_until = 0.0
    self._next_request_at = 0.0
    self._status = ""
    self.set_visible(lambda: self._eligible)

  def render_centered(self, rect):
    scale = 2 if rect.height > 500 else 1
    width, height = 220 * scale, 76 * scale
    self.render(rl.Rectangle(rect.x + (rect.width - width) / 2, rect.y + (rect.height - height) / 2, width, height))

  def interacting(self) -> bool:
    return self._touch_capture or self._clock() < self._capture_until

  def consumes_touch(self, pos) -> bool:
    return self.interacting() or (self.is_visible and rl.check_collision_point_rec(pos, self.rect))

  def _update_state(self):
    self._eligible = show_manual_resume_button(self._state)
    if not self._eligible:
      self._press_armed = False
      self._touch_capture = False

  def _can_request(self):
    return self.enabled and show_manual_resume_button(self._state) and self._clock() >= self._next_request_at

  def _handle_mouse_press(self, _):
    self._touch_capture = True
    self._press_armed = self._can_request()

  def _handle_mouse_release(self, _):
    if self._press_armed and self._can_request():
      self._next_request_at = self._clock() + RESUME_CLICK_INTERVAL
      try:
        queued = self._request()
      except OSError:
        queued = False
      self._status = REQUEST_QUEUED if queued else REQUEST_UNAVAILABLE
    self._press_armed = False

  def _process_mouse_events(self):
    super()._process_mouse_events()
    if any(event.slot == 0 and event.left_released for event in gui_app.mouse_events):
      if self._touch_capture:
        # The parent camera processes the same release after this child.
        self._capture_until = self._clock() + 0.1
      self._touch_capture = False
      self._press_armed = False

  def _render(self, rect):
    scale = rect.height / 76
    waiting = self._clock() < self._next_request_at
    background = rl.Color(36, 74, 98, 245) if waiting else rl.Color(18, 101, 152, 245)
    if self.is_pressed:
      background = rl.Color(15, 76, 115, 255)
    rl.draw_rectangle_rounded(rect, 0.25, 10, background)
    rl.draw_rectangle_rounded_lines_ex(rect, 0.25, 10, 2 * scale, rl.Color(145, 212, 247, 255))
    title = self._status if waiting else RESUME_LABEL
    gui_label(rl.Rectangle(rect.x, rect.y + 7 * scale, rect.width, 32 * scale), title,
              font_size=round(26 * scale), font_weight=FontWeight.KOREAN,
              alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER)
    gui_label(rl.Rectangle(rect.x, rect.y + 44 * scale, rect.width, 20 * scale), RESUME_SUBTITLE,
              font_size=round(13 * scale), font_weight=FontWeight.KOREAN,
              color=rl.Color(224, 239, 249, 255), alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER)
