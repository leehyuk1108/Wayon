#!/usr/bin/env python3
import base64
import io
import json
import math
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from cereal import log, messaging
from openpilot.common.params import Params
from openpilot.common.realtime import set_core_affinity
from openpilot.system.camera_lease import CameraLease
from openpilot.system.hardware import PC
from openpilot.system.hardware.hw import Paths
from openpilot.system.wayon_impact import peek_impact_event, remove_impact_event, update_impact_event
from openpilot.system.wayon_vehicle_events import (
  DEFAULT_DOOR_LOCK_WAKE_FILTER_MAX_S,
  DEFAULT_DOOR_LOCK_WAKE_FILTER_MIN_S,
  peek_vehicle_events,
  remove_vehicle_event,
  remove_vehicle_events,
)
from openpilot.system.wayon_identity import ensure_wayon_identity
from openpilot.system.wayon_drive_report import DriveReportAccumulator
from openpilot.system.wayon_drive_quality import (
  cutin_risk_stage,
  resolve_operating_state,
  telemetry_signature,
)

CONFIG_PATH = Path(os.getenv("WAYON_CLOUD_CONFIG", str(Path.home() / ".wayon_cloud" / "config.json") if PC else "/data/wayon_cloud/config.json"))
ROUTE_STATE_PATH = Path(os.getenv("WAYON_CLOUD_ROUTE_STATE", str(CONFIG_PATH.with_name("route_state.json"))))
UPLOAD_HEALTH_PATH = Path(os.getenv("WAYON_CLOUD_UPLOAD_HEALTH", "/dev/shm/wayon_cloud_health.json"))
NAVDY_HEALTH_PATH = Path(os.getenv("WAYON_NAVDY_HEALTH", "/dev/shm/navdy_bridge_health.json"))
USER_AGENT = "wayon-cloud-uploader/1.0"
GPS_SERVICE_MAX_AGE_S = 5.0
GPS_TIMESTAMP_MAX_AGE_MS = 15_000
LAST_GPS_POSITION_MAX_AGE_MS = 120_000
IMPACT_MEDIA_ROOT = Path(os.getenv("WAYON_IMPACT_MEDIA_ROOT", "/data/wayon_cloud/impact_media"))
LAST_SUPPRESSED_VEHICLE_PAIR_PATH = Path(os.getenv(
  "WAYON_LAST_SUPPRESSED_VEHICLE_PAIR",
  "/data/wayon_cloud/last_suppressed_vehicle_pair.json",
))
MAX_IMPACT_CAPTURE_ATTEMPTS = 3
IMPACT_UPLOAD_RETRY_DELAYS_S = (60, 300, 900, 3600, 21600)
WAYON_WIDE_SNAPSHOT_WARMUP_S = 0.5
WAYON_DRIVER_SNAPSHOT_WARMUP_S = 0.8
WAYON_SNAPSHOT_EXPOSURE_READY_RATIO = 0.78
WAYON_SNAPSHOT_EXPOSURE_STABLE_FRAMES = 3
WAYON_SNAPSHOT_EXPOSURE_MAX_WAIT_S = 5.0
WAYON_WIDE_SNAPSHOT_TARGET_MEDIAN = 70.0
WAYON_WIDE_SNAPSHOT_MIN_GAMMA = 0.62
OFFROAD_SNAPSHOT_TIMEOUT_S = 30.0
DEFAULT_VEHICLE_STATUS_URL = (
  "https://mycarserver-fb85e-default-rtdb.firebaseio.com/car_status.json"
)
DEFAULT_DOOR_LOCK_REFRESH_MARKER_WINDOW_S = 30.0
DOOR_LOCK_REFRESH_MARKER_FUTURE_TOLERANCE_S = 3.0

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
DEFAULT_AMBIENT_COMMAND_POLL_INTERVAL = 5.0
AMBIENT_OVERRIDE_PATH = Path(os.getenv("WAYON_AMBIENT_OVERRIDE_PATH", "/data/params/d/WayonAmbientOverride"))
CONFIG_RELOAD_INTERVAL = 60.0
LOOP_SLEEP_ONROAD = 1.0
LOOP_SLEEP_OFFROAD = 1.0
LOG_FILE_CANDIDATES = ("qlog.zst", "qlog.bz2", "qlog", "rlog.zst", "rlog.bz2", "rlog")
STATE_SERVICES = ["deviceState", "pandaStates", "gpsLocationExternal", "gpsLocation", "selfdriveState"]
TELEMETRY_SERVICES = STATE_SERVICES + ["carState", "radarState"]


def utc_now():
  return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json_file(path):
  try:
    with Path(path).open("r", encoding="utf-8") as f:
      payload = json.load(f)
    return payload if isinstance(payload, dict) else {}
  except (OSError, TypeError, ValueError, json.JSONDecodeError):
    return {}


def write_json_atomic(path, payload):
  path = Path(path)
  try:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)
  except OSError:
    pass


def iso_age_seconds(value, now_epoch=None):
  try:
    timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
  except (TypeError, ValueError):
    return None
  return max(0.0, (time.time() if now_epoch is None else now_epoch) - timestamp)


def service_timestamps_payload(sm, services):
  now_monotonic = time.monotonic()
  result = {}
  for service in services:
    receive_time = float(sm.recv_time.get(service, 0.0))
    age = now_monotonic - receive_time if receive_time > 0.0 else None
    seen = bool(sm.seen.get(service, False))
    alive = bool(sm.alive.get(service, False)) if hasattr(sm, "alive") else seen
    freq_ok = bool(sm.freq_ok.get(service, False)) if hasattr(sm, "freq_ok") else alive
    result[service] = {
      "seen": seen,
      "alive": alive,
      "frequencyOk": freq_ok,
      "ageSeconds": round(max(0.0, age), 3) if age is not None else None,
    }
  return result


