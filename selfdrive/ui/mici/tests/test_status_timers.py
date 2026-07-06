from openpilot.selfdrive.ui.mici.onroad.status_timers import (
  format_duration_words,
  format_mmss,
  should_show_parking_brake_timer,
  should_show_standstill_timer,
)


def test_format_mmss_clamps_negative_elapsed_time():
  assert format_mmss(-3) == "00:00"


def test_format_mmss_uses_minutes_and_seconds():
  assert format_mmss(125) == "02:05"


def test_format_duration_words_uses_singular_and_plural_labels():
  assert format_duration_words(61) == ("1 minute", "1 second")
  assert format_duration_words(125) == ("2 minutes", "5 seconds")


def test_standstill_timer_waits_until_started_for_one_minute():
  assert not should_show_standstill_timer(
    enabled=True,
    started=True,
    in_reverse=False,
    is_driver_stream=False,
    standstill=True,
    seconds_since_started=59.9,
    standstill_duration=120,
  )
  assert should_show_standstill_timer(
    enabled=True,
    started=True,
    in_reverse=False,
    is_driver_stream=False,
    standstill=True,
    seconds_since_started=60.0,
    standstill_duration=1,
  )


def test_standstill_timer_hides_when_not_normal_forward_onroad():
  base = dict(
    enabled=True,
    started=True,
    in_reverse=False,
    is_driver_stream=False,
    standstill=True,
    seconds_since_started=90.0,
    standstill_duration=30,
  )

  assert not should_show_standstill_timer(**(base | {"enabled": False}))
  assert not should_show_standstill_timer(**(base | {"started": False}))
  assert not should_show_standstill_timer(**(base | {"in_reverse": True}))
  assert not should_show_standstill_timer(**(base | {"is_driver_stream": True}))
  assert not should_show_standstill_timer(**(base | {"standstill": False}))


def test_parking_brake_timer_only_draws_without_conflicting_alert():
  assert should_show_parking_brake_timer(parking_brake_active=True, alert_event_name="")
  assert should_show_parking_brake_timer(parking_brake_active=True, alert_event_name="parkBrake")
  assert should_show_parking_brake_timer(parking_brake_active=True, alert_event_name="silentParkBrake")
  assert not should_show_parking_brake_timer(parking_brake_active=True, alert_event_name="steerSaturated")
  assert not should_show_parking_brake_timer(parking_brake_active=False, alert_event_name="")
