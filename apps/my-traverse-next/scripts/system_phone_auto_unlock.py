"""Parked Traverse door automation using a bonded Bluetooth link."""

import argparse
import asyncio
from collections import deque
from datetime import datetime, timedelta, timezone
import errno
import json
import math
import os
from pathlib import Path
import re
from statistics import median
import socket
import struct
import tempfile
import time
from urllib.request import ProxyHandler, Request, build_opener

from comma_rssi_receiver import diagnostic_waiting
from comma_system_phone import configured_address, read_link_rssi
import system_phone_settings as link_settings
from gmone_door_control import (
  PRIVATE_DIR, DoorCommand, NoRedirect, Result, one_request, private_directory, read_credentials,
  run_command, send_command, vehicle_check,
)
from wayon_door_pair import read_private_file
from wayon_door_proximity import CarObservations

ORIGIN = "https://wayon-cloud.hyuklee.workers.dev"
CLOUD_CONFIG = Path("/data/wayon_cloud/config.json")
LOCAL_LOCK_STATE = Path("/data/wayon_cloud/door_lock_status.json")
LOCK_AGE = 120
KST = timezone(timedelta(hours=9))
SECURITY = struct.pack("BB", 4, 0)
MAX_GAP = 6.0
CONFIRM_S = 3.0
DEPARTURE_CONFIRM_S = 5.0
DEPARTURE_WINDOW_S = 45.0
ABSENCE_CONFIRM_S = 18.0
ABSENCE_MAX_GAP = 9.0
RETURN_CONFIRM_WINDOW_S = 15.0
RETURN_MAX_MISSES = 2
LOCAL_LOCK_EDGE_MAX_AGE_S = 12
AUTO_LOCK_EDGE_WINDOW_S = 8
UNLOCK_TRACE_WINDOW_S = 75
UNLOCK_TRACE_MAX_SAMPLES = 400
# Near the car the controller refreshes link RSSI every ~0.13 s, so poll faster while an unlock is possible.
FAST_ZONE_MARGIN_DB = 10
FAST_HOLD_S = 3.0
FAST_PERIOD_S = .2
FULL_SAMPLE_INTERVAL_S = 1.0
RECEIVED_PERIOD_S = 1.25
# The car waking for a remote command can trip the park guard for a moment; keep the arrival through that.
PARK_BLIP_S = 20
# Walking up to the car shows as a sudden step from a slow plateau (16:01, 16:54, 17:11, 17:45 traces,
# 2026-11-12). A phone left at the desk rose at most +5 dB over its 10 s median in 1060 fast readings.
RISE_WINDOW_S = 10.0
RISE_MIN_DB = 7
RISE_MIN_SAMPLES = 3
RISE_FLOOR_BELOW_NEAR_DB = 3
# A phone at the desk spiked once onto the floor straight from its plateau (18:22, 18:26: previous reading
# -22, -27), while every walk up to the car came through readings within 3 dB of it (18:08, 18:09: -21).
RISE_PREVIOUS_S = 1.5
RISE_PREVIOUS_BELOW_FLOOR_DB = 3
LOCK_COOLDOWN_S = 10
LOCK_GRACE_S = 10
UNLOCK_COOLDOWN_S = 8
IDLE_MISS_MIN_PERIOD_S = .5
UNLOCK = DoorCommand.UNLOCK
LOCK = DoorCommand.LOCK
LOCK_MARKER = "system-lock-enabled"
LINK_ERROR = object()
CONNECT_NOT_READY = object()
PHONE_UNREACHABLE = (errno.EHOSTDOWN, errno.EHOSTUNREACH, errno.ETIMEDOUT)
GMONE_SOURCES = ("gmone-direct", "gmone-direct-android", "gmone-official-cache")


def action_cooldown(action):
  return UNLOCK_COOLDOWN_S if action is UNLOCK else LOCK_COOLDOWN_S


def obj(value):
  return value if isinstance(value, dict) else {}


def epoch(value):
  if not isinstance(value, str) or len(value) > 40:
    return None
  try:
    parsed = datetime.fromisoformat(value)
    return parsed.timestamp() if parsed.tzinfo is not None else None
  except (ValueError, OverflowError):
    return None


