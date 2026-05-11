import math
import time

import pyray as rl

from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app

BLIND_SPOT_PULSE_MIN_ALPHA = 0.25
BLIND_SPOT_FAST_PULSE_PERIOD = 0.32
BLIND_SPOT_SOLID_ALPHA = 1.0


class BlindSpotIndicators:
  def __init__(self):
    self._txt_blind_spot_left: rl.Texture = gui_app.texture('icons_mici/onroad/blind_spot_left.png', 108, 128)
    self._txt_blind_spot_right: rl.Texture = gui_app.texture('icons_mici/onroad/blind_spot_left.png', 108, 128, flip_x=True)

    self._blind_spot_left_alpha_filter = FirstOrderFilter(0, 0.06, 1 / gui_app.target_fps)
    self._blind_spot_right_alpha_filter = FirstOrderFilter(0, 0.06, 1 / gui_app.target_fps)
    self._blind_spot_left_start_time: float | None = None
    self._blind_spot_right_start_time: float | None = None

  @staticmethod
  def _pulse_alpha(start_time: float) -> float:
    elapsed = time.monotonic() - start_time
    pulse = (math.cos(2.0 * math.pi * elapsed / BLIND_SPOT_FAST_PULSE_PERIOD) + 1.0) / 2.0
    return BLIND_SPOT_PULSE_MIN_ALPHA + (1.0 - BLIND_SPOT_PULSE_MIN_ALPHA) * pulse

  def _update_alpha_filter(self, alpha_filter: FirstOrderFilter, detected: bool, alerting: bool, start_time: float | None) -> float | None:
    if not detected:
      alpha_filter.update(0.0)
      return None

    if alerting:
      if start_time is None:
        start_time = time.monotonic()
      alpha_filter.update(self._pulse_alpha(start_time))
      return start_time

    alpha_filter.update(BLIND_SPOT_SOLID_ALPHA)
    return None

  def update(self) -> None:
    if ui_state.sm.recv_frame["carState"] < ui_state.started_frame:
      return

    car_state = ui_state.sm["carState"]
    self._blind_spot_left_start_time = self._update_alpha_filter(
      self._blind_spot_left_alpha_filter,
      car_state.leftBlindspot,
      car_state.leftBlinker,
      self._blind_spot_left_start_time,
    )
    self._blind_spot_right_start_time = self._update_alpha_filter(
      self._blind_spot_right_alpha_filter,
      car_state.rightBlindspot,
      car_state.rightBlinker,
      self._blind_spot_right_start_time,
    )

  @property
  def detected(self) -> bool:
    return self._blind_spot_left_alpha_filter.x > 0.01 or self._blind_spot_right_alpha_filter.x > 0.01

  def render(self, rect: rl.Rectangle) -> None:
    if not self.detected:
      return

    margin_x = 20
    y_offset = 100

    if self._blind_spot_left_alpha_filter.x > 0.01:
      pos_x = int(rect.x + margin_x)
      pos_y = int(rect.y + y_offset)
      alpha = int(255 * self._blind_spot_left_alpha_filter.x)
      rl.draw_texture_ex(self._txt_blind_spot_left, rl.Vector2(pos_x, pos_y), 0.0, 1.0, rl.Color(255, 255, 255, alpha))

    if self._blind_spot_right_alpha_filter.x > 0.01:
      pos_x = int(rect.x + rect.width - margin_x - self._txt_blind_spot_right.width)
      pos_y = int(rect.y + y_offset)
      alpha = int(255 * self._blind_spot_right_alpha_filter.x)
      rl.draw_texture_ex(self._txt_blind_spot_right, rl.Vector2(pos_x, pos_y), 0.0, 1.0, rl.Color(255, 255, 255, alpha))
