import time

import numpy as np
import pyray as rl
from cereal import car, log
from msgq.visionipc import VisionStreamType
from openpilot.selfdrive.ui.ui_state import ui_state, UIStatus
from openpilot.selfdrive.ui.mici.onroad import SIDE_PANEL_WIDTH
from openpilot.selfdrive.ui.mici.onroad.alert_renderer import AlertRenderer
from openpilot.selfdrive.ui.mici.onroad.driver_state import DriverStateRenderer
from openpilot.selfdrive.ui.mici.onroad.hud_renderer import HudRenderer
from openpilot.selfdrive.ui.mici.onroad.model_renderer import ModelRenderer
from openpilot.selfdrive.ui.mici.onroad.confidence_ball import ConfidenceBall
from openpilot.selfdrive.ui.mici.onroad.cameraview import CameraView
from openpilot.selfdrive.ui.mici.onroad.status_timers import format_duration_words, should_show_standstill_timer
from openpilot.system.ui.lib.application import FontWeight, gui_app, MousePos, MouseEvent
from openpilot.system.ui.widgets.label import UnifiedLabel
from openpilot.system.ui.widgets import Widget
from openpilot.common.filter_simple import BounceFilter
from openpilot.common.transformations.camera import DEVICE_CAMERAS, DeviceCameraConfig, view_frame_from_device_frame
from openpilot.common.transformations.orientation import rot_from_euler
from enum import IntEnum

if gui_app.sunnypilot_ui():
  from openpilot.selfdrive.ui.sunnypilot.mici.onroad.hud_renderer import HudRendererSP as HudRenderer
  from openpilot.selfdrive.ui.sunnypilot.ui_state import OnroadTimerStatus

OpState = log.SelfdriveState.OpenpilotState
CALIBRATED = log.LiveCalibrationData.Status.calibrated
ROAD_CAM = VisionStreamType.VISION_STREAM_ROAD
WIDE_CAM = VisionStreamType.VISION_STREAM_WIDE_ROAD
DRIVER_CAM = VisionStreamType.VISION_STREAM_DRIVER
DEFAULT_DEVICE_CAMERA = DEVICE_CAMERAS["tici", "ar0231"]


class BookmarkState(IntEnum):
  HIDDEN = 0
  DRAGGING = 1
  TRIGGERED = 2

WIDE_CAM_MAX_SPEED = 5.0  # m/s (10 mph)
ROAD_CAM_MIN_SPEED = 10  # m/s (25 mph)

CAM_Y_OFFSET = 20
STANDSTILL_ENGAGED_COLOR = rl.Color(0x80, 0xd8, 0xa6, 0xff)
STANDSTILL_EXPERIMENTAL_COLOR = rl.Color(255, 175, 3, 255)
STANDSTILL_TRAFFIC_COLOR = rl.Color(255, 95, 50, 255)


