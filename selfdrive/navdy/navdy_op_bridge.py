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
import subprocess
import sys
import time
from typing import Any


KPH_PER_MS = 3.6
DEFAULT_ACTION = "com.navdy.OPENPILOT_STATE"
DEFAULT_COMPONENT = "com.navdy.hud.app/.openpilot.OpenpilotStateReceiver"
DISPLAY_ON_TEXT = "Display Power: state=ON"
DISPLAY_OFF_TEXT = "Display Power: state=OFF"
WAKEFULNESS_AWAKE_TEXT = "mWakefulness=Awake"
WAKEFULNESS_ASLEEP_TEXT = "mWakefulness=Asleep"
INTERACTIVE_ON_TEXT = "mHalInteractiveModeEnabled=true"
INTERACTIVE_OFF_TEXT = "mHalInteractiveModeEnabled=false"
KEYEVENT_POWER = "26"
KEYEVENT_WAKEUP = "224"


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


def gear_text(car_state: Any) -> str:
  return enum_text(getattr(car_state, "gearShifter", "unknown")).lower()


def speed_kph_from_car_state(car_state: Any) -> float:
  v_cruise_cluster = finite_float(getattr(car_state, "vCruiseCluster", 0.0))
  if 0.0 < v_cruise_cluster < 255.0:
    return v_cruise_cluster

  v_cruise = finite_float(getattr(car_state, "vCruise", 0.0))
  if 0.0 < v_cruise < 255.0:
    return v_cruise

  cruise_state = getattr(car_state, "cruiseState", None)
  cruise_speed_ms = finite_float(getattr(cruise_state, "speed", 0.0))
  return cruise_speed_ms * KPH_PER_MS if cruise_speed_ms > 0.0 else 0.0


def payload_from_messages(selfdrive_state: Any, car_state: Any, seq: int) -> dict[str, Any]:
  left_blinker = bool(getattr(car_state, "leftBlinker", False))
  right_blinker = bool(getattr(car_state, "rightBlinker", False))
  left_blindspot = bool(getattr(car_state, "leftBlindspot", False))
  right_blindspot = bool(getattr(car_state, "rightBlindspot", False))
  enabled = bool(getattr(selfdrive_state, "enabled", False))
  active = bool(getattr(selfdrive_state, "active", False))

  v_ego_cluster = finite_float(getattr(car_state, "vEgoCluster", 0.0))
  v_ego_ms = finite_float(getattr(car_state, "vEgo", 0.0))
  v_ego_kph = v_ego_cluster if v_ego_cluster > 0.0 else v_ego_ms * KPH_PER_MS

  return {
    "schema": "navdy.openpilot.v1",
    "seq": seq,
    "ts": round(time.time(), 3),
    "state": enum_text(getattr(selfdrive_state, "state", "unknown")),
    "enabled": enabled,
    "active": active,
    "engaged": active,
    "disengaged": not enabled,
    "engageable": bool(getattr(selfdrive_state, "engageable", False)),
    "setSpeedKph": rounded(speed_kph_from_car_state(car_state)),
    "vEgoKph": rounded(v_ego_kph),
    "gear": gear_text(car_state),
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
  cmd = adb_base_cmd(args)
  cmd += ["shell", "am", "broadcast"]
  if args.component:
    cmd += ["-n", args.component]
  cmd += ["-a", args.action, "--es", "payload", shlex.quote(json_payload)]
  return run_adb(args, cmd[len(adb_base_cmd(args)):]).returncode == 0


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
  if DISPLAY_ON_TEXT in text:
    return True
  if DISPLAY_OFF_TEXT in text:
    return False
  if WAKEFULNESS_AWAKE_TEXT in text or INTERACTIVE_ON_TEXT in text:
    return True
  if WAKEFULNESS_ASLEEP_TEXT in text or INTERACTIVE_OFF_TEXT in text:
    return False
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
  if args.adb_path:
    send_adb(payload, args)


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


def panda_ignition_started(panda_states: Any) -> bool:
  try:
    return any(bool(getattr(panda_state, "ignitionLine", False) or
                    getattr(panda_state, "ignitionCan", False))
               for panda_state in panda_states)
  except TypeError:
    return False


def power_started(sm: Any) -> bool:
  return bool(getattr(sm["deviceState"], "started", False)) or panda_ignition_started(sm["pandaStates"])


def manage_navdy_power(args: argparse.Namespace, started: bool, now: float, offroad_since: float | None,
                       last_target_on: bool | None) -> tuple[float | None, bool | None]:
  if not args.manage_navdy_power:
    return offroad_since, last_target_on

  if started:
    if last_target_on is not True:
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
  services = ["selfdriveState", "carState"]
  if args.manage_navdy_power:
    services += ["deviceState", "pandaStates"]
  sm = messaging.SubMaster(services, poll="pandaStates" if args.manage_navdy_power else "carState")
  seq = 0
  period = 1.0 / max(args.hz, 0.1)
  last_signature = None
  last_emit_at = 0.0
  once_deadline = time.monotonic() + max(args.once_timeout_sec, 0.1)
  offroad_since = None
  last_power_target_on = None
  while True:
    sm.update(int(period * 1000))
    has_update = any(sm.updated[service] for service in services)
    if not has_update and not (args.once and time.monotonic() >= once_deadline):
      continue
    now = time.monotonic()
    if args.manage_navdy_power:
      started = power_started(sm)
      offroad_since, last_power_target_on = manage_navdy_power(
          args, started, now, offroad_since, last_power_target_on)
    payload = payload_from_messages(sm["selfdriveState"], sm["carState"], seq)
    signature = payload_signature(payload)
    if signature != last_signature or now - last_emit_at >= max(args.heartbeat_sec, 0.1) or args.once:
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
  parser.add_argument("--action", default=DEFAULT_ACTION, help="Android broadcast action on Navdy.")
  parser.add_argument("--component", default=DEFAULT_COMPONENT, help="Explicit Android receiver component.")
  parser.add_argument("--heartbeat-sec", type=float, default=1.0, help="Re-send unchanged live state at this interval.")
  parser.add_argument("--once-timeout-sec", type=float, default=3.0, help="For --once, emit cached state after this wait.")
  parser.add_argument("--manage-navdy-power", action="store_true", help="Wake Navdy on onroad and sleep it on offroad.")
  parser.add_argument("--power-off-delay-sec", type=float, default=30.0, help="Offroad duration before Navdy display sleep.")
  return parser.parse_args()


def main() -> int:
  args = parse_args()
  setattr(args, "_last_adb_recover_at", 0.0)
  if args.adb_path:
    recover_adb(args, "startup", force=True)
  if args.synthetic:
    run_synthetic(args)
  else:
    run_live(args)
  return 0


if __name__ == "__main__":
  sys.exit(main())
