import pyray as rl

from cereal import custom, log
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.selfdrive.ui import UI_BORDER_SIZE
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import FONT_SCALE, FontWeight, gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.lib.text_measure import measure_text_cached

CIRCULAR_ALERT_ANIMATION_Y = 28.0
STAR_GREEN_LIGHT = int(custom.StarPilotOnroadEvent.EventName.greenLight)
STAR_LEAD_DEPARTING = int(custom.StarPilotOnroadEvent.EventName.leadDeparting)


def _enum_raw(value) -> int:
  return int(getattr(value, "raw", value))


class CircularAlertsRenderer:
  def __init__(self):
    self._green_light_alert_img = gui_app.texture("images/green_light.png", 250, 250)
    self._lead_depart_alert_img = gui_app.texture("images/lead_depart.png", 250, 250)

    self._e2e_alert_display_timer = 0
    self._e2e_alert_frame = 0
    self._green_light_alert = False
    self._lead_depart_alert = False
    self._alert_text = ""
    self._alert_img = None
    self._allow_e2e_alerts = False
    self._alpha_filter = FirstOrderFilter(0.0, 0.08, 1 / gui_app.target_fps)
    self._y_offset_filter = FirstOrderFilter(CIRCULAR_ALERT_ANIMATION_Y, 0.08, 1 / gui_app.target_fps)

  def _starpilot_event_active(self, event_name: int, alert_event_name: str) -> bool:
    sm = ui_state.sm
    if sm.recv_frame.get("starpilotOnroadEvents", -1) >= ui_state.started_frame:
      for event in sm["starpilotOnroadEvents"]:
        if _enum_raw(event.name) == event_name:
          return True

    if sm.recv_frame.get("starpilotSelfdriveState", -1) >= ui_state.started_frame:
      alert_type = sm["starpilotSelfdriveState"].alertType
      if alert_type.split("/", 1)[0] == alert_event_name:
        return True

    return False

  def update(self) -> None:
    sm = ui_state.sm
    green_light_alert = self._starpilot_event_active(STAR_GREEN_LIGHT, "greenLight")
    lead_depart_alert = self._starpilot_event_active(STAR_LEAD_DEPARTING, "leadDeparting")

    self._green_light_alert = green_light_alert
    self._lead_depart_alert = lead_depart_alert
    self._allow_e2e_alerts = (
      sm["selfdriveState"].alertSize == log.SelfdriveState.AlertSize.none and
      sm.recv_frame.get("driverStateV2", -1) > ui_state.started_frame
    )

    if self._green_light_alert or self._lead_depart_alert:
      self._e2e_alert_display_timer = 3 * gui_app.target_fps

    if self._e2e_alert_display_timer > 0:
      self._e2e_alert_frame += 1
      self._e2e_alert_display_timer -= 1

      if self._green_light_alert:
        self._alert_text = tr("GREEN\nLIGHT")
        self._alert_img = self._green_light_alert_img
      elif self._lead_depart_alert:
        self._alert_text = tr("LEAD VEHICLE\nDEPARTING")
        self._alert_img = self._lead_depart_alert_img
    else:
      self._e2e_alert_frame = 0

  def render(self, rect: rl.Rectangle) -> None:
    is_visible = self._allow_e2e_alerts and self._e2e_alert_display_timer > 0
    alpha = self._alpha_filter.update(1.0 if is_visible else 0.0)
    y_offset = self._y_offset_filter.update(0.0 if is_visible else CIRCULAR_ALERT_ANIMATION_Y)

    if alpha <= 0.01:
      return

    e2e_alert_size = 250
    width_adjustment = 100

    x = rect.x + rect.width - e2e_alert_size - width_adjustment - (UI_BORDER_SIZE * 3)
    y = rect.y + rect.height / 2 + 20 + y_offset

    alert_rect = rl.Rectangle(x - e2e_alert_size, y - e2e_alert_size, e2e_alert_size * 2, e2e_alert_size * 2)
    center = rl.Vector2(alert_rect.x + alert_rect.width / 2, alert_rect.y + alert_rect.height / 2)

    is_pulsing = (self._e2e_alert_frame % gui_app.target_fps) < (gui_app.target_fps / 2.5)
    frame_color = rl.Color(255, 255, 255, 75) if is_pulsing else rl.Color(0, 255, 0, 75)

    rl.draw_circle_v(center, e2e_alert_size, self._with_alpha(rl.Color(0, 0, 0, 190), alpha))
    rl.draw_ring(center, e2e_alert_size - 7.5, e2e_alert_size + 7.5, 0, 360, 0, self._with_alpha(frame_color, alpha))

    if self._alert_img:
      img_x = center.x - self._alert_img.width / 2
      img_y = center.y - self._alert_img.height / 2
      rl.draw_texture_ex(self._alert_img, rl.Vector2(img_x, img_y), 0.0, 1.0, self._with_alpha(rl.WHITE, alpha))

    txt_color = rl.Color(255, 255, 255, 255) if is_pulsing else rl.Color(0, 255, 0, 190)
    txt_color = self._with_alpha(txt_color, alpha)
    font = gui_app.font(FontWeight.BOLD)
    text_size = 48
    spacing = 0

    lines = self._alert_text.split("\n")
    bottom_y = (alert_rect.y + alert_rect.height) - (alert_rect.height / 7)
    current_y = bottom_y - (len(lines) * text_size * FONT_SCALE)

    for line in lines:
      measure = measure_text_cached(font, line, text_size, spacing)
      line_x = center.x - measure.x / 2
      rl.draw_text_ex(font, line, rl.Vector2(line_x, current_y), text_size, spacing, txt_color)
      current_y += text_size * FONT_SCALE

  @staticmethod
  def _with_alpha(color: rl.Color, alpha: float) -> rl.Color:
    alpha = max(0.0, min(float(alpha), 1.0))
    if hasattr(color, "r"):
      return rl.Color(color.r, color.g, color.b, int(color.a * alpha))

    r, g, b = color[:3]
    a = color[3] if len(color) > 3 else 255
    return rl.Color(r, g, b, int(a * alpha))
