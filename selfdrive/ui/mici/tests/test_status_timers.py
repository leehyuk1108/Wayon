from openpilot.selfdrive.ui.mici.onroad.status_timers import (
  format_mmss,
  should_show_parking_brake_timer,
)


def test_format_mmss_clamps_negative_elapsed_time():
  assert format_mmss(-3) == "00:00"


def test_format_mmss_uses_minutes_and_seconds():
  assert format_mmss(125) == "02:05"


def test_parking_brake_timer_only_draws_without_conflicting_alert():
  assert should_show_parking_brake_timer(parking_brake_active=True, alert_event_name="")
  assert should_show_parking_brake_timer(parking_brake_active=True, alert_event_name="parkBrake")
  assert should_show_parking_brake_timer(parking_brake_active=True, alert_event_name="silentParkBrake")
  assert not should_show_parking_brake_timer(parking_brake_active=True, alert_event_name="steerSaturated")
  assert not should_show_parking_brake_timer(parking_brake_active=False, alert_event_name="")
