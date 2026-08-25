from cereal import log
from pathlib import Path

from openpilot.system.ui.widgets.scroller import NavScroller
from openpilot.selfdrive.selfdrived.simulation_mode import get_simulation_ignore_phone_dm, put_simulation_ignore_phone_dm
from openpilot.selfdrive.ui.mici.widgets.button import BigParamControl, BigMultiParamToggle, BigToggle
from openpilot.system.ui.lib.application import gui_app
from openpilot.selfdrive.ui.layouts.settings.common import restart_needed_callback
from openpilot.selfdrive.ui.ui_state import ui_state

PERSONALITY_TO_INT = log.LongitudinalPersonality.schema.enumerants
REMOTE_SIMULATION_FLAG = Path("/data/RemoteSimulation")


class SimulationIgnorePhoneDMControl(BigToggle):
  def __init__(self):
    super().__init__("simulation: ignore phone DM", "", initial_state=get_simulation_ignore_phone_dm(ui_state.params))

  def _handle_mouse_release(self, mouse_pos):
    super()._handle_mouse_release(mouse_pos)
    put_simulation_ignore_phone_dm(self._checked, ui_state.params)

  def refresh(self):
    self.set_checked(get_simulation_ignore_phone_dm(ui_state.params))


class RemoteSimulationControl(BigToggle):
  def __init__(self):
    super().__init__("remote simulation", "", initial_state=REMOTE_SIMULATION_FLAG.is_file())

  def _handle_mouse_release(self, mouse_pos):
    super()._handle_mouse_release(mouse_pos)
    try:
      if self._checked:
        REMOTE_SIMULATION_FLAG.touch()
      else:
        REMOTE_SIMULATION_FLAG.unlink(missing_ok=True)
    except OSError:
      self._checked = REMOTE_SIMULATION_FLAG.is_file()

  def refresh(self):
    self.set_checked(REMOTE_SIMULATION_FLAG.is_file())


class TogglesLayoutMici(NavScroller):
  def __init__(self):
    super().__init__()

    self._personality_toggle = BigMultiParamToggle("driving personality", "LongitudinalPersonality", ["aggressive", "standard", "relaxed"])
    self._experimental_btn = BigParamControl("experimental mode", "ExperimentalMode")
    is_metric_toggle = BigParamControl("use metric units", "IsMetric")
    ldw_toggle = BigParamControl("lane departure warnings", "IsLdwEnabled")
    standstill_timer_toggle = BigParamControl("standstill timer", "StandstillTimer")
    always_on_dm_toggle = BigParamControl("always-on driver monitor", "AlwaysOnDM")
    simulation_ignore_phone_dm_toggle = SimulationIgnorePhoneDMControl()
    remote_simulation_toggle = RemoteSimulationControl()
    record_front = BigParamControl("record & upload driver camera", "RecordFront", toggle_callback=restart_needed_callback)
    record_mic = BigParamControl("record & upload mic audio", "RecordAudio", toggle_callback=restart_needed_callback)
    enable_openpilot = BigParamControl("enable sunnypilot", "OpenpilotEnabledToggle", toggle_callback=restart_needed_callback)

    self._scroller.add_widgets([
      self._personality_toggle,
      self._experimental_btn,
      is_metric_toggle,
      ldw_toggle,
      standstill_timer_toggle,
      always_on_dm_toggle,
      simulation_ignore_phone_dm_toggle,
      remote_simulation_toggle,
      record_front,
      record_mic,
      enable_openpilot,
    ])

    # Toggle lists
    self._refresh_toggles = (
      ("ExperimentalMode", self._experimental_btn),
      ("IsMetric", is_metric_toggle),
      ("IsLdwEnabled", ldw_toggle),
      ("StandstillTimer", standstill_timer_toggle),
      ("AlwaysOnDM", always_on_dm_toggle),
      ("SimulationIgnorePhoneDM", simulation_ignore_phone_dm_toggle),
      ("RemoteSimulation", remote_simulation_toggle),
      ("RecordFront", record_front),
      ("RecordAudio", record_mic),
      ("OpenpilotEnabledToggle", enable_openpilot),
    )

    enable_openpilot.set_enabled(lambda: not ui_state.engaged)
    record_front.set_enabled(False if ui_state.params.get_bool("RecordFrontLock") else (lambda: not ui_state.engaged))
    record_mic.set_enabled(lambda: not ui_state.engaged)
    remote_simulation_toggle.set_enabled(lambda: not ui_state.started)

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
        ui_state.params.remove("ExperimentalMode")

    # Refresh toggles from params to mirror external changes
    for _, item in self._refresh_toggles:
      item.refresh()
