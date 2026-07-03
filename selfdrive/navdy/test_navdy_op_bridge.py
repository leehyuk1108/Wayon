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


if __name__ == "__main__":
  test_payload_exports_standstill_and_op_available()
