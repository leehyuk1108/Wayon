MIN_STANDSTILL_DISPLAY_SECONDS = 60.0
PARKING_BRAKE_EVENT_NAMES = ("parkBrake", "silentParkBrake")


def _elapsed_seconds(elapsed: float | int) -> int:
  return max(0, int(elapsed))


def format_mmss(elapsed: float | int) -> str:
  seconds = _elapsed_seconds(elapsed)
  return f"{seconds // 60:02d}:{seconds % 60:02d}"


def format_duration_words(total_seconds: float | int) -> tuple[str, str]:
  seconds = _elapsed_seconds(total_seconds)
  minutes = seconds // 60
  remaining_seconds = seconds % 60
  minute_text = f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"
  second_text = f"{remaining_seconds} second" if remaining_seconds == 1 else f"{remaining_seconds} seconds"
  return minute_text, second_text


def should_show_standstill_timer(*, enabled: bool, started: bool, in_reverse: bool, is_driver_stream: bool,
                                 standstill: bool, seconds_since_started: float,
                                 standstill_duration: float | int) -> bool:
  return (
    enabled and
    started and
    not in_reverse and
    not is_driver_stream and
    standstill and
    seconds_since_started >= MIN_STANDSTILL_DISPLAY_SECONDS and
    _elapsed_seconds(standstill_duration) > 0
  )


def should_show_parking_brake_timer(*, parking_brake_active: bool, alert_event_name: str) -> bool:
  return parking_brake_active and (not alert_event_name or alert_event_name in PARKING_BRAKE_EVENT_NAMES)