class BookmarkIcon(Widget):
  PEEK_THRESHOLD = 50  # If icon peeks out this much, snap it fully visible
  FULL_VISIBLE_OFFSET = 200  # How far onscreen when fully visible
  HIDDEN_OFFSET = -50  # How far offscreen when hidden

  def __init__(self, bookmark_callback):
    super().__init__()
    self._bookmark_callback = bookmark_callback
    self._icon = gui_app.texture("icons_mici/onroad/bookmark.png", 180, 180)
    self._offset_filter = BounceFilter(0.0, 0.1, 1 / gui_app.target_fps)

    # State
    self._interacting = False
    self._state = BookmarkState.HIDDEN
    self._swipe_start_x = 0.0
    self._swipe_current_x = 0.0
    self._is_swiping = False
    self._is_swiping_left: bool = False
    self._triggered_time: float = 0.0

  def is_swiping_left(self) -> bool:
    """Check if currently swiping left (for scroller to disable)."""
    return self._is_swiping_left

  def interacting(self):
    interacting, self._interacting = self._interacting, False
    return interacting

  def _update_state(self):
    if self._state == BookmarkState.DRAGGING:
      # Allow pulling past activated position with rubber band effect
      swipe_offset = self._swipe_start_x - self._swipe_current_x
      swipe_offset = min(swipe_offset, self.FULL_VISIBLE_OFFSET + 50)
      self._offset_filter.update(swipe_offset)

    elif self._state == BookmarkState.TRIGGERED:
      # Continue animating to fully visible
      self._offset_filter.update(self.FULL_VISIBLE_OFFSET)
      # Stay in TRIGGERED state for 1 second
      if rl.get_time() - self._triggered_time >= 1.5:
        self._state = BookmarkState.HIDDEN

    elif self._state == BookmarkState.HIDDEN:
      self._offset_filter.update(self.HIDDEN_OFFSET)

      if self._offset_filter.x < 1e-3:
        self._interacting = False

  def _handle_mouse_event(self, mouse_event: MouseEvent):
    if not ui_state.started:
      return

    if mouse_event.left_pressed:
      # Store relative position within widget
      self._swipe_start_x = mouse_event.pos.x
      self._swipe_current_x = mouse_event.pos.x
      self._is_swiping = True
      self._is_swiping_left = False
      self._state = BookmarkState.DRAGGING

    elif mouse_event.left_down and self._is_swiping:
      self._swipe_current_x = mouse_event.pos.x
      swipe_offset = self._swipe_start_x - self._swipe_current_x
      self._is_swiping_left = swipe_offset > 0
      if self._is_swiping_left:
        self._interacting = True

    elif mouse_event.left_released:
      if self._is_swiping:
        swipe_distance = self._swipe_start_x - self._swipe_current_x

        # If peeking past threshold, transition to animating to fully visible and bookmark
        if swipe_distance > self.PEEK_THRESHOLD:
          self._state = BookmarkState.TRIGGERED
          self._triggered_time = rl.get_time()
          self._bookmark_callback()
        else:
          # Otherwise, transition back to hidden
          self._state = BookmarkState.HIDDEN

        # Reset swipe state
        self._is_swiping = False
        self._is_swiping_left = False

  def _render(self, _):
    """Render the bookmark icon."""
    if self._offset_filter.x > 0:
      icon_x = self.rect.x + self.rect.width - round(self._offset_filter.x)
      icon_y = self.rect.y + (self.rect.height - self._icon.height) / 2  # Vertically centered
      rl.draw_texture_ex(self._icon, rl.Vector2(icon_x, icon_y), 0.0, 1.0, rl.WHITE)


class StandstillTimerOverlay:
  def __init__(self):
    self._last_started_frame = -1
    self._standstill_duration = 0
    self._standstill_started_at: float | None = None
    self._font_bold = gui_app.font(FontWeight.BOLD)
    self._font_medium = gui_app.font(FontWeight.MEDIUM)

  def _reset(self):
    self._standstill_duration = 0
    self._standstill_started_at = None

  @staticmethod
  def _blend_colors(start: rl.Color, end: rl.Color, transition: float) -> rl.Color:
    transition = float(np.clip(transition, 0.0, 1.0))
    return rl.Color(
      int(start.r + transition * (end.r - start.r)),
      int(start.g + transition * (end.g - start.g)),
      int(start.b + transition * (end.b - start.b)),
      255,
    )

  def _get_duration_color(self) -> rl.Color:
    if self._standstill_duration < 60:
      return STANDSTILL_ENGAGED_COLOR
    if self._standstill_duration < 150:
      transition = (self._standstill_duration - 60) / 90.0
      return self._blend_colors(STANDSTILL_ENGAGED_COLOR, STANDSTILL_EXPERIMENTAL_COLOR, transition)
    if self._standstill_duration < 300:
      transition = (self._standstill_duration - 150) / 150.0
      return self._blend_colors(STANDSTILL_EXPERIMENTAL_COLOR, STANDSTILL_TRAFFIC_COLOR, transition)
    return STANDSTILL_TRAFFIC_COLOR

  def _update_state(self, in_reverse: bool, is_driver_stream: bool) -> bool:
    if not ui_state.started:
      self._last_started_frame = -1
      self._reset()
      return False

    if ui_state.started_frame != self._last_started_frame:
      self._last_started_frame = ui_state.started_frame
      self._reset()

    if ui_state.sm.recv_frame["carState"] < ui_state.started_frame:
      self._reset()
      return False

    car_state = ui_state.sm["carState"]
    if in_reverse or is_driver_stream or not ui_state.standstill_timer or not car_state.standstill:
      self._reset()
      return False

    now = time.monotonic()
    if self._standstill_started_at is None:
      self._standstill_started_at = now
      self._standstill_duration = 0
    else:
      self._standstill_duration = int(now - self._standstill_started_at)

    return should_show_standstill_timer(
      enabled=ui_state.standstill_timer,
      started=ui_state.started,
      in_reverse=in_reverse,
      is_driver_stream=is_driver_stream,
      standstill=car_state.standstill,
      seconds_since_started=now - ui_state.started_time,
      standstill_duration=self._standstill_duration,
    )

  @staticmethod
  def _fit_font_size(font: rl.Font, text: str, initial_size: int, max_width: float, minimum_size: int) -> int:
    font_size = max(initial_size, minimum_size)
    while font_size > minimum_size and rl.measure_text_ex(font, text, font_size, 0).x > max_width:
      font_size -= 2
    return font_size

  def _draw_centered_text(self, rect: rl.Rectangle, text: str, y: float, font: rl.Font, font_size: int,
                          color: rl.Color) -> None:
    text_size = rl.measure_text_ex(font, text, font_size, 0)
    text_pos = rl.Vector2(rect.x + rect.width / 2 - text_size.x / 2, rect.y + y - text_size.y / 2)
    rl.draw_text_ex(font, text, rl.Vector2(text_pos.x + 2, text_pos.y + 2), font_size, 0, rl.Color(0, 0, 0, 170))
    rl.draw_text_ex(font, text, text_pos, font_size, 0, color)

  def _draw_stop_icon(self, rect: rl.Rectangle, y: float, color: rl.Color) -> None:
    center = rl.Vector2(rect.x + rect.width / 2, rect.y + y)
    rl.draw_circle_v(center, 43, rl.Color(0, 0, 0, 150))
    rl.draw_ring(center, 34, 43, 0, 360, 0, color)
    self._draw_centered_text(rl.Rectangle(center.x - 72, center.y - 24, 144, 48), "STOP", 24,
                             self._font_bold, 34, rl.Color(255, 255, 255, 245))

  def render(self, rect: rl.Rectangle, in_reverse: bool, is_driver_stream: bool) -> bool:
    if not self._update_state(in_reverse, is_driver_stream):
      return False

    minute_text, second_text = format_duration_words(self._standstill_duration)
    duration_color = self._get_duration_color()
    max_text_width = max(rect.width - 36, 120)
    minute_font_size = self._fit_font_size(self._font_bold, minute_text, int(rect.height * 0.29), max_text_width, 28)
    second_font_size = self._fit_font_size(self._font_medium, second_text, int(rect.height * 0.13), max_text_width, 16)

    self._draw_stop_icon(rect, rect.height * 0.24, duration_color)
    self._draw_centered_text(rect, minute_text, rect.height * 0.45, self._font_bold, minute_font_size, duration_color)
    self._draw_centered_text(rect, second_text, rect.height * 0.63, self._font_medium, second_font_size,
                             rl.Color(255, 255, 255, 242))
    return True