def connection_state(ok, detail, updated_at=None, age_seconds=None):
  return {
    "state": "ok" if ok else "fault",
    "detail": detail,
    "updatedAt": updated_at,
    "ageSeconds": round(age_seconds, 1) if age_seconds is not None else None,
  }


def connection_diagnostics(sm, services, gps, panda, vehicle, openpilot):
  timestamps = service_timestamps_payload(sm, services)
  navdy = read_json_file(NAVDY_HEALTH_PATH)
  navdy_age = iso_age_seconds(navdy.get("updatedAt"))
  upload = read_json_file(UPLOAD_HEALTH_PATH)
  upload_age = iso_age_seconds(upload.get("lastSuccessAt"))
  can = vehicle.get("can") if isinstance(vehicle, dict) else {}
  car_seen = timestamps.get("carState", {}).get("seen", False)
  car_ok = (not vehicle.get("available", False)) or (
    car_seen and bool(can.get("valid", False)) and not bool(can.get("timeout", False)))
  panda_ok = panda is not None and not panda.get("heartbeatLost", False) and panda.get("faultStatus") in ("none", "normal", "")
  navdy_ok = navdy_age is not None and navdy_age <= 8.0 and bool(navdy.get("transportConnected", False))
  gps_timestamp_ms = gps.get("timestampMillis")
  gps_age = max(0.0, time.time() - float(gps_timestamp_ms) / 1000.0) if gps_timestamp_ms else None
  service_age = lambda name: timestamps.get(name, {}).get("ageSeconds")
  return {
    "comma": connection_state(timestamps.get("deviceState", {}).get("alive", False), "cereal device state",
                              age_seconds=service_age("deviceState")),
    "vehicleCan": connection_state(car_ok, "CAN valid" if car_ok else "CAN unavailable or invalid",
                                   age_seconds=service_age("carState")),
    "panda": connection_state(panda_ok, "safety interface online" if panda_ok else "panda fault or heartbeat missing",
                              age_seconds=service_age("pandaStates")),
    "gps": connection_state(bool(gps.get("fresh", False)), str(gps.get("source") or "unavailable"),
                            age_seconds=gps_age),
    "openpilot": connection_state(bool(openpilot.get("available", False)), str(openpilot.get("state") or "unavailable"),
                                  age_seconds=service_age("selfdriveState")),
    "navdy": connection_state(navdy_ok, str(navdy.get("transport") or "disconnected"),
                              navdy.get("updatedAt"), navdy_age),
    "cloud": connection_state(upload_age is not None and upload_age <= 600.0,
                              "last telemetry upload", upload.get("lastSuccessAt"), upload_age),
  }


def radar_cutin_payload(sm):
  try:
    lead = sm["radarState"].leadCutInRisk
    if not bool(lead.status):
      return cutin_risk_stage(0.0)
    result = cutin_risk_stage(lead.score, lead.dRel, lead.vRel)
    result.update({
      "trackId": int(lead.radarTrackId),
      "distanceM": round(float(lead.dRel), 2),
      "lateralM": round(float(lead.yRel), 2),
      "relativeSpeedMps": round(float(lead.vRel), 2),
    })
    return result
  except Exception:
    return cutin_risk_stage(0.0)


def read_config():
  try:
    identity = ensure_wayon_identity(CONFIG_PATH)
    if identity is not None:
      return identity
  except Exception as exc:
    print(f"Wayon cloud: identity setup failed: {exc}")

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


def get_json(config, path, params=None):
  response = requests.get(
    f"{config['endpoint']}{path}",
    params=params,
    headers={
      "Authorization": f"Bearer {config['token']}",
      "User-Agent": USER_AGENT,
    },
    timeout=15,
  )
  response.raise_for_status()
  return response.json() if response.content else {}


def write_ambient_override(params, serialized, path=AMBIENT_OVERRIDE_PATH):
  try:
    params.put("WayonAmbientOverride", serialized)
    return
  except Exception:
    pass

  path = Path(path)
  path.parent.mkdir(parents=True, exist_ok=True)
  temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
  temporary.write_text(serialized, encoding="utf-8")
  os.replace(temporary, path)


def apply_ambient_command(params, command, path=AMBIENT_OVERRIDE_PATH):
  if not isinstance(command, dict) or not command.get("id"):
    return False
  payload = command.get("payload")
  if not isinstance(payload, dict):
    return False

  stored = {
    **payload,
    "id": str(command["id"]),
    "deviceId": str(command.get("deviceId") or ""),
    "createdAt": command.get("createdAt"),
    "expiresAt": command.get("expiresAt"),
  }
  write_ambient_override(params, json.dumps(stored, separators=(",", ":")), path)
  return True


def poll_ambient_command(config, params, device_id):
  response = get_json(config, "/api/ambient/command", {"deviceId": device_id})
  command = response.get("command") if isinstance(response, dict) else None
  if not apply_ambient_command(params, command):
    return False

  post_json(config, "/api/ambient/ack", {
    "id": command["id"],
    "deviceId": device_id,
    "applied": True,
    "stage": "comma_params",
    "acknowledgedAt": utc_now(),
  })
  return True


def fetch_vehicle_status(config):
  response = requests.get(
    str(config.get("vehicle_status_url", DEFAULT_VEHICLE_STATUS_URL)),
    headers={"User-Agent": USER_AGENT},
    timeout=5,
  )
  response.raise_for_status()
  payload = response.json()
  return payload if isinstance(payload, dict) else {}


