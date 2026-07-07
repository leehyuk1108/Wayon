#!/usr/bin/env python3
import base64
import io
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from cereal import log, messaging
from openpilot.common.params import Params
from openpilot.common.realtime import set_core_affinity
from openpilot.system.hardware import PC
from openpilot.system.hardware.hw import Paths

CONFIG_PATH = Path(os.getenv("WAYON_CLOUD_CONFIG", str(Path.home() / ".wayon_cloud" / "config.json") if PC else "/data/wayon_cloud/config.json"))
ROUTE_STATE_PATH = Path(os.getenv("WAYON_CLOUD_ROUTE_STATE", str(CONFIG_PATH.with_name("route_state.json"))))
USER_AGENT = "wayon-cloud-uploader/1.0"

DEFAULT_TELEMETRY_INTERVAL_ONROAD = 30.0
DEFAULT_TELEMETRY_INTERVAL_OFFROAD = 300.0
DEFAULT_ROUTE_SUMMARY_INTERVAL_OFFROAD = 60.0
DEFAULT_ROUTE_SUMMARY_GRACE_PERIOD = 45.0
DEFAULT_ROUTE_SUMMARY_MAX_AGE = 24.0 * 60.0 * 60.0
DEFAULT_LATEST_ROUTE_GPS_MAX_AGE = 2.0 * 60.0 * 60.0
DEFAULT_ROUTE_POINT_INTERVAL = 10.0
DEFAULT_ROUTE_POINT_MIN_DISTANCE_M = 15.0
DEFAULT_ROUTE_POINT_LIMIT = 720
DEFAULT_SNAPSHOT_INTERVAL_OFFROAD = 3600.0
CONFIG_RELOAD_INTERVAL = 60.0
LOOP_SLEEP_ONROAD = 1.0
LOOP_SLEEP_OFFROAD = 1.0
LOG_FILE_CANDIDATES = ("qlog.zst", "qlog.bz2", "qlog", "rlog.zst", "rlog.bz2", "rlog")
STATE_SERVICES = ["deviceState", "pandaStates", "gpsLocationExternal", "gpsLocation", "selfdriveState"]
TELEMETRY_SERVICES = STATE_SERVICES + ["carState"]


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


def car_state_speed_payload(car_state):
  v_ego_cluster = float(car_state.vEgoCluster)
  if v_ego_cluster != 0.0:
    return {"speedMps": max(0.0, v_ego_cluster), "source": "vEgoCluster"}
  return {"speedMps": max(0.0, float(car_state.vEgo)), "source": "vEgo"}


def vehicle_speed_payload(sm, started):
  if not started:
    return {"speedMps": 0.0, "source": "offroad"}

  try:
    return car_state_speed_payload(sm["carState"])
  except Exception:
    return {}


def last_gps_payload(params):
  try:
    location = params.get("LastGPSPosition")
    if isinstance(location, bytes):
      location = location.decode("utf-8", "replace")
    data = json.loads(location or "{}")
  except Exception:
    return {}

  latitude = data.get("latitude")
  longitude = data.get("longitude")
  if latitude is None or longitude is None:
    return {}

  payload = {
    "latitude": float(latitude),
    "longitude": float(longitude),
    "bearingDeg": float(data.get("bearing", 0.0)),
    "source": "lastGpsPosition",
  }

  try:
    param_path = Path("/data/params/d/LastGPSPosition")
    if param_path.is_file():
      payload["timestampMillis"] = int(param_path.stat().st_mtime * 1000)
  except Exception:
    pass

  return payload