def lock_status(document, scope, now, newest_event=None, *, expected_locked=True):
  """Never substitute a recent HTTP receipt or the app's optimistic label for a vehicle observation."""
  status = obj(obj(document).get("vehicleStatus"))
  if (status.get("ok") is not True or status.get("source") not in GMONE_SOURCES
      or status.get("clientScope") != scope):
    return "unknown", None
  data = obj(status.get("data"))
  doors = obj(obj(obj(data.get("gmone_details")).get("closures")).get("doors"))
  value = doors.get("raw")
  observed = epoch(status.get("updatedAt"))
  collected = epoch(status.get("collectedAt"))
  try:
    provider_time = datetime.strptime(data.get("last_update"), "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST).timestamp()
  except (TypeError, ValueError):
    return "unknown", None
  if (type(value) is not int or value not in (0, 1, 2) or observed is None or collected is None or
      observed > now + 2 or observed > collected + 2 or collected > now + 2 or
      abs(provider_time - observed) >= 2):
    return "unknown", None
  locked = value == 0
  state = "locked" if locked else "unlocked"
  if locked != expected_locked:
    return state, None
  event = obj(newest_event)
  if event.get("known") is True:
    event_time = epoch(event.get("occurredAt"))
    if event_time is None or event_time > now + 2 or type(event.get("locked")) is not bool:
      return "unknown", None
    if event_time >= observed - 1 and event["locked"] != locked:
      return ("locked" if event["locked"] else "unlocked"), None
  if status.get("stale") is not False or now - observed > LOCK_AGE:
    return "stale", None
  return state, observed


class Approach:
  def __init__(self, near, far):
    if not link_settings.valid_thresholds(near, far):
      raise ValueError("unmeasured system link thresholds")
    self.near, self.far = near, far
    self.awaiting_first_reading = True
    self.manual_lock_at = None
    self.reset()

  def reset(self):
    self._reset_signal()
    self._reset_loss_lock()
    self.seen_near = False
    self.missing_since = self.last_missing = None
    self.reacquired_at = None
    self.loss_departed = False
    self.presence_at = None
    self.history = deque()
    self.unlock_trigger = None
    self._clear_return()

  def record(self, now, value):
    """Keep the last seconds of authenticated readings, regular and fast, for the sudden-rise unlock."""
    while self.history and not 0 <= now - self.history[0][0] <= RISE_WINDOW_S:
      self.history.popleft()
    self.history.append((now, value))

  def rise_floor(self):
    return max(self.near - RISE_FLOOR_BELOW_NEAR_DB, self.far + 1)

  def sudden_rise(self, now, value):
    """A jump well above the last seconds' level onto the doorstep, before the near threshold is reached.

    Walking up to the car shows as one step from a slow plateau, while a phone lying still drifts slowly."""
    floor = self.rise_floor()
    if value < floor:
      return False
    recent = [reading for at, reading in self.history if 0 < now - at <= RISE_PREVIOUS_S]
    if not recent or recent[-1] < floor - RISE_PREVIOUS_BELOW_FLOOR_DB:
      return False
    prior = [reading for at, reading in self.history if 0 < now - at <= RISE_WINDOW_S]
    return len(prior) >= RISE_MIN_SAMPLES and value - median(prior) >= RISE_MIN_DB

  def note_unlock(self, now):
    """An automatic unlock means the phone holder reached the car, even without a 3 s near run, so a
    later measured departure or signal loss may lock again."""
    if self.manual_lock_at is None:
      self.presence_at = self.loss_near_at = now
      self.seen_near = True

  def guard_reset(self, keep_presence=False):
    """The park guard blocked sampling: drop live evidence, optionally keeping a recent arrival."""
    presence = self.presence_at if keep_presence else None
    self.reset()
    if presence is not None:
      self.presence_at = self.loss_near_at = presence
      self.seen_near = True

  def _clear_return(self):
    self.return_at = self.return_sample_at = None
    self.return_misses = 0

  def _confirm_return(self, now):
    if self.manual_lock_at is None:
      self.return_at = self.return_sample_at = now
      self.return_misses = 0

  def _update_return(self, now, value, connect_not_ready):
    if self.return_at is None:
      return
    if (not 0 < now - self.return_sample_at <= ABSENCE_MAX_GAP or
        now - self.return_at > DEPARTURE_WINDOW_S or
        (value is LINK_ERROR and not connect_not_ready)):
      self._clear_return()
    elif value is None or connect_not_ready:
      self.return_misses += 1
      self.return_sample_at = now
      if self.return_misses > RETURN_MAX_MISSES:
        self._clear_return()
    elif self.return_misses:
      self.reacquired_at = now
      self._clear_return()
    else:
      self.return_sample_at = now

  def hold_after_local_lock(self, now):
    self.manual_lock_at = now
    self.armed = False
    self.far_at = self.reacquired_at = None
    self.presence_at = None
    self._clear_return()

  def _reset_signal(self):
    self.last = self.since = None
    self.band = None
    self.count = 0
    self.armed = False
    self.far_at = None
    self.near_at = None

  def _reset_loss_lock(self):
    self.loss_near_at = self.loss_since = None
    self.loss_count = 0

  def observe(self, now, value):
    return self.transition(now, value) is UNLOCK

  def transition(self, now, value, enable_lock=False, *, connect_not_ready=False):
    self._update_return(now, value, connect_not_ready)
    if self.reacquired_at is not None and not 0 <= now - self.reacquired_at <= RETURN_CONFIRM_WINDOW_S:
      self.reacquired_at = None
    if value is None or value is LINK_ERROR:
      previous = self.last_missing if self.last_missing is not None else self.last
      self._reset_signal()
      if self.awaiting_first_reading or self.seen_near:
        if self.last_missing is None or not 0 < now - self.last_missing <= ABSENCE_MAX_GAP:
          self.missing_since = now
          self.loss_departed = False
        self.last_missing = now
      if value is LINK_ERROR:
        self.loss_departed = False
      if (value is LINK_ERROR or self.loss_near_at is None or
          not 0 < now - self.loss_near_at <= DEPARTURE_WINDOW_S or
          previous is None or not 0 < now - previous <= ABSENCE_MAX_GAP):
        self._reset_loss_lock()
      else:
        if self.loss_since is None:
          self.loss_since = previous
        self.loss_count += 1
        if self.loss_count >= 2 and now - self.loss_since >= DEPARTURE_CONFIRM_S:
          self._reset_loss_lock()
          self.presence_at = None
          self.loss_departed = True
          self._confirm_return(now)
          if enable_lock:
            return LOCK
      return None
    self.awaiting_first_reading = False
    self.loss_since = None
    self.loss_count = 0
    if self.last_missing is not None:
      if (0 < now - self.last_missing <= ABSENCE_MAX_GAP and
          (self.loss_departed or now - self.missing_since >= ABSENCE_CONFIRM_S)):
        self.reacquired_at = now
      self.missing_since = self.last_missing = None
    self.loss_departed = False
    if self.last is not None and not 0 < now - self.last <= MAX_GAP:
      self.reset()
    if self.far_at is not None and now - self.far_at > DEPARTURE_WINDOW_S:
      self.armed = False
    self.last = now
    band = "near" if value >= self.near else "far" if value <= self.far else None
    if band != self.band or self.since is None:
      self.band, self.since, self.count = band, now, 1
    else:
      self.count += 1
    if self.presence_at is not None and band != "far":
      # Still around the car after an automatic unlock: keep the walk-away lock armed.
      self.presence_at = self.loss_near_at = now
    rise = band != "near" and self.sudden_rise(now, value)
    self.record(now, value)
    if (band == "near" or rise) and self.manual_lock_at is None and (self.armed or self.reacquired_at is not None):
      self.unlock_trigger = "rise" if rise else "near"
      self.armed = False
      self.reacquired_at = None
      self._clear_return()
      return UNLOCK
    if band is None or self.count < 3 or now - self.since < CONFIRM_S:
      return None
    if band == "far":
      if self.manual_lock_at is not None and now - max(self.since, self.manual_lock_at) >= DEPARTURE_CONFIRM_S:
        self.manual_lock_at = None
        self.reacquired_at = None
      if self.manual_lock_at is None:
        self.armed = True
        self.far_at = now
        self._confirm_return(now)
      present = any(at is not None and now - at <= DEPARTURE_WINDOW_S for at in (self.near_at, self.presence_at))
      if enable_lock and present and now - self.since >= DEPARTURE_CONFIRM_S:
        self.near_at = self.presence_at = None
        self._reset_loss_lock()
        return LOCK
    else:
      self.seen_near = True
      self.near_at = now
      self.loss_near_at = now
    return None

  def unlock_ready(self, now):
    """Whether a near sample at `now` would unlock, without touching band or departure evidence."""
    if self.manual_lock_at is not None:
      return False
    if self.reacquired_at is not None and 0 <= now - self.reacquired_at <= RETURN_CONFIRM_WINDOW_S:
      return True
    return (self.armed and self.last is not None and 0 <= now - self.last <= MAX_GAP and
            self.far_at is not None and now - self.far_at <= DEPARTURE_WINDOW_S)

  def still_near(self, now):
    return self.still_in_band(now, UNLOCK)

  def still_in_band(self, now, action):
    return self.band == ("near" if action is UNLOCK else "far") and self.last is not None and 0 <= now - self.last <= 2.5


class LockGrace:
  def __init__(self):
    self.reset()

  def reset(self):
    self.deadline = self.last = None
    self.deferred_until = None

  def defer_until(self, when):
    first = self.deferred_until is None
    self.deferred_until = max(when, self.deferred_until or when)
    return first

  def apply(self, now, value, action, approach):
    if self.deadline is not None:
      reason = None
      if value is LINK_ERROR or not 0 < now - self.last <= ABSENCE_MAX_GAP:
        reason = "evidence_interrupted"
      elif value is not None and value >= approach.near:
        reason = "returned_near"
      elif now > self.deadline + LOCK_COOLDOWN_S + ABSENCE_MAX_GAP:
        reason = "cooldown_expired"
      elif now >= self.deadline:
        if value is None or value <= approach.far:
          self.last = now
          if self.deferred_until is None or now >= self.deferred_until:
            return LOCK, None
        else:
          reason = "departure_not_confirmed"
      if reason is not None:
        self.reset()
        return (None if action is LOCK else action), "canceled: " + reason
      self.last = now
    if action is LOCK:
      if self.deadline is None:
        self.deadline, self.last = now + LOCK_GRACE_S, now
        return None, f"pending: grace={LOCK_GRACE_S:g}s"
      return None, None
    return action, None


class LocalLockEdge:
  def __init__(self, path=LOCAL_LOCK_STATE):
    self.path = path
    self.last_observed = 0
    self.last_locked = None
    self.auto_lock_at = None

  def external_lock(self, now):
    try:
      with self.path.open(encoding="utf-8") as stream:
        state = obj(json.loads(stream.read(4096)))
    except (OSError, ValueError):
      return False
    observed = epoch(state.get("observedAt"))
    locked = state.get("locked")
    if (type(locked) is not bool or observed is None or observed <= self.last_observed or
        not 0 <= now - observed <= LOCAL_LOCK_EDGE_MAX_AGE_S):
      return False
    self.last_observed = observed
    self.last_locked = locked
    if not locked:
      return False
    expected = self.auto_lock_at is not None and 0 <= observed - self.auto_lock_at <= AUTO_LOCK_EDGE_WINDOW_S
    if expected:
      self.auto_lock_at = None
    return not expected


class UnlockTiming:
  def __init__(self):
    self.samples = deque(maxlen=UNLOCK_TRACE_MAX_SAMPLES)
    self.last_blocked = None
    self.last_blocked_log = -math.inf

  def record(self, started, now, status, rssi, decision=None):
    while self.samples and now - self.samples[0][0] > UNLOCK_TRACE_WINDOW_S:
      self.samples.popleft()
    self.samples.append((now, round(now - started, 3), status, rssi, decision))

  def report(self, now, revision, outcome, vehicle_observed_at=None):
    samples = [[round(at - now, 3), duration, status, rssi, decision]
               for at, duration, status, rssi, decision in self.samples]
    trace = {"outcome": outcome, "revision": revision,
             "columns": ["offset_s", "sample_duration_s", "status", "rssi", "decision"], "samples": samples}
    if vehicle_observed_at is not None:
      trace["vehicle_observed_at"] = vehicle_observed_at
    print("system phone unlock timing:", json.dumps(trace, separators=(",", ":")), flush=True)

  def blocked(self, now, revision, reason):
    changed = self.last_blocked != reason
    self.last_blocked = reason
    if reason is not None and changed and now - self.last_blocked_log >= 20:
      self.last_blocked_log = now
      self.report(now, revision, reason)


class Cloud:
  def __init__(self):
    with CLOUD_CONFIG.open(encoding="utf-8") as stream:
      config = json.load(stream)
    if config.get("endpoint", "").rstrip("/") != ORIGIN or not isinstance(config.get("token"), str) or not config["token"]:
      raise ValueError("invalid Wayon origin")
    self.headers = {"Authorization": "Bearer " + config["token"], "Cache-Control": "no-store",
                    "User-Agent": "WayonDoorStatus/1.0"}
    self.opener = build_opener(ProxyHandler({}), NoRedirect())

  def read(self, path):
    req = Request(ORIGIN + path, headers=self.headers)
    with self.opener.open(req, timeout=4) as response:
      body = response.read(524289)
    if len(body) > 524288:
      raise ValueError("Wayon response too large")
    return obj(json.loads(body))

  def status(self, scope, compare_event=False, *, expected_locked=True):
    if not compare_event:
      return lock_status(self.read("/api/gmone/status"), scope, time.time(), expected_locked=expected_locked)
    state = self.read("/api/state")
    gmone = obj(obj(obj(state.get("vehicleStatus")).get("sources")).get("gmone"))
    return lock_status({"vehicleStatus": gmone}, scope, time.time(), state.get("vehicleLock"), expected_locked=expected_locked)


async def secure_sample(address, parked):
  if not parked():
    return LINK_ERROR
  try:
    with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP) as link:
      link.setblocking(False)
      link.setsockopt(274, 4, SECURITY)  # SOL_BLUETOOTH / BT_SECURITY, secure-connections only
      try:
        await asyncio.wait_for(asyncio.get_running_loop().sock_connect(link, (address, 1)), 3)
      except TimeoutError:
        return None
      except OSError as error:
        if error.errno == errno.ENOTCONN:
          return CONNECT_NOT_READY
        return None if error.errno in PHONE_UNREACHABLE else LINK_ERROR
      if link.getsockopt(274, 4, 2) != struct.pack("BB", 4, 16) or not parked():
        return LINK_ERROR
      value = await read_link_rssi(address)
      return value if value is not None and parked() and link.getsockopt(274, 4, 2) == struct.pack("BB", 4, 16) else LINK_ERROR
  except (OSError, TimeoutError):
    return LINK_ERROR


