import pyray as rl
from collections.abc import Callable
from openpilot.system.ui.widgets import Widget
from openpilot.system.ui.widgets.label import UnifiedLabel
from openpilot.system.ui.lib.application import FontWeight, MousePos


class MiciHomeLayout(Widget):
  def __init__(self):
    super().__init__()
    self._on_settings_click: Callable | None = None

    self._greeting_label = UnifiedLabel("안녕하세요!", font_size=72, font_weight=FontWeight.KOREAN, alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                       alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE, wrap_text=False)
    self._message_label = UnifiedLabel("안전한 주행 되세요", font_size=40, font_weight=FontWeight.KOREAN, text_color=rl.GRAY,
                                       alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                       alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE, wrap_text=False)

  def set_callbacks(self, on_settings: Callable | None = None):
    self._on_settings_click = on_settings

  def _handle_mouse_release(self, mouse_pos: MousePos):
    if self._on_settings_click:
      self._on_settings_click()

  def _render(self, _):
    content_x = self.rect.x + 28
    content_w = self.rect.width - 56

    self._greeting_label.render(rl.Rectangle(content_x, self.rect.y + 28, content_w, 96))
    self._message_label.render(rl.Rectangle(content_x, self.rect.y + 132, content_w, 58))