def gps_payload(sm, params=None, allow_route_log_fallback=True):
  candidates = []
  for socket in ("gpsLocationExternal", "gpsLocation"):
    try:
      gps = sm[socket]
      if gps.hasFix and abs(gps.latitude) > 0.001 and abs(gps.longitude) > 0.001:
        candidates.append((sm.recv_time.get(socket, 0), gps))
    except Exception:
      continue

  if not candidates:
    if allow_route_log_fallback:
      route_gps = latest_route_gps_payload()
      if route_gps:
        return route_gps
    return last_gps_payload(params) if params is not None else {}

  _, gps = max(candidates, key=lambda item: item[0])
  return {
    "latitude": float(gps.latitude),
    "longitude": float(gps.longitude),
    "altitude": float(gps.altitude),
    "bearingDeg": float(gps.bearingDeg),
    "accuracyM": float(gps.horizontalAccuracy),
    "timestampMillis": int(gps.unixTimestampMillis),
    "source": enum_name(gps.source),
    "satellites": int(gps.satelliteCount),
  }


def telemetry_payload(sm, params, device_id, started_override=False):
  device_state = sm["deviceState"]
  panda_state = first_panda_state(sm["pandaStates"])
  started = bool(device_state.started) or bool(started_override)
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
    "onroad": started,
    "ignition": ignition,
    "enabled": enabled,
    "voltageV": voltage_v,
    "currentMa": current_ma,
    "powerW": power_w,
    "devicePowerW": float(device_state.powerDrawW),
    "thermalStatus": enum_name(device_state.thermalStatus),
    "fanPercent": int(device_state.fanSpeedPercentDesired),
    "screenBrightnessPercent": int(device_state.screenBrightnessPercent),
    "gps": gps_payload(sm, params, allow_route_log_fallback=not started),
    "vehicleSpeedMps": vehicle_speed.get("speedMps"),
    "vehicleSpeedSource": vehicle_speed.get("source"),
    "dongleId": get_param_str(params, "DongleId"),
  }


def fresh_telemetry_payload(params, device_id, started):
  services = TELEMETRY_SERVICES if started else STATE_SERVICES
  sm = messaging.SubMaster(services)
  deadline = time.monotonic() + (2.0 if started else 1.0)
  while time.monotonic() < deadline:
    sm.update(100)
    if sm.seen["deviceState"] and (not started or sm.seen["carState"]):
      break
  return telemetry_payload(sm, params, device_id, started_override=started)


def haversine_m(a, b):
  lat1 = math.radians(a["latitude"])
  lon1 = math.radians(a["longitude"])
  lat2 = math.radians(b["latitude"])
  lon2 = math.radians(b["longitude"])
  d_lat = lat2 - lat1
  d_lon = lon2 - lon1
  h = math.sin(d_lat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2.0) ** 2
  return 6371000.0 * 2.0 * math.atan2(math.sqrt(h), math.sqrt(1.0 - h))


def route_distance_m(route):
  return sum(haversine_m(route[i - 1], route[i]) for i in range(1, len(route)))


def read_route_state():
  try:
    with ROUTE_STATE_PATH.open("r", encoding="utf-8") as f:
      state = json.load(f)
  except FileNotFoundError:
    return {"uploaded_routes": []}
  except Exception as exc:
    print(f"Wayon cloud: failed to read route state: {exc}")
    return {"uploaded_routes": []}

  uploaded_routes = state.get("uploaded_routes", [])
  if not isinstance(uploaded_routes, list):
    uploaded_routes = []
  return {"uploaded_routes": [str(route) for route in uploaded_routes]}


