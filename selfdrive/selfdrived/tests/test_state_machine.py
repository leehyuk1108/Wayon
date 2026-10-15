import pytest

from cereal import log
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.selfdrived.state import StateMachine, SOFT_DISABLE_TIME
from openpilot.selfdrive.selfdrived.events import Events, ET, EVENTS, NormalPermanentAlert

State = log.SelfdriveState.OpenpilotState

# The event types that maintain the current state
MAINTAIN_STATES = {State.enabled: (None,), State.disabled: (None,), State.softDisabling: (ET.SOFT_DISABLE,),
                   State.preEnabled: (ET.PRE_ENABLE,), State.overriding: (ET.OVERRIDE_LATERAL, ET.OVERRIDE_LONGITUDINAL)}
ALL_STATES = tuple(State.schema.enumerants.values())
# The event types checked in DISABLED section of state machine
ENABLE_EVENT_TYPES = (ET.ENABLE, ET.PRE_ENABLE, ET.OVERRIDE_LATERAL, ET.OVERRIDE_LONGITUDINAL)


def make_event(event_types):
  event = {}
  for ev in event_types:
    event[ev] = NormalPermanentAlert("alert")
  EVENTS[0] = event
  return 0


class TestStateMachine:
  def setup_method(self):
    self.events = Events()
    self.state_machine = StateMachine()
    self.state_machine.soft_disable_timer = int(SOFT_DISABLE_TIME / DT_CTRL)

  def test_immediate_disable(self):
    for state in ALL_STATES:
      for et in MAINTAIN_STATES[state]:
        self.events.add(make_event([et, ET.IMMEDIATE_DISABLE]))
        self.state_machine.state = state
        self.state_machine.update(self.events)
        assert State.disabled == self.state_machine.state
        self.events.clear()

  def test_user_disable(self):
    for state in ALL_STATES:
      for et in MAINTAIN_STATES[state]:
        self.events.add(make_event([et, ET.USER_DISABLE]))
        self.state_machine.state = state
        self.state_machine.update(self.events)
        assert State.disabled == self.state_machine.state
        self.events.clear()

  def test_soft_disable(self):
    for state in ALL_STATES:
      if state == State.preEnabled:  # preEnabled considers NO_ENTRY instead
        continue
      for et in MAINTAIN_STATES[state]:
        self.events.add(make_event([et, ET.SOFT_DISABLE]))
        self.state_machine.state = state
        self.state_machine.update(self.events)
        assert self.state_machine.state == State.disabled if state == State.disabled else State.softDisabling
        self.events.clear()

  def test_soft_disable_timer(self):
    self.state_machine.state = State.enabled
    self.events.add(make_event([ET.SOFT_DISABLE]))
    self.state_machine.update(self.events)
    for _ in range(int(SOFT_DISABLE_TIME / DT_CTRL)):
      assert self.state_machine.state == State.softDisabling
      self.state_machine.update(self.events)

    assert self.state_machine.state == State.disabled

  @pytest.mark.parametrize("initial_state", [State.enabled, State.overriding])
  def test_soft_disable_six_second_boundary(self, initial_state):
    assert SOFT_DISABLE_TIME == 6
    self.state_machine.state = initial_state
    self.events.add(make_event([ET.SOFT_DISABLE]))
    assert self.state_machine.update(self.events) == (True, True)
    frames = round(6 / DT_CTRL)
    assert self.state_machine.soft_disable_timer == frames

    for frame in range(1, frames):
      assert self.state_machine.update(self.events) == (True, True)
      assert self.state_machine.state == State.softDisabling
      assert self.state_machine.soft_disable_timer == frames - frame
      assert ET.SOFT_DISABLE in self.state_machine.current_alert_types

    assert self.state_machine.update(self.events) == (False, False)
    assert self.state_machine.state == State.disabled

  def test_soft_disable_recovers_and_new_fault_gets_full_timer(self):
    self.state_machine.state = State.enabled
    self.events.add(make_event([ET.SOFT_DISABLE]))
    self.state_machine.update(self.events)
    for _ in range(round(4 / DT_CTRL)):
      self.state_machine.update(self.events)

    self.events.clear()
    assert self.state_machine.update(self.events) == (True, True)
    assert self.state_machine.state == State.enabled
    assert ET.SOFT_DISABLE not in self.state_machine.current_alert_types

    self.events.add(make_event([ET.SOFT_DISABLE]))
    self.state_machine.update(self.events)
    assert self.state_machine.soft_disable_timer == round(6 / DT_CTRL)

  @pytest.mark.parametrize("event_type", [ET.USER_DISABLE, ET.IMMEDIATE_DISABLE])
  def test_disable_interrupts_extended_soft_disable(self, event_type):
    self.state_machine.state = State.enabled
    self.events.add(make_event([ET.SOFT_DISABLE]))
    self.state_machine.update(self.events)
    for _ in range(round(4 / DT_CTRL)):
      self.state_machine.update(self.events)

    self.events.clear()
    self.events.add(make_event([ET.SOFT_DISABLE, event_type]))
    assert self.state_machine.update(self.events) == (False, False)
    assert self.state_machine.state == State.disabled
    assert event_type in self.state_machine.current_alert_types

  def test_other_alert_does_not_restart_soft_disable_timer(self):
    self.state_machine.state = State.enabled
    self.events.add(make_event([ET.SOFT_DISABLE]))
    self.state_machine.update(self.events)
    for _ in range(round(4 / DT_CTRL)):
      self.state_machine.update(self.events)

    remaining = self.state_machine.soft_disable_timer
    self.events.clear()
    self.events.add(make_event([ET.SOFT_DISABLE, ET.WARNING]))
    for _ in range(remaining - 1):
      assert self.state_machine.update(self.events) == (True, True)
    assert self.state_machine.update(self.events) == (False, False)

  def test_no_entry(self):
    # Make sure noEntry keeps us disabled
    for et in ENABLE_EVENT_TYPES:
      self.events.add(make_event([ET.NO_ENTRY, et]))
      self.state_machine.update(self.events)
      assert self.state_machine.state == State.disabled
      self.events.clear()

  def test_no_entry_pre_enable(self):
    # preEnabled with noEntry event
    self.state_machine.state = State.preEnabled
    self.events.add(make_event([ET.NO_ENTRY, ET.PRE_ENABLE]))
    self.state_machine.update(self.events)
    assert self.state_machine.state == State.preEnabled

  def test_maintain_states(self):
    # Given current state's event type, we should maintain state
    for state in ALL_STATES:
      for et in MAINTAIN_STATES[state]:
        self.state_machine.state = state
        self.events.add(make_event([et]))
        self.state_machine.update(self.events)
        assert self.state_machine.state == state
        self.events.clear()
