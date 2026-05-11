import pyray as rl
import math
import cereal.messaging as messaging
from openpilot.selfdrive.ui.mici.layouts.home import MiciHomeLayout
from openpilot.selfdrive.ui.mici.layouts.settings.settings import SettingsLayout
from openpilot.selfdrive.ui.mici.layouts.offroad_alerts import MiciOffroadAlerts
from openpilot.selfdrive.ui.mici.onroad.augmented_road_view import AugmentedRoadView
from openpilot.selfdrive.ui.ui_state import device, ui_state
from openpilot.selfdrive.ui.mici.layouts.onboarding import OnboardingWindow
from openpilot.system.ui.widgets.scroller import Scroller
from openpilot.system.ui.lib.scroll_panel2 import ScrollState
from openpilot.system.ui.lib.application import gui_app


ONROAD_DELAY = 2.5  # seconds
FADE_DURATION = 0.55  # seconds
SCREEN_WAKE_FADE_DURATION = 0.85  # seconds
SCREEN_SLEEP_FADE_DURATION = 0.85  # seconds
OFFROAD_SNAP_EPS = 2.0  # px

SURFACE_OFFROAD = "offroad"
SURFACE_ONROAD = "onroad"


class MiciMainLayout(Scroller):
  def __init__(self):
    super().__init__(snap_items=True, spacing=0, pad=0, scroll_indicator=False, edge_shadows=False)

    self._pm = messaging.PubMaster(['bookmarkButton'])

    self._prev_onroad = False
    self._prev_standstill = False
    self._prev_active_alerts = 0
    self._onroad_time_delay: float | None = None
    self._trip_distance_m = 0.0
    self._trip_duration_s = 0.0
    self._trip_last_sample_time: float | None = None
    self._setup = False

    # Initialize widgets
    self._home_layout = MiciHomeLayout()
    self._alerts_layout = MiciOffroadAlerts()
    self._settings_layout = SettingsLayout()
    self._onroad_layout = self._child(AugmentedRoadView(bookmark_callback=self._on_bookmark_clicked))

    # Initialize widget rects
    for widget in (self._home_layout, self._settings_layout, self._alerts_layout, self._onroad_layout):
      widget.set_rect(rl.Rectangle(0, 0, gui_app.width, gui_app.height))

    # Keep the original Mici Scroller behavior for offroad alerts <-> home.
    self._scroller.add_widgets([
      self._alerts_layout,
      self._home_layout,
    ])
    self._scroller.set_reset_scroll_at_show(False)

    self._active_surface = SURFACE_OFFROAD
    self._from_surface = SURFACE_OFFROAD
    self._target_surface = SURFACE_OFFROAD
    self._fade_start_time: float | None = None
    self._screen_wake_fade_pending = False
    self._screen_wake_fade_start_time: float | None = None
    self._screen_sleep_fade_start_time: float | None = None

    # Set callbacks
    self._setup_callbacks()

    gui_app.add_nav_stack_tick(self._handle_transitions)
    gui_app.push_widget(self)

    # Start onboarding if terms or training not completed, make sure to push after self
    self._onboarding_window = OnboardingWindow(lambda: gui_app.pop_widgets_to(self))
    if not self._onboarding_window.completed:
      gui_app.push_widget(self._onboarding_window)

  def _setup_callbacks(self):
    self._home_layout.set_callbacks(on_settings=lambda: gui_app.push_widget(self._settings_layout))
    self._scroller.set_enabled(lambda: self.enabled and self._active_surface == SURFACE_OFFROAD and not self._is_transitioning())
    self._scroller.set_scrolling_enabled(lambda: self._active_surface == SURFACE_OFFROAD and not self._is_transitioning())
    self._onroad_layout.set_enabled(lambda: self.enabled and self._active_surface == SURFACE_ONROAD and not self._is_transitioning())
    device.add_interactive_timeout_callback(self._on_interactive_timeout)

  def _is_transitioning(self) -> bool:
    return self._fade_start_time is not None

  def _sync_offroad_scroll(self, smooth: bool = False):
    if smooth:
      target_layout = self._alerts_layout if self._alerts_layout.active_alerts() > 0 else self._home_layout
      self._scroller.scroll_to(target_layout.rect.x, smooth=True)
    else:
      target_offset = 0.0 if self._alerts_layout.active_alerts() > 0 else -self._rect.width
      self._scroller.scroll_panel.set_offset(target_offset)

  def _snap_offroad_scroll(self, force: bool = False):
    if self._active_surface != SURFACE_OFFROAD or self._is_transitioning() or self._scroller.is_auto_scrolling:
      return

    panel = self._scroller.scroll_panel
    current_offset = panel.get_offset()
    target_layout = self._alerts_layout if current_offset > -self._rect.width / 2.0 else self._home_layout
    target_offset = 0.0 if target_layout is self._alerts_layout else -self._rect.width
    if abs(current_offset - target_offset) <= OFFROAD_SNAP_EPS:
      panel.set_offset(target_offset)
      return

    if force or panel.state == ScrollState.STEADY:
      self._scroller.scroll_to(target_layout.rect.x, smooth=True, block_interaction=True)

  def _start_transition(self, surface: str, instant: bool = False, fade_from_black: bool = False):
    if instant or not self._setup:
      self._active_surface = surface
      self._from_surface = surface
      self._target_surface = surface
      self._fade_start_time = None
      return

    if surface == self._target_surface and (self._fade_start_time is not None or surface == self._active_surface):
      return

    self._from_surface = self._active_surface if not fade_from_black else surface
    self._target_surface = surface
    self._fade_start_time = rl.get_time()
    if fade_from_black:
      self._fade_start_time -= FADE_DURATION / 2.0

  def _transition_progress(self) -> float:
    if self._fade_start_time is None:
      return 1.0
    return max(0.0, min(1.0, (rl.get_time() - self._fade_start_time) / FADE_DURATION))

  def _current_render_state(self) -> tuple[str, float]:
    progress = self._transition_progress()
    if progress >= 1.0:
      self._active_surface = self._target_surface
      self._from_surface = self._target_surface
      self._fade_start_time = None
      return self._active_surface, 0.0

    surface = self._from_surface if progress < 0.5 else self._target_surface
    fade_phase = progress * 2.0 if progress < 0.5 else (1.0 - progress) * 2.0
    fade_alpha = fade_phase * fade_phase * (3.0 - 2.0 * fade_phase)
    return surface, fade_alpha

  def _screen_wake_fade_alpha(self) -> float:
    if self._screen_wake_fade_pending and device.awake:
      self._screen_wake_fade_pending = False
      self._screen_wake_fade_start_time = rl.get_time()
      self._screen_sleep_fade_start_time = None

    if self._screen_wake_fade_start_time is None:
      return 0.0

    progress = max(0.0, min(1.0, (rl.get_time() - self._screen_wake_fade_start_time) / SCREEN_WAKE_FADE_DURATION))
    if progress >= 1.0:
      self._screen_wake_fade_start_time = None
      return 0.0

    eased = progress * progress * (3.0 - 2.0 * progress)
    return 1.0 - eased

  def _screen_sleep_fade_alpha(self) -> float:
    if self._screen_sleep_fade_start_time is None:
      return 0.0

    if not getattr(device, "timed_out", True):
      self._screen_sleep_fade_start_time = None
      return 0.0

    progress = max(0.0, min(1.0, (rl.get_time() - self._screen_sleep_fade_start_time) / SCREEN_SLEEP_FADE_DURATION))
    eased = progress * progress * (3.0 - 2.0 * progress)
    return eased

  def _reset_trip_tracking(self):
    self._trip_distance_m = 0.0
    self._trip_duration_s = 0.0
    self._trip_last_sample_time = rl.get_time()

  def _sample_trip_tracking(self, force: bool = False):
    if self._trip_last_sample_time is None:
      self._trip_last_sample_time = rl.get_time()
      return

    now = rl.get_time()
    dt = max(0.0, min(now - self._trip_last_sample_time, 1.0))
    self._trip_last_sample_time = now
    if dt <= 0.0:
      return

    self._trip_duration_s += dt
    if not force and ui_state.sm.recv_frame["carState"] < ui_state.started_frame:
      return

    car_state = ui_state.sm["carState"]
    v_ego_cluster = float(car_state.vEgoCluster)
    v_ego = v_ego_cluster if v_ego_cluster != 0.0 else float(car_state.vEgo)
    if math.isfinite(v_ego):
      self._trip_distance_m += max(0.0, v_ego) * dt

  def _update_trip_tracking(self):
    if ui_state.started:
      self._sample_trip_tracking()

  def _finish_trip_tracking(self):
    self._sample_trip_tracking(force=True)
    self._home_layout.set_trip_summary(self._trip_distance_m, self._trip_duration_s)
    self._trip_last_sample_time = None

  def _render(self, _):
    for widget in (self._home_layout, self._settings_layout, self._alerts_layout, self._onroad_layout):
      widget.set_rect(self._rect)

    if not self._setup:
      self._active_surface = SURFACE_ONROAD if ui_state.started else SURFACE_OFFROAD
      self._from_surface = self._active_surface
      self._target_surface = self._active_surface
      self._prev_onroad = ui_state.started
      self._prev_standstill = ui_state.sm["carState"].standstill
      self._prev_active_alerts = self._alerts_layout.active_alerts()
      if not ui_state.started:
        self._sync_offroad_scroll()
      self._setup = True

    surface, fade_alpha = self._current_render_state()
    if surface == SURFACE_OFFROAD:
      super()._render(self._rect)
      if fade_alpha == 0.0:
        self._snap_offroad_scroll(force=any(ev.left_released for ev in gui_app.mouse_events))
    else:
      self._onroad_layout.render(self._rect)

    screen_fade_alpha = max(fade_alpha, self._screen_wake_fade_alpha(), self._screen_sleep_fade_alpha())
    if screen_fade_alpha > 0.0:
      rl.draw_rectangle_rec(self._rect, rl.Color(0, 0, 0, int(255 * screen_fade_alpha)))

  def _handle_transitions(self):
    # Don't pop if onboarding
    if not self._setup or gui_app.widget_in_stack(self._onboarding_window):
      return

    self._update_trip_tracking()

    if ui_state.started != self._prev_onroad:
      self._prev_onroad = ui_state.started

      # onroad: after delay, pop nav stack and fade to onroad.
      # offroad: fade back to the offroad surface, but don't pop nav stack (can stay in settings).
      if ui_state.started:
        self._reset_trip_tracking()
        self._onroad_time_delay = rl.get_time()
      else:
        self._finish_trip_tracking()
        self._onroad_time_delay = None
        self._sync_offroad_scroll()
        self._start_transition(SURFACE_OFFROAD)

    # FIXME: these two pops can interrupt user interacting in the settings
    if self._onroad_time_delay is not None and rl.get_time() - self._onroad_time_delay >= ONROAD_DELAY:
      gui_app.pop_widgets_to(self, lambda: self._start_transition(SURFACE_ONROAD))
      self._onroad_time_delay = None

    # When car leaves standstill, pop nav stack and fade to onroad
    CS = ui_state.sm["carState"]
    if ui_state.started and not CS.standstill and self._prev_standstill:
      gui_app.pop_widgets_to(self, lambda: self._start_transition(SURFACE_ONROAD))
    if not ui_state.started:
      active_alerts = self._alerts_layout.active_alerts()
      if active_alerts != self._prev_active_alerts:
        self._prev_active_alerts = active_alerts
        self._sync_offroad_scroll(smooth=True)
    self._prev_standstill = CS.standstill

  def _on_interactive_timeout(self):
    # Don't pop if onboarding
    if gui_app.widget_in_stack(self._onboarding_window):
      return

    if ui_state.started:
      # Don't pop if at standstill
      if not ui_state.sm["carState"].standstill:
        gui_app.pop_widgets_to(self, lambda: self._start_transition(SURFACE_ONROAD))
    else:
      delay_sleep_for = getattr(device, "delay_sleep_for", None)
      if delay_sleep_for is not None:
        delay_sleep_for(SCREEN_SLEEP_FADE_DURATION)
      self._screen_sleep_fade_start_time = rl.get_time()
      self._screen_wake_fade_pending = True
      gui_app.pop_widgets_to(self, instant=True)
      self._sync_offroad_scroll()
      self._start_transition(SURFACE_OFFROAD, instant=True)

  def _on_bookmark_clicked(self):
    user_bookmark = messaging.new_message('bookmarkButton')
    user_bookmark.valid = True
    self._pm.send('bookmarkButton', user_bookmark)