def write_route_state(state):
  try:
    ROUTE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = ROUTE_STATE_PATH.with_suffix(f"{ROUTE_STATE_PATH.suffix}.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
      json.dump(state, f, ensure_ascii=False, separators=(",", ":"))
    tmp_path.replace(ROUTE_STATE_PATH)
  except Exception as exc:
    print(f"Wayon cloud: failed to write route state: {exc}")


def mark_route_uploaded(route_name):
  state = read_route_state()
  uploaded_routes = [route for route in state.get("uploaded_routes", []) if route != route_name]
  uploaded_routes.insert(0, route_name)
  write_route_state({"uploaded_routes": uploaded_routes[:100]})


def parse_segment_dir_name(name):
  try:
    route_name, segment = name.rsplit("--", 1)
  except ValueError:
    return None

  if not segment.isdigit() or not route_name:
    return None
  return route_name, int(segment)


def route_started_at(route_name):
  try:
    return datetime.strptime(route_name, "%Y-%m-%d--%H-%M-%S").replace(tzinfo=timezone.utc)
  except ValueError:
    return None


def iso_from_timestamp_ms(timestamp_ms):
  try:
    timestamp_ms = int(timestamp_ms)
  except Exception:
    return None

  if timestamp_ms <= 0:
    return None
  return datetime.fromtimestamp(timestamp_ms / 1000.0, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def segment_log_file(segment_dir):
  for filename in LOG_FILE_CANDIDATES:
    path = segment_dir / filename
    if path.is_file() and path.stat().st_size > 0:
      return path
  return None


def latest_route_gps_payload(max_age_s=DEFAULT_LATEST_ROUTE_GPS_MAX_AGE):
  try:
    from openpilot.tools.lib.logreader import LogReader

    log_root = Path(Paths.log_root())
    if not log_root.is_dir():
      return {}

    now = time.time()
    segment_dirs = sorted(
      (path for path in log_root.iterdir() if path.is_dir()),
      key=lambda path: path.stat().st_mtime,
      reverse=True,
    )

    latest = None
    for segment_dir in segment_dirs[:8]:
      log_file = segment_log_file(segment_dir)
      if log_file is None:
        continue
      if now - max(segment_dir.stat().st_mtime, log_file.stat().st_mtime) > max_age_s:
        continue

      for msg in LogReader(str(log_file), sort_by_time=True, only_union_types=True):
        which = msg.which()
        if which not in ("gpsLocationExternal", "gpsLocation"):
          continue
        gps = getattr(msg, which)
        if not gps.hasFix or abs(gps.latitude) <= 0.001 or abs(gps.longitude) <= 0.001:
          continue

        latest = {
          "latitude": float(gps.latitude),
          "longitude": float(gps.longitude),
          "altitude": float(gps.altitude),
          "bearingDeg": float(gps.bearingDeg),
          "accuracyM": float(gps.horizontalAccuracy),
          "timestampMillis": int(gps.unixTimestampMillis),
          "source": f"routeLog:{which}",
          "satellites": int(gps.satelliteCount),
        }

      if latest:
        return latest
  except Exception as exc:
    print(f"Wayon cloud: failed to read latest route GPS: {exc}")

  return {}


def recent_route_groups(max_age_s):
  log_root = Path(Paths.log_root())
  if not log_root.is_dir():
    return []

  now = time.time()
  groups = {}
  for segment_dir in log_root.iterdir():
    if not segment_dir.is_dir():
      continue

    parsed = parse_segment_dir_name(segment_dir.name)
    if parsed is None:
      continue

    route_name, segment = parsed
    log_file = segment_log_file(segment_dir)
    if log_file is None:
      continue

    mtime = max(segment_dir.stat().st_mtime, log_file.stat().st_mtime)
    if now - mtime > max_age_s:
      continue

    group = groups.setdefault(route_name, {"route_name": route_name, "segments": [], "mtime": 0.0})
    group["segments"].append((segment, segment_dir, log_file))
    group["mtime"] = max(group["mtime"], mtime)

  route_groups = []
  for group in groups.values():
    group["segments"].sort(key=lambda item: item[0])
    route_groups.append(group)

  return sorted(route_groups, key=lambda item: item["mtime"], reverse=True)


def downsample_route(route, limit):
  if len(route) <= limit:
    return route
  if limit < 2:
    return route[:limit]

  step = (len(route) - 1) / float(limit - 1)
  return [route[round(i * step)] for i in range(limit)]


def gps_point_from_log(gps, timestamp_offset_s, route_start, speed_payload):
  if not gps.hasFix or abs(gps.latitude) <= 0.001 or abs(gps.longitude) <= 0.001:
    return None

  point_time = iso_from_timestamp_ms(gps.unixTimestampMillis)
  if point_time is None and route_start is not None and timestamp_offset_s is not None:
    point_time = datetime.fromtimestamp(route_start.timestamp() + timestamp_offset_s, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

  point = {
    "time": point_time or utc_now(),
    "latitude": float(gps.latitude),
    "longitude": float(gps.longitude),
    "speedMps": speed_payload.get("speedMps") if speed_payload else max(0.0, float(gps.speed)),
    "speedSource": speed_payload.get("source") if speed_payload else "gps",
    "bearingDeg": float(gps.bearingDeg),
  }

  try:
    point["accuracyM"] = float(gps.horizontalAccuracy)
  except Exception:
    pass
  return point


def should_add_route_point(route, point, last_point_mono, point_mono, point_interval_s, min_distance_m):
  if not route:
    return True
  if point_mono is not None and last_point_mono is not None and point_mono - last_point_mono >= point_interval_s:
    return True
  return haversine_m(route[-1], point) >= min_distance_m


def summarize_route_from_logs(route_group, config, device_id):
  from openpilot.tools.lib.logreader import LogReader

  route_name = route_group["route_name"]
  route_start = route_started_at(route_name)
  route = []
  speed_samples = []
  first_mono = None
  last_mono = None
  last_point_mono = None
  last_vehicle_speed = None

  point_interval_s = float(config.get("route_point_interval_s", DEFAULT_ROUTE_POINT_INTERVAL))
  min_distance_m = float(config.get("route_point_min_distance_m", DEFAULT_ROUTE_POINT_MIN_DISTANCE_M))
  point_limit = int(config.get("route_point_limit", DEFAULT_ROUTE_POINT_LIMIT))

  for _, _, log_file in route_group["segments"]:
    try:
      reader = LogReader(str(log_file), sort_by_time=True, only_union_types=True)
      for msg in reader:
        which = msg.which()
        msg_mono = float(msg.logMonoTime) / 1e9
        if first_mono is None:
          first_mono = msg_mono
        last_mono = msg_mono

        if which == "carState":
          try:
            last_vehicle_speed = car_state_speed_payload(msg.carState)
            if last_vehicle_speed.get("speedMps") is not None:
              speed_samples.append(float(last_vehicle_speed["speedMps"]))
          except Exception:
            pass
          continue

        if which not in ("gpsLocationExternal", "gpsLocation"):
          continue

        gps = getattr(msg, which)
        timestamp_offset_s = None if first_mono is None else msg_mono - first_mono
        point = gps_point_from_log(gps, timestamp_offset_s, route_start, last_vehicle_speed)
        if point is None:
          continue

        if should_add_route_point(route, point, last_point_mono, msg_mono, point_interval_s, min_distance_m):
          route.append(point)
          last_point_mono = msg_mono
    except Exception as exc:
      print(f"Wayon cloud: failed to read route log {log_file}: {exc}")

  if len(route) < 2:
    return None

  duration_s = 0
  if first_mono is not None and last_mono is not None:
    duration_s = max(0, int(last_mono - first_mono))

  distance_m = route_distance_m(route)
  started_at = route[0]["time"]
  ended_at = route[-1]["time"]
  avg_speed_mps = distance_m / duration_s if duration_s > 0 else 0.0
  max_speed_mps = max(speed_samples) if speed_samples else max(float(point.get("speedMps") or 0.0) for point in route)
  payload_route = downsample_route(route, point_limit)

  return {
    "id": f"{device_id}-{route_name}",
    "deviceId": device_id,
    "startedAt": started_at,
    "endedAt": ended_at,
    "durationS": duration_s,
    "distanceM": distance_m,
    "startLat": route[0]["latitude"],
    "startLon": route[0]["longitude"],
    "endLat": route[-1]["latitude"],
    "endLon": route[-1]["longitude"],
    "source": "openpilotRoute",
    "routeName": route_name,
    "segmentCount": len(route_group["segments"]),
    "avgSpeedMps": avg_speed_mps,
    "maxSpeedMps": max_speed_mps,
    "route": payload_route,
  }


def upload_recent_route_summary(config, device_id):
  state = read_route_state()
  uploaded_routes = set(state.get("uploaded_routes", []))
  max_age_s = float(config.get("route_summary_max_age_s", DEFAULT_ROUTE_SUMMARY_MAX_AGE))
  grace_period_s = float(config.get("route_summary_grace_period_s", DEFAULT_ROUTE_SUMMARY_GRACE_PERIOD))

  route_groups = recent_route_groups(max_age_s)
  if not route_groups:
    return False

  # Only summarize the latest route. This avoids slowly backfilling old drives
  # after a reboot while still catching the route that just finished.
  route_group = route_groups[0]
  route_name = route_group["route_name"]
  if route_name in uploaded_routes:
    return False
  if time.time() - route_group["mtime"] < grace_period_s:
    return False

  payload = summarize_route_from_logs(route_group, config, device_id)
  if payload is None:
    return False

  post_json(config, "/api/trips", payload)
  mark_route_uploaded(route_name)
  print(f"Wayon cloud: uploaded route summary {route_name} ({len(payload['route'])} route points)")
  return True



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
  set_core_affinity([0, 1, 2, 3])
  params = Params()
  sm = messaging.SubMaster(STATE_SERVICES)

  config = None
  next_config_load = 0.0
  next_telemetry = 0.0
  next_route_summary = 0.0
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

    if not sm.seen["deviceState"]:
      time.sleep(LOOP_SLEEP_OFFROAD)
      continue

    device_id = str(config.get("device_id") or get_param_str(params, "DongleId") or "unknown")
    started = bool(sm["deviceState"].started)

    telemetry_interval = float(config.get(
      "telemetry_interval_onroad" if started else "telemetry_interval_offroad",
      DEFAULT_TELEMETRY_INTERVAL_ONROAD if started else DEFAULT_TELEMETRY_INTERVAL_OFFROAD,
    ))
    route_summary_interval = float(config.get("route_summary_interval_offroad", DEFAULT_ROUTE_SUMMARY_INTERVAL_OFFROAD))
    route_summary_grace_period = float(config.get("route_summary_grace_period_s", DEFAULT_ROUTE_SUMMARY_GRACE_PERIOD))
    snapshot_interval = float(config.get("snapshot_interval_offroad", DEFAULT_SNAPSHOT_INTERVAL_OFFROAD))

    if started and not previous_started:
      print(f"Wayon cloud: using {telemetry_interval:.0f}s lightweight onroad telemetry")
      next_telemetry = now

    if not started and previous_started:
      next_telemetry = now
      route_summary_due = now + route_summary_grace_period
      next_route_summary = route_summary_due if next_route_summary <= now else min(next_route_summary, route_summary_due)
      next_snapshot = min(next_snapshot, now + 30.0)

    if now >= next_telemetry:
      try:
        post_json(config, "/api/telemetry", fresh_telemetry_payload(params, device_id, started))
        next_telemetry = now + max(5.0, telemetry_interval)
      except Exception as exc:
        print(f"Wayon cloud: telemetry upload failed: {exc}")
        next_telemetry = now + 30.0

    if not started and now >= next_route_summary:
      try:
        upload_recent_route_summary(config, device_id)
      except Exception as exc:
        print(f"Wayon cloud: route summary upload failed: {exc}")
      next_route_summary = now + max(30.0, route_summary_interval)

    if not started and now >= next_snapshot:
      upload_offroad_snapshot(config, device_id)
      next_snapshot = now + max(300.0, snapshot_interval)

    previous_started = started
    time.sleep(LOOP_SLEEP_ONROAD if started else LOOP_SLEEP_OFFROAD)


if __name__ == "__main__":
  main()
