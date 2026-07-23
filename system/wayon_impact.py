#!/usr/bin/env python3
import fcntl
import json
import math
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

STANDARD_GRAVITY = 9.80665
DEFAULT_IMPACT_QUEUE_PATH = Path(os.getenv(
  "WAYON_IMPACT_QUEUE", "/data/wayon_cloud/impact_queue.jsonl"))
DEFAULT_IMPACT_DIAGNOSTICS_PATH = Path(os.getenv(
  "WAYON_IMPACT_DIAGNOSTICS", "/data/wayon_cloud/impact_diagnostics.jsonl"))
DEFAULT_DOOR_LOCK_STATE_PATH = Path(os.getenv(
  "WAYON_DOOR_LOCK_STATE", "/data/wayon_cloud/door_lock_status.json"))
MAX_QUEUED_IMPACTS = 64
MAX_IMPACT_DIAGNOSTICS_BYTES = 512 * 1024
DEFAULT_ARM_DELAY_S = 5.0
DEFAULT_MIN_DYNAMIC_G = 0.018
DEFAULT_MIN_JERK_G_PER_S = 1.8
DEFAULT_IMPULSE_DYNAMIC_G = 0.028
DEFAULT_IMPULSE_JERK_G_PER_S = 5.0
DEFAULT_STRONG_DYNAMIC_G = 0.12
DETECTOR_VERSION = 3


def utc_now() -> str:
  return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def vector_norm(vector: tuple[float, float, float]) -> float:
  return math.sqrt(sum(component * component for component in vector))


class DoorLockTracker:
  def __init__(
    self,
    required: bool = False,
    bus: int = 0,
    address: int = 0x130,
    byte_index: int = 0,
    mask: int = 0x06,
    unlocked_value: int = 0x02,
    arm_delay_s: float = 3.0,
    state_path: Path = DEFAULT_DOOR_LOCK_STATE_PATH,
  ) -> None:
    self.required = required
    self.bus = bus
    self.address = address
    self.byte_index = max(0, byte_index)
    self.mask = max(1, min(0xFF, mask))
    self.unlocked_value = unlocked_value & self.mask
    self.arm_delay_s = max(0.0, arm_delay_s)
    self.state_path = state_path
    self.locked: bool | None = None
    self.locked_since: float | None = None
    self.observed_at: str | None = None
    self._load()

  def _load(self) -> None:
    if not self.required:
      return
    try:
      payload = json.loads(self.state_path.read_text(encoding="utf-8"))
      if isinstance(payload.get("locked"), bool):
        self.locked = payload["locked"]
        self.locked_since = -math.inf if self.locked else None
        self.observed_at = payload.get("observedAt")
    except (OSError, TypeError, ValueError):
      pass

  def _persist(self) -> None:
    self.state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
      "locked": self.locked,
      "observedAt": self.observed_at,
      "bus": self.bus,
      "address": self.address,
      "byteIndex": self.byte_index,
      "mask": self.mask,
    }
    temporary = self.state_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, self.state_path)

  def update(self, bus: int, address: int, data: bytes, now: float) -> bool:
    if bus != self.bus or address != self.address or len(data) <= self.byte_index:
      return False

    unlocked = data[self.byte_index] & self.mask == self.unlocked_value
    locked = not unlocked
    changed = locked != self.locked
    if not changed:
      return False

    self.locked = locked
    self.locked_since = now if locked else None
    self.observed_at = utc_now()
    self._persist()
    return True

  def detection_allowed(self, now: float) -> bool:
    if not self.required:
      return True
    return self.locked is True and self.locked_since is not None \
      and now - self.locked_since >= self.arm_delay_s


