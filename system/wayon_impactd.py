#!/usr/bin/env python3
import json
import os
import time
from pathlib import Path

from cereal import messaging

from openpilot.system.wayon_impact import ImpactDetector, enqueue_impact_event, utc_now


CONFIG_PATH = Path(os.getenv("WAYON_CLOUD_CONFIG", "/data/wayon_cloud/config.json"))
STATUS_PATH = Path(os.getenv("WAYON_IMPACT_STATUS", "/data/wayon_cloud/impact_status.json"))


def read_config() -> dict:
  try:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
      config = json.load(handle)
      return config if isinstance(config, dict) else {}
  except (OSError, ValueError):
    return {}


def detector_from_config(config: dict) -> ImpactDetector:
  return ImpactDetector(
    arm_delay_s=float(config.get("impact_arm_delay_s", 45.0)),
    warmup_s=float(config.get("impact_warmup_s", 3.0)),
    cooldown_s=float(config.get("impact_cooldown_s", 30.0)),
    min_dynamic_g=float(config.get("impact_min_dynamic_g", 0.38)),
    min_jerk_g_per_s=float(config.get("impact_min_jerk_g_per_s", 3.5)),
    strong_dynamic_g=float(config.get("impact_strong_dynamic_g", 0.85)),
  )


def write_status(state: str, **details) -> None:
  STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
  payload = {"state": state, "updatedAt": utc_now(), **details}
  temporary = STATUS_PATH.with_suffix(".tmp")
  temporary.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
  os.replace(temporary, STATUS_PATH)


def sensor_vector(message, measurement: str) -> tuple[float, float, float] | None:
  try:
    values = getattr(message, measurement).v
    if len(values) != 3:
      return None
    return tuple(float(value) for value in values)
  except Exception:
    return None


def main() -> None:
  config = read_config()
  detector = detector_from_config(config)
  sm = messaging.SubMaster(["accelerometer", "gyroscope"], poll="accelerometer")
  latest_gyro = (0.0, 0.0, 0.0)
  received_first_sample = False
  reported_armed = False

  write_status("starting", armDelayS=detector.arm_delay_s)
  print(f"Wayon impact: waiting for IMU, arm delay {detector.arm_delay_s:.0f}s", flush=True)

  while True:
    sm.update(1000)
    now = time.monotonic()

    if sm.updated["gyroscope"] and sm.valid["gyroscope"]:
      gyro = sensor_vector(sm["gyroscope"], "gyroUncalibrated")
      if gyro is not None:
        latest_gyro = gyro

    if not sm.updated["accelerometer"] or not sm.valid["accelerometer"]:
      continue
    accel = sensor_vector(sm["accelerometer"], "acceleration")
    if accel is None:
      continue

    if not received_first_sample:
      received_first_sample = True
      write_status("warmingUp", armDelayS=detector.arm_delay_s)
      print("Wayon impact: IMU samples received", flush=True)

    event = detector.update(accel, latest_gyro, now)
    if detector.armed and not reported_armed:
      reported_armed = True
      write_status("armed", armDelayS=detector.arm_delay_s)
      print("Wayon impact: armed", flush=True)

    if event is not None:
      enqueue_impact_event(event)
      write_status("impactQueued", lastEvent=event)
      print(
        f"Wayon impact: queued {event['severity']} impact "
        f"({event['peakDynamicG']:.2f}g, {event['peakJerkGPerSec']:.1f}g/s)",
        flush=True,
      )


if __name__ == "__main__":
  main()
