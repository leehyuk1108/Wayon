#!/usr/bin/env python3
from types import SimpleNamespace

import navdy_op_bridge


def test_payload_exports_standstill_and_op_available():
  cruise_state = SimpleNamespace(standstill=True, speed=27.7)
  car_state = SimpleNamespace(
    cruiseState=cruise_state,
    gearShifter="drive",
    leftBlinker=False,
    rightBlinker=False,
    leftBlindspot=False,
    rightBlindspot=False,
    standstill=True,
    vCruise=100.0,
    vCruiseCluster=0.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )
  selfdrive_state = SimpleNamespace(
    active=False,
    alertText1="",
    alertText2="",
    enabled=False,
    engageable=True,
    state="preEnabled",
  )

  payload = navdy_op_bridge.payload_from_messages(selfdrive_state, car_state, 7)

  assert payload["standstill"] is True
  assert payload["cruiseStandstill"] is True
  assert payload["opAvailable"] is True
  assert payload["engaged"] is False


def test_available_services_skips_missing_starpilot_plan():
  messaging = SimpleNamespace(SERVICE_LIST={"selfdriveState": object(), "carState": object()})

  assert navdy_op_bridge.available_services(
      messaging, ["selfdriveState", "carState", "starpilotPlan"]) == ["selfdriveState", "carState"]


def test_live_payload_ready_uses_recent_messages_not_alive_flags():
  sm = SimpleNamespace(
    alive={"selfdriveState": False, "carState": False},
    recv_time={"selfdriveState": 10.0, "carState": 10.1},
    seen={"selfdriveState": True, "carState": True},
  )

  assert navdy_op_bridge.live_payload_ready(sm, True, now=10.2)
  assert not navdy_op_bridge.live_payload_ready(sm, True, now=11.2)


def test_no_navdy_power_off_skips_offroad_sleep_command():
  calls = []
  original = navdy_op_bridge.set_navdy_display
  try:
    navdy_op_bridge.set_navdy_display = lambda *args: calls.append(args) or True
    args = SimpleNamespace(manage_navdy_power=True, no_navdy_power_off=True)

    offroad_since, target = navdy_op_bridge.manage_navdy_power(args, False, 12.0, 10.0, True)

    assert offroad_since is None
    assert target is True
    assert calls == []
  finally:
    navdy_op_bridge.set_navdy_display = original


if __name__ == "__main__":
  test_payload_exports_standstill_and_op_available()
  test_available_services_skips_missing_starpilot_plan()
  test_live_payload_ready_uses_recent_messages_not_alive_flags()
  test_no_navdy_power_off_skips_offroad_sleep_command()