class ImpactDetector:
  def __init__(
    self,
    arm_delay_s: float = DEFAULT_ARM_DELAY_S,
    warmup_s: float = 3.0,
    cooldown_s: float = 30.0,
    min_dynamic_g: float = DEFAULT_MIN_DYNAMIC_G,
    min_jerk_g_per_s: float = DEFAULT_MIN_JERK_G_PER_S,
    impulse_dynamic_g: float = DEFAULT_IMPULSE_DYNAMIC_G,
    impulse_jerk_g_per_s: float = DEFAULT_IMPULSE_JERK_G_PER_S,
    strong_dynamic_g: float = DEFAULT_STRONG_DYNAMIC_G,
    candidate_window_s: float = 0.18,
  ) -> None:
    self.arm_delay_s = max(0.0, arm_delay_s)
    self.warmup_s = max(0.0, warmup_s)
    self.cooldown_s = max(0.0, cooldown_s)
    self.min_dynamic_g = max(0.01, min_dynamic_g)
    self.min_jerk_g_per_s = max(0.1, min_jerk_g_per_s)
    self.impulse_dynamic_g = max(self.min_dynamic_g, impulse_dynamic_g)
    self.impulse_jerk_g_per_s = max(self.min_jerk_g_per_s, impulse_jerk_g_per_s)
    self.strong_dynamic_g = max(self.min_dynamic_g, strong_dynamic_g)
    self.candidate_window_s = max(0.05, candidate_window_s)

    self.first_sample_at: float | None = None
    self.last_sample_at: float | None = None
    self.last_accel: tuple[float, float, float] | None = None
    self.gravity: list[float] | None = None
    self.last_trigger_at = -math.inf
    self.armed = False
    self.last_dynamic_g = 0.0
    self.last_total_g = 0.0
    self.last_jerk_g_per_s = 0.0
    self.last_gyro_rad_per_s = 0.0
    self._reset_candidate()

  def _reset_candidate(self) -> None:
    self.candidate_started_at: float | None = None
    self.candidate_hits = 0
    self.candidate_samples = 0
    self.peak_dynamic_g = 0.0
    self.peak_total_g = 0.0
    self.peak_jerk_g_per_s = 0.0
    self.peak_gyro_rad_per_s = 0.0
    self.candidate_clipped = False
    self.candidate_impulsive = False

  def _update_candidate(self, now: float, dynamic_g: float, total_g: float,
                        jerk_g_per_s: float, gyro_rad_per_s: float,
                        clipped: bool, qualifying: bool, impulsive: bool) -> None:
    if self.candidate_started_at is None:
      self.candidate_started_at = now

    self.candidate_samples += 1
    self.peak_dynamic_g = max(self.peak_dynamic_g, dynamic_g)
    self.peak_total_g = max(self.peak_total_g, total_g)
    self.peak_jerk_g_per_s = max(self.peak_jerk_g_per_s, jerk_g_per_s)
    self.peak_gyro_rad_per_s = max(self.peak_gyro_rad_per_s, gyro_rad_per_s)
    self.candidate_clipped = self.candidate_clipped or clipped
    self.candidate_impulsive = self.candidate_impulsive or impulsive
    if qualifying or (dynamic_g >= self.min_dynamic_g * 0.75
                      and jerk_g_per_s >= self.min_jerk_g_per_s * 0.5):
      self.candidate_hits += 1

  def _build_event(self, now: float) -> dict:
    if self.peak_dynamic_g >= 1.25:
      severity = "severe"
    elif self.peak_dynamic_g >= 0.75:
      severity = "moderate"
    else:
      severity = "light"

    started_at = self.candidate_started_at if self.candidate_started_at is not None else now
    return {
      "id": str(uuid.uuid4()),
      "detectedAt": utc_now(),
      "severity": severity,
      "peakDynamicG": round(self.peak_dynamic_g, 3),
      "peakTotalG": round(self.peak_total_g, 3),
      "peakJerkGPerSec": round(self.peak_jerk_g_per_s, 2),
      "peakGyroRadPerSec": round(self.peak_gyro_rad_per_s, 3),
      "durationMs": max(1, round((now - started_at) * 1000.0)),
      "sampleCount": self.candidate_samples,
      "sensorHz": 104,
      "sensorClipped": self.candidate_clipped,
      "detectorVersion": DETECTOR_VERSION,
    }

  def update(self, accel: tuple[float, float, float], gyro: tuple[float, float, float],
             now: float, detection_enabled: bool = True) -> dict | None:
    if len(accel) != 3 or len(gyro) != 3 or not all(math.isfinite(value) for value in (*accel, *gyro)):
      return None

    if self.first_sample_at is None:
      self.first_sample_at = now
      self.last_sample_at = now
      self.last_accel = accel
      self.gravity = list(accel)
      return None

    assert self.gravity is not None
    assert self.last_sample_at is not None
    assert self.last_accel is not None
    dt = min(0.2, max(0.001, now - self.last_sample_at))
    self.last_sample_at = now

    dynamic = tuple(accel[index] - self.gravity[index] for index in range(3))
    dynamic_g = vector_norm(dynamic) / STANDARD_GRAVITY
    total_g = vector_norm(accel) / STANDARD_GRAVITY
    jerk_g_per_s = vector_norm(tuple(
      accel[index] - self.last_accel[index] for index in range(3))) / STANDARD_GRAVITY / dt
    gyro_rad_per_s = vector_norm(gyro)
    self.last_dynamic_g = dynamic_g
    self.last_total_g = total_g
    self.last_jerk_g_per_s = jerk_g_per_s
    self.last_gyro_rad_per_s = gyro_rad_per_s
    self.last_accel = accel

    ready_at = self.first_sample_at + max(self.arm_delay_s, self.warmup_s)
    self.armed = now >= ready_at

    # Track gravity only while the vehicle is quiet. This preserves impact energy.
    if self.candidate_started_at is None and dynamic_g < 0.18:
      alpha = 1.0 - math.exp(-dt / 8.0)
      for index in range(3):
        self.gravity[index] += alpha * (accel[index] - self.gravity[index])

    if not detection_enabled or not self.armed or now - self.last_trigger_at < self.cooldown_s:
      self._reset_candidate()
      return None

    clipped = max(abs(component) for component in accel) >= STANDARD_GRAVITY * 1.95
    qualifying = (dynamic_g >= self.min_dynamic_g and jerk_g_per_s >= self.min_jerk_g_per_s)
    qualifying = qualifying or dynamic_g >= self.strong_dynamic_g
    impulsive = dynamic_g >= self.impulse_dynamic_g and jerk_g_per_s >= self.impulse_jerk_g_per_s
    qualifying = qualifying or impulsive

    if self.candidate_started_at is None:
      if not qualifying:
        return None
      self._update_candidate(now, dynamic_g, total_g, jerk_g_per_s, gyro_rad_per_s,
                             clipped, qualifying, impulsive)
    else:
      self._update_candidate(now, dynamic_g, total_g, jerk_g_per_s, gyro_rad_per_s,
                             clipped, qualifying, impulsive)

    candidate_age = now - self.candidate_started_at
    confirmed = self.peak_dynamic_g >= self.strong_dynamic_g or self.candidate_impulsive or (
      self.candidate_hits >= 2
      and self.peak_dynamic_g >= self.min_dynamic_g
      and self.peak_jerk_g_per_s >= self.min_jerk_g_per_s
    )
    if confirmed:
      event = self._build_event(now)
      self.last_trigger_at = now
      self._reset_candidate()
      return event

    if candidate_age >= self.candidate_window_s:
      self._reset_candidate()
    return None


