#!/usr/bin/env python3
import base64
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from cereal import log, messaging
from openpilot.common.params import Params
from openpilot.system.hardware import PC

CONFIG_PATH = Path(os.getenv("WAYON_CLOUD_CONFIG", str(Path.home() / ".wayon_cloud" / "config.json") if PC else "/data/wayon_cloud/config.json"))
USER_AGENT = "wayon-cloud-uploader/1.0"

DEFAULT_TELEMETRY_INTERVAL_ONROAD = 15.0
DEFAULT_TELEMETRY_INTERVAL_OFFROAD = 300.0
DEFAULT_SNAPSHOT_INTERVAL_OFFROAD = 3600.0
CONFIG_RELOAD_INTERVAL = 60.0


def utc_now():
  return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_config():
  try:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
      config = json.load(f)
  except FileNotFoundError:
    return None
  except Exception as exc:
    print(f"Wayon cloud: failed to read config: {exc}")
    return None

  endpoint = str(config.get("endpoint", "")).rstrip("/")
  token = str(config.get("token", ""))
  if not endpoint or not token:
    return None

  config["endpoint"] = endpoint
  config["token"] = token
  return config


def get_param_str(params, key):
  value = params.get(key)
  if isinstance(value, bytes):
    return value.decode("utf-8", "replace")
  return str(value or "")


def post_json(config, path, payload):
  response = requests.post(
    f"{config['endpoint']}{path}",
    json=payload,
    headers={
      "Authorization": f"Bearer {config['token']}",
      "Content-Type": "application/json",
      "User-Agent": USER_AGENT,
    },
    timeout=15,
  )
  response.raise_for_status()
  return response.json() if response.content else {}


def enum_name(value):
  try:
    return str(value).split(".")[-1]
  except Exception:
    return ""


def first_panda_state(panda_states):
  for panda_state in panda_states:
    if panda_state.pandaType != log.PandaState.PandaType.unknown:
      return panda_state
  return panda_states[0] if len(panda_states) else None


def current_ma_from_raw(raw_current):
  if raw_current is None:
    return None

  current = float(raw_current)
  return current / 1000.0 if current > 10000.0 else current


def voltage_v_from_raw(raw_voltage):
  if raw_voltage is None:
    return None

  voltage = float(raw_voltage)
  return voltage / 1000.0 if voltage > 100.0 else voltage


def vehicle_speed_payload(sm, started):
  if not started:
    return {"speedMps": 0.0, "source": "offroad"}

  try:
    car_state = sm["carState"]
    v_ego_cluster = float(car_state.vEgoCluster)
    if v_ego_cluster != 0.0:
      return {"speedMps": max(0.0, v_ego_cluster), "source": "vEgoCluster"}
    return {"speedMps": max(0.0, float(car_state.vEgo)), "source": "vEgo"}
  except Exception:
    return {}


def telemetry_payload(sm, params, device_id):
  device_state = sm["deviceState"]
  panda_state = first_panda_state(sm["pandaStates"])
  started = bool(device_state.started)
  vehicle_speed = vehicle_speed_payload(sm, started)

  ignition = False
  voltage_v = None
  current_ma = None
  if panda_state is not None:
    ignition = bool(panda_state.ignitionLine or panda_state.ignitionCan)
    voltage_v = voltage_v_from_raw(panda_state.voltage)
    current_ma = current_ma_from_raw(panda_state.current)

  power_w = voltage_v * current_ma / 1000.0 if voltage_v is not None and current_ma is not None else None

  enabled = False
  try:
    enabled = bool(sm["selfdriveState"].enabled)
  except Exception:
    pass

  return {
    "deviceId": device_id,
    "updatedAt": utc_now(),
    "onroad": bool(device_state.started),
    "ignition": ignition,
    "enabled": enabled,
    "voltageV": voltage_v,
    "currentMa": current_ma,
    "powerW": power_w,
    "devicePowerW": float(device_state.powerDrawW),
    "thermalStatus": enum_name(device_state.thermalStatus),
    "fanPercent": int(device_state.fanSpeedPercentDesired),
    "screenBrightnessPercent": int(device_state.screenBrightnessPercent),
    "vehicleSpeedMps": vehicle_speed.get("speedMps"),
    "vehicleSpeedSource": vehicle_speed.get("source"),
    "dongleId": get_param_str(params, "DongleId"),
  }