def finish_door_action(action, execute, observed_at, *, unlock_allowed=None):
  if action not in (LOCK, UNLOCK):
    raise ValueError("invalid door action")

  def fresh():
    return (0 <= time.monotonic() - observed_at <= 2.5 and not diagnostic_waiting() and
            (action is UNLOCK or not execute or (PRIVATE_DIR / LOCK_MARKER).is_file()))

  def check(command):
    if not fresh():
      return "observation_expired"
    if command is UNLOCK and unlock_allowed is not None and not unlock_allowed():
      return "local_lock_guard"
    reason = vehicle_check(command, require_closed=False) if command is LOCK else vehicle_check(command)
    if not fresh():
      return "observation_expired"
    if command is UNLOCK and unlock_allowed is not None and not unlock_allowed():
      return "local_lock_guard"
    return reason

  def send_once(command, credentials):
    if not record_intent(PRIVATE_DIR, time.time(), command):
      return Result("rate_limited")
    reason = check(command)
    return Result(reason) if reason else send_command(command, credentials)

  with one_request(PRIVATE_DIR):
    return run_command(action, execute, check=check, credentials=lambda: read_credentials(PRIVATE_DIR),
                       send=send_once).state


def intent_name(action):
  return "system-unlock-last-intent" if action is UNLOCK else "system-lock-last-intent"


