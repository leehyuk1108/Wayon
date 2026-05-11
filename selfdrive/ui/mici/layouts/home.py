import pyray as rl
import time
from collections.abc import Callable
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.label import UnifiedLabel
from openpilot.system.ui.lib.application import FontWeight, MousePos

TRIP_SUMMARY_DISPLAY_SECONDS = 10 * 60


class MiciHomeLayout(Widget):
  def __init__(self):
    super().__init__()
    self._on_settings_click: Callable | None = None
    self._trip_summary_distance_m = 0.0
    self._trip_summary_duration_s = 0.0
    self._trip_summary_expires_at = 0.0

    self._greeting_label = UnifiedLabel("안녕하세요!", font_size=72, font_weight=FontWeight.KOREAN,
                                        alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                        alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE, wrap_text=False)
    self._message_label = UnifiedLabel("안전한 주행 되세요", font_size=40, font_weight=FontWeight.KOREAN, text_color=rl.GRAY,
                                       alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                       alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE, wrap_text=False)
    self._title_label = UnifiedLabel("수고하셨습니다", font_size=30, font_weight=FontWeight.KOREAN, text_color=rl.Color(255, 255, 255, 215),
                                     alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                     alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE, wrap_text=False)
    self._distance_value_label = UnifiedLabel(self._distance_text, font_size=52, font_weight=FontWeight.KOREAN,
                                              alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                              alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE, wrap_text=False)
    self._duration_value_label = UnifiedLabel(self._duration_text, font_size=52, font_weight=FontWeight.KOREAN,
                                              alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                              alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE, wrap_text=False)
    self._distance_caption_label = UnifiedLabel("주행 거리", font_size=18, font_weight=FontWeight.KOREAN, text_color=rl.Color(255, 255, 255, 145),
                                                alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                                alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE, wrap_text=False)
    self._duration_caption_label = UnifiedLabel("주행 시간", font_size=18, font_weight=FontWeight.KOREAN, text_color=rl.Color(255, 255, 255, 145),
                                                alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                                alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE, wrap_text=False)

  def set_callbacks(self, on_settings: Callable | None = None):
    self._on_settings_click = on_settings

  def set_trip_summary(self, distance_m: float, duration_s: float):
    self._trip_summary_distance_m = max(0.0, distance_m)
    self._trip_summary_duration_s = max(0.0, duration_s)
    self._trip_summary_expires_at = time.monotonic() + TRIP_SUMMARY_DISPLAY_SECONDS

  def _show_trip_summary(self) -> bool:
    return time.monotonic() < self._trip_summary_expires_at

  def _distance_text(self) -> str:
    return f"{self._trip_summary_distance_m / 1000.0:.1f}km"

  def _duration_text(self) -> str:
    minutes = max(1, int(round(self._trip_summary_duration_s / 60.0)))
    if minutes >= 60:
      hours = minutes // 60
      remaining_minutes = minutes % 60
      return f"{hours}시간 {remaining_minutes}분"
    return f"{minutes}분"

  def _handle_mouse_release(self, mouse_pos: MousePos):
    if self._on_settings_click:
      self._on_settings_click()

  def _render(self, _):
    content_x = self.rect.x + 18
    content_w = self.rect.width - 36

    if not self._show_trip_summary():
      self._greeting_label.render(rl.Rectangle(content_x, self.rect.y + 28, content_w, 96))
      self._message_label.render(rl.Rectangle(content_x, self.rect.y + 132, content_w, 58))
      return

    title_h = 38
    value_h = 64
    caption_h = 24
    columns_top = self.rect.y + 84
    captions_top = self.rect.y + 146
    column_w = content_w / 2.0
    divider_x = content_x + column_w
    divider_top = self.rect.y + 82
    divider_h = 88

    self._title_label.render(rl.Rectangle(content_x, self.rect.y + 20, content_w, title_h))
    rl.draw_rectangle(int(divider_x), int(divider_top), 2, int(divider_h), rl.Color(255, 255, 255, 32))
    self._distance_value_label.render(rl.Rectangle(content_x, columns_top, column_w, value_h))
    self._duration_value_label.render(rl.Rectangle(divider_x, columns_top, column_w, value_h))
    self._distance_caption_label.render(rl.Rectangle(content_x, captions_top, column_w, caption_h))
    self._duration_caption_label.render(rl.Rectangle(divider_x, captions_top, column_w, caption_h))