def jpeg_base64(array):
  from PIL import Image

  buffer = io.BytesIO()
  Image.fromarray(array).save(buffer, "JPEG", quality=72, optimize=True)
  return base64.b64encode(buffer.getvalue()).decode("ascii")


def upload_offroad_snapshot(config, device_id):
  try:
    wide, driver = capture_offroad_images()
    if wide is None and driver is None:
      return False

    payload = {
      "deviceId": device_id,
      "capturedAt": utc_now(),
      "wideJpegBase64": jpeg_base64(wide) if wide is not None else None,
      "driverJpegBase64": jpeg_base64(driver) if driver is not None else None,
    }
    post_json(config, "/api/snapshot", payload)
    print("Wayon cloud: uploaded offroad snapshot")
    return True
  except Exception as exc:
    print(f"Wayon cloud: snapshot upload failed: {exc}")
    return False


def capture_offroad_images():
  import subprocess

  from openpilot.selfdrive.selfdrived.alertmanager import set_offroad_alert
  from openpilot.system.camerad.snapshot import get_snapshots
  from openpilot.system.manager.process_config import managed_processes

  params = Params()

  if (not params.get_bool("IsOffroad")) or params.get_bool("IsTakingSnapshot"):
    return None, None

  params.put_bool("IsTakingSnapshot", True)
  set_offroad_alert("Offroad_IsTakingSnapshot", True)
  time.sleep(2.0)

  try:
    try:
      subprocess.check_call(["pgrep", "camerad"])
      return None, None
    except subprocess.CalledProcessError:
      pass

    if not PC:
      managed_processes["camerad"].start()

    return get_snapshots("wideRoadCameraState", "driverCameraState")
  finally:
    managed_processes["camerad"].stop()
    params.put_bool("IsTakingSnapshot", False)
    set_offroad_alert("Offroad_IsTakingSnapshot", False)


def main():
  params = Params()
  sm = messaging.SubMaster(["deviceState", "pandaStates", "selfdriveState", "carState"])

  config = None
  next_config_load = 0.0
  next_telemetry = 0.0
  next_snapshot = 0.0
  previous_started = False

  while True:
    sm.update(1000)
    now = time.monotonic()

    if config is None or now >= next_config_load:
      config = read_config()
      next_config_load = now + CONFIG_RELOAD_INTERVAL
      if config is None:
        time.sleep(5.0)
        continue

    device_id = str(config.get("device_id") or get_param_str(params, "DongleId") or "unknown")
    started = bool(sm["deviceState"].started)
    telemetry_interval = float(config.get(
      "telemetry_interval_onroad" if started else "telemetry_interval_offroad",
      DEFAULT_TELEMETRY_INTERVAL_ONROAD if started else DEFAULT_TELEMETRY_INTERVAL_OFFROAD,
    ))
    snapshot_interval = float(config.get("snapshot_interval_offroad", DEFAULT_SNAPSHOT_INTERVAL_OFFROAD))

    if not started and previous_started:
      next_snapshot = min(next_snapshot, now + 30.0)

    if now >= next_telemetry:
      try:
        post_json(config, "/api/telemetry", telemetry_payload(sm, params, device_id))
        next_telemetry = now + max(5.0, telemetry_interval)
      except Exception as exc:
        print(f"Wayon cloud: telemetry upload failed: {exc}")
        next_telemetry = now + 30.0

    if not started and now >= next_snapshot:
      upload_offroad_snapshot(config, device_id)
      next_snapshot = now + max(300.0, snapshot_interval)

    previous_started = started


if __name__ == "__main__":
  main()
