from dataclasses import dataclass


AUTO_HOLD_EPB_EXPECTED_SECONDS = 120.0
AUTO_HOLD_SIGNAL_GRACE_SECONDS = 2.0
AUTO_HOLD_TRANSFER_VISIBLE_SECONDS = 4.0
AUTO_HOLD_RELEASE_SPEED_MS = 0.5


@dataclass(frozen=True)
class AutoHoldSessionState:
  active: bool
  elapsed_s: float
  expected_progress: float
  epb_transferred: bool
  epb_transition_age_s: float


class AutoHoldSessionTracker:
  """Owns one stable GM hydraulic-hold session across transient UI/control events."""

  def __init__(self) -> None:
    self._active = False
    self._started_at = 0.0
    self._last_hold_seen_at = 0.0
    self._last_elapsed_s = 0.0
    self._epb_transferred_at: float | None = None

  def reset(self) -> None:
    self._active = False
    self._started_at = 0.0
    self._last_hold_seen_at = 0.0
    self._last_elapsed_s = 0.0
    self._epb_transferred_at = None

  def update(self, now: float, *, hold_requested: bool, epb_closed: bool,
             speed_ms: float, gas_pressed: bool, drivable_gear: bool) -> AutoHoldSessionState:
    now = max(0.0, float(now))

    if self._active and epb_closed:
      self._last_elapsed_s = max(0.0, now - self._started_at)
      self._active = False
      self._epb_transferred_at = now
    elif self._active:
      if hold_requested:
        self._last_hold_seen_at = now

      released = gas_pressed or not drivable_gear or speed_ms > AUTO_HOLD_RELEASE_SPEED_MS
      signal_expired = not hold_requested and now - self._last_hold_seen_at > AUTO_HOLD_SIGNAL_GRACE_SECONDS
      if released or signal_expired:
        self.reset()
    elif hold_requested and not epb_closed and drivable_gear and not gas_pressed:
      self._active = True
      self._started_at = now
      self._last_hold_seen_at = now
      self._last_elapsed_s = 0.0
      self._epb_transferred_at = None

    elapsed_s = max(0.0, now - self._started_at) if self._active else self._last_elapsed_s
    progress = min(1.0, elapsed_s / AUTO_HOLD_EPB_EXPECTED_SECONDS)
    transition_age_s = -1.0
    epb_transferred = False
    if self._epb_transferred_at is not None:
      transition_age_s = max(0.0, now - self._epb_transferred_at)
      epb_transferred = transition_age_s <= AUTO_HOLD_TRANSFER_VISIBLE_SECONDS
      if not epb_transferred:
        self._epb_transferred_at = None
        self._last_elapsed_s = 0.0
        elapsed_s = 0.0
        progress = 0.0

    return AutoHoldSessionState(
      active=self._active,
      elapsed_s=elapsed_s,
      expected_progress=progress,
      epb_transferred=epb_transferred,
      epb_transition_age_s=transition_age_s,
    )
