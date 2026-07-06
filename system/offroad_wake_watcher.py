#!/usr/bin/env python3
from __future__ import annotations

import os
import time
from pathlib import Path

from cereal import car
import cereal.messaging as messaging
from opendbc.can.parser import CANParser

from openpilot.common.params import Params


GM_MAKES = {"Buick", "Cadillac", "Chevrolet", "Gmc", "Holden"}
WATCH_BUSES = (0, 1, 2, 128, 130)
POLL_TIMEOUT_MS = 250
WAKE_COOLDOWN_SEC = 10.0
CAN_BURST_QUIET_SEC = 2.0
MIN_CAN_BURST_FRAMES = 8


def raw_memory_param_path(params: Params, key: str) -> Path:
  return Path(params.get_param_path(key))


def get_memory_int(params: Params, key: str, default: int = 0) -> int:
  value = None
  try:
    value = params.get(key, return_default=True)
  except Exception:
    pass

  if value is None:
    try:
      value = raw_memory_param_path(params, key).read_bytes()
    except OSError:
      return default

  try:
    if isinstance(value, (bytes, bytearray)):
      value = value.decode("utf-8", errors="ignore")
    return int(value or default)
  except (TypeError, ValueError):
    return default


def put_memory_int(params: Params, key: str, value: int) -> None:
  data = str(int(value))
  try:
    params.put(key, data)
    return
  except Exception:
    pass

  key_path = raw_memory_param_path(params, key)
  tmp_path = key_path.with_name(f".tmp_{key}_{os.getpid()}")
  try:
    key_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(data)
    os.replace(tmp_path, key_path)
  except OSError:
    try:
      tmp_path.unlink(missing_ok=True)
    except OSError:
      pass


def build_parser(dbc_name: str, messages: list[str], bus: int) -> CANParser:
  return CANParser(dbc_name, [(msg, float("nan")) for msg in messages], bus)


def param_text(params: Params, key: str) -> str:
  try:
    raw = params.get(key, return_default=True)
  except Exception:
    return ""
  return raw.decode("utf-8", errors="ignore") if isinstance(raw, (bytes, bytearray)) else str(raw or "")


def persistent_car_params(params: Params) -> car.CarParams | None:
  try:
    cp_bytes = params.get("CarParamsPersistent")
  except Exception:
    return None
  if cp_bytes is None:
    return None
  try:
    return messaging.log_from_bytes(cp_bytes, car.CarParams)
  except Exception:
    return None


def is_gm_make(params: Params) -> bool:
  make = param_text(params, "CarMake")
  if make:
    return make in GM_MAKES or make.lower() == "gm"

  CP = persistent_car_params(params)
  if CP is None:
    return False

  brand = getattr(CP, "brand", "")
  car_name = getattr(CP, "carName", "")
  return brand.lower() == "gm" or car_name.lower() == "gm"


def ignition_on(panda_states) -> bool:
  return any(state.ignitionLine or state.ignitionCan for state in panda_states)


def parser_active(parsers: list[CANParser], parser_input) -> bool:
  active = False
  for cp in parsers:
    cp.update(parser_input)

    if "Door_Open_Switch_Status_LS" in cp.vl:
      door_vals = cp.vl["Door_Open_Switch_Status_LS"]
      active |= bool(door_vals.get("DrDoorOpenSwAct", 0))
      active |= bool(door_vals.get("PsDoorOpenSwAct", 0))

    if "Door_Handle_Switch_Status_LS" in cp.vl:
      handle_vals = cp.vl["Door_Handle_Switch_Status_LS"]
      active |= any(bool(handle_vals.get(signal, 0)) for signal in (
        "DrvDrHndleSwAtv",
        "PasDrHndleSwAtv",
        "RLDrHndleSwAtv",
        "RRDrHndleSwAtv",
        "RCHndleSwAtv",
      ))

    if "DriverDoorStatus" in cp.vl:
      active |= bool(cp.vl["DriverDoorStatus"].get("DriverDoorOpened", 0))

    if "BCMDoorBeltStatus" in cp.vl:
      door_vals = cp.vl["BCMDoorBeltStatus"]
      active |= any(bool(door_vals.get(signal, 0)) for signal in (
        "FrontLeftDoor",
        "FrontRightDoor",
        "RearLeftDoor",
        "RearRightDoor",
      ))

  return active


def main() -> None:
  params = Params()
  params_memory = Params()

  modern_parsers = [
    build_parser("gm_global_a_lowspeed_1818125", ["Door_Open_Switch_Status_LS", "Door_Handle_Switch_Status_LS"], bus)
    for bus in WATCH_BUSES
  ]
  legacy_parsers = [
    build_parser("gm_global_a_lowspeed", ["DriverDoorStatus"], bus)
    for bus in WATCH_BUSES
  ]
  bcm_parsers = [
    build_parser("gm_global_a_powertrain_generated", ["BCMDoorBeltStatus"], bus)
    for bus in (0, 128)
  ]

  sm = messaging.SubMaster(["deviceState", "pandaStates", "can"])

  last_active = False
  last_trigger_time = 0.0
  last_can_activity_time = 0.0
  last_counter = get_memory_int(params_memory, "OffroadWakeCounter")

  while True:
    sm.update(POLL_TIMEOUT_MS)
    now = time.monotonic()

    if not is_gm_make(params):
      last_active = False
      continue

    if bool(sm["deviceState"].started) or ignition_on(sm["pandaStates"]):
      last_active = False
      continue

    can_msgs = sm["can"] if sm.updated["can"] else []
    if not can_msgs:
      continue

    parser_frames = [(int(msg.address), bytes(msg.dat), int(msg.src)) for msg in can_msgs]
    parser_input = [(time.monotonic_ns(), parser_frames)]
    active = (
      parser_active(modern_parsers, parser_input) or
      parser_active(legacy_parsers, parser_input) or
      parser_active(bcm_parsers, parser_input)
    )

    watched_can_frames = sum(1 for msg in can_msgs if int(msg.src) in WATCH_BUSES)
    burst_active = watched_can_frames >= MIN_CAN_BURST_FRAMES and (now - last_can_activity_time) >= CAN_BURST_QUIET_SEC
    if watched_can_frames > 0:
      last_can_activity_time = now

    should_wake = active or burst_active
    if should_wake and not last_active and (now - last_trigger_time) >= WAKE_COOLDOWN_SEC:
      last_counter += 1
      put_memory_int(params_memory, "OffroadWakeCounter", last_counter)
      last_trigger_time = now

    last_active = should_wake


if __name__ == "__main__":
  main()