def intent_cooldown_left(directory, issued_at, action):
  try:
    previous = json.loads(read_private_file(directory, intent_name(action)))
  except FileNotFoundError:
    return 0
  if type(previous) not in (float, int) or not math.isfinite(previous):
    raise ValueError("invalid previous door attempt")
  return max(0, action_cooldown(action) - (issued_at - previous))


def record_intent(directory, issued_at, action=UNLOCK):
  # Reserve the attempt before dispatch; a timeout is not proof it failed.
  if intent_cooldown_left(directory, issued_at, action):
    return False
  with tempfile.NamedTemporaryFile(dir=directory, prefix=".unlock-", delete=False) as stream:
    temporary = Path(stream.name)
    try:
      stream.write(json.dumps(issued_at).encode("ascii"))
      stream.flush()
      os.fsync(stream.fileno())
      os.replace(temporary, directory / intent_name(action))
    finally:
      temporary.unlink(missing_ok=True)
  return True


async def monitor(car, address, approach, execute, enable_lock, profile_directory=None, revision=0, lock_edge=None):
  last_attempt = {action: float("-inf") for action in (LOCK, UNLOCK)}
  lock_grace = LockGrace()
  timing = UnlockTiming() if execute else None
  paused = False
  fast_zone_at = None
  fast_mode = False
  last_full = -math.inf
  guard_blocked_at = None

  def fast_window(now):
    return (fast_zone_at is not None and 0 <= now - fast_zone_at <= FAST_HOLD_S and
            approach.unlock_ready(now) and now - last_attempt[UNLOCK] >= UNLOCK_COOLDOWN_S)

  def parked():
    nonlocal paused, guard_blocked_at
    car_parked = car.parked()
    diagnostic = car_parked and diagnostic_waiting()
    allowed = car_parked and not diagnostic
    at = time.monotonic()
    if not allowed:
      paused = True
      if guard_blocked_at is None:
        guard_blocked_at = at
        if execute:
          reason = "diagnostic" if diagnostic else getattr(getattr(car, "ignition", None), "reason", "unknown")
          print(f"system phone park guard: blocked reason={reason} "
                f"arrival={approach.presence_at is not None}", flush=True)
      approach.guard_reset(keep_presence=at - guard_blocked_at <= PARK_BLIP_S)
      if lock_grace.deadline is not None:
        lock_grace.reset()
        if execute:
          print("system phone lock canceled: park_guard", flush=True)
    elif guard_blocked_at is not None:
      if execute:
        print(f"system phone park guard: cleared after={at - guard_blocked_at:.1f}s "
              f"arrival={approach.presence_at is not None}", flush=True)
      guard_blocked_at = None
    return allowed

  def unlock_allowed():
    if lock_edge is not None and lock_edge.external_lock(time.time()):
      approach.hold_after_local_lock(time.monotonic())
      if execute:
        print("system phone unlock held: local_lock", flush=True)
    return approach.manual_lock_at is None

  while True:
    if profile_directory is not None:
      try:
        data, updated = link_settings.profile(profile_directory)
        if (updated, data["near"], data["far"]) != (revision, approach.near, approach.far):
          new_approach = Approach(data["near"], data["far"])
          new_approach.manual_lock_at = approach.manual_lock_at
          new_approach.presence_at = approach.presence_at
          approach = new_approach
          approach.awaiting_first_reading = False
          lock_grace.reset()
          fast_zone_at = None
          fast_mode = False
          if timing is not None:
            timing.samples.clear()
          revision = updated
          print(f"system phone link thresholds applied: revision={revision} near={approach.near} far={approach.far}", flush=True)
      except (OSError, ValueError):
        pass
    paused = False
    sample_started = time.monotonic()
    value = await secure_sample(address, parked)
    now = time.monotonic()
    connect_not_ready = value is CONNECT_NOT_READY
    retry_not_ready = connect_not_ready and not (approach.loss_count or lock_grace.deadline is not None)
    if connect_not_ready:
      value = LINK_ERROR
    permitted = parked() and not paused
    status = ("park_required" if not permitted else "not_seen" if value is None
              else "link_error" if value is LINK_ERROR else "received")
    if profile_directory is not None:
      try:
        link_settings.publish(revision, value if status == "received" else None, status)
      except (OSError, ValueError):
        pass
    if not permitted:
      fast_zone_at = None
      fast_mode = False
      if timing is not None:
        timing.record(sample_started, now, status, None)
        timing.blocked(now, revision, None)
      await asyncio.sleep(3)
      continue
    received = status == "received"
    if not received:
      fast_zone_at = None
    elif value >= approach.near - FAST_ZONE_MARGIN_DB:
      fast_zone_at = now
    if (fast_mode and received and now - last_full < FULL_SAMPLE_INTERVAL_S and
        not ((value >= approach.near or approach.sudden_rise(now, value)) and approach.unlock_ready(now))):
      # Extra reading between regular samples: only a qualifying near value may act, so band,
      # departure and lock evidence keep their regular cadence.
      if timing is not None:
        timing.record(sample_started, now, status, value, "fast")
      approach.record(now, value)
      fast_mode = fast_window(now)
      await asyncio.sleep(max(0.0, FAST_PERIOD_S - (now - sample_started)) if fast_mode
                          else max(0.0, RECEIVED_PERIOD_S - (now - last_full)))
      continue
    last_full = now
    last_edge = lock_edge.last_observed if timing is not None and lock_edge is not None else None
    unlock_allowed()
    action = approach.transition(now, value, enable_lock, connect_not_ready=connect_not_ready)
    action, lock_event = lock_grace.apply(now, value, action, approach)
    if timing is not None:
      rssi = value if status == "received" else None
      reason = None
      if rssi is not None and rssi >= approach.near and action is not UNLOCK:
        reason = "local_lock" if approach.manual_lock_at is not None else "return_not_armed"
      timing.record(sample_started, now, "enotconn" if connect_not_ready else status, rssi,
                    "candidate" if action is UNLOCK else reason)
      timing.blocked(now, revision, reason)
      if (action is not UNLOCK and last_edge is not None and lock_edge.last_observed != last_edge and
          lock_edge.last_locked is False):
        timing.report(now, revision, "vehicle_unlock_observed", lock_edge.last_observed)
    if lock_event is not None and execute:
      print(f"system phone lock {lock_event}", flush=True)
    if action is not None and profile_directory is not None:
      try:
        data, active_revision = link_settings.profile(profile_directory)
        if (active_revision, data["near"], data["far"]) != (revision, approach.near, approach.far):
          continue
      except (OSError, ValueError):
        continue
    if action is LOCK:
      try:
        remaining = max(last_attempt[LOCK] + LOCK_COOLDOWN_S - now,
                        intent_cooldown_left(PRIVATE_DIR, time.time(), LOCK) if execute else 0)
        if remaining > 0:
          if lock_grace.defer_until(now + remaining) and execute:
            print("system phone lock waiting: cooldown", flush=True)
          action = None
      except (ValueError, OSError) as error:
        lock_grace.reset()
        action = None
        print("system phone lock unavailable:", type(error).__name__, flush=True)
    if action is UNLOCK and now - last_attempt[action] < UNLOCK_COOLDOWN_S:
      if execute:
        print(f"system phone {action.name.lower()} skipped: cooldown", flush=True)
        timing.report(now, revision, "cooldown")
    elif action is not None and parked():
      previous = last_attempt[action]
      last_attempt[action] = now
      label = action.name.lower()
      try:
        if action is UNLOCK and execute:
          print(f"system phone unlock dispatch: authenticated_rssi={value} trigger={approach.unlock_trigger}",
                flush=True)
        if action is LOCK and execute:
          trigger = "signal_loss" if value is None else "measured_departure"
          print(f"system phone lock dispatch: trigger={trigger}", flush=True)
        lock_started = time.time() if lock_edge is not None and action is LOCK and execute else None
        unlock_check = {"unlock_allowed": unlock_allowed} if lock_edge is not None and action is UNLOCK else {}
        result = await asyncio.to_thread(finish_door_action, action, execute, now, **unlock_check)
        print(f"system phone {label} result:", result, flush=True)
        if action is UNLOCK and result in ("http_response", "unknown"):
          # The car may now be open: re-arm the walk-away lock from this arrival.
          approach.note_unlock(now)
          if execute and approach.presence_at is not None:
            print("system phone lock armed: after_auto_unlock", flush=True)
        if timing is not None:
          # Lock traces show whether the holder was really walking away when the car locked.
          timing.report(now, revision, result if action is UNLOCK else f"lock_{result}")
        if action is LOCK:
          if result == "http_response" and lock_started is not None:
            lock_edge.auto_lock_at = lock_started
          if result == "rate_limited":
            # The persisted guard rejected it before sending; keep watching for a near return.
            last_attempt[LOCK] = previous
            if lock_grace.defer_until(time.monotonic() + 1) and execute:
              print("system phone lock waiting: cooldown", flush=True)
          else:
            lock_grace.reset()
      except (ValueError, OSError, RuntimeError) as error:
        if action is LOCK:
          lock_grace.reset()
        print(f"system phone {label} unavailable:", type(error).__name__, flush=True)
    fast_mode = fast_window(now)
    if value is None and (approach.loss_count or lock_grace.deadline is not None):
      await asyncio.sleep(.5)
    elif value is None or retry_not_ready:
      # A timed-out connection already paced the retry; only throttle immediate failures.
      await asyncio.sleep(max(0.0, IDLE_MISS_MIN_PERIOD_S - (now - sample_started)))
    elif fast_mode:
      await asyncio.sleep(max(0.0, FAST_PERIOD_S - (now - sample_started)))
    else:
      await asyncio.sleep(3 if value is LINK_ERROR else RECEIVED_PERIOD_S)