def impact_media_directory(event_id, media_root=IMPACT_MEDIA_ROOT):
  safe_id = "".join(character for character in str(event_id) if character.isalnum() or character in "-_")[:128]
  return Path(media_root) / (safe_id or "unknown")


def jpeg_bytes(array, quality=78):
  from PIL import Image

  buffer = io.BytesIO()
  Image.fromarray(array).save(buffer, "JPEG", quality=quality, optimize=True)
  return buffer.getvalue()


def write_bytes_atomic(path, data):
  path.parent.mkdir(parents=True, exist_ok=True)
  temporary = path.with_suffix(path.suffix + ".tmp")
  temporary.write_bytes(data)
  os.replace(temporary, path)


def read_impact_media(event_id, media_root=IMPACT_MEDIA_ROOT):
  directory = impact_media_directory(event_id, media_root)
  media = {}
  for camera in ("wide", "driver"):
    path = directory / f"{camera}.jpg"
    if path.is_file():
      media[camera] = path.read_bytes()

  captured_at = None
  try:
    captured_at = json.loads((directory / "capture.json").read_text(encoding="utf-8")).get("capturedAt")
  except (OSError, TypeError, ValueError):
    pass
  return media, captured_at


def capture_and_store_impact_media(event_id, media_root=IMPACT_MEDIA_ROOT, capture_fn=None):
  media, captured_at = read_impact_media(event_id, media_root)
  if len(media) == 2:
    return media, captured_at

  capture_fn = capture_fn or capture_offroad_images
  wide, driver = capture_fn()
  directory = impact_media_directory(event_id, media_root)
  captured_at = captured_at or utc_now()
  for camera, image in (("wide", wide), ("driver", driver)):
    if camera not in media and image is not None:
      write_bytes_atomic(directory / f"{camera}.jpg", jpeg_bytes(image))
  write_bytes_atomic(
    directory / "capture.json",
    json.dumps({"capturedAt": captured_at}, separators=(",", ":")).encode("utf-8"),
  )
  return read_impact_media(event_id, media_root)


def remove_impact_media(event_id, media_root=IMPACT_MEDIA_ROOT):
  shutil.rmtree(impact_media_directory(event_id, media_root), ignore_errors=True)


def _impact_retry_due(event, now=None):
  retry_at = str(event.get("nextUploadAt") or "")
  if not retry_at:
    return True
  try:
    retry_time = datetime.fromisoformat(retry_at.replace("Z", "+00:00"))
    if retry_time.tzinfo is None:
      retry_time = retry_time.replace(tzinfo=timezone.utc)
    return (now or datetime.now(timezone.utc)) >= retry_time
  except ValueError:
    return True


def _update_queued_impact(event_id, values, queue_path):
  if queue_path is None:
    return update_impact_event(event_id, values)
  return update_impact_event(event_id, values, queue_path)


