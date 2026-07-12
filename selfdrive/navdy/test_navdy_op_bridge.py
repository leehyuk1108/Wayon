#!/usr/bin/env python3
import sys
import types
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import navdy_op_bridge

openpilot_module = types.ModuleType("openpilot")
openpilot_common_module = types.ModuleType("openpilot.common")
openpilot_realtime_module = types.ModuleType("openpilot.common.realtime")
openpilot_realtime_module.set_core_affinity = lambda cores: None
sys.modules.setdefault("openpilot", openpilot_module)
sys.modules.setdefault("openpilot.common", openpilot_common_module)
sys.modules.setdefault("openpilot.common.realtime", openpilot_realtime_module)

import navdy_power_bridge


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


def test_payload_keeps_pre_enabled_stop_icon_for_cruise_standstill():
  car_state = SimpleNamespace(
    cruiseState=SimpleNamespace(standstill=True, speed=0.0),
    gearShifter="drive",
    standstill=False,
    vCruise=80.0,
    vCruiseCluster=80.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )
  selfdrive_state = SimpleNamespace(active=False, enabled=False, engageable=True, state="preEnabled")

  payload = navdy_op_bridge.payload_from_messages(selfdrive_state, car_state, 8)

  assert payload["state"] == "preEnabled"
  assert payload["standstill"] is True
  assert payload["cruiseStandstill"] is True
  assert payload["setSpeedKph"] == 80.0


def test_payload_hides_stop_icon_while_disengaged_at_standstill():
  car_state = SimpleNamespace(
    cruiseState=SimpleNamespace(standstill=True, speed=0.0),
    gearShifter="drive",
    standstill=True,
    vCruise=80.0,
    vCruiseCluster=80.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )
  selfdrive_state = SimpleNamespace(active=False, enabled=False, engageable=True, state="disabled")

  payload = navdy_op_bridge.payload_from_messages(selfdrive_state, car_state, 9)

  assert payload["standstill"] is False
  assert payload["cruiseStandstill"] is False


def test_payload_shows_stop_icon_while_engaged_at_standstill():
  car_state = SimpleNamespace(
    cruiseState=SimpleNamespace(standstill=False, speed=0.0),
    gearShifter="drive",
    standstill=True,
    vCruise=80.0,
    vCruiseCluster=80.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )
  selfdrive_state = SimpleNamespace(active=True, enabled=True, engageable=True, state="enabled")

  payload = navdy_op_bridge.payload_from_messages(selfdrive_state, car_state, 10)

  assert payload["standstill"] is True
  assert payload["cruiseStandstill"] is True


def test_payload_uses_structured_reverse_alert_when_gear_sample_is_unavailable():
  selfdrive_state = SimpleNamespace(
    active=False,
    enabled=False,
    engageable=False,
    state="disabled",
    alertType="reverseGear/permanent",
  )

  payload = navdy_op_bridge.payload_from_messages(
      selfdrive_state, navdy_op_bridge.default_car_state(), 9)

  assert payload["gear"] == "reverse"


def test_available_services_skips_missing_starpilot_plan():
  messaging = SimpleNamespace(SERVICE_LIST={"selfdriveState": object(), "carStateSP": object()})

  assert navdy_op_bridge.available_services(
      messaging, ["selfdriveState", "carStateSP", "starpilotPlan"]) == ["selfdriveState", "carStateSP"]


def test_car_state_sp_mirror_exports_navdy_vehicle_signals():
  car_state_sp = SimpleNamespace(
    navdyCruiseStandstill=True,
    navdyCruiseSpeed=27.7,
    navdyCruiseSpeedCluster=28.0,
    navdyGearShifter="drive",
    navdyLeftBlinker=True,
    navdyRightBlinker=False,
    navdyLeftBlindspot=True,
    navdyRightBlindspot=False,
    navdyStandstill=True,
    navdyVCruise=99.0,
    navdyVCruiseCluster=100.0,
    navdyVEgo=10.0,
    navdyVEgoCluster=10.5,
  )

  car_state = navdy_op_bridge.car_state_from_sp(car_state_sp)

  assert car_state.gearShifter == "drive"
  assert car_state.vCruiseCluster == 100.0
  assert car_state.standstill is True
  assert car_state.cruiseState.standstill is True
  assert car_state.leftBlinker is True
  assert car_state.leftBlindspot is True


