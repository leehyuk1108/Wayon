from openpilot.selfdrive.car.auto_hold_session import (
  AUTO_HOLD_EPB_EXPECTED_SECONDS,
  AUTO_HOLD_SIGNAL_GRACE_SECONDS,
  AUTO_HOLD_TRANSFER_VISIBLE_SECONDS,
  AutoHoldSessionTracker,
)


def update(tracker, now, **kwargs):
  defaults = dict(hold_requested=True, epb_closed=False, speed_ms=0.0,
                  gas_pressed=False, drivable_gear=True)
  defaults.update(kwargs)
  return tracker.update(now, **defaults)


def test_session_timer_survives_transient_hold_signal_loss():
  tracker = AutoHoldSessionTracker()
  assert update(tracker, 10.0).active
  state = update(tracker, 11.0, hold_requested=False)
  assert state.active
  assert state.elapsed_s == 1.0
  state = update(tracker, 11.5)
  assert state.active
  assert state.elapsed_s == 1.5


def test_session_resets_after_real_release_or_signal_timeout():
  tracker = AutoHoldSessionTracker()
  update(tracker, 10.0)
  assert not update(tracker, 10.1, gas_pressed=True).active

  update(tracker, 20.0)
  state = update(tracker, 20.0 + AUTO_HOLD_SIGNAL_GRACE_SECONDS + 0.01, hold_requested=False)
  assert not state.active
  assert state.elapsed_s == 0.0


def test_epb_transfer_freezes_timer_and_expires_banner():
  tracker = AutoHoldSessionTracker()
  update(tracker, 10.0)
  state = update(tracker, 10.0 + AUTO_HOLD_EPB_EXPECTED_SECONDS, epb_closed=True)
  assert not state.active
  assert state.epb_transferred
  assert state.elapsed_s == AUTO_HOLD_EPB_EXPECTED_SECONDS
  assert state.expected_progress == 1.0

  state = update(tracker, 10.0 + AUTO_HOLD_EPB_EXPECTED_SECONDS + AUTO_HOLD_TRANSFER_VISIBLE_SECONDS + 0.01,
                 hold_requested=False, epb_closed=True)
  assert not state.epb_transferred
  assert state.elapsed_s == 0.0


def test_existing_epb_does_not_start_hydraulic_session():
  tracker = AutoHoldSessionTracker()
  state = update(tracker, 10.0, epb_closed=True)
  assert not state.active
  assert not state.epb_transferred
