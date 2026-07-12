PARKING_BRAKE_EVENT_NAMES = ("parkBrake", "silentParkBrake")


def _elapsed_seconds(elapsed: float | int) -> int:
  return max(0, int(elapsed))


def format_mmss(elapsed: float | int) -> str:
  seconds = _elapsed_seconds(elapsed)
  return f"{seconds // 60:02d}:{seconds % 60:02d}"


def should_show_parking_brake_timer(*, parking_brake_active: bool, alert_event_name: str) -> bool:
  return parking_brake_active and (not alert_event_name or alert_event_name in PARKING_BRAKE_EVENT_NAMES)