def test_navdy_bridge_avoids_saturated_car_state_service():
  assert navdy_op_bridge.NAVDY_CAR_STATE_SERVICE == "carStateSP"


def test_live_payload_ready_uses_recent_messages_not_alive_flags():
  sm = SimpleNamespace(
    alive={"selfdriveState": False, "carStateSP": False},
    recv_time={"selfdriveState": 10.0, "carStateSP": 10.1},
    seen={"selfdriveState": True, "carStateSP": True},
  )

  assert navdy_op_bridge.live_payload_ready(sm, True, now=10.2)
  assert not navdy_op_bridge.live_payload_ready(sm, True, now=11.2)


def test_live_payload_ready_allows_missing_car_state_when_selfdrive_is_recent():
  sm = SimpleNamespace(
    alive={"selfdriveState": False, "carStateSP": False},
    recv_time={"selfdriveState": 10.0, "carStateSP": 0.0},
    seen={"selfdriveState": True, "carStateSP": False},
  )

  assert navdy_op_bridge.live_payload_ready(sm, True, now=10.2)


def test_default_car_state_keeps_payload_safe_without_vehicle_sample():
  selfdrive_state = SimpleNamespace(
    active=False,
    alertText1="",
    alertText2="",
    enabled=False,
    engageable=True,
    state="disabled",
  )
  controls_state = SimpleNamespace(vCruiseClusterDEPRECATED=42.0, vCruiseDEPRECATED=0.0)

  payload = navdy_op_bridge.payload_from_messages(
      selfdrive_state, navdy_op_bridge.default_car_state(), 8, controls_state)

  assert payload["vEgoKph"] == 0.0
  assert payload["gear"] == "unknown"
  assert payload["setSpeedKph"] == 42.0


def test_manager_defaults_use_starpilot_socket_transport():
  assert "--socket-transport" in navdy_power_bridge.DEFAULT_ARGS


def test_manager_defaults_match_starpilot_responsiveness():
  assert navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--hz") + 1] == "5"
  assert navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--heartbeat-sec") + 1] == "3"
  assert navdy_power_bridge.DEFAULT_ARGS[navdy_power_bridge.DEFAULT_ARGS.index("--power-on-ensure-sec") + 1] == "5"


def test_should_emit_payload_respects_min_emit_interval():
  args = SimpleNamespace(once=False, min_emit_sec=1.0, heartbeat_sec=5.0)
  payload = {"state": "enabled", "vEgoKph": 10.0}
  changed_payload = {"state": "enabled", "vEgoKph": 11.0}
  last_signature = navdy_op_bridge.payload_signature(payload)

  should_emit, _ = navdy_op_bridge.should_emit_payload(changed_payload, args, 10.5, last_signature, 10.0)
  assert not should_emit

  should_emit, _ = navdy_op_bridge.should_emit_payload(changed_payload, args, 11.1, last_signature, 10.0)
  assert should_emit


def test_manager_child_ignores_inherited_manager_argv():
  assert navdy_power_bridge.should_use_default_args(
      "navdy_bridge", ["manager.py", "--socket-transport"])


if __name__ == "__main__":
  test_payload_exports_standstill_and_op_available()
  test_available_services_skips_missing_starpilot_plan()
  test_live_payload_ready_uses_recent_messages_not_alive_flags()
  test_live_payload_ready_allows_missing_car_state_when_selfdrive_is_recent()
  test_default_car_state_keeps_payload_safe_without_vehicle_sample()
  test_manager_defaults_use_starpilot_socket_transport()
  test_manager_defaults_match_starpilot_responsiveness()
  test_should_emit_payload_respects_min_emit_interval()
  test_manager_child_ignores_inherited_manager_argv()
