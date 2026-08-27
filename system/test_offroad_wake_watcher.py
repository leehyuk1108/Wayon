#!/usr/bin/env python3
from types import SimpleNamespace

from openpilot.system import offroad_wake_watcher


def fake_parser(message, current, updates):
  return SimpleNamespace(vl={message: current}, vl_all={message: updates})


def test_updated_door_state_ignores_cached_values():
  stale_open = fake_parser(
    "BCMDoorBeltStatus",
    {"FrontLeftDoor": 1, "FrontRightDoor": 0, "RearLeftDoor": 0, "RearRightDoor": 0},
    {"FrontLeftDoor": [], "FrontRightDoor": [], "RearLeftDoor": [], "RearRightDoor": []},
  )
  updated_closed = fake_parser(
    "BCMDoorBeltStatus",
    {"FrontLeftDoor": 0, "FrontRightDoor": 0, "RearLeftDoor": 0, "RearRightDoor": 0},
    {"FrontLeftDoor": [0], "FrontRightDoor": [0], "RearLeftDoor": [0], "RearRightDoor": [0]},
  )

  assert offroad_wake_watcher.updated_door_state([stale_open, updated_closed]) is False


def test_updated_door_state_detects_any_updated_door():
  parser = fake_parser(
    "Door_Open_Switch_Status_LS",
    {"DrDoorOpenSwAct": 0, "PsDoorOpenSwAct": 1},
    {"DrDoorOpenSwAct": [0], "PsDoorOpenSwAct": [1]},
  )

  assert offroad_wake_watcher.updated_door_state([parser]) is True