class AugmentedRoadView(CameraView):
  def __init__(self, bookmark_callback=None, stream_type: VisionStreamType = VisionStreamType.VISION_STREAM_ROAD):
    super().__init__("camerad", stream_type)
    self._bookmark_callback = bookmark_callback
    self._set_placeholder_color(rl.BLACK)

    self.device_camera: DeviceCameraConfig | None = None
    self.view_from_calib = view_frame_from_device_frame.copy()
    self.view_from_wide_calib = view_frame_from_device_frame.copy()

    self._matrix_cache_key: tuple | None = None
    self._cached_matrix: np.ndarray | None = None
    self._content_rect = rl.Rectangle()
    self._last_click_time = 0.0

    # Bookmark icon with swipe gesture
    self._bookmark_icon = BookmarkIcon(bookmark_callback)

    self._model_renderer = ModelRenderer()
    self._hud_renderer = HudRenderer()
    self._alert_renderer = AlertRenderer()
    self._driver_state_renderer = DriverStateRenderer()
    self._confidence_ball = ConfidenceBall()
    self._standstill_timer = StandstillTimerOverlay()
    self._offroad_label = UnifiedLabel("start the car to\nuse sunnypilot", 54, FontWeight.DISPLAY,
                                       text_color=rl.Color(255, 255, 255, int(255 * 0.9)),
                                       alignment=rl.GuiTextAlignment.TEXT_ALIGN_CENTER,
                                       alignment_vertical=rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE)

    self._fade_texture = gui_app.texture("icons_mici/onroad/onroad_fade.png")

  def is_swiping_left(self) -> bool:
    """Check if currently swiping left (for scroller to disable)."""
    return self._bookmark_icon.is_swiping_left()

  def _update_state(self):
    super()._update_state()

    # update offroad label
    if ui_state.panda_type == log.PandaState.PandaType.unknown:
      self._offroad_label.set_text("system booting")
    elif ui_state.ignition and not ui_state.started:
      self._offroad_label.set_text("openpilot can't start\ncheck alerts")
    else:
      self._offroad_label.set_text("start the car to\nuse sunnypilot")

  def _handle_mouse_release(self, mouse_pos: MousePos):
    # Don't trigger click callback if bookmark was triggered
    if not self._bookmark_icon.interacting():
      super()._handle_mouse_release(mouse_pos)

  def _render(self, _):
    # Draw text if not onroad
    if not ui_state.started:
      rl.draw_rectangle_rec(self.rect, rl.BLACK)
      self._offroad_label.render(self._rect)
      return

    self._switch_stream_if_needed(ui_state.sm)

    # Update calibration before rendering
    self._update_calibration()

    # Create inner content area with border padding
    self._content_rect = rl.Rectangle(
      self.rect.x,
      self.rect.y,
      self.rect.width - SIDE_PANEL_WIDTH,
      self.rect.height,
    )

    # Enable scissor mode to clip all rendering within content rectangle boundaries
    # This creates a rendering viewport that prevents graphics from drawing outside the border
    rl.begin_scissor_mode(
      int(self._content_rect.x),
      int(self._content_rect.y),
      int(self._content_rect.width),
      int(self._content_rect.height)
    )

    # Render the base camera view
    super()._render(self._content_rect)

    # Draw all UI overlays
    self._model_renderer.render(self._content_rect)

    # Fade out bottom of overlays for looks
    rl.draw_texture_ex(self._fade_texture, rl.Vector2(self._content_rect.x, self._content_rect.y), 0.0, 1.0, rl.WHITE)

    alert_to_render, not_animating_out = self._alert_renderer.will_render()

    # Hide DMoji when disengaged unless AlwaysOnDM is enabled
    should_draw_dmoji = (not self._hud_renderer.drawing_top_icons() and
                         (ui_state.status != UIStatus.DISENGAGED or ui_state.always_on_dm))
    self._driver_state_renderer.set_should_draw(should_draw_dmoji)
    self._driver_state_renderer.set_position(self._rect.x + 16, self._rect.y + 10)
    self._driver_state_renderer.render()

    self._hud_renderer.set_can_draw_top_icons(alert_to_render is None)
    self._hud_renderer.set_wheel_critical_icon(alert_to_render is not None and not not_animating_out and
                                               alert_to_render.visual_alert == car.CarControl.HUDControl.VisualAlert.steerRequired)
    self._alert_renderer.render(self._content_rect)
    self._hud_renderer.render(self._content_rect)
    parking_brake_timer_visible = self._alert_renderer.parking_brake_timer_visible()
    if not parking_brake_timer_visible:
      self._standstill_timer.render(self._content_rect, self._is_in_reverse(), self.stream_type == DRIVER_CAM)

    # Draw fake rounded border
    rl.draw_rectangle_rounded_lines_ex(self._content_rect, 0.2 * 1.02, 10, 50, rl.BLACK)

    # End clipping region
    rl.end_scissor_mode()

    # Custom UI extension point - add custom overlays here
    # Use self._content_rect for positioning within camera bounds
    self._confidence_ball.render(self.rect)

    self._bookmark_icon.render(self.rect)

  def _switch_stream_if_needed(self, sm):
    if sm['selfdriveState'].experimentalMode and WIDE_CAM in self.available_streams:
      v_ego = sm['carState'].vEgo
      if v_ego < WIDE_CAM_MAX_SPEED:
        target = WIDE_CAM
      elif v_ego > ROAD_CAM_MIN_SPEED:
        target = ROAD_CAM
      else:
        # Hysteresis zone - keep current stream
        target = self.stream_type
    else:
      target = ROAD_CAM

    if self.stream_type != target:
      self.switch_stream(target)

  @staticmethod
  def _is_in_reverse() -> bool:
    if ui_state.sm.recv_frame["carState"] < ui_state.started_frame:
      return False

    try:
      gear = ui_state.sm["carState"].gearShifter
    except Exception:
      return False

    reverse_enum = getattr(car.CarState.GearShifter, "reverse", None)
    if reverse_enum is not None and gear == reverse_enum:
      return True

    return str(gear).split(".")[-1].lower() == "reverse"

  def _update_calibration(self):
    # Update device camera if not already set
    sm = ui_state.sm
    if not self.device_camera and sm.seen['roadCameraState'] and sm.seen['deviceState']:
      self.device_camera = DEVICE_CAMERAS[(str(sm['deviceState'].deviceType), str(sm['roadCameraState'].sensor))]

    # Check if live calibration data is available and valid
    if not (sm.updated["liveCalibration"] and sm.valid['liveCalibration']):
      return

    calib = sm['liveCalibration']
    if len(calib.rpyCalib) != 3 or calib.calStatus != CALIBRATED:
      return

    # Update view_from_calib matrix
    device_from_calib = rot_from_euler(calib.rpyCalib)
    self.view_from_calib = view_frame_from_device_frame @ device_from_calib

    # Update wide calibration if available
    if hasattr(calib, 'wideFromDeviceEuler') and len(calib.wideFromDeviceEuler) == 3:
      wide_from_device = rot_from_euler(calib.wideFromDeviceEuler)
      self.view_from_wide_calib = view_frame_from_device_frame @ wide_from_device @ device_from_calib

  def _calc_frame_matrix(self, rect: rl.Rectangle) -> np.ndarray:
    cache_key = (
      ui_state.sm.recv_frame['liveCalibration'],
      int(self._content_rect.width),
      int(self._content_rect.height),
      self.stream_type,
      round(ui_state.sm['carState'].vEgo, 1),
    )

    if cache_key == self._matrix_cache_key and self._cached_matrix is not None:
      return self._cached_matrix

    # Get camera configuration
    device_camera = self.device_camera or DEFAULT_DEVICE_CAMERA
    is_wide_camera = self.stream_type == WIDE_CAM
    intrinsic = device_camera.ecam.intrinsics if is_wide_camera else device_camera.fcam.intrinsics
    calibration = self.view_from_wide_calib if is_wide_camera else self.view_from_calib
    if is_wide_camera:
      zoom = 0.7 * 1.5
    else:
      zoom = np.interp(ui_state.sm['carState'].vEgo, [10, 30], [0.8, 1.0])

    # Calculate transforms for vanishing point
    inf_point = np.array([1000.0, 0.0, 0.0])
    calib_transform = intrinsic @ calibration
    kep = calib_transform @ inf_point

    # Calculate center points and dimensions
    w, h = self._content_rect.width, self._content_rect.height
    cx, cy = intrinsic[0, 2], intrinsic[1, 2]

    # Calculate max allowed offsets with margins
    margin = 5
    max_x_offset = cx * zoom - w / 2 - margin
    max_y_offset = cy * zoom - h / 2 - margin

    # Calculate and clamp offsets to prevent out-of-bounds issues
    try:
      if abs(kep[2]) > 1e-6:
        x_offset = np.clip((kep[0] / kep[2] - cx) * zoom, -max_x_offset, max_x_offset)
        y_offset = np.clip((kep[1] / kep[2] - cy) * zoom + CAM_Y_OFFSET, -max_y_offset, max_y_offset)
      else:
        x_offset, y_offset = 0, 0
    except (ZeroDivisionError, OverflowError):
      x_offset, y_offset = 0, 0

    # Cache the computed transformation matrix to avoid recalculations
    self._matrix_cache_key = cache_key
    self._cached_matrix = np.array([
      [zoom * 2 * cx / w, 0, -x_offset / w * 2],
      [0, zoom * 2 * cy / h, -y_offset / h * 2],
      [0, 0, 1.0]
    ])

    # built without rect.x/y so cache stays hot during scroll. ModelRenderer adds offset at draw time
    video_transform = np.array([
      [zoom, 0.0, (w / 2 - x_offset) - (cx * zoom)],
      [0.0, zoom, (h / 2 - y_offset) - (cy * zoom)],
      [0.0, 0.0, 1.0]
    ])
    self._model_renderer.set_transform(video_transform @ calib_transform)

    return self._cached_matrix

  def show_event(self):
    if gui_app.sunnypilot_ui():
      ui_state.reset_onroad_sleep_timer(OnroadTimerStatus.RESUME)

  def hide_event(self):
    if gui_app.sunnypilot_ui():
      ui_state.reset_onroad_sleep_timer(OnroadTimerStatus.PAUSE)


if __name__ == "__main__":
  gui_app.init_window("OnRoad Camera View")
  road_camera_view = AugmentedRoadView(lambda: None, stream_type=ROAD_CAM)
  print("***press space to switch camera view***")
  try:
    for _ in gui_app.render():
      ui_state.update()
      if rl.is_key_released(rl.KeyboardKey.KEY_SPACE):
        if WIDE_CAM in road_camera_view.available_streams:
          stream = ROAD_CAM if road_camera_view.stream_type == WIDE_CAM else WIDE_CAM
          road_camera_view.switch_stream(stream)
      road_camera_view.render(rl.Rectangle(0, 0, gui_app.width, gui_app.height))
  finally:
    road_camera_view.close()
