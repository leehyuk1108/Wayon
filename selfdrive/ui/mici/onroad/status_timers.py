PARKING_BRAKE_EVENT_NAMES = ("parkBrake", "silentParkBrake")
AUTO_HOLD_EVENT_NAMES = ("resumeRequired", "brakeHold", "silentBrakeHold")


def _elapsed_seconds(elapsed: float | int) -> int:
  return max(0, int(elapsed))


def format_mmss(elapsed: float | int) -> str:
  seconds = _elapsed_seconds(elapsed)
  return f"{seconds // 60:02d}:{seconds % 60:02d}"


def should_show_parking_brake_timer(*, parking_brake_active: bool, alert_event_name: str) -> bool:
  return parking_brake_active and (not alert_event_name or alert_event_name in PARKING_BRAKE_EVENT_NAMES)


def should_show_auto_hold_timer(*, brake_hold_active: bool, alert_event_name: str, has_alert: bool) -> bool:
  return alert_event_name in AUTO_HOLD_EVENT_NAMES or (brake_hold_active and not has_alert)
