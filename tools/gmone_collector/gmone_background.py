#!/usr/bin/env python3
"""Independent, bounded vehicle-status collection. Never imports vehicle control."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import UTC, datetime
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import math
import os
from pathlib import Path
import re
import signal
import sys
import time

try:
  from openpilot.tools.gmone_collector import gmone_collector as protocol
  from openpilot.tools.gmone_collector.gmone_store import _without_sensitive_fields
except ModuleNotFoundError:
  import gmone_collector as protocol
  from gmone_store import _without_sensitive_fields

LOG = logging.getLogger("gmone_background")
MAX_AGE = 86400
POLL_SECONDS = 60
ACTIVE_INTERVAL = 3600
ACTIVE_MIN_GAP = 300
ACTIVE_DAILY_LIMIT = 36


def failure_code(exc):
  if isinstance(exc, protocol.ProtocolError):
    if exc.status_code is not None:
      return "http_" + str(exc.status_code)
    for prefix, code in (("Network error", "network"), ("Non-JSON", "non_json"),
                         ("Unexpected response type", "response_type"), ("JSON response exceeds", "response_size")):
      if str(exc).startswith(prefix):
        return code
  return type(exc).__name__


def iso(seconds):
  return datetime.fromtimestamp(seconds, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def epoch(value):
  if isinstance(value, bool):
    return None
  try:
    value = float(value)
    value = value / 1000 if value > 10_000_000_000 else value
    return value if math.isfinite(value) and value > 0 else None
  except (ValueError, TypeError):
    return None


def parse_iso(value):
  try:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.timestamp() if dt.tzinfo is not None else None
  except (TypeError, ValueError, AttributeError):
    return None


def account_fingerprint(email):
  return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def atomic_json(path, value):
  data = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
  if len(data) > 512 * 1024:
    raise ValueError("state_size")
  path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
  temporary = path.with_suffix(path.suffix + ".new")
  with open(temporary, "wb") as stream:
    os.chmod(temporary, 0o600)
    stream.write(data)
    stream.flush()
    os.fsync(stream.fileno())
  os.replace(temporary, path)


@contextmanager
def instance_lock(path):
  path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
  with open(path, "a+b") as lock:
    lock.seek(0)
    if os.name == "nt":
      import msvcrt
      if path.stat().st_size == 0:
        lock.write(b"0")
        lock.flush()
      lock.seek(0)
      msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    else:
      import fcntl
      fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    yield


class State:
  def __init__(self, path, scope):
    if not isinstance(scope, str) or not re.fullmatch(r"[a-f0-9]{64}", scope):
      raise ValueError("invalid_scope")
    self.path = path
    self.data = {"version": 1, "scope": scope}
    if path.exists():
      if path.stat().st_size > 512 * 1024:
        raise ValueError("state_size")
      data = json.loads(path.read_text(encoding="utf-8"))
      if data.get("version") != 1 or data.get("scope") != scope:
        raise ValueError("state_scope_mismatch")
      self.data = data

  def save(self):
    atomic_json(self.path, self.data)

  def offer(self, raw, observed, source, now, request_started=None):
    observed = epoch(observed)
    if observed is None or not -120 <= now - observed <= MAX_AGE or not isinstance(raw, dict) or not raw:
      return False
    status = _without_sensitive_fields(protocol.normalize_car_status(raw, observed, data_source=source))
    # The source observation time, never receipt time, determines freshness/order.
    status["collector_last_success"] = status["last_update"]
    digest = hashlib.sha256(json.dumps(status, sort_keys=True, allow_nan=False).encode()).hexdigest()
    if observed < self.data.get("latestEpoch", 0):
      return False
    if observed == self.data.get("latestEpoch") and digest == self.data.get("latestDigest"):
      return False
    pending = {"schemaVersion": "wayon-gmone-v1", "clientScope": self.data["scope"],
               "source": source, "vehicleUpdatedAt": iso(observed), "collectedAt": iso(now), "status": status}
    if source == "gmone-direct" and request_started is not None:
      pending["refreshStartedAt"] = iso(request_started)
    self.data.update(latestEpoch=observed, latestDigest=digest, pending=pending)
    self.save()
    return True

  def reserve_active(self, now, requested_at=None):
    requested = parse_iso(requested_at)
    manual = (requested is not None and 0 <= now - requested <= 3600
              and requested > self.data.get("handledRequest", 0))
    periodic = now - max(self.data.get("lastActive", 0), self.data.get("latestEpoch", 0)) >= ACTIVE_INTERVAL
    if not (manual or periodic) or now - self.data.get("lastActive", 0) < ACTIVE_MIN_GAP:
      return False
    if now - self.data.get("budgetStart", 0) >= 86400:
      self.data.update(budgetStart=now, activeCount=0)
    if self.data.get("activeCount", 0) >= ACTIVE_DAILY_LIMIT:
      return False
    self.data["activeCount"] = self.data.get("activeCount", 0) + 1
    self.data["lastActive"] = now
    if manual:
      self.data["handledRequest"] = requested
    # Persist before the external read: a crash/restart must not repeat it.
    self.save()
    return True

  def upload(self, post, now):
    pending = self.data.get("pending")
    if not pending or now < self.data.get("nextUpload", 0):
      return "idle"
    if now - (parse_iso(pending["collectedAt"]) or 0) > MAX_AGE:
      self.data.pop("pending", None)
      self.save()
      return "expired"
    try:
      result = post(pending)
      if result.get("ok") is not True:
        raise ValueError("upload_ack")
    except protocol.ProtocolError as exc:
      if exc.status_code != 409 or exc.error_code != "snapshot_not_newer":
        self.failed_upload(now)
        raise
      # Only this explicit conflict confirms a newer valid server snapshot.
      result = {"superseded": True}
    except Exception:
      self.failed_upload(now)
      raise
    self.data.pop("pending", None)
    self.data.update(uploadFailures=0, nextUpload=0, lastDelivered=now,
                     lastDelivery="superseded" if result.get("superseded") else "stored")
    self.save()
    return self.data["lastDelivery"]

  def failed_upload(self, now):
    failures = min(8, self.data.get("uploadFailures", 0) + 1)
    self.data.update(uploadFailures=failures, nextUpload=now + min(900, 30 * 2 ** (failures - 1)))
    self.save()


class StatusClient(protocol.GmoneClient):
  def _post(self, path, operation, login, body):
    if operation not in (8, 21, 66) or (operation == 21 and body.get("refresh_dtc") is not False):
      raise protocol.ProtocolError("background_operation_blocked")
    response = super()._post(path, operation, login, body)
    auth = response.get("login") or {}
    if operation != 8 and "success" in auth and auth["success"] != 0:
      raise protocol.AuthenticationError("authenticated_request_rejected")
    if operation == 66:
      result = response.get("body") or {}
      self.result_diagnostic = {"code": result.get("success") if type(result.get("success")) is int else -1,
                                "hasData": isinstance(result.get("fetched_data"), dict)}
    return response

  def login(self, email, password):
    response = self._post("/b1_init", 8, {"email": email, "password": password}, {})
    login, body = response.get("login") or {}, response.get("body") or {}
    if login.get("success") != 0 or body.get("success") != 0:
      raise protocol.AuthenticationError("login_rejected")
    uuid = login.get("user_info_uuid") or (login.get("user_info") or {}).get("user_uuid")
    token = login.get("token_key")
    cars = login.get("car_info")
    if not isinstance(cars, dict) or len(cars) != 1 or not isinstance(uuid, str) or not uuid or not isinstance(token, str) or not token:
      raise protocol.AuthenticationError("ambiguous_account")
    self._uuid, self._token, self._vin = uuid, token, next(iter(cars))


class Collector:
  def __init__(self, config, state, email, password, firebase_key, upload_token, now=time.time):
    if config["accountFingerprint"] != account_fingerprint(email):
      raise ValueError("account_scope_mismatch")
    if config["url"] != "https://wayon-cloud.hyuklee.workers.dev":
      raise ValueError("cloud_origin")
    self.config, self.state, self.now = config, state, now
    self.email, self.password, self.token = email, password, upload_token
    self.client = StatusClient()
    self.cache = protocol.OfficialFirebaseClient(firebase_key)
    self.health = {"version": 1}
    self.next_cache = self.next_login = 0
    self.login_failures = self.cache_failures = 0
    self.cloud_verified = False

  def cloud(self, path, payload=None):
    if payload is not None and not self.cloud_verified:
      raise ValueError("cloud_identity_unverified")
    result = protocol._json_request(self.config["url"] + path, payload,
      method="GET" if payload is None else "POST", timeout=12,
      headers={"authorization": "Bearer " + self.token})
    if result.get("deviceId") != self.config["deviceId"]:
      self.cloud_verified = False
      raise ValueError("cloud_device_mismatch")
    if payload is None and path == "/api/gmone/refresh":
      self.cloud_verified = True
    return result

  def step(self):
    now = self.now()
    self.health["checkedAt"] = iso(now)
    # Cloud outage does not invalidate GMOne authentication or trigger a vehicle read.
    self.cloud_verified = False
    try:
      refresh = self.cloud("/api/gmone/refresh")
      self.health.pop("cloudError", None)
    except Exception as exc:
      self.health["cloudError"] = type(exc).__name__
      refresh = None
    try:
      delivery = self.state.upload(lambda body: self.cloud("/api/gmone/status", body), now) if refresh is not None else "idle"
      if delivery != "idle":
        self.health.update(delivery=delivery, deliveryAt=iso(now))
        self.health.pop("uploadError", None)
        self.health.pop("uploadFailure", None)
        LOG.info("snapshot %s", delivery)
    except Exception as exc:
      self.health["uploadError"] = type(exc).__name__
      self.health["uploadFailure"] = failure_code(exc)
    if now < self.next_login:
      return
    try:
      if not self.client.authenticated:
        self.client.login(self.email, self.password)
        self.login_failures = 0
      if now >= self.next_cache:
        self.next_cache = now + POLL_SECONDS
        try:
          cached = self.cache.read_cached_status(self.email, self.password, self.client.vin,
                                                 expected_user_uuid=self.client.user_uuid)
          offered = self.state.offer(cached.get("car_status"), cached.get("time"), "gmone-official-cache", self.now())
          self.health.update(cacheCheckedAt=iso(self.now()), cacheChanged=offered)
          self.health.pop("cacheError", None)
          self.health.pop("cacheFailure", None)
          self.cache_failures = 0
        except Exception as exc:
          self.health["cacheError"] = type(exc).__name__
          self.health["cacheFailure"] = failure_code(exc)
          self.cache_failures = min(6, self.cache_failures + 1)
          self.next_cache = self.now() + min(3600, 60 * 2 ** self.cache_failures)
      # Never wake a vehicle while the upload server is unreachable.
      active_start = self.now()
      if refresh is not None and self.state.reserve_active(active_start, refresh.get("requestedAt") if refresh.get("pending") else None):
        self.health["activeAttemptAt"] = iso(active_start)
        for key in ("resultDiagnostic", "resultTimedOut", "resultPolls", "activeResult"):
          self.health.pop(key, None)
        if hasattr(self.client, "result_diagnostic"):
          del self.client.result_diagnostic
        # This is an opaque server history cursor, not a wall-clock timestamp.
        response = self.client.read_car_status(last_received_time=self.state.data.get("historyCursor", 0), refresh_dtc=False)
        auth = response.get("login") or {}
        if "success" in auth and auth["success"] != 0:
          raise protocol.AuthenticationError("status_session_expired")
        response, timing = protocol.resolve_async_response(self.client, response)
        self.health["resultPolls"] = timing.get("result_poll_count", 0)
        self.health["resultTimedOut"] = bool(timing.get("result_timed_out"))
        if hasattr(self.client, "result_diagnostic"):
          self.health["resultDiagnostic"] = self.client.result_diagnostic
        body = response.get("body") or {}
        self.health["activeResult"] = body.get("success") if isinstance(body.get("success"), int) else -1
        # fetched_data is nested inside an authenticated op-66 response and
        # normally has no repeated login object (same contract as the app).
        auth = response.get("login") or {}
        if "success" in auth and auth["success"] != 0:
          raise protocol.AuthenticationError("result_session_expired")
        if body.get("success") == 0 and not timing.get("result_timed_out"):
          cycles = body.get("running_cycles_data")
          if isinstance(cycles, list):
            times = [item.get("time") for item in cycles if isinstance(item, dict)]
            cursors = [value for value in times if type(value) is int and value >= 0]
            if cursors:
              self.state.data["historyCursor"] = max(self.state.data.get("historyCursor", 0), max(cursors))
              self.state.save()
          self.health["statusResponseBytes"] = len(json.dumps(response).encode())
          self.state.offer(body.get("car_status"), response.get("timestamp"), "gmone-direct", self.now(), active_start)
        LOG.info("status read completed code=%s", self.health["activeResult"])
      self.health.pop("collectionError", None)
      self.health.pop("collectionFailure", None)
    except protocol.AuthenticationError:
      self.client.clear_session()
      self.cache.clear_session()
      self.login_failures = min(6, self.login_failures + 1)
      self.next_login = now + min(3600, 60 * 2 ** self.login_failures)
      self.health["collectionError"] = "AuthenticationError"
    except Exception as exc:
      self.health["collectionError"] = type(exc).__name__
      self.health["collectionFailure"] = failure_code(exc)
      self.health["lastCollectionFailure"] = {"at": iso(self.now()), "code": failure_code(exc)}
      if not self.client.authenticated:
        self.login_failures = min(6, self.login_failures + 1)
        self.next_login = now + min(3600, 60 * 2 ** self.login_failures)
    try:
      delivery = self.state.upload(lambda body: self.cloud("/api/gmone/status", body), self.now()) if refresh is not None else "idle"
      if delivery != "idle":
        self.health.update(delivery=delivery, deliveryAt=iso(self.now()))
        self.health.pop("uploadError", None)
        self.health.pop("uploadFailure", None)
        LOG.info("snapshot %s", delivery)
    except Exception as exc:
      self.health["uploadError"] = type(exc).__name__
      self.health["uploadFailure"] = failure_code(exc)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--root", type=Path, required=True)
  parser.add_argument("--once", action="store_true")
  args = parser.parse_args()
  root = args.root
  (root / "logs").mkdir(parents=True, exist_ok=True)
  handler = RotatingFileHandler(root / "logs/background.log", maxBytes=512 * 1024, backupCount=3, encoding="utf-8")
  logging.basicConfig(level=logging.INFO, handlers=[handler], format="%(asctime)s %(levelname)s %(message)s")
  with instance_lock(root / "data/background.lock"):
    config = json.loads((root / "config/background.json").read_text(encoding="utf-8-sig"))
    email_config = json.loads((root / "config/gmone.json").read_text(encoding="utf-8-sig"))
    os.environ["GMONE_EMAIL"] = email_config["email"]
    email, password = protocol.load_credentials(protocol.DEFAULT_KEYCHAIN_SERVICE)
    state = State(root / "data/background-state.json", config["clientScope"])
    collector = Collector(config, state, email, password,
      protocol.load_firebase_api_key(protocol.DEFAULT_FIREBASE_API_KEY_KEYCHAIN_SERVICE),
      protocol.load_wayon_upload_token(protocol.DEFAULT_WAYON_UPLOAD_TOKEN_KEYCHAIN_SERVICE))
    stopping = False
    def stop(*_):
      nonlocal stopping
      stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    LOG.info("background collector started")
    while not stopping:
      try:
        collector.step()
        atomic_json(root / "data/background-health.json", collector.health)
      except Exception as exc:
        LOG.warning("cycle failed: %s", type(exc).__name__)
      if args.once:
        break
      for _ in range(30):
        if stopping:
          break
        time.sleep(1)
    LOG.info("background collector stopped")


if __name__ == "__main__":
  try:
    main()
  except Exception as exc:
    LOG.error("startup failed: %s", type(exc).__name__)
    sys.exit(1)