async def sample(car, address):
  for _ in range(6):
    value = await secure_sample(address, car.parked)
    print("secure RSSI:", None if value is LINK_ERROR or value is CONNECT_NOT_READY else value, flush=True)
    await asyncio.sleep(.75)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("mode", choices=("status", "sample", "monitor"))
  parser.add_argument("--execute", action="store_true")
  args = parser.parse_args()
  if args.execute and args.mode != "monitor":
    parser.error("execution is only allowed in monitor mode")
  try:
    from openpilot.cereal import messaging
    car = CarObservations(messaging)
    private_directory(PRIVATE_DIR)
    if args.mode == "sample":
      address = configured_address(PRIVATE_DIR / "system-phone.address")
      asyncio.run(sample(car, address))
      return
    profile, revision = link_settings.profile(PRIVATE_DIR)
    if args.mode == "status":
      scope = profile.get("scope")
      if not isinstance(scope, str) or not re.fullmatch(r"[0-9a-f]{64}", scope):
        raise ValueError("unverified vehicle scope")
      print("vehicle lock source:", Cloud().status(scope, True)[0])
      return
    address = configured_address(PRIVATE_DIR / "system-phone.address")
    policy = Approach(profile.get("near"), profile.get("far"))
    if args.execute and not (PRIVATE_DIR / "system-unlock-enabled").is_file():
      raise ValueError("automatic system unlock not enabled")
    enable_lock = (PRIVATE_DIR / LOCK_MARKER).is_file()
    print(f"system phone unlock ready: execute={args.execute} near={policy.near} far={policy.far} "
          f"auto_lock={enable_lock} lock_requires_closed=False vehicle_status_query=False "
          f"return_after_signal_loss={ABSENCE_CONFIRM_S:g}s unlock_first_near_sample=True "
          f"startup_absence_enabled=True lock_after_signal_loss={DEPARTURE_CONFIRM_S:g}s "
          f"unlock_after_confirmed_departure=True unlock_cooldown={UNLOCK_COOLDOWN_S:g}s "
          f"lock_grace={LOCK_GRACE_S:g}s lock_cooldown={LOCK_COOLDOWN_S:g}s lock_waits_for_cooldown=True "
          f"idle_miss_retry_min_period={IDLE_MISS_MIN_PERIOD_S:g}s return_max_misses={RETURN_MAX_MISSES} "
          f"local_lock_guard={args.execute} unlock_timing={args.execute} "
          f"fast_near_period={FAST_PERIOD_S:g}s fast_zone=near-{FAST_ZONE_MARGIN_DB}dB "
          f"fast_hold={FAST_HOLD_S:g}s rise_unlock=+{RISE_MIN_DB}dB/{RISE_WINDOW_S:g}s "
          f"rise_floor={policy.rise_floor()}", flush=True)
    lock_edge = LocalLockEdge() if args.execute else None
    asyncio.run(monitor(car, address, policy, args.execute, enable_lock, PRIVATE_DIR, revision, lock_edge))
  except (ValueError, OSError, RuntimeError, ImportError):
    parser.exit(2, "system-phone automatic unlock unavailable\n")


if __name__ == "__main__":
  main()
