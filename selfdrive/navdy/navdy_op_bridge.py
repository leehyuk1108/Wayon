#!/usr/bin/env python3
"""Read openpilot state and forward compact JSON for Navdy tests.

Run on comma/openpilot root. Default prints JSON lines.
If Navdy enumerates as ADB from comma, add --adb-serial or --adb-path.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import socket
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from typing import Any


KPH_PER_MS = 3.6
DEFAULT_ACTION = "com.navdy.OPENPILOT_STATE"
DEFAULT_COMPONENT = "com.navdy.hud.app/.openpilot.OpenpilotStateReceiver"
DEFAULT_SERVICE_COMPONENT = "com.navdy.hud.app/.openpilot.OpenpilotStateService"
DEFAULT_SOCKET_PORT = 18765
DEFAULT_DEVICE_SOCKET_PORT = 8765
DISPLAY_ON_TEXT = "Display Power: state=ON"
DISPLAY_OFF_TEXT = "Display Power: state=OFF"
WAKEFULNESS_AWAKE_TEXT = "mWakefulness=Awake"
WAKEFULNESS_ASLEEP_TEXT = "mWakefulness=Asleep"
INTERACTIVE_ON_TEXT = "mHalInteractiveModeEnabled=true"
INTERACTIVE_OFF_TEXT = "mHalInteractiveModeEnabled=false"
KEYEVENT_POWER = "26"
KEYEVENT_WAKEUP = "224"
ONROAD_PROCESS_NAMES = (
  "selfdrive.controls.controlsd",
  "selfdrive.selfdrived.selfdrived",
  "selfdrive.car.card",
  "selfdrive.modeld.modeld",
  "./camerad",
)
NAVDY_CAR_STATE_SERVICE = "carStateSP"


def quiet_completed(cmd: list[str], returncode: int = 1) -> subprocess.CompletedProcess:
  return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr="")


def finite_float(value: Any, default: float = 0.0) -> float:
  try:
    value = float(value)
  except (TypeError, ValueError):
    return default
  return value if math.isfinite(value) else default


def rounded(value: float, digits: int = 1) -> float:
  return round(finite_float(value), digits)


def enum_text(value: Any) -> str:
  text = str(value)
  return text.split(".")[-1]


def blinker_text(left: bool, right: bool) -> str:
  if left and right:
    return "hazard"
  if left:
    return "left"
  if right:
    return "right"
  return "off"


def blindspot_text(left: bool, right: bool) -> str:
  if left and right:
    return "both"
  if left:
    return "left"
  if right:
    return "right"
  return "off"


def hold_bool(args: argparse.Namespace, name: str, value: bool, now: float, hold_sec: float) -> bool:
  attr = f"_hold_{name}_until"
  if value:
    setattr(args, attr, now + max(hold_sec, 0.0))
    return True
  return now < float(getattr(args, attr, 0.0))


def stabilize_display_payload(payload: dict[str, Any], args: argparse.Namespace, now: float) -> dict[str, Any]:
  set_speed = finite_float(payload.get("setSpeedKph", 0.0))
  if set_speed > 0.0:
    setattr(args, "_last_set_speed_kph", set_speed)
  elif payload.get("enabled") or payload.get("active") or payload.get("engaged"):
    last_set_speed = finite_float(getattr(args, "_last_set_speed_kph", 0.0))
    if last_set_speed > 0.0:
      payload["setSpeedKph"] = rounded(last_set_speed)

  left_blinker = hold_bool(args, "left_blinker", bool(payload.get("leftBlinker", False)),
                           now, args.blinker_hold_sec)
  right_blinker = hold_bool(args, "right_blinker", bool(payload.get("rightBlinker", False)),
                            now, args.blinker_hold_sec)
  left_blindspot = hold_bool(args, "left_blindspot", bool(payload.get("leftBlindspot", False)),
                             now, args.blindspot_hold_sec)
  right_blindspot = hold_bool(args, "right_blindspot", bool(payload.get("rightBlindspot", False)),
                              now, args.blindspot_hold_sec)

  payload["leftBlinker"] = left_blinker
  payload["rightBlinker"] = right_blinker
  payload["blinkers"] = blinker_text(left_blinker, right_blinker)
  payload["leftBlindspot"] = left_blindspot
  payload["rightBlindspot"] = right_blindspot
  payload["blindspot"] = blindspot_text(left_blindspot, right_blindspot)
  payload["opAvailable"] = bool(payload.get("opAvailable",
                                            payload.get("engageable") or payload.get("enabled") or payload.get("active")))
  payload["standstill"] = bool(payload.get("standstill", payload.get("cruiseStandstill", False)))
  payload["cruiseStandstill"] = bool(payload.get("cruiseStandstill", payload.get("standstill", False)))
  return payload


def reverse_gear_alert_active(selfdrive_state: Any) -> bool:
  alert_type = str(getattr(selfdrive_state, "alertType", "")).split("/", 1)[0]
  return alert_type in ("reverseGear", "silentReverseGear")


def gear_text(car_state: Any, selfdrive_state: Any = None) -> str:
  # The car process may stop publishing a gear sample as soon as reverse takes
  # the system offroad. selfdriveState keeps the structured reverse event alive.
  if reverse_gear_alert_active(selfdrive_state):
    return "reverse"
  return enum_text(getattr(car_state, "gearShifter", "unknown")).lower()


def default_car_state() -> Any:
  return SimpleNamespace(
    cruiseState=SimpleNamespace(standstill=False, speed=0.0, speedCluster=0.0),
    gearShifter="unknown",
    leftBlinker=False,
    rightBlinker=False,
    leftBlindspot=False,
    rightBlindspot=False,
    standstill=False,
    vCruise=0.0,
    vCruiseCluster=0.0,
    vEgo=0.0,
    vEgoCluster=0.0,
  )


def car_state_from_sp(car_state_sp: Any) -> Any:
  return SimpleNamespace(
    cruiseState=SimpleNamespace(
      standstill=bool(getattr(car_state_sp, "navdyCruiseStandstill", False)),
      speed=finite_float(getattr(car_state_sp, "navdyCruiseSpeed", 0.0)),
      speedCluster=finite_float(getattr(car_state_sp, "navdyCruiseSpeedCluster", 0.0)),
    ),
    gearShifter=str(getattr(car_state_sp, "navdyGearShifter", "unknown")),
    leftBlinker=bool(getattr(car_state_sp, "navdyLeftBlinker", False)),
    rightBlinker=bool(getattr(car_state_sp, "navdyRightBlinker", False)),
    leftBlindspot=bool(getattr(car_state_sp, "navdyLeftBlindspot", False)),
    rightBlindspot=bool(getattr(car_state_sp, "navdyRightBlindspot", False)),
    standstill=bool(getattr(car_state_sp, "navdyStandstill", False)),
    vCruise=finite_float(getattr(car_state_sp, "navdyVCruise", 0.0)),
    vCruiseCluster=finite_float(getattr(car_state_sp, "navdyVCruiseCluster", 0.0)),
    vEgo=finite_float(getattr(car_state_sp, "navdyVEgo", 0.0)),
    vEgoCluster=finite_float(getattr(car_state_sp, "navdyVEgoCluster", 0.0)),
  )


def is_cruise_standstill(car_state: Any) -> bool:
  return bool(getattr(getattr(car_state, "cruiseState", None), "standstill", False))


def planner_speed_to_kph(value: Any) -> float:
  speed = finite_float(value, 0.0)
  return speed * KPH_PER_MS if 0.0 < speed < 80.0 else 0.0


def set_speed_kph(car_state: Any, controls_state: Any = None,
                  starpilot_plan: Any = None, longitudinal_plan: Any = None) -> float:
  for holder, names in (
      (car_state, ("vCruiseCluster", "vCruise")),
      (controls_state, ("vCruiseClusterDEPRECATED", "vCruiseDEPRECATED")),
  ):
    for name in names:
      speed = finite_float(getattr(holder, name, 0.0))
      if 0.0 < speed < 255.0:
        return speed

  cruise_state = getattr(car_state, "cruiseState", None)
  for name in ("speedCluster", "speed"):
    speed_ms = finite_float(getattr(cruise_state, name, 0.0))
    if speed_ms > 0.0:
      return speed_ms * KPH_PER_MS

  for holder, name in ((starpilot_plan, "vCruise"), (longitudinal_plan, "vCruiseDEPRECATED")):
    speed = planner_speed_to_kph(getattr(holder, name, 0.0))
    if speed > 0.0:
      return speed

  return 0.0


def payload_from_messages(selfdrive_state: Any, car_state: Any, seq: int,
                          controls_state: Any = None, starpilot_plan: Any = None,
                          longitudinal_plan: Any = None) -> dict[str, Any]:
  left_blinker = bool(getattr(car_state, "leftBlinker", False))
  right_blinker = bool(getattr(car_state, "rightBlinker", False))
  left_blindspot = bool(getattr(car_state, "leftBlindspot", False))
  right_blindspot = bool(getattr(car_state, "rightBlindspot", False))
  enabled = bool(getattr(selfdrive_state, "enabled", False))
  active = bool(getattr(selfdrive_state, "active", False))
  engageable = bool(getattr(selfdrive_state, "engageable", False))
  state = enum_text(getattr(selfdrive_state, "state", "unknown"))
  cruise_standstill = is_cruise_standstill(car_state)
  vehicle_standstill = bool(getattr(car_state, "standstill", False) or cruise_standstill)
  # preEnabled is the stopped engagement-wait state. Otherwise show the stop
  # icon only while openpilot is engaged and the vehicle is stationary.
  show_stop_icon = state == "preEnabled" or ((enabled or active) and vehicle_standstill)

  v_ego_cluster = finite_float(getattr(car_state, "vEgoCluster", 0.0))
  v_ego_ms = finite_float(getattr(car_state, "vEgo", 0.0))
  v_ego_kph = (v_ego_cluster if v_ego_cluster > 0.0 else v_ego_ms) * KPH_PER_MS

  return {
    "schema": "navdy.openpilot.v1",
    "seq": seq,
    "ts": round(time.time(), 3),
    "state": state,
    "enabled": enabled,
    "active": active,
    "engaged": active,
    "disengaged": not enabled,
    "engageable": engageable,
    "opAvailable": engageable,
    "standstill": show_stop_icon,
    "cruiseStandstill": show_stop_icon,
    "setSpeedKph": rounded(set_speed_kph(car_state, controls_state, starpilot_plan, longitudinal_plan)),
    "vEgoKph": rounded(v_ego_kph),
    "gear": gear_text(car_state, selfdrive_state),
    "leftBlinker": left_blinker,
    "rightBlinker": right_blinker,
    "blinkers": blinker_text(left_blinker, right_blinker),
    "leftBlindspot": left_blindspot,
    "rightBlindspot": right_blindspot,
    "blindspot": blindspot_text(left_blindspot, right_blindspot),
    "alertText1": str(getattr(selfdrive_state, "alertText1", "")),
    "alertText2": str(getattr(selfdrive_state, "alertText2", "")),
  }


def synthetic_payload(args: argparse.Namespace, seq: int) -> dict[str, Any]:
  left = (seq % 20) < 5
  right = 10 <= (seq % 20) < 15
  if args.synthetic_left_blindspot or args.synthetic_right_blindspot:
    left_blindspot = args.synthetic_left_blindspot
    right_blindspot = args.synthetic_right_blindspot
  else:
    left_blindspot = 5 <= (seq % 24) < 10
    right_blindspot = 15 <= (seq % 24) < 20
  return {
    "schema": "navdy.openpilot.v1",
    "seq": seq,
    "ts": round(time.time(), 3),
    "state": "enabled",
    "enabled": True,
    "active": True,
    "engaged": True,
    "disengaged": False,
    "engageable": True,
    "opAvailable": True,
    "standstill": args.synthetic_standstill,
    "cruiseStandstill": args.synthetic_standstill,
    "setSpeedKph": 100.0,
    "vEgoKph": 82.0,
    "gear": args.synthetic_gear,
    "leftBlinker": left,
    "rightBlinker": right,
    "blinkers": blinker_text(left, right),
    "leftBlindspot": left_blindspot,
    "rightBlindspot": right_blindspot,
    "blindspot": blindspot_text(left_blindspot, right_blindspot),
    "alertText1": "",
    "alertText2": "",
  }


def send_adb(payload: dict[str, Any], args: argparse.Namespace) -> bool:
  json_payload = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
  shell_cmd = "am broadcast"
  if args.component:
    shell_cmd += " -n " + shlex.quote(args.component)
  shell_cmd += " -a " + shlex.quote(args.action)
  shell_cmd += " --es payload " + shlex.quote(json_payload)
  return run_adb(args, ["shell", shell_cmd]).returncode == 0


def adb_sender_loop(args: argparse.Namespace) -> None:
  cond = getattr(args, "_adb_sender_cond")
  while True:
    with cond:
      while getattr(args, "_adb_sender_pending", None) is None:
        cond.wait()
      payload = getattr(args, "_adb_sender_pending")
      setattr(args, "_adb_sender_pending", None)
    send_adb(payload, args)


def start_adb_sender(args: argparse.Namespace) -> None:
  if not args.adb_path or args.once or args.sync_adb:
    return
  setattr(args, "_adb_sender_pending", None)
  setattr(args, "_adb_sender_cond", threading.Condition())
  thread = threading.Thread(target=adb_sender_loop, args=(args,), daemon=True)
  setattr(args, "_adb_sender_thread", thread)
  thread.start()


def queue_adb(payload: dict[str, Any], args: argparse.Namespace) -> None:
  cond = getattr(args, "_adb_sender_cond", None)
  if cond is None:
    send_adb(payload, args)
    return
  with cond:
    setattr(args, "_adb_sender_pending", dict(payload))
    cond.notify()


def ensure_socket_forward(args: argparse.Namespace) -> None:
  if not args.adb_path:
    return
  run_adb(args, ["forward", f"tcp:{args.socket_port}", f"tcp:{args.device_socket_port}"])
  run_adb(args, ["shell", "am", "startservice", "-n", args.service_component])


def close_socket(args: argparse.Namespace) -> None:
  conn = getattr(args, "_socket_conn", None)
  setattr(args, "_socket_conn", None)
  if conn is not None:
    try:
      conn.close()
    except OSError:
      pass


def connect_socket(args: argparse.Namespace, force: bool = False) -> bool:
  if getattr(args, "_socket_conn", None) is not None:
    return True

  now = time.monotonic()
  last = float(getattr(args, "_last_socket_connect_at", 0.0))
  if not force and now - last < max(args.socket_reconnect_sec, 0.1):
    return False
  setattr(args, "_last_socket_connect_at", now)

  if args.adb_path:
    ensure_socket_forward(args)
  try:
    conn = socket.create_connection((args.socket_host, args.socket_port),
                                    timeout=max(args.socket_timeout_sec, 0.05))
    conn.settimeout(max(args.socket_timeout_sec, 0.05))
  except OSError:
    close_socket(args)
    return False
  setattr(args, "_socket_conn", conn)
  return True


def start_socket_transport(args: argparse.Namespace) -> None:
  if args.socket_transport:
    connect_socket(args, force=True)


def socket_send(payload: dict[str, Any], args: argparse.Namespace) -> bool:
  if not args.socket_transport or not connect_socket(args):
    return False
  json_payload = json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n"
  try:
    getattr(args, "_socket_conn").sendall(json_payload.encode("utf-8"))
    return True
  except OSError:
    close_socket(args)
    if connect_socket(args, force=True):
      try:
        getattr(args, "_socket_conn").sendall(json_payload.encode("utf-8"))
        return True
      except OSError:
        close_socket(args)
  return False


def adb_base_cmd(args: argparse.Namespace) -> list[str]:
  cmd = [args.adb_path]
  if args.adb_server_port > 0:
    cmd += ["-P", str(args.adb_server_port)]
  if args.adb_serial:
    cmd += ["-s", args.adb_serial]
  return cmd


def recover_adb(args: argparse.Namespace, reason: str, force: bool = False) -> None:
  if not args.adb_path:
    return
  now = time.monotonic()
  last = float(getattr(args, "_last_adb_recover_at", 0.0))
  if not force and now - last < max(args.adb_recover_sec, 0.1):
    return
  setattr(args, "_last_adb_recover_at", now)

  base = adb_base_cmd(args)
  try:
    subprocess.run(base + ["start-server"], check=False, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=max(args.adb_timeout_sec, 0.1))
    if args.adb_wait_device_sec > 0.0:
      subprocess.run(base + ["wait-for-device"], check=False, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, timeout=max(args.adb_wait_device_sec, 0.1))
  except subprocess.TimeoutExpired:
    if args.stdout:
      print(f"adb recover timeout reason={reason}", flush=True)


def run_adb(args: argparse.Namespace, adb_args: list[str], capture: bool = False) -> subprocess.CompletedProcess:
  cmd = adb_base_cmd(args) + adb_args
  stdout = subprocess.PIPE if capture else subprocess.DEVNULL
  stderr = subprocess.PIPE if capture else subprocess.DEVNULL
  try:
    proc = subprocess.run(cmd, check=False, stdout=stdout, stderr=stderr, text=True,
                          timeout=max(args.adb_timeout_sec, 0.1))
  except subprocess.TimeoutExpired:
    recover_adb(args, "timeout")
    return quiet_completed(cmd, 124)
  if proc.returncode != 0:
    recover_adb(args, "returncode")
  return proc


def adb_shell(args: argparse.Namespace, shell_args: list[str], capture: bool = False) -> subprocess.CompletedProcess:
  return run_adb(args, ["shell"] + shell_args, capture=capture)


def set_stay_on_while_plugged_in(args: argparse.Namespace, stay_on: bool) -> None:
  if args.adb_path:
    value = "1" if stay_on else "0"
    adb_shell(args, ["settings", "put", "global", "stay_on_while_plugged_in", value])


def navdy_display_on(args: argparse.Namespace) -> bool | None:
  if not args.adb_path:
    return None
  proc = adb_shell(args, ["dumpsys", "power"], capture=True)
  if proc.returncode != 0:
    return None
  text = proc.stdout or ""
  if DISPLAY_OFF_TEXT in text:
    return False
  if WAKEFULNESS_ASLEEP_TEXT in text or INTERACTIVE_OFF_TEXT in text:
    return False
  if DISPLAY_ON_TEXT in text:
    return True
  if WAKEFULNESS_AWAKE_TEXT in text or INTERACTIVE_ON_TEXT in text:
    return True
  return None


def set_navdy_display(args: argparse.Namespace, should_be_on: bool, reason: str) -> bool:
  if not args.adb_path:
    return False
  current = navdy_display_on(args)
  if current is should_be_on:
    return True
  if current is None:
    recover_adb(args, f"power-{reason}")
    if not should_be_on:
      return False
  keyevent = KEYEVENT_WAKEUP if should_be_on else KEYEVENT_POWER
  set_stay_on_while_plugged_in(args, should_be_on)
  proc = adb_shell(args, ["input", "keyevent", keyevent])
  if args.stdout:
    print(f"navdy display {'on' if should_be_on else 'off'} reason={reason}", flush=True)
  if proc.returncode != 0:
    return False
  time.sleep(0.5 if should_be_on else 2.0)
  verified = navdy_display_on(args)
  return proc.returncode == 0 if verified is None else verified is should_be_on


def emit(payload: dict[str, Any], args: argparse.Namespace) -> None:
  line = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
  if args.stdout:
    print(line, flush=True)
  if socket_send(payload, args):
    return
  if args.adb_path and args.adb_fallback:
    queue_adb(payload, args)


def import_messaging():
  for root in (os.getcwd(), "/data/openpilot"):
    if os.path.isdir(os.path.join(root, "cereal")) and root not in sys.path:
      sys.path.insert(0, root)
  try:
    from cereal import messaging  # pylint: disable=import-outside-toplevel
  except Exception as exc:
    raise SystemExit(f"Cannot import cereal.messaging. Run from openpilot root on comma: {exc}") from exc
  return messaging


def maybe_reexec_openpilot_python(args: argparse.Namespace) -> None:
  if args.synthetic:
    return
  venv_python = "/usr/local/venv/bin/python3"
  if os.path.exists(venv_python) and sys.executable != venv_python:
    os.execv(venv_python, [venv_python] + sys.argv)


def payload_signature(payload: dict[str, Any]) -> tuple[Any, ...]:
  return (
    payload.get("state"),
    payload.get("enabled"),
    payload.get("active"),
    payload.get("engaged"),
    payload.get("opAvailable"),
    payload.get("standstill"),
    payload.get("cruiseStandstill"),
    payload.get("setSpeedKph"),
    payload.get("vEgoKph"),
    payload.get("gear"),
    payload.get("leftBlinker"),
    payload.get("rightBlinker"),
    payload.get("leftBlindspot"),
    payload.get("rightBlindspot"),
    payload.get("alertText1"),
    payload.get("alertText2"),
  )


def should_emit_payload(payload: dict[str, Any], args: argparse.Namespace, now: float,
                        last_signature: tuple[Any, ...] | None, last_emit_at: float) -> tuple[bool, tuple[Any, ...]]:
  signature = payload_signature(payload)
  if not args.once and last_emit_at > 0.0 and now - last_emit_at < max(args.min_emit_sec, 0.0):
    return False, signature
  return (
    signature != last_signature or
    now - last_emit_at >= max(args.heartbeat_sec, 0.1) or
    args.once
  ), signature


def panda_ignition_started(panda_states: Any) -> bool:
  try:
    return any(bool(getattr(panda_state, "ignitionLine", False) or
                    getattr(panda_state, "ignitionCan", False))
               for panda_state in panda_states)
  except TypeError:
    return False


def service_active(sm: Any, service: str) -> bool:
  try:
    return bool(sm.alive[service] or sm.updated[service])
  except (KeyError, TypeError):
    return False


def openpilot_messages_started(sm: Any) -> bool:
  return any(service_active(sm, service)
             for service in (NAVDY_CAR_STATE_SERVICE, "selfdriveState", "controlsState"))


def onroad_process_started(args: argparse.Namespace, now: float) -> bool:
  last = bool(getattr(args, "_last_onroad_process_started", False))
  last_check = float(getattr(args, "_last_onroad_process_check_at", 0.0))
  if now - last_check < max(args.onroad_process_check_sec, 0.1):
    return last

  setattr(args, "_last_onroad_process_check_at", now)
  try:
    proc = subprocess.run(["ps", "-eo", "cmd"], check=False, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True, timeout=1.0)
  except subprocess.TimeoutExpired:
    return last

  started = False
  if proc.returncode == 0:
    started = any(process_name in line
                  for line in proc.stdout.splitlines()
                  for process_name in ONROAD_PROCESS_NAMES)

  if args.stdout and started != last:
    print(f"onroad process fallback started={started}", flush=True)
  setattr(args, "_last_onroad_process_started", started)
  return started


def power_started(sm: Any, args: argparse.Namespace | None = None, now: float = 0.0) -> bool:
  if bool(getattr(sm["deviceState"], "started", False)) or panda_ignition_started(sm["pandaStates"]):
    return True
  if openpilot_messages_started(sm):
    return True
  return bool(args and onroad_process_started(args, now))


def service_recent(sm: Any, service: str, now: float, max_age: float = 1.0) -> bool:
  return bool(sm.seen[service] and now - sm.recv_time[service] <= max_age)


def live_payload_ready(sm: Any, started: bool, now: float | None = None) -> bool:
  if not started:
    return True
  now = time.monotonic() if now is None else now
  return bool(service_recent(sm, "selfdriveState", now))


def available_services(messaging: Any, requested: list[str]) -> list[str]:
  service_list = getattr(messaging, "SERVICE_LIST", None)
  if service_list is None:
    return requested
  return [service for service in requested if service in service_list]


def sm_optional(sm: Any, services: list[str], service: str) -> Any:
  return sm[service] if service in services else None


def due_for_power_on_ensure(args: argparse.Namespace, now: float) -> bool:
  last = float(getattr(args, "_last_power_on_ensure_at", 0.0))
  if now - last < max(args.power_on_ensure_sec, 0.1):
    return False
  setattr(args, "_last_power_on_ensure_at", now)
  return True


def manage_navdy_power(args: argparse.Namespace, started: bool, now: float, offroad_since: float | None,
                       last_target_on: bool | None) -> tuple[float | None, bool | None]:
  if not args.manage_navdy_power:
    return offroad_since, last_target_on

  if started:
    if last_target_on is not True or due_for_power_on_ensure(args, now):
      if set_navdy_display(args, True, "onroad"):
        last_target_on = True
    return None, last_target_on

  if offroad_since is None:
    offroad_since = now
  if now - offroad_since >= max(args.power_off_delay_sec, 0.0) and last_target_on is not False:
    if set_navdy_display(args, False, "offroad"):
      last_target_on = False
  return offroad_since, last_target_on


def run_live(args: argparse.Namespace) -> None:
  maybe_reexec_openpilot_python(args)
  messaging = import_messaging()
  services = available_services(
      messaging, ["selfdriveState", NAVDY_CAR_STATE_SERVICE, "controlsState", "starpilotPlan", "longitudinalPlan"])
  if args.manage_navdy_power:
    services += available_services(messaging, ["deviceState", "pandaStates"])
  sm = messaging.SubMaster(services)
  seq = 0
  period = 1.0 / max(args.hz, 0.1)
  last_signature = None
  last_emit_at = 0.0
  once_deadline = time.monotonic() + max(args.once_timeout_sec, 0.1)
  offroad_since = None
  last_power_target_on = None
  while True:
    time.sleep(period)
    sm.update(0)
    now = time.monotonic()
    has_update = any(sm.updated[service] for service in services)
    started = power_started(sm, args, now) if args.manage_navdy_power else True
    if args.manage_navdy_power:
      offroad_since, last_power_target_on = manage_navdy_power(
          args, started, now, offroad_since, last_power_target_on)
    if not has_update and not (args.once and now >= once_deadline):
      continue
    if not live_payload_ready(sm, started, now):
      continue
    if service_recent(sm, NAVDY_CAR_STATE_SERVICE, now):
      car_state = car_state_from_sp(sm[NAVDY_CAR_STATE_SERVICE])
    else:
      car_state = default_car_state()
    payload = payload_from_messages(sm["selfdriveState"],
                                    car_state,
                                    seq,
                                    sm_optional(sm, services, "controlsState"),
                                    sm_optional(sm, services, "starpilotPlan"),
                                    sm_optional(sm, services, "longitudinalPlan"))
    payload = stabilize_display_payload(payload, args, now)
    should_emit, signature = should_emit_payload(payload, args, now, last_signature, last_emit_at)
    if should_emit:
      emit(payload, args)
      last_signature = signature
      last_emit_at = now
      seq += 1
      if args.once:
        return
      continue
    seq += 1


def run_synthetic(args: argparse.Namespace) -> None:
  seq = 0
  period = 1.0 / max(args.hz, 0.1)
  offroad_since = None
  last_power_target_on = None
  while True:
    now = time.monotonic()
    offroad_since, last_power_target_on = manage_navdy_power(
        args, args.synthetic_started, now, offroad_since, last_power_target_on)
    emit(synthetic_payload(args, seq), args)
    seq += 1
    if args.once:
      return
    time.sleep(period)


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--hz", type=float, default=5.0, help="Update rate for bridge output.")
  parser.add_argument("--once", action="store_true", help="Send one payload and exit.")
  parser.add_argument("--synthetic", action="store_true", help="Send fake OP data without cereal imports.")
  parser.add_argument("--synthetic-gear", default="drive", help="Gear text for --synthetic payloads.")
  parser.add_argument("--synthetic-started", action="store_true", help="Synthetic onroad flag for power tests.")
  parser.add_argument("--synthetic-standstill", action="store_true", help="Force standstill true in --synthetic payloads.")
  parser.add_argument("--synthetic-left-blindspot", action="store_true", help="Force left BSM true in --synthetic payloads.")
  parser.add_argument("--synthetic-right-blindspot", action="store_true", help="Force right BSM true in --synthetic payloads.")
  parser.add_argument("--stdout", action="store_true", default=True, help="Print JSON lines.")
  parser.add_argument("--no-stdout", dest="stdout", action="store_false", help="Do not print JSON lines.")
  parser.add_argument("--adb-path", default="", help="Path to adb on comma. Empty disables adb broadcast.")
  parser.add_argument("--adb-server-port", type=int, default=0, help="ADB server port, e.g. 5038 on comma.")
  parser.add_argument("--adb-serial", default="", help="Navdy adb serial if multiple devices appear.")
  parser.add_argument("--adb-timeout-sec", type=float, default=4.0, help="ADB command timeout.")
  parser.add_argument("--adb-recover-sec", type=float, default=5.0, help="Minimum interval between adb recovery attempts.")
  parser.add_argument("--adb-wait-device-sec", type=float, default=1.0, help="Short wait-for-device timeout after adb start-server.")
  parser.add_argument("--sync-adb", action="store_true", help="Send ADB broadcasts on the polling thread.")
  parser.add_argument("--socket-transport", action="store_true", help="Use adb forward + Navdy socket service for low-latency payloads.")
  parser.add_argument("--socket-host", default="127.0.0.1", help="Host address for forwarded Navdy socket.")
  parser.add_argument("--socket-port", type=int, default=DEFAULT_SOCKET_PORT, help="Host TCP port forwarded to Navdy.")
  parser.add_argument("--device-socket-port", type=int, default=DEFAULT_DEVICE_SOCKET_PORT, help="Navdy TCP port for the socket service.")
  parser.add_argument("--service-component", default=DEFAULT_SERVICE_COMPONENT, help="Android service component for socket transport.")
  parser.add_argument("--socket-timeout-sec", type=float, default=0.25, help="Socket connect/write timeout.")
  parser.add_argument("--socket-reconnect-sec", type=float, default=1.0, help="Minimum interval between socket reconnect attempts.")
  parser.add_argument("--no-adb-fallback", dest="adb_fallback", action="store_false", help="Disable broadcast fallback when socket send fails.")
  parser.set_defaults(adb_fallback=True)
  parser.add_argument("--action", default=DEFAULT_ACTION, help="Android broadcast action on Navdy.")
  parser.add_argument("--component", default=DEFAULT_COMPONENT, help="Explicit Android receiver component.")
  parser.add_argument("--heartbeat-sec", type=float, default=3.0, help="Re-send unchanged live state at this interval.")
  parser.add_argument("--min-emit-sec", type=float, default=0.0, help="Minimum interval between live payload sends.")
  parser.add_argument("--once-timeout-sec", type=float, default=3.0, help="For --once, emit cached state after this wait.")
  parser.add_argument("--manage-navdy-power", action="store_true", help="Wake Navdy on onroad and sleep it on offroad.")
  parser.add_argument("--power-off-delay-sec", type=float, default=30.0, help="Offroad duration before Navdy display sleep.")
  parser.add_argument("--power-on-ensure-sec", type=float, default=1.0,
                      help="Re-check Navdy display state at this interval while onroad.")
  parser.add_argument("--onroad-process-check-sec", type=float, default=1.0,
                      help="Minimum interval for onroad process fallback checks.")
  parser.add_argument("--blinker-hold-sec", type=float, default=1.6,
                      help="Keep blinker icon visible after a true sample.")
  parser.add_argument("--blindspot-hold-sec", type=float, default=1.6,
                      help="Keep blindspot icon visible after a true sample.")
  return parser.parse_args()


def main() -> int:
  args = parse_args()
  setattr(args, "_last_adb_recover_at", 0.0)
  setattr(args, "_last_power_on_ensure_at", 0.0)
  setattr(args, "_last_onroad_process_check_at", 0.0)
  setattr(args, "_last_onroad_process_started", False)
  setattr(args, "_last_set_speed_kph", 0.0)
  setattr(args, "_last_socket_connect_at", 0.0)
  setattr(args, "_socket_conn", None)
  if args.adb_path:
    recover_adb(args, "startup", force=True)
  start_socket_transport(args)
  if args.adb_path:
    start_adb_sender(args)
  if args.synthetic:
    run_synthetic(args)
  else:
    run_live(args)
  return 0


if __name__ == "__main__":
  sys.exit(main())