def _read_events(handle) -> list[dict]:
  handle.seek(0)
  events = []
  for line in handle:
    try:
      event = json.loads(line)
      if isinstance(event, dict) and event.get("id"):
        events.append(event)
    except (TypeError, ValueError):
      continue
  return events


def _write_events(handle, events: list[dict]) -> None:
  handle.seek(0)
  handle.truncate()
  for event in events:
    handle.write(json.dumps(event, separators=(",", ":"), ensure_ascii=False) + "\n")
  handle.flush()
  os.fsync(handle.fileno())


def enqueue_impact_event(event: dict, path: Path = DEFAULT_IMPACT_QUEUE_PATH,
                         max_events: int = MAX_QUEUED_IMPACTS) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("a+", encoding="utf-8") as handle:
    fcntl.flock(handle, fcntl.LOCK_EX)
    events = [queued for queued in _read_events(handle) if queued.get("id") != event.get("id")]
    events.append(dict(event))
    _write_events(handle, events[-max(1, max_events):])
    fcntl.flock(handle, fcntl.LOCK_UN)


def append_impact_diagnostic(record: dict, path: Path = DEFAULT_IMPACT_DIAGNOSTICS_PATH,
                             max_bytes: int = MAX_IMPACT_DIAGNOSTICS_BYTES) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  line = json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n"
  with path.open("a", encoding="utf-8") as handle:
    handle.write(line)

  max_bytes = max(1024, max_bytes)
  if path.stat().st_size <= max_bytes:
    return

  keep_bytes = max_bytes // 2
  with path.open("rb") as handle:
    handle.seek(max(0, path.stat().st_size - keep_bytes))
    retained = handle.read()
  newline = retained.find(b"\n")
  if newline >= 0:
    retained = retained[newline + 1:]
  temporary = path.with_suffix(path.suffix + ".tmp")
  temporary.write_bytes(retained)
  os.replace(temporary, path)


def peek_impact_event(path: Path = DEFAULT_IMPACT_QUEUE_PATH) -> dict | None:
  try:
    with path.open("r", encoding="utf-8") as handle:
      fcntl.flock(handle, fcntl.LOCK_SH)
      events = _read_events(handle)
      fcntl.flock(handle, fcntl.LOCK_UN)
  except FileNotFoundError:
    return None
  return events[0] if events else None


def update_impact_event(event_id: str, updates: dict,
                        path: Path = DEFAULT_IMPACT_QUEUE_PATH) -> dict | None:
  try:
    with path.open("r+", encoding="utf-8") as handle:
      fcntl.flock(handle, fcntl.LOCK_EX)
      events = _read_events(handle)
      updated_event = None
      for index, event in enumerate(events):
        if event.get("id") == event_id:
          updated_event = {**event, **updates}
          events[index] = updated_event
          break
      if updated_event is not None:
        _write_events(handle, events)
      fcntl.flock(handle, fcntl.LOCK_UN)
      return updated_event
  except FileNotFoundError:
    return None


def remove_impact_event(event_id: str, path: Path = DEFAULT_IMPACT_QUEUE_PATH) -> bool:
  try:
    with path.open("r+", encoding="utf-8") as handle:
      fcntl.flock(handle, fcntl.LOCK_EX)
      events = _read_events(handle)
      remaining = [event for event in events if event.get("id") != event_id]
      removed = len(remaining) != len(events)
      if removed:
        _write_events(handle, remaining)
      fcntl.flock(handle, fcntl.LOCK_UN)
      return removed
  except FileNotFoundError:
    return False
