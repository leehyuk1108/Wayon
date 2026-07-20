#!/usr/bin/env python3
import fcntl
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_VEHICLE_EVENT_QUEUE_PATH = Path(os.getenv(
  "WAYON_VEHICLE_EVENT_QUEUE", "/data/wayon_cloud/vehicle_event_queue.jsonl"))
MAX_QUEUED_VEHICLE_EVENTS = 128
DEFAULT_PARKING_UNLOCKED_REMINDER_DELAY_S = 180.0
DEFAULT_DOOR_LOCK_NOTIFICATION_PAIR_WINDOW_S = 8.0


def utc_now() -> str:
  return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def door_lock_event(locked: bool, test: bool = False) -> dict:
  return {
    "id": str(uuid.uuid4()),
    "eventType": "door_lock",
    "occurredAt": utc_now(),
    "locked": bool(locked),
    "test": bool(test),
  }


def parking_unlocked_event(delay_s: float, test: bool = False) -> dict:
  return {
    "id": str(uuid.uuid4()),
    "eventType": "parking_unlocked",
    "occurredAt": utc_now(),
    "delaySeconds": int(round(max(0.0, delay_s))),
    "test": bool(test),
  }


class DoorLockNotificationDebouncer:
  def __init__(self, pair_window_s: float = DEFAULT_DOOR_LOCK_NOTIFICATION_PAIR_WINDOW_S) -> None:
    self.pair_window_s = max(0.0, float(pair_window_s))
    self._pending_unlock_event: dict | None = None
    self._pending_unlock_at: float | None = None

  @property
  def has_pending_unlock(self) -> bool:
    return self._pending_unlock_event is not None

  def _take_pending_unlock(self) -> dict | None:
    event = self._pending_unlock_event
    self._pending_unlock_event = None
    self._pending_unlock_at = None
    return event

  def flush(self, now: float) -> list[dict]:
    if self._pending_unlock_event is None or self._pending_unlock_at is None:
      return []
    if now - self._pending_unlock_at < self.pair_window_s:
      return []

    event = self._take_pending_unlock()
    return [event] if event is not None else []

  def on_change(self, event: dict, now: float) -> list[dict]:
    locked = event.get("locked")
    if locked is False:
      ready = self.flush(now)
      self._pending_unlock_event = dict(event)
      self._pending_unlock_at = now
      return ready

    if locked is not True:
      return []

    if self._pending_unlock_event is None or self._pending_unlock_at is None:
      return [dict(event)]

    if now - self._pending_unlock_at <= self.pair_window_s:
      self._take_pending_unlock()
      return []

    pending = self._take_pending_unlock()
    return ([pending] if pending is not None else []) + [dict(event)]


class ParkingUnlockReminder:
  def __init__(self, delay_s: float = DEFAULT_PARKING_UNLOCKED_REMINDER_DELAY_S,
               enabled: bool = True) -> None:
    self.delay_s = max(0.0, float(delay_s))
    self.unlocked_since: float | None = None
    self.completed = not enabled

  def update(self, locked: bool | None, now: float) -> bool:
    if self.completed:
      return False
    if locked is True:
      self.completed = True
      self.unlocked_since = None
      return False
    if locked is not False:
      return False
    if self.unlocked_since is None:
      self.unlocked_since = now
    if now - self.unlocked_since < self.delay_s:
      return False

    self.completed = True
    return True


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


def enqueue_vehicle_event(event: dict, path: Path = DEFAULT_VEHICLE_EVENT_QUEUE_PATH,
                          max_events: int = MAX_QUEUED_VEHICLE_EVENTS) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("a+", encoding="utf-8") as handle:
    fcntl.flock(handle, fcntl.LOCK_EX)
    events = [queued for queued in _read_events(handle) if queued.get("id") != event.get("id")]
    events.append(dict(event))
    _write_events(handle, events[-max(1, max_events):])
    fcntl.flock(handle, fcntl.LOCK_UN)


def peek_vehicle_event(path: Path = DEFAULT_VEHICLE_EVENT_QUEUE_PATH) -> dict | None:
  try:
    with path.open("r", encoding="utf-8") as handle:
      fcntl.flock(handle, fcntl.LOCK_SH)
      events = _read_events(handle)
      fcntl.flock(handle, fcntl.LOCK_UN)
  except FileNotFoundError:
    return None
  return events[0] if events else None


def remove_vehicle_event(event_id: str, path: Path = DEFAULT_VEHICLE_EVENT_QUEUE_PATH) -> bool:
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
