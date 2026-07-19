#!/usr/bin/env python3
import json
import os
import time
from pathlib import Path

from cereal import messaging
from openpilot.system.wayon_impact import (
  DEFAULT_ARM_DELAY_S,
  DEFAULT_DOOR_LOCK_STATE_PATH,
  DEFAULT_IMPULSE_DYNAMIC_G,
  DEFAULT_IMPULSE_JERK_G_PER_S,
  DEFAULT_MIN_DYNAMIC_G,
  DEFAULT_MIN_JERK_G_PER_S,
  DEFAULT_STRONG_DYNAMIC_G,
  DoorLockTracker,
  ImpactDetector,
  append_impact_diagnostic,
  enqueue_impact_event,
  utc_now,
)

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
    arm_delay_s=float(config.get("impact_arm_delay_s", DEFAULT_ARM_DELAY_S)),
    warmup_s=float(config.get("impact_warmup_s", 3.0)),
    cooldown_s=float(config.get("impact_cooldown_s", 30.0)),
    min_dynamic_g=float(config.get("impact_min_dynamic_g", DEFAULT_MIN_DYNAMIC_G)),
    min_jerk_g_per_s=float(config.get("impact_min_jerk_g_per_s", DEFAULT_MIN_JERK_G_PER_S)),
    impulse_dynamic_g=float(config.get("impact_impulse_dynamic_g", DEFAULT_IMPULSE_DYNAMIC_G)),
    impulse_jerk_g_per_s=float(config.get("impact_impulse_jerk_g_per_s", DEFAULT_IMPULSE_JERK_G_PER_S)),
    strong_dynamic_g=float(config.get("impact_strong_dynamic_g", DEFAULT_STRONG_DYNAMIC_G)),
  )


def config_bool(config: dict, key: str, default: bool = False) -> bool:
  value = config.get(key, default)
  if isinstance(value, str):
    return value.strip().lower() in ("1", "true", "yes", "on")
  return bool(value)


def lock_tracker_from_config(config: dict) -> DoorLockTracker:
  return DoorLockTracker(
    required=config_bool(config, "impact_require_door_locked"),
    bus=int(config.get("impact_lock_can_bus", 0)),
    address=int(config.get("impact_lock_can_address", 0x19D)),
    byte_index=int(config.get("impact_lock_can_byte", 4)),
    mask=int(config.get("impact_lock_can_mask", 0x01)),
    unlocked_value=int(config.get("impact_lock_can_unlocked_value", 0x01)),
    arm_delay_s=float(config.get("impact_lock_arm_delay_s", 3.0)),
    state_path=Path(config.get("impact_lock_state_path", DEFAULT_DOOR_LOCK_STATE_PATH)),
  )


def detector_status(detector: ImpactDetector, lock_tracker: DoorLockTracker) -> dict:
  return {
    "armDelayS": detector.arm_delay_s,
    "minDynamicG": detector.min_dynamic_g,
    "minJerkGPerSec": detector.min_jerk_g_per_s,
    "impulseDynamicG": detector.impulse_dynamic_g,
    "impulseJerkGPerSec": detector.impulse_jerk_g_per_s,
    "strongDynamicG": detector.strong_dynamic_g,
    "requireDoorLocked": lock_tracker.required,
    "doorsLocked": lock_tracker.locked,
  }


def operating_state(detector: ImpactDetector, lock_tracker: DoorLockTracker,
                    received_first_sample: bool, now: float) -> str:
  if not received_first_sample or not detector.armed:
    return "warmingUp"
  if lock_tracker.required and lock_tracker.locked is None:
    return "waitingForLockState"
  if lock_tracker.required and lock_tracker.locked is False:
    return "pausedUnlocked"
  if not lock_tracker.detection_allowed(now):
    return "lockSettling"
  return "armed"


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
  lock_tracker = lock_tracker_from_config(config)
  sm = messaging.SubMaster(["accelerometer", "gyroscope", "can"], poll="accelerometer")
  latest_gyro = (0.0, 0.0, 0.0)
  received_first_sample = False
  reported_state: str | None = None
  diagnostic_interval_s = max(10.0, float(config.get("impact_diagnostic_interval_s", 60.0)))
  next_diagnostic_at: float | None = None
  diagnostic_samples = 0
  peak_dynamic_g = 0.0
  peak_total_g = 0.0
  peak_jerk_g_per_s = 0.0
  peak_gyro_rad_per_s = 0.0

  write_status("starting", **detector_status(detector, lock_tracker))
  print(f"Wayon impact: waiting for IMU, arm delay {detector.arm_delay_s:.0f}s", flush=True)

  while True:
    sm.update(1000)
    now = time.monotonic()

    if sm.updated["can"]:
      for frame in sm["can"]:
        lock_tracker.update(int(frame.src), int(frame.address), bytes(frame.dat), now)

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
      print("Wayon impact: IMU samples received", flush=True)

    event = detector.update(accel, latest_gyro, now, lock_tracker.detection_allowed(now))
    state = operating_state(detector, lock_tracker, received_first_sample, now)
    if state != reported_state:
      reported_state = state
      write_status(state, **detector_status(detector, lock_tracker))
      print(f"Wayon impact: {state}", flush=True)

    if detector.armed and next_diagnostic_at is None:
      next_diagnostic_at = now + diagnostic_interval_s

    if detector.armed:
      diagnostic_samples += 1
      peak_dynamic_g = max(peak_dynamic_g, detector.last_dynamic_g)
      peak_total_g = max(peak_total_g, detector.last_total_g)
      peak_jerk_g_per_s = max(peak_jerk_g_per_s, detector.last_jerk_g_per_s)
      peak_gyro_rad_per_s = max(peak_gyro_rad_per_s, detector.last_gyro_rad_per_s)

    if detector.armed and next_diagnostic_at is not None and now >= next_diagnostic_at:
      diagnostic = {
        "measuredAt": utc_now(),
        "windowS": diagnostic_interval_s,
        "sampleCount": diagnostic_samples,
        "peakDynamicG": round(peak_dynamic_g, 4),
        "peakTotalG": round(peak_total_g, 4),
        "peakJerkGPerSec": round(peak_jerk_g_per_s, 2),
        "peakGyroRadPerSec": round(peak_gyro_rad_per_s, 4),
        **detector_status(detector, lock_tracker),
      }
      append_impact_diagnostic(diagnostic)
      write_status(state, recentPeak=diagnostic, **detector_status(detector, lock_tracker))
      next_diagnostic_at = now + diagnostic_interval_s
      diagnostic_samples = 0
      peak_dynamic_g = 0.0
      peak_total_g = 0.0
      peak_jerk_g_per_s = 0.0
      peak_gyro_rad_per_s = 0.0

    if event is not None:
      enqueue_impact_event(event)
      write_status("impactQueued", lastEvent=event, **detector_status(detector, lock_tracker))
      print(
        f"Wayon impact: queued {event['severity']} impact "
        f"({event['peakDynamicG']:.2f}g, {event['peakJerkGPerSec']:.1f}g/s)",
        flush=True,
      )


if __name__ == "__main__":
  main()
