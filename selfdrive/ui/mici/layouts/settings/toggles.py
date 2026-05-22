from cereal import log

from openpilot.system.ui.widgets.scroller import NavScroller
from openpilot.selfdrive.ui.mici.widgets.button import BigParamControl, BigMultiParamToggle, BigToggle
from openpilot.system.ui.lib.application import gui_app
from openpilot.selfdrive.ui.layouts.settings.common import restart_needed_callback
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.starpilot.common.simulation_dm import get_simulation_ignore_phone_dm, put_simulation_ignore_phone_dm

PERSONALITY_TO_INT = log.LongitudinalPersonality.schema.enumerants


class SimulationIgnorePhoneDMControl(BigToggle):
  def __init__(self):
    super().__init__("simulation: ignore phone DM", "", initial_state=get_simulation_ignore_phone_dm(ui_state.params))

  def _handle_mouse_release(self, mouse_pos):
    super()._handle_mouse_release(mouse_pos)
    put_simulation_ignore_phone_dm(self._checked, ui_state.params)

  def refresh(self):
    self.set_checked(get_simulation_ignore_phone_dm(ui_state.params))


class TogglesLayoutMici(NavScroller):
  def __init__(self):
    super().__init__()

    self._personality_toggle = BigMultiParamToggle("driving personality", "LongitudinalPersonality", ["aggressive", "standard", "relaxed"])
    self._safe_mode_btn = BigParamControl("safe mode", "SafeMode", toggle_callback=restart_needed_callback)
    self._experimental_btn = BigParamControl("experimental mode", "ExperimentalMode")
    is_metric_toggle = BigParamControl("use metric units", "IsMetric")
    ldw_toggle = BigParamControl("lane departure warnings", "IsLdwEnabled")
    always_on_dm_toggle = BigParamControl("always-on driver monitor", "AlwaysOnDM")
    simulation_ignore_phone_dm_toggle = SimulationIgnorePhoneDMControl()
    record_front = BigParamControl("record & upload driver camera", "RecordFront", toggle_callback=restart_needed_callback)
    record_mic = BigParamControl("record & upload mic audio", "RecordAudio", toggle_callback=restart_needed_callback)
    enable_openpilot = BigParamControl("enable openpilot", "OpenpilotEnabledToggle", toggle_callback=restart_needed_callback)

    self._scroller.add_widgets([
      self._personality_toggle,
      self._safe_mode_btn,
      self._experimental_btn,
      is_metric_toggle,
      ldw_toggle,
      always_on_dm_toggle,
      simulation_ignore_phone_dm_toggle,
      record_front,
      record_mic,
      enable_openpilot,
    ])

    # Toggle lists
    self._refresh_toggles = (
      ("ExperimentalMode", self._experimental_btn),
      ("SafeMode", self._safe_mode_btn),
      ("IsMetric", is_metric_toggle),
      ("IsLdwEnabled", ldw_toggle),
      ("AlwaysOnDM", always_on_dm_toggle),
      ("SimulationIgnorePhoneDM", simulation_ignore_phone_dm_toggle),
      ("RecordFront", record_front),
      ("RecordAudio", record_mic),
      ("OpenpilotEnabledToggle", enable_openpilot),
    )

    enable_openpilot.set_enabled(lambda: not ui_state.engaged)
    record_front.set_enabled(False if ui_state.params.get_bool("RecordFrontLock") else (lambda: not ui_state.engaged))
    record_mic.set_enabled(lambda: not ui_state.engaged)

    if ui_state.params.get_bool("ShowDebugInfo"):
      gui_app.set_show_touches(True)
      gui_app.set_show_fps(True)

    ui_state.add_engaged_transition_callback(self._update_toggles)

  def _update_state(self):
    super()._update_state()

    if ui_state.sm.updated["selfdriveState"]:
      personality = PERSONALITY_TO_INT[ui_state.sm["selfdriveState"].personality]
      if personality != ui_state.personality and ui_state.started:
        self._personality_toggle.set_value(self._personality_toggle._options[personality])
      ui_state.personality = personality

  def show_event(self):
    super().show_event()
    self._update_toggles()

  def _update_toggles(self):
    ui_state.update_params()
    safe_mode = ui_state.params.get_bool("SafeMode")
    self._experimental_btn.set_enabled(not safe_mode)
    self._personality_toggle.set_enabled(not safe_mode)
    if safe_mode:
      if ui_state.params.get_bool("ExperimentalMode"):
        ui_state.params.put_bool("ExperimentalMode", False)
      if ui_state.params.get("LongitudinalPersonality", return_default=True) != int(log.LongitudinalPersonality.relaxed):
        ui_state.params.put_int("LongitudinalPersonality", int(log.LongitudinalPersonality.relaxed))
      self._experimental_btn.set_checked(False)
      self._personality_toggle.set_value("relaxed")

    # CP gating for experimental mode
    if ui_state.CP is not None:
      if ui_state.has_longitudinal_control:
        self._experimental_btn.set_visible(True)
        self._personality_toggle.set_visible(True)
      else:
        # no long for now
        self._experimental_btn.set_visible(False)
        self._experimental_btn.set_checked(False)
        self._personality_toggle.set_visible(False)
        self._experimental_btn.set_enabled(False)
        self._personality_toggle.set_enabled(False)
        ui_state.params.remove("ExperimentalMode")

    # Refresh toggles from params to mirror external changes
    for _, item in self._refresh_toggles:
      item.refresh()