def _defer_impact_upload(event, event_id, queue_path, now=None):
  attempts = int(event.get("uploadAttempts", 0)) + 1
  delay = IMPACT_UPLOAD_RETRY_DELAYS_S[min(attempts - 1, len(IMPACT_UPLOAD_RETRY_DELAYS_S) - 1)]
  retry_at = (now or datetime.now(timezone.utc)).timestamp() + delay
  retry_iso = datetime.fromtimestamp(retry_at, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
  _update_queued_impact(event_id, {"uploadAttempts": attempts, "nextUploadAt": retry_iso}, queue_path)


def upload_pending_impacts(config, device_id, queue_path=None, limit=3,
                           media_root=IMPACT_MEDIA_ROOT, capture_fn=None, now=None):
  uploaded = 0
  for _ in range(max(1, limit)):
    event = peek_impact_event() if queue_path is None else peek_impact_event(queue_path)
    if event is None:
      break
    if not _impact_retry_due(event, now):
      break

    payload = {**event, "deviceId": device_id}
    event_id = str(event.get("id", ""))
    media = {}
    captured_at = None
    attempts = int(event.get("captureAttempts", 0))
    capture_complete = False

    try:
      if event.get("captureRequested"):
        media, captured_at = capture_and_store_impact_media(event_id, media_root, capture_fn)
        attempts += 1
        capture_complete = all(camera in media for camera in ("wide", "driver"))

      # Persist completion of the event upload before attempting media. A media
      # retry must not resend the notification-bearing /api/impact request.
      if not event.get("impactUploaded"):
        post_json(config, "/api/impact", payload)
        event = _update_queued_impact(event_id, {
          "impactUploaded": True,
          "uploadAttempts": 0,
          "nextUploadAt": None,
        }, queue_path) or {**event, "impactUploaded": True}

      if event.get("captureRequested"):
        if not capture_complete and attempts < MAX_IMPACT_CAPTURE_ATTEMPTS:
          _update_queued_impact(event_id, {"captureAttempts": attempts}, queue_path)
          raise RuntimeError(f"impact camera capture incomplete ({attempts}/{MAX_IMPACT_CAPTURE_ATTEMPTS})")

        capture_status = "complete" if capture_complete else "partial" if media else "failed"
        post_json(config, "/api/impact-media", {
          "id": event_id,
          "deviceId": device_id,
          "capturedAt": captured_at or utc_now(),
          "captureStatus": capture_status,
          "captureAttempts": attempts,
          "wideJpegBase64": base64.b64encode(media["wide"]).decode("ascii") if "wide" in media else None,
          "driverJpegBase64": base64.b64encode(media["driver"]).decode("ascii") if "driver" in media else None,
        })
        remove_impact_media(event_id, media_root)
    except Exception:
      latest = peek_impact_event() if queue_path is None else peek_impact_event(queue_path)
      _defer_impact_upload(latest or event, event_id, queue_path, now)
      raise

    if queue_path is None:
      remove_impact_event(event_id)
    else:
      remove_impact_event(event_id, queue_path)
    uploaded += 1
  return uploaded


def _vehicle_event_datetime(event):
  try:
    parsed = datetime.fromisoformat(str(event.get("occurredAt", "")).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
  except (TypeError, ValueError):
    return None


def _next_door_relock(events, unlock_event):
  unlock_at = _vehicle_event_datetime(unlock_event)
  if unlock_at is None:
    return None, None
  for event in events[1:]:
    if event.get("eventType") != "door_lock":
      continue
    if event.get("locked") is not True:
      return None, None
    locked_at = _vehicle_event_datetime(event)
    if locked_at is None:
      return event, None
    return event, (locked_at - unlock_at).total_seconds()
  return None, None


def _epoch_seconds(value):
  if isinstance(value, str):
    value = value.rsplit("_", 1)[-1].strip()
  try:
    timestamp = float(value)
  except (TypeError, ValueError):
    return None
  if timestamp > 100_000_000_000:
    timestamp /= 1000.0
  return timestamp if timestamp > 0.0 and math.isfinite(timestamp) else None


def _matching_vehicle_refresh_marker(config, unlock_event, fetch_status_fn):
  unlock_at = _vehicle_event_datetime(unlock_event)
  if unlock_at is None:
    return None
  try:
    status = fetch_status_fn(config)
  except Exception as exc:
    print(f"Wayon vehicle: refresh marker unavailable, sending alerts: {exc}", flush=True)
    return None

  window_s = max(0.0, float(config.get(
    "door_lock_refresh_marker_window_s",
    DEFAULT_DOOR_LOCK_REFRESH_MARKER_WINDOW_S,
  )))
  unlock_timestamp = unlock_at.timestamp()
  for key in ("refresh_action", "cmd_refresh"):
    marker_timestamp = _epoch_seconds(status.get(key))
    if marker_timestamp is None:
      continue
    elapsed_s = unlock_timestamp - marker_timestamp
    if -DOOR_LOCK_REFRESH_MARKER_FUTURE_TOLERANCE_S <= elapsed_s <= window_s:
      return {"source": key, "timestamp": marker_timestamp, "elapsedSeconds": elapsed_s}
  return None


def _record_suppressed_vehicle_pair(unlock_event, relock_event, elapsed_s, path,
                                    refresh_marker=None):
  record = {
    "recordedAt": utc_now(),
    "reason": "vehicle_status_refresh",
    "elapsedSeconds": round(elapsed_s, 3),
    "unlockEvent": unlock_event,
    "relockEvent": relock_event,
  }
  if refresh_marker is not None:
    record["refreshMarker"] = refresh_marker
  temp_path = path.with_suffix(path.suffix + ".tmp")
  try:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_text(json.dumps(record, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    os.replace(temp_path, path)
  except OSError as exc:
    print(f"Wayon vehicle: failed to record suppressed pair: {exc}", flush=True)


def upload_pending_vehicle_events(config, device_id, queue_path=None, limit=3, now=None,
                                  suppressed_state_path=None, fetch_status_fn=None):
  uploaded = 0
  fetch_status_fn = fetch_status_fn or fetch_vehicle_status
  for _ in range(max(1, limit)):
    events = peek_vehicle_events() if queue_path is None else peek_vehicle_events(queue_path)
    event = events[0] if events else None
    if event is None:
      break

    if event.get("eventType") == "door_lock" and event.get("locked") is False:
      filter_max_s = max(0.0, float(config.get(
        "door_lock_notification_pair_window_s",
        DEFAULT_DOOR_LOCK_WAKE_FILTER_MAX_S,
      )))
      filter_min_s = min(filter_max_s, max(0.0, float(config.get(
        "door_lock_notification_pair_min_s",
        DEFAULT_DOOR_LOCK_WAKE_FILTER_MIN_S,
      ))))
      relock_event, relock_elapsed_s = _next_door_relock(events, event)

      if relock_event is not None and relock_elapsed_s is not None \
          and filter_min_s <= relock_elapsed_s <= filter_max_s:
        refresh_marker = _matching_vehicle_refresh_marker(config, event, fetch_status_fn)
        if refresh_marker is not None:
          state_path = suppressed_state_path or LAST_SUPPRESSED_VEHICLE_PAIR_PATH
          _record_suppressed_vehicle_pair(
            event, relock_event, relock_elapsed_s, state_path, refresh_marker)
          event_ids = {str(event.get("id", "")), str(relock_event.get("id", ""))}
          if queue_path is None:
            remove_vehicle_events(event_ids)
          else:
            remove_vehicle_events(event_ids, queue_path)
          print(
            f"Wayon vehicle: suppressed status refresh pair ({relock_elapsed_s:.3f}s)",
            flush=True,
          )
          continue

      if relock_event is None:
        occurred_at = _vehicle_event_datetime(event)
        current_time = now or datetime.now(timezone.utc)
        if occurred_at is not None and (current_time - occurred_at).total_seconds() <= filter_max_s:
          break

    payload = {**event, "deviceId": device_id}
    post_json(config, "/api/vehicle-event", payload)
    event_id = str(event.get("id", ""))
    if queue_path is None:
      remove_vehicle_event(event_id)
    else:
      remove_vehicle_event(event_id, queue_path)
    uploaded += 1
  return uploaded


def enum_name(value):
  try:
    return str(value).split(".")[-1]
  except Exception:
    return ""


def numeric_list(values):
  try:
    return [float(value) for value in values]
  except Exception:
    return []


def device_details_payload(device_state):
  temperatures = {
    "cpu": numeric_list(device_state.cpuTempC),
    "gpu": numeric_list(device_state.gpuTempC),
    "dsp": float(device_state.dspTempC),
    "memory": float(device_state.memoryTempC),
    "modem": numeric_list(device_state.modemTempC),
    "pmic": numeric_list(device_state.pmicTempC),
    "intake": float(device_state.intakeTempC),
    "exhaust": float(device_state.exhaustTempC),
    "gnss": float(device_state.gnssTempC),
    "bottomSoc": float(device_state.bottomSocTempC),
    "max": float(device_state.maxTempC),
  }
  try:
    temperatures["zones"] = [
      {"name": str(zone.name), "tempC": float(zone.temp)}
      for zone in device_state.thermalZones
    ]
  except Exception:
    temperatures["zones"] = []

  return {
    "type": enum_name(device_state.deviceType),
    "network": {
      "type": enum_name(device_state.networkType),
      "strength": enum_name(device_state.networkStrength),
      "metered": bool(device_state.networkMetered),
    },
    "usage": {
      "freeSpacePercent": float(device_state.freeSpacePercent),
      "memoryPercent": int(device_state.memoryUsagePercent),
      "gpuPercent": int(device_state.gpuUsagePercent),
      "cpuPercent": [int(value) for value in device_state.cpuUsagePercent],
    },
    "power": {
      "drawW": float(device_state.powerDrawW),
      "somDrawW": float(device_state.somPowerDrawW),
      "offroadUsageUwh": int(device_state.offroadPowerUsageUwh),
      "offroadUsageWh": float(device_state.offroadPowerUsageUwh) / 1_000_000.0,
      "carBatteryCapacityUwh": int(device_state.carBatteryCapacityUwh),
      "carBatteryCapacityWh": float(device_state.carBatteryCapacityUwh) / 1_000_000.0,
    },
    "thermal": {
      "status": enum_name(device_state.thermalStatus),
      "fanPercent": int(device_state.fanSpeedPercentDesired),
      "temperaturesC": temperatures,
    },
    "screenBrightnessPercent": int(device_state.screenBrightnessPercent),
  }


def panda_details_payload(panda_state):
  if panda_state is None:
    return None

  voltage_v = voltage_v_from_raw(panda_state.voltage)
  current_ma = current_ma_from_raw(panda_state.current)
  return {
    "type": enum_name(panda_state.pandaType),
    "ignitionLine": bool(panda_state.ignitionLine),
    "ignitionCan": bool(panda_state.ignitionCan),
    "voltageV": voltage_v,
    "currentMa": current_ma,
    "estimatedPowerW": voltage_v * current_ma / 1000.0 if voltage_v is not None and current_ma is not None else None,
    "faultStatus": enum_name(panda_state.faultStatus),
    "faults": [enum_name(fault) for fault in panda_state.faults],
    "uptimeS": int(panda_state.uptime),
    "heartbeatLost": bool(panda_state.heartbeatLost),
    "interruptLoad": float(panda_state.interruptLoad),
    "rxBufferOverflow": int(panda_state.rxBufferOverflow),
    "txBufferOverflow": int(panda_state.txBufferOverflow),
    "spiErrorCount": int(panda_state.spiErrorCount),
    "harnessStatus": enum_name(panda_state.harnessStatus),
    "controlsAllowed": bool(panda_state.controlsAllowed),
    "controlsAllowedLateral": bool(panda_state.controlsAllowedLateral),
    "controlsAllowedLongitudinal": bool(panda_state.controlsAllowedLongitudinal),
    "safetyModel": enum_name(panda_state.safetyModel),
    "safetyParam": int(panda_state.safetyParam),
    "safetyRxInvalid": int(panda_state.safetyRxInvalid),
    "safetyTxBlocked": int(panda_state.safetyTxBlocked),
    "safetyRxChecksInvalid": bool(panda_state.safetyRxChecksInvalid),
  }


def vehicle_details_payload(sm, started):
  if not started:
    return {"available": False, "reason": "offroad"}

  try:
    car_state = sm["carState"]
    cruise = car_state.cruiseState
    speed = car_state_speed_payload(car_state)
    return {
      "available": True,
      "speedMps": speed["speedMps"],
      "speedKph": speed["speedMps"] * 3.6,
      "speedSource": speed["source"],
      "rawSpeedMps": float(car_state.vEgoRaw),
      "accelerationMps2": float(car_state.aEgo),
      "yawRateRadPerSec": float(car_state.yawRate),
      "standstill": bool(car_state.standstill),
      "gear": enum_name(car_state.gearShifter),
      "steeringAngleDeg": float(car_state.steeringAngleDeg),
      "steeringRateDegPerSec": float(car_state.steeringRateDeg),
      "steeringPressed": bool(car_state.steeringPressed),
      "gasPressed": bool(car_state.gasPressed),
      "brakePressed": bool(car_state.brakePressed),
      "parkingBrake": bool(car_state.parkingBrake),
      "brakeHoldActive": bool(car_state.brakeHoldActive),
      "leftBlinker": bool(car_state.leftBlinker),
      "rightBlinker": bool(car_state.rightBlinker),
      "leftBlindspot": bool(car_state.leftBlindspot),
      "rightBlindspot": bool(car_state.rightBlindspot),
      "doorOpen": bool(car_state.doorOpen),
      "seatbeltUnlatched": bool(car_state.seatbeltUnlatched),
      "fuelGauge": float(car_state.fuelGauge),
      "charging": bool(car_state.charging),
      "can": {
        "valid": bool(car_state.canValid),
        "timeout": bool(car_state.canTimeout),
        "errorCounter": int(car_state.canErrorCounter),
      },
      "steeringFault": {
        "temporary": bool(car_state.steerFaultTemporary),
        "permanent": bool(car_state.steerFaultPermanent),
      },
      "cruise": {
        "enabled": bool(cruise.enabled),
        "available": bool(cruise.available),
        "standstill": bool(cruise.standstill),
        "nonAdaptive": bool(cruise.nonAdaptive),
        "speedMps": float(cruise.speed),
        "speedKph": float(cruise.speed) * 3.6,
        "clusterSpeedMps": float(cruise.speedCluster),
      },
    }
  except Exception:
    return {"available": False, "reason": "carState_unavailable"}


def openpilot_details_payload(sm):
  try:
    state = sm["selfdriveState"]
    return {
      "available": True,
      "state": enum_name(state.state),
      "enabled": bool(state.enabled),
      "active": bool(state.active),
      "engageable": bool(state.engageable),
      "experimentalMode": bool(state.experimentalMode),
      "personality": enum_name(state.personality),
      "alert": {
        "text1": str(state.alertText1),
        "text2": str(state.alertText2),
        "type": str(state.alertType),
        "status": enum_name(state.alertStatus),
        "size": enum_name(state.alertSize),
        "sound": enum_name(state.alertSound),
        "hudVisual": enum_name(state.alertHudVisual),
      },
    }
  except Exception:
    return {"available": False}


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


def gps_payload(sm, params):
  candidates = []
  now_monotonic = time.monotonic()
  now_millis = int(time.time() * 1000)
  for socket in ("gpsLocationExternal", "gpsLocation"):
    try:
      gps = sm[socket]
      receive_age = now_monotonic - sm.recv_time.get(socket, 0.0)
      timestamp_millis = int(gps.unixTimestampMillis)
      timestamp_fresh = timestamp_millis <= 0 or abs(now_millis - timestamp_millis) <= GPS_TIMESTAMP_MAX_AGE_MS
      if (sm.seen.get(socket, False) and receive_age <= GPS_SERVICE_MAX_AGE_S and timestamp_fresh and
          gps.hasFix and abs(gps.latitude) > 0.001 and abs(gps.longitude) > 0.001):
        candidates.append((sm.recv_time.get(socket, 0), gps))
    except Exception:
      continue

  if not candidates:
    fallback = last_gps_payload(params)
    if fallback:
      timestamp_millis = fallback.get("timestampMillis", 0)
      fallback["fresh"] = bool(timestamp_millis and abs(now_millis - timestamp_millis) <= LAST_GPS_POSITION_MAX_AGE_MS)
      return fallback
    return {"fresh": False, "source": "unavailable"}

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
    "fresh": True,
  }


def resolve_onroad_state(device_state_started: bool, started_override: bool | None = None) -> bool:
  return bool(device_state_started) if started_override is None else bool(started_override)


def telemetry_payload(sm, params, device_id, started_override: bool | None = None):
  device_state = sm["deviceState"]
  panda_state = first_panda_state(sm["pandaStates"])
  started = resolve_onroad_state(device_state.started, started_override)
  vehicle_speed = vehicle_speed_payload(sm, started)

  ignition = False
  voltage_v = None
  current_ma = None
  if panda_state is not None:
    ignition = bool(panda_state.ignitionLine or panda_state.ignitionCan)
    voltage_v = voltage_v_from_raw(panda_state.voltage)
    current_ma = current_ma_from_raw(panda_state.current)

  power_w = voltage_v * current_ma / 1000.0 if voltage_v is not None and current_ma is not None else None

  device = device_details_payload(device_state)
  panda = panda_details_payload(panda_state)
  vehicle = vehicle_details_payload(sm, started)
  openpilot = openpilot_details_payload(sm)
  gps = gps_payload(sm, params)
  services = list(getattr(sm, "services", TELEMETRY_SERVICES if started else STATE_SERVICES))
  service_timestamps = service_timestamps_payload(sm, services)
  connections = connection_diagnostics(sm, services, gps, panda, vehicle, openpilot)
  connected = connections.get("comma", {}).get("state") == "ok" and connections.get("vehicleCan", {}).get("state") == "ok"
  system_state = resolve_operating_state(
    connected=connected,
    onroad=started,
    door_open=bool(vehicle.get("doorOpen", False)),
    gear=str(vehicle.get("gear") or "unknown"),
  )

  return {
    "schemaVersion": "wayon-telemetry-v3",
    "deviceId": device_id,
    "updatedAt": utc_now(),
    "timestamps": {
      "generatedAt": utc_now(),
      "services": service_timestamps,
    },
    "connections": connections,
    "systemState": system_state,
    "onroad": started,
    "ignition": ignition,
    "enabled": bool(openpilot.get("enabled", False)),
    "voltageV": voltage_v,
    "currentMa": current_ma,
    "powerW": power_w,
    "devicePowerW": float(device_state.powerDrawW),
    "thermalStatus": enum_name(device_state.thermalStatus),
    "fanPercent": int(device_state.fanSpeedPercentDesired),
    "screenBrightnessPercent": int(device_state.screenBrightnessPercent),
    "gps": gps,
    "vehicleSpeedMps": vehicle_speed.get("speedMps"),
    "vehicleSpeedSource": vehicle_speed.get("source"),
    "dongleId": get_param_str(params, "DongleId"),
    "device": device,
    "panda": panda,
    "vehicle": vehicle,
    "openpilot": openpilot,
    "cutInRisk": radar_cutin_payload(sm) if started else cutin_risk_stage(0.0),
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


def connection_status_signature(payload):
  return tuple(sorted(
    (name, str(item.get("state") or "unknown"))
    for name, item in (payload.get("connections") or {}).items()
    if isinstance(item, dict)
  ))


def health_event_from_telemetry(payload, previous_signature=None):
  signature = connection_status_signature(payload)
  voltage = payload.get("voltageV")
  thermal = str(payload.get("thermalStatus") or "").lower()
  panda = payload.get("panda") or {}
  cutin = payload.get("cutInRisk") or {}
  issues = []
  severity = "normal"
  if voltage is not None and float(voltage) <= 11.5:
    issues.append(f"12V battery {float(voltage):.1f}V")
    severity = "critical"
  elif voltage is not None and float(voltage) < 11.9:
    issues.append(f"12V battery {float(voltage):.1f}V")
    severity = "warning"
  if thermal in ("yellow", "red", "danger", "overheated"):
    issues.append(f"device thermal {thermal}")
    severity = "critical" if thermal in ("red", "danger", "overheated") else "warning"
  if str(panda.get("faultStatus") or "none").lower() not in ("", "none", "normal"):
    issues.append(f"safety interface {panda.get('faultStatus')}")
    severity = "warning" if severity == "normal" else severity
  cutin_level = int(cutin.get("level") or 0)
  if cutin_level >= 2:
    issues.append(f"cut-in risk {cutin.get('name') or cutin_level}")
    severity = "critical" if cutin_level >= 3 else "warning"
  health_signature = (signature, tuple(issues), severity)
  if health_signature == previous_signature:
    return None, health_signature
  faults = [name for name, state in signature if state != "ok"]
  details = faults + issues
  return {
    "id": f"health-{payload.get('deviceId', 'unknown')}-{int(time.time() * 1000)}",
    "deviceId": payload.get("deviceId"),
    "occurredAt": payload.get("updatedAt") or utc_now(),
    "category": "vehicle_health" if issues else "connection",
    "severity": "warning" if faults and severity == "normal" else severity,
    "title": "Vehicle attention required" if issues else "Connection degraded" if faults else "Connections restored",
    "detail": ", ".join(details) if details else "All monitored connections are healthy",
    "snapshot": {
      "connections": payload.get("connections") or {},
      "voltageV": voltage,
      "thermalStatus": payload.get("thermalStatus"),
      "systemState": payload.get("systemState"),
    },
  }, health_signature


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
  report_routes = state.get("drive_report_routes", [])
  if not isinstance(report_routes, list):
    report_routes = []
  return {
    "uploaded_routes": [str(route) for route in uploaded_routes],
    "drive_report_routes": [str(route) for route in report_routes],
  }


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
  report_routes = [route for route in state.get("drive_report_routes", []) if route != route_name]
  report_routes.insert(0, route_name)
  write_route_state({
    "uploaded_routes": uploaded_routes[:100],
    "drive_report_routes": report_routes[:100],
  })


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
  drive_report = DriveReportAccumulator(route_start)

  point_interval_s = float(config.get("route_point_interval_s", DEFAULT_ROUTE_POINT_INTERVAL))
  min_distance_m = float(config.get("route_point_min_distance_m", DEFAULT_ROUTE_POINT_MIN_DISTANCE_M))
  point_limit = int(config.get("route_point_limit", DEFAULT_ROUTE_POINT_LIMIT))

  for _, _, log_file in route_group["segments"]:
    try:
      reader = LogReader(str(log_file), sort_by_time=True, only_union_types=True)
      for msg in reader:
        which = msg.which()
        msg_mono = float(msg.logMonoTime) / 1e9
        if which in ("carState", "gpsLocationExternal", "gpsLocation"):
          if first_mono is None:
            first_mono = msg_mono
          last_mono = msg_mono
        drive_report.update(msg)

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
  analysis = drive_report.finalize(payload_route)

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
    "analysis": analysis,
    "route": payload_route,
  }


def upload_recent_route_summary(config, device_id):
  state = read_route_state()
  uploaded_routes = set(state.get("uploaded_routes", []))
  report_routes = set(state.get("drive_report_routes", []))
  max_age_s = float(config.get("route_summary_max_age_s", DEFAULT_ROUTE_SUMMARY_MAX_AGE))
  grace_period_s = float(config.get("route_summary_grace_period_s", DEFAULT_ROUTE_SUMMARY_GRACE_PERIOD))

  route_groups = recent_route_groups(max_age_s)
  if not route_groups:
    return False

  # Only summarize the latest route. This avoids slowly backfilling old drives
  # after a reboot while still catching the route that just finished.
  route_group = route_groups[0]
  route_name = route_group["route_name"]
  if route_name in uploaded_routes and route_name in report_routes:
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
  return base64.b64encode(jpeg_bytes(array, quality=72)).decode("ascii")


def enhance_wide_snapshot(image, target_median=WAYON_WIDE_SNAPSHOT_TARGET_MEDIAN,
                          min_gamma=WAYON_WIDE_SNAPSHOT_MIN_GAMMA):
  import numpy as np

  if image is None:
    return None

  frame = np.asarray(image)
  if frame.ndim != 3 or frame.shape[2] < 3 or frame.size == 0:
    return image

  rgb = frame[:, :, :3].astype(np.float32)
  luma = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
  median = float(np.median(luma))
  target = max(1.0, min(254.0, float(target_median)))
  if not math.isfinite(median) or median <= 0.0 or median >= target:
    return image

  gamma = math.log(target / 255.0) / math.log(max(1.0, median) / 255.0)
  gamma = max(0.1, min(1.0, max(float(min_gamma), gamma)))
  corrected_luma = 255.0 * np.power(np.clip(luma / 255.0, 0.0, 1.0), gamma)
  gain = corrected_luma / np.maximum(luma, 1.0)

  enhanced = frame.copy()
  enhanced[:, :, :3] = np.clip(rgb * gain[:, :, None], 0.0, 255.0).astype(frame.dtype)
  return enhanced


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

  if not params.get_bool("IsOffroad"):
    return None, None

  lease = CameraLease("wayon_snapshot", 45.0)
  if not lease.acquire():
    return None, None

  snapshot_flag_set = False
  try:
    if params.get_bool("IsTakingSnapshot"):
      return None, None

    params.put_bool("IsTakingSnapshot", True, block=True)
    snapshot_flag_set = True
    set_offroad_alert("Offroad_IsTakingSnapshot", True)
    started_camerad = False

    try:
      subprocess.check_call(["pgrep", "camerad"])
      return None, None
    except subprocess.CalledProcessError:
      pass

    if not PC:
      managed_processes["camerad"].start()
      started_camerad = True

    try:
      wide, driver = get_snapshots(
        "wideRoadCameraState",
        "driverCameraState",
        warmup_s=WAYON_WIDE_SNAPSHOT_WARMUP_S,
        front_warmup_s=WAYON_DRIVER_SNAPSHOT_WARMUP_S,
        timeout_s=OFFROAD_SNAPSHOT_TIMEOUT_S,
        exposure_ready_ratio=WAYON_SNAPSHOT_EXPOSURE_READY_RATIO,
        exposure_stable_frames=WAYON_SNAPSHOT_EXPOSURE_STABLE_FRAMES,
        exposure_max_wait_s=WAYON_SNAPSHOT_EXPOSURE_MAX_WAIT_S,
      )
      return enhance_wide_snapshot(wide), driver
    finally:
      if started_camerad:
        managed_processes["camerad"].stop()
  finally:
    if snapshot_flag_set:
      params.put_bool("IsTakingSnapshot", False, block=True)
      set_offroad_alert("Offroad_IsTakingSnapshot", False)
    lease.release()


def main():
  set_core_affinity([0, 1, 2, 3])
  params = Params()
  sm = messaging.SubMaster(TELEMETRY_SERVICES)

  config = None
  next_config_load = 0.0
  next_telemetry = 0.0
  next_route_summary = 0.0
  next_snapshot = 0.0
  next_impact_upload = 0.0
  next_vehicle_event_upload = 0.0
  next_ambient_command_poll = 0.0
  previous_started = False
  last_telemetry_signature = None
  last_telemetry_upload_at = 0.0
  last_connection_signature = None

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
    if now >= next_ambient_command_poll:
      try:
        poll_ambient_command(config, params, device_id)
        next_ambient_command_poll = now + max(1.0, float(config.get(
          "ambient_command_poll_interval", DEFAULT_AMBIENT_COMMAND_POLL_INTERVAL)))
      except Exception as exc:
        print(f"Wayon cloud: ambient command poll failed: {exc}")
        next_ambient_command_poll = now + 60.0

    if not sm.seen["deviceState"]:
      time.sleep(LOOP_SLEEP_OFFROAD)
      continue

    started = bool(sm["deviceState"].started)

    if now >= next_impact_upload:
      try:
        uploaded_impacts = upload_pending_impacts(config, device_id)
        next_impact_upload = now + (0.2 if uploaded_impacts >= 3 else 1.0)
      except Exception as exc:
        print(f"Wayon cloud: impact upload failed: {exc}")
        next_impact_upload = now + 15.0

    if now >= next_vehicle_event_upload:
      try:
        uploaded_vehicle_events = upload_pending_vehicle_events(config, device_id)
        next_vehicle_event_upload = now + (0.2 if uploaded_vehicle_events >= 3 else 1.0)
      except Exception as exc:
        print(f"Wayon cloud: vehicle event upload failed: {exc}")
        next_vehicle_event_upload = now + 15.0

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
        payload = telemetry_payload(sm, params, device_id, started_override=started)
        signature = telemetry_signature(payload)
        heartbeat_due = now - last_telemetry_upload_at >= max(5.0, telemetry_interval)
        if signature != last_telemetry_signature or heartbeat_due:
          post_json(config, "/api/telemetry", payload)
          last_telemetry_signature = signature
          last_telemetry_upload_at = now
          write_json_atomic(UPLOAD_HEALTH_PATH, {
            "lastSuccessAt": utc_now(),
            "lastReason": "state_changed" if not heartbeat_due else "heartbeat",
          })
          health_event, last_connection_signature = health_event_from_telemetry(
            payload, last_connection_signature)
          if health_event is not None:
            post_json(config, "/api/health-event", health_event)
        next_telemetry = now + (5.0 if started else 15.0)
      except Exception as exc:
        print(f"Wayon cloud: telemetry upload failed: {exc}")
        write_json_atomic(UPLOAD_HEALTH_PATH, {
          "lastSuccessAt": read_json_file(UPLOAD_HEALTH_PATH).get("lastSuccessAt"),
          "lastFailureAt": utc_now(),
          "lastError": str(exc)[:240],
        })
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
