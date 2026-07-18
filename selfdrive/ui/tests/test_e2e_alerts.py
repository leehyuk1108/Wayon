from openpilot.selfdrive.ui.sunnypilot.onroad.e2e_alerts import (
  E2EAlertController,
  GREEN_LIGHT_ALERT,
  LEAD_DEPART_ALERT,
)


def test_holds_green_light_alert_for_three_seconds():
  controller = E2EAlertController()

  assert controller.update(True, False, now=10.0) == GREEN_LIGHT_ALERT
  assert controller.update(False, False, now=12.9) == GREEN_LIGHT_ALERT
  assert controller.update(False, False, now=13.0) is None


def test_green_light_has_priority_and_reset_clears_alert():
  controller = E2EAlertController()

  assert controller.update(True, True, now=20.0) == GREEN_LIGHT_ALERT
  assert controller.update(False, True, now=21.0) == LEAD_DEPART_ALERT
  controller.reset()
  assert controller.update(False, False, now=21.1) is None


def test_non_driving_gear_clears_held_alert_immediately():
  controller = E2EAlertController()

  assert controller.update(True, False, now=30.0) == GREEN_LIGHT_ALERT
  assert controller.update(False, False, now=30.1, allowed=False) is None
  assert controller.update(False, False, now=30.2) is None
