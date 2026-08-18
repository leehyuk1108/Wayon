#!/usr/bin/env python3
"""Fetch GMOne vehicle data without the Android accessibility scraper.

The collector client is deliberately read-only. Vehicle and account mutations
live outside this module so a background refresh cannot issue a control command.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from typing import Any
from urllib import error, parse, request
from zoneinfo import ZoneInfo
from datetime import UTC, datetime

try:
  from openpilot.tools.gmone_collector.gmone_store import GmoneStore
except ModuleNotFoundError:
  from gmone_store import GmoneStore


DEFAULT_SERVER = "https://mp.gmone.co.kr:28354"
DEFAULT_FIREBASE_URL = "https://mycarserver-fb85e-default-rtdb.firebaseio.com/car_status.json"
DEFAULT_OFFICIAL_FIREBASE_URL = "https://multipack-connected.firebaseio.com"
DEFAULT_KEYCHAIN_SERVICE = "com.wayon.gmone-collector.password"
DEFAULT_FIREBASE_API_KEY_KEYCHAIN_SERVICE = "com.wayon.gmone-collector.firebase-api-key"
DEFAULT_WAYON_UPLOAD_TOKEN_KEYCHAIN_SERVICE = "com.wayon.gmone-collector.wayon-upload-token"
DEFAULT_POLL_SECONDS = 600
DEFAULT_MAX_CACHE_AGE_SECONDS = 24 * 60 * 60
DEFAULT_ASYNC_TIMEOUT_SECONDS = 30
DEFAULT_RESULT_POLL_SECONDS = 3
DEFAULT_WAYON_REFRESH_CHECK_SECONDS = 30
LOGIN_OPERATION = 8
STATUS_OPERATION = 21
RUNNING_CYCLES_OPERATION = 45
READ_MULTIPACK_OPTION_OPERATION = 59
READ_MULTIPACK_INFO_OPERATION = 63
RESULT_FETCH_OPERATION = 66
EV_BATTERY_CHARGE_OPERATION = 70
ALLOWED_OPERATIONS = frozenset((
  LOGIN_OPERATION,
  STATUS_OPERATION,
  RUNNING_CYCLES_OPERATION,
  READ_MULTIPACK_OPTION_OPERATION,
  READ_MULTIPACK_INFO_OPERATION,
  RESULT_FETCH_OPERATION,
  EV_BATTERY_CHARGE_OPERATION,
))

CAR_CONTROL_RESULTS = {
  0: "success",
  1: "failed",
  2: "multipack_not_connected",
  3: "inside_not_connected",
  4: "inside_not_found",
  5: "vehicle_not_park",
  6: "function_all_disabled",
  7: "function_not_finished",
  8: "vehicle_communication_failed",
  9: "vehicle_not_power_off",
  10: "remote_start_no_remaining_start",
  11: "remote_start_not_running",
  12: "vehicle_busy",
  13: "request_success",
  14: "not_executed",
}

LOGIN_RESULTS = {
  0: "success",
}

LOG = logging.getLogger("gmone_collector")


class CollectorError(RuntimeError):
  pass


class AuthenticationError(CollectorError):
  pass


class ProtocolError(CollectorError):
  def __init__(self, message: str, status_code: int | None = None):
    super().__init__(message)
    self.status_code = status_code


def _as_number(value: Any) -> float | None:
  if isinstance(value, bool) or value is None:
    return None
  if isinstance(value, (int, float)):
    return float(value)
  if isinstance(value, str):
    match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
    if match:
      return float(match.group(0))
  return None


def _compact_number(value: Any) -> str | None:
  number = _as_number(value)
  if number is None:
    return None
  if number.is_integer():
    return str(int(number))
  return f"{number:.2f}".rstrip("0").rstrip(".")


def _battery_voltage(value: Any) -> str | None:
  number = _as_number(value)
  if number is None:
    return None
  if number >= 1000:
    number /= 1000
  elif number >= 100:
    number /= 10
  return f"{number:.2f}".rstrip("0").rstrip(".")


def _mileage(value: Any) -> str | None:
  number = _as_number(value)
  if number is None:
    return None
  return f"{round(number):,}"


def _timestamp_kst(timestamp: Any) -> str:
  number = _as_number(timestamp)
  if number is None:
    dt = datetime.now(UTC)
  else:
    seconds = number / 1000 if number > 10_000_000_000 else number
    dt = datetime.fromtimestamp(seconds, UTC)
  return dt.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")


def _timestamp_seconds(timestamp: Any) -> float | None:
  number = _as_number(timestamp)
  if number is None:
    return None
  return number / 1000 if number > 10_000_000_000 else number


def _tire_pressure_text(car_status: dict[str, Any]) -> str | None:
  values = [
    car_status.get("trPrsLf"),
    car_status.get("trPrsLr"),
    car_status.get("trPrsRf"),
    car_status.get("trPrsRr"),
  ]
  normalized = [_tire_pressure_kpa(value) for value in values]
  if not any(value is not None for value in normalized):
    return None
  lines = ["타이어 정보"]
  lines.extend(f"{value} kpa" if value is not None else "--" for value in normalized)
  return "\n".join(lines)


def _tire_pressure_kpa(value: Any) -> str | None:
  number = _as_number(value)
  if number is None:
    return None
  # Direct module responses use a 4 kPa/bit TPMS value, while the official
  # cache already contains kPa. Preserve either representation correctly.
  if 0 < number < 100:
    number *= 4
  return _compact_number(number)


def _number_value(value: Any) -> int | float | None:
  number = _as_number(value)
  if number is None:
    return None
  return int(number) if number.is_integer() else number


def _present_numbers(source: dict[str, Any], mapping: dict[str, str]) -> dict[str, int | float]:
  result: dict[str, int | float] = {}
  for destination, source_key in mapping.items():
    value = _number_value(source.get(source_key))
    if value is not None:
      result[destination] = value
  return result


def _binary_state(value: Any) -> dict[str, Any] | None:
  raw = _number_value(value)
  if raw is None:
    return None
  return {"raw": raw, "active": raw != 0}


def build_gmone_details(car_status: dict[str, Any]) -> dict[str, Any]:
  """Preserve every non-secret status value while exposing stable UI groups."""
  tires = {}
  for destination, source_key in {
    "frontLeftKpa": "trPrsLf",
    "frontRightKpa": "trPrsRf",
    "rearLeftKpa": "trPrsLr",
    "rearRightKpa": "trPrsRr",
  }.items():
    value = _tire_pressure_kpa(car_status.get(source_key))
    if value is not None:
      tires[destination] = _number_value(value)

  closures = {}
  for destination, source_key in {
    "doors": "door",
    "hood": "hood",
    "trunk": "trunk",
    "sunroof": "srf",
    "windowFrontLeft": "winLf",
    "windowFrontRight": "winRf",
    "windowRearLeft": "winLr",
    "windowRearRight": "winRr",
  }.items():
    state = _binary_state(car_status.get(source_key))
    if state is not None:
      closures[destination] = state

  dtc_records = car_status.get("dtc")
  if not isinstance(dtc_records, list):
    dtc_records = []
  safe_dtc_records = [
    {str(key): value for key, value in record.items() if isinstance(value, (str, int, float, bool))}
    for record in dtc_records
    if isinstance(record, dict)
  ]
  failed_dtc_count = sum(1 for record in safe_dtc_records if (_as_number(record.get("fail")) or 0) != 0)

  raw_status = {
    str(key): value
    for key, value in car_status.items()
    if key != "dtc" and isinstance(value, (str, int, float, bool))
  }
  ev_fields = _present_numbers(car_status, {
    "chargerCouplerStatusRaw": "evChgrCplrStats",
    "chargerPowerLevelRaw": "evChgrPwrLvl",
    "chargerSystemStatusRaw": "evChgrSysStats",
    "chargeCompleteTimeRaw": "evChrgCpltTm",
    "chargeCompleteTimeSetRaw": "evChrgCpltTmSet",
    "chargeStartTimeRaw": "evChrgStTm",
    "chargeStartTimeSetRaw": "evChrgStTmSet",
    "chargeStatusRaw": "evChrgStat",
    "rangeAverageKm": "evRngAvg",
    "rangeMaximumKm": "evRngMax",
    "rangeMinimumKm": "evRngMin",
  })
  ev_meaningful = any(value not in (0, 4_294_934_896) for value in ev_fields.values())

  details: dict[str, Any] = {
    "schemaVersion": "gmone-details-v1",
    "fuel": _present_numbers(car_status, {
      "capacityLiters": "fCap",
      "levelLiters": "fLvl",
      "rangeKm": "fRng",
    }),
    "battery12v": _present_numbers(car_status, {
      "voltageV": "volt",
      "chargePercent": "btChrg",
      "healthPercent": "btHlth",
      "temperatureC": "btTmp",
    }),
    "tires": tires,
    "closures": closures,
    "vehicleState": {
      **_present_numbers(car_status, {
        "engineRaw": "eng",
        "lightRaw": "light",
        "hornRaw": "hrnStats",
        "statusCounterRaw": "bCnt",
      }),
      "engineRunning": (_as_number(car_status.get("eng")) or 0) != 0,
    },
    "maintenance": _present_numbers(car_status, {
      "oilLifePercent": "olLfe",
      "defLevelPercent": "defLvl",
      "defRemainingDistanceKm": "defRmngDis",
    }),
    "diagnostics": {
      "reportedCount": int(_as_number(car_status.get("dtcCnt")) or len(safe_dtc_records)),
      "failedCount": failed_dtc_count,
      "records": safe_dtc_records,
    },
    "remoteStart": {
      **_present_numbers(car_status, {
        "levelRaw": "rsiLvl",
        "remainingStarts": "rvsRmng",
        "remainingTimeRaw": "rvsRmngTm",
      }),
      "remainingTimeValid": bool(car_status.get("rvsRmngTmVld", False)),
    },
    "ev": {"supported": ev_meaningful, **ev_fields},
    "rawStatus": raw_status,
  }
  return details


def normalize_car_status(
  car_status: dict[str, Any],
  response_timestamp: Any,
  *,
  data_source: str = "gmone-direct",
  collector_status: str = "success",
) -> dict[str, Any]:
  """Translate the official protocol fields to the existing app schema."""
  field_converters = {
    "battery": ("volt", _battery_voltage),
    "battery_level": ("btChrg", _compact_number),
    "battery_life": ("btHlth", _compact_number),
    "fuel": ("fLvl", _compact_number),
    "mileage": ("odo", _mileage),
    "oil": ("olLfe", _compact_number),
    "range": ("fRng", _compact_number),
  }
  normalized: dict[str, Any] = {}
  for destination, (source, converter) in field_converters.items():
    converted = converter(car_status.get(source))
    if converted is not None:
      normalized[destination] = converted

  tire_pressure = _tire_pressure_text(car_status)
  if tire_pressure is not None:
    normalized["tire_pressure"] = tire_pressure
    normalized["tire_pressure_all"] = tire_pressure

  normalized["gmone_details"] = build_gmone_details(car_status)

  normalized.update({
    "last_update": _timestamp_kst(response_timestamp),
    "source": data_source,
    "collector_status": collector_status,
    "collector_source": "gmone-direct",
    "collector_data_source": data_source,
    "collector_last_success": _timestamp_kst(None),
    "refresh_status": "success",
  })
  return normalized


def _read_keychain_credentials(service: str) -> tuple[str, str]:
  metadata = subprocess.run(
    ["security", "find-generic-password", "-s", service],
    check=False,
    capture_output=True,
    text=True,
  )
  if metadata.returncode != 0:
    raise AuthenticationError(f"macOS Keychain item not found for service {service!r}")
  account_match = re.search(r'"acct"<blob>="([^"]+)"', metadata.stdout)
  if account_match is None:
    raise AuthenticationError("Could not read the account name from macOS Keychain")

  secret = subprocess.run(
    ["security", "find-generic-password", "-s", service, "-w"],
    check=False,
    capture_output=True,
    text=True,
  )
  if secret.returncode != 0:
    raise AuthenticationError("Could not read the password from macOS Keychain")
  return account_match.group(1), secret.stdout.rstrip("\n")


def load_credentials(keychain_service: str) -> tuple[str, str]:
  email = os.environ.get("GMONE_EMAIL")
  password = os.environ.get("GMONE_PASSWORD")
  if email and password:
    return email, password
  if sys.platform == "darwin":
    return _read_keychain_credentials(keychain_service)
  if sys.platform == "win32" and email:
    try:
      import keyring
    except ImportError as exc:
      raise AuthenticationError("Install keyring or set GMONE_PASSWORD in the service environment") from exc
    password = keyring.get_password(keychain_service, email)
    if password:
      return email, password
  raise AuthenticationError(
    "Set GMONE_EMAIL and GMONE_PASSWORD in a protected service environment file"
  )


def load_firebase_api_key(keychain_service: str) -> str:
  api_key = os.environ.get("GMONE_FIREBASE_API_KEY")
  if api_key:
    return api_key
  if sys.platform == "darwin":
    secret = subprocess.run(
      ["security", "find-generic-password", "-s", keychain_service, "-w"],
      check=False,
      capture_output=True,
      text=True,
    )
    if secret.returncode == 0 and secret.stdout.strip():
      return secret.stdout.strip()
    raise AuthenticationError(f"macOS Keychain item not found for service {keychain_service!r}")
  raise AuthenticationError("Set GMONE_FIREBASE_API_KEY in a protected service environment file")


def load_wayon_upload_token(keychain_service: str) -> str:
  token = os.environ.get("WAYON_UPLOAD_TOKEN")
  if token:
    return token
  if sys.platform == "darwin":
    secret = subprocess.run(
      ["security", "find-generic-password", "-s", keychain_service, "-w"],
      check=False,
      capture_output=True,
      text=True,
    )
    if secret.returncode == 0 and secret.stdout.strip():
      return secret.stdout.strip()
  if sys.platform == "win32":
    try:
      import keyring
    except ImportError as exc:
      raise AuthenticationError("Install keyring or set WAYON_UPLOAD_TOKEN in the service environment") from exc
    token = keyring.get_password(keychain_service, "upload-token")
    if token:
      return token
  raise AuthenticationError("Wayon upload token is not available in the platform credential store")


def _redacted_url(url: str) -> str:
  parts = parse.urlsplit(url)
  query = "<redacted>" if parts.query else ""
  return parse.urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def _json_request(
  url: str,
  payload: dict[str, Any] | None = None,
  method: str = "POST",
  timeout: float = 20,
  headers: dict[str, str] | None = None,
) -> dict[str, Any]:
  data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
  req = request.Request(
    url,
    data=data,
    method=method,
    headers={
      "content-type": "application/json",
      "accept": "application/json",
      "user-agent": "WayonGmoneCollector/1.0",
      **(headers or {}),
    },
  )
  try:
    with request.urlopen(req, timeout=timeout) as response:
      body = response.read()
  except error.HTTPError as exc:
    raise ProtocolError(f"HTTP {exc.code} from {_redacted_url(url)}", status_code=exc.code) from exc
  except error.URLError as exc:
    raise ProtocolError(f"Network error contacting {_redacted_url(url)}: {exc.reason}") from exc
  try:
    decoded = json.loads(body)
  except json.JSONDecodeError as exc:
    raise ProtocolError(f"Non-JSON response from {_redacted_url(url)}") from exc
  if not isinstance(decoded, dict):
    raise ProtocolError(f"Unexpected response type from {_redacted_url(url)}")
  return decoded


class GmoneClient:
  def __init__(self, server: str = DEFAULT_SERVER, timeout: float = 20):
    self.server = server.rstrip("/")
    self.timeout = timeout
    self.ticket_id = 0
    self._uuid: str | None = None
    self._token: str | None = None
    self._vin: str | None = None

  @property
  def authenticated(self) -> bool:
    return self._uuid is not None and self._token is not None

  @property
  def user_uuid(self) -> str | None:
    return self._uuid

  @property
  def vin(self) -> str | None:
    return self._vin

  def clear_session(self) -> None:
    self._uuid = None
    self._token = None
    self._vin = None

  def _next_ticket(self) -> int:
    ticket = self.ticket_id
    self.ticket_id = (self.ticket_id + 1) % 256
    return ticket

  def _post(self, path: str, operation: int, login: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    if operation not in ALLOWED_OPERATIONS:
      raise ProtocolError(f"Operation {operation} is blocked by the read-only allowlist")
    payload = {
      "header": {"id": operation, "ticket_id": self._next_ticket(), "revision": 0},
      "login": login,
      "body": body,
    }
    return _json_request(f"{self.server}{path}", payload, timeout=self.timeout)

  def login(self, email: str, password: str) -> None:
    response = self._post(
      "/b1_init",
      LOGIN_OPERATION,
      {"email": email, "password": password},
      {},
    )
    login = response.get("login") or {}
    body = response.get("body") or {}
    login_result = int(login.get("success", -1))
    body_result = int(body.get("success", -1))
    if login_result != 0 or body_result != 0:
      result_name = LOGIN_RESULTS.get(login_result, f"code_{login_result}")
      raise AuthenticationError(f"GMOne login failed: {result_name}")

    user_info = login.get("user_info") or {}
    user_uuid = user_info.get("user_uuid")
    token = login.get("token_key")
    if not isinstance(user_uuid, str) or not user_uuid or not isinstance(token, str) or not token:
      raise ProtocolError("GMOne login response did not include a session token")
    self._uuid = user_uuid
    self._token = token
    car_info = login.get("car_info") or {}
    self._vin = next((key for key in car_info if isinstance(key, str) and key), None)

  def read_car_status(self, last_received_time: int = 0, *, refresh_dtc: bool = False) -> dict[str, Any]:
    return self._authenticated_post(
      STATUS_OPERATION,
      {"refresh_dtc": refresh_dtc, "last_received_time": last_received_time},
    )

  def read_running_cycles(self, last_received_time: int = 0) -> dict[str, Any]:
    return self._authenticated_post(
      RUNNING_CYCLES_OPERATION,
      {"last_received_time": last_received_time},
    )

  def read_multipack_option(self) -> dict[str, Any]:
    return self._authenticated_post(READ_MULTIPACK_OPTION_OPERATION, {})

  def read_multipack_info(self) -> dict[str, Any]:
    return self._authenticated_post(READ_MULTIPACK_INFO_OPERATION, {})

  def read_ev_battery_charge_data(self, last_received_time: int = 0) -> dict[str, Any]:
    return self._authenticated_post(
      EV_BATTERY_CHARGE_OPERATION,
      {"last_received_time": last_received_time},
    )

  def fetch_result(self, ticket_uuid: str) -> dict[str, Any]:
    if not ticket_uuid.strip():
      raise ProtocolError("A non-empty result ticket is required")
    return self._authenticated_post(RESULT_FETCH_OPERATION, {"ticket_uuid": ticket_uuid})

  def _authenticated_post(self, operation: int, body: dict[str, Any]) -> dict[str, Any]:
    if self._uuid is None or self._token is None:
      raise AuthenticationError("GMOne login is required before reading vehicle data")
    return self._post(
      "/b1_connect_m",
      operation,
      {"uuid": self._uuid, "token_key": self._token},
      body,
    )


class OfficialFirebaseClient:
  """Read the cached status used by the official GMOne app."""

  def __init__(self, api_key: str, database_url: str = DEFAULT_OFFICIAL_FIREBASE_URL, timeout: float = 20):
    self.api_key = api_key
    self.database_url = database_url.rstrip("/")
    self.timeout = timeout
    self._id_token: str | None = None
    self._local_id: str | None = None
    self._expires_at = 0.0

  def clear_session(self) -> None:
    self._id_token = None
    self._local_id = None
    self._expires_at = 0.0

  def authenticate(self, email: str, password: str) -> None:
    query = parse.urlencode({"key": self.api_key})
    response = _json_request(
      f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?{query}",
      {"email": email, "password": password, "returnSecureToken": True},
      timeout=self.timeout,
    )
    id_token = response.get("idToken")
    local_id = response.get("localId")
    expires_in = _as_number(response.get("expiresIn")) or 3600
    if not isinstance(id_token, str) or not id_token or not isinstance(local_id, str) or not local_id:
      raise AuthenticationError("Official Firebase login did not return a valid session")
    self._id_token = id_token
    self._local_id = local_id
    self._expires_at = time.monotonic() + max(60, expires_in - 60)

  def _session_valid(self) -> bool:
    return self._id_token is not None and self._local_id is not None and time.monotonic() < self._expires_at

  def read_cached_status(
    self,
    email: str,
    password: str,
    vin: str,
    expected_user_uuid: str | None = None,
  ) -> dict[str, Any]:
    if not self._session_valid():
      self.authenticate(email, password)
    if expected_user_uuid is not None and self._local_id != expected_user_uuid:
      self.clear_session()
      raise AuthenticationError("GMOne and official Firebase account identifiers do not match")

    def fetch() -> dict[str, Any]:
      assert self._local_id is not None and self._id_token is not None
      user_id = parse.quote(self._local_id, safe="")
      vehicle_id = parse.quote(vin, safe="")
      query = parse.urlencode({"auth": self._id_token})
      return _json_request(
        f"{self.database_url}/users/{user_id}/car_status/status/{vehicle_id}.json?{query}",
        None,
        method="GET",
        timeout=self.timeout,
      )

    try:
      return fetch()
    except ProtocolError as exc:
      if exc.status_code not in (401, 403):
        raise
      self.clear_session()
      self.authenticate(email, password)
      return fetch()


class CollectorState:
  def __init__(self, path: Path):
    self.path = path
    self.last_running_cycle_time = 0

  def load(self) -> None:
    try:
      data = json.loads(self.path.read_text())
      self.last_running_cycle_time = max(0, int(data.get("last_running_cycle_time", 0)))
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
      self.last_running_cycle_time = 0

  def update_cycles(self, response: dict[str, Any]) -> None:
    cycles = (response.get("body") or {}).get("running_cycles_data") or []
    received_times = [int(item["time"]) for item in cycles if isinstance(item, dict) and _as_number(item.get("time")) is not None]
    if received_times:
      self.last_running_cycle_time = max(self.last_running_cycle_time, max(received_times))

  def save(self) -> None:
    self.path.parent.mkdir(parents=True, exist_ok=True)
    temporary = self.path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"last_running_cycle_time": self.last_running_cycle_time}) + "\n")
    os.chmod(temporary, 0o600)
    temporary.replace(self.path)


def publish_firebase(firebase_url: str, payload: dict[str, Any], timeout: float = 20) -> None:
  _json_request(firebase_url, payload, method="PATCH", timeout=timeout)


def _utc_iso(timestamp: Any) -> str | None:
  seconds = _timestamp_seconds(timestamp)
  if seconds is None:
    return None
  return datetime.fromtimestamp(seconds, UTC).isoformat()


def build_wayon_payload(
  normalized: dict[str, Any],
  diagnostic: dict[str, Any],
  store: GmoneStore | None,
) -> dict[str, Any]:
  timing = store.latest_snapshot("refresh_timing") if store is not None else None
  status = dict(normalized)
  details = dict(status.get("gmone_details") or {})
  payload: dict[str, Any] = {
    "schemaVersion": "wayon-gmone-v1",
    "source": normalized.get("source", "gmone-direct"),
    "collectedAt": datetime.now(UTC).isoformat(),
    "vehicleUpdatedAt": _utc_iso((timing or {}).get("response_server_time")),
    "status": status,
    "diagnostic": diagnostic,
  }
  if store is None:
    return payload

  vehicle = dict(store.latest_snapshot("car_status") or {})
  vehicle.pop("dtc", None)
  if vehicle:
    payload["vehicle"] = vehicle
  health = store.latest_snapshot("dtc")
  if health:
    payload["health"] = health
    diagnostics = dict(details.get("diagnostics") or {})
    diagnostics.update(health)
    records = health.get("records")
    if isinstance(records, list):
      diagnostics["reportedCount"] = int(_as_number(health.get("count")) or len(records))
      diagnostics["failedCount"] = sum(
        1
        for record in records
        if isinstance(record, dict) and (_as_number(record.get("fail")) or 0) != 0
      )
    details["diagnostics"] = diagnostics
  module = {
    "option": store.latest_snapshot("multipack_option") or {},
    "info": store.latest_snapshot("multipack_info") or {},
    "evCharge": store.latest_snapshot("ev_charge_data") or {},
  }
  if any(module.values()):
    payload["module"] = module
    option_body = module["option"].get("multipack_option") if isinstance(module["option"], dict) else None
    info_body = module["info"].get("multipack_info") if isinstance(module["info"], dict) else None
    firmware = None
    if isinstance(info_body, dict):
      firmware = next((value for value in info_body.values() if isinstance(value, dict)), None)
    ev_charge_body = module["evCharge"].get("ev_charge_data") if isinstance(module["evCharge"], dict) else None
    details["module"] = {
      "settings": option_body if isinstance(option_body, dict) else {},
      "firmware": firmware if isinstance(firmware, dict) else {},
      "evChargeHistory": ev_charge_body if isinstance(ev_charge_body, list) else [],
    }
  details["runningCycles"] = store.running_cycle_summary()
  details["refresh"] = {
    "timing": timing or {},
    "collector": diagnostic,
  }
  status["gmone_details"] = details
  return payload


def publish_wayon(wayon_url: str, token: str, payload: dict[str, Any], timeout: float = 20) -> None:
  endpoint = wayon_url.rstrip("/")
  if not endpoint.endswith("/api/gmone/status"):
    endpoint = f"{endpoint}/api/gmone/status"
  _json_request(
    endpoint,
    payload,
    method="POST",
    timeout=timeout,
    headers={"authorization": f"Bearer {token}"},
  )


def wayon_refresh_pending(wayon_url: str, token: str, timeout: float = 20) -> bool:
  endpoint = f"{wayon_url.rstrip('/')}/api/gmone/refresh"
  response = _json_request(
    endpoint,
    None,
    method="GET",
    timeout=timeout,
    headers={"authorization": f"Bearer {token}"},
  )
  return response.get("pending") is True


def collector_diagnostic(result_code: int, response_timestamp: Any) -> dict[str, Any]:
  return {
    "collector_status": CAR_CONTROL_RESULTS.get(result_code, f"unknown_{result_code}"),
    "collector_last_attempt": _timestamp_kst(response_timestamp),
    "collector_source": "gmone-direct",
  }


def resolve_async_response(
  client: GmoneClient,
  response: dict[str, Any],
  *,
  timeout_seconds: float = DEFAULT_ASYNC_TIMEOUT_SECONDS,
  poll_seconds: float = DEFAULT_RESULT_POLL_SECONDS,
  sleep: Any = time.sleep,
) -> tuple[dict[str, Any], dict[str, Any]]:
  """Resolve GMOne's request-success response without repeating the request."""
  body = response.get("body") or {}
  ticket_uuid = body.get("ticket_uuid")
  wait_response = bool(body.get("wait_response", False))
  metadata = {
    "request_server_time": _timestamp_seconds(response.get("timestamp")),
    "request_result_code": int(body.get("success", -1)),
    "wait_response": wait_response,
    "result_poll_count": 0,
    "result_timed_out": False,
  }
  if not wait_response or not isinstance(ticket_uuid, str) or not ticket_uuid:
    metadata["response_server_time"] = _timestamp_seconds(response.get("timestamp"))
    return response, metadata

  deadline = time.monotonic() + timeout_seconds
  while time.monotonic() < deadline:
    sleep(min(poll_seconds, max(0, deadline - time.monotonic())))
    fetched = client.fetch_result(ticket_uuid)
    metadata["result_poll_count"] += 1
    fetched_body = fetched.get("body") or {}
    fetched_data = fetched_body.get("fetched_data")
    if isinstance(fetched_data, dict):
      metadata["result_fetch_server_time"] = _timestamp_seconds(fetched.get("timestamp"))
      metadata["response_server_time"] = _timestamp_seconds(fetched_data.get("timestamp"))
      metadata["result_code"] = int((fetched_data.get("body") or {}).get("success", -1))
      return fetched_data, metadata

  metadata["result_timed_out"] = True
  metadata["response_server_time"] = _timestamp_seconds(response.get("timestamp"))
  return response, metadata


def collect_auxiliary_data(
  client: GmoneClient,
  state: CollectorState,
  store: GmoneStore,
  *,
  async_timeout_seconds: float = DEFAULT_ASYNC_TIMEOUT_SECONDS,
  result_poll_seconds: float = DEFAULT_RESULT_POLL_SECONDS,
) -> None:
  requests = (
    ("multipack_option", client.read_multipack_option),
    ("multipack_info", client.read_multipack_info),
    ("ev_charge_data", lambda: client.read_ev_battery_charge_data(state.last_running_cycle_time)),
  )
  for kind, read in requests:
    try:
      initial_response = read()
      response, timing = resolve_async_response(
        client,
        initial_response,
        timeout_seconds=async_timeout_seconds,
        poll_seconds=result_poll_seconds,
      )
    except CollectorError as exc:
      LOG.warning("Auxiliary GMOne read failed for %s: %s", kind, exc)
      continue
    body = response.get("body") or {}
    if int(body.get("success", -1)) != 0 or len(body) <= 1:
      continue
    store.save_snapshot(kind, "gmone-direct", body, _timestamp_seconds(response.get("timestamp")))
    store.save_snapshot(f"{kind}_timing", "gmone-direct", timing, timing.get("response_server_time"))


def collect_running_cycles(client: GmoneClient, state: CollectorState, store: GmoneStore | None) -> int:
  response = client.read_running_cycles(state.last_running_cycle_time)
  body = response.get("body") or {}
  if int(body.get("success", -1)) != 0:
    return 0
  cycles = body.get("running_cycles_data") or []
  if not isinstance(cycles, list):
    return 0
  state.update_cycles(response)
  state.save()
  if store is None:
    return len(cycles)
  return store.save_running_cycles(cycle for cycle in cycles if isinstance(cycle, dict))


def collect_cached_once(
  client: GmoneClient,
  email: str,
  password: str,
  official_firebase_client: OfficialFirebaseClient | None,
  *,
  max_cache_age_seconds: int = DEFAULT_MAX_CACHE_AGE_SECONDS,
  store: GmoneStore | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
  """Read already-published GMOne data without sending a vehicle refresh request."""
  diagnostic = {
    "collector_status": "passive_cache_check",
    "collector_last_attempt": _timestamp_kst(None),
    "collector_source": "gmone-direct",
    "collector_mode": "passive",
  }
  if official_firebase_client is None:
    diagnostic["collector_cache_status"] = "disabled"
    return None, diagnostic

  if not client.authenticated:
    client.login(email, password)
  if client.vin is None:
    diagnostic["collector_cache_status"] = "vehicle_identity_unavailable"
    return None, diagnostic

  try:
    cached = official_firebase_client.read_cached_status(
      email,
      password,
      client.vin,
      expected_user_uuid=client.user_uuid,
    )
  except CollectorError as exc:
    diagnostic["collector_cache_status"] = "unavailable"
    LOG.warning("Passive official GMOne cache read failed: %s", exc)
    return None, diagnostic

  cached_car_status = cached.get("car_status")
  if not isinstance(cached_car_status, dict):
    diagnostic["collector_cache_status"] = "empty"
    return None, diagnostic

  cached_timestamp = _timestamp_seconds(cached.get("time"))
  now_timestamp = datetime.now(UTC).timestamp()
  if cached_timestamp is None or now_timestamp - cached_timestamp > max_cache_age_seconds:
    diagnostic["collector_cache_status"] = "stale"
    if cached_timestamp is not None:
      diagnostic["collector_cache_last_update"] = _timestamp_kst(cached_timestamp)
    return None, diagnostic

  latest_stored_timestamp = store.latest_snapshot_server_time("car_status") if store is not None else None
  if latest_stored_timestamp is not None and cached_timestamp <= latest_stored_timestamp:
    diagnostic.update({
      "collector_status": "passive_no_change",
      "collector_cache_status": "not_newer",
      "collector_cache_last_update": _timestamp_kst(cached_timestamp),
    })
    return None, diagnostic

  if store is not None:
    store.save_snapshot("car_status", "gmone-official-cache", cached_car_status, cached_timestamp)
    dtc_records = cached_car_status.get("dtc")
    if isinstance(dtc_records, list):
      store.save_snapshot(
        "dtc",
        "gmone-official-cache",
        {"count": cached_car_status.get("dtcCnt"), "records": dtc_records},
        cached_timestamp,
      )

  diagnostic.update({
    "collector_status": "success_cached",
    "collector_cache_status": "success",
    "collector_cache_last_update": _timestamp_kst(cached_timestamp),
  })
  normalized = normalize_car_status(
    cached_car_status,
    cached_timestamp,
    data_source="gmone-official-cache",
    collector_status="success_cached",
  )
  normalized["collector_mode"] = "passive"
  normalized["collector_cache_status"] = "success"
  return normalized, diagnostic


def collect_once(
  client: GmoneClient,
  state: CollectorState,
  email: str,
  password: str,
  official_firebase_client: OfficialFirebaseClient | None = None,
  max_cache_age_seconds: int = DEFAULT_MAX_CACHE_AGE_SECONDS,
  store: GmoneStore | None = None,
  refresh_dtc: bool = False,
  async_timeout_seconds: float = DEFAULT_ASYNC_TIMEOUT_SECONDS,
  result_poll_seconds: float = DEFAULT_RESULT_POLL_SECONDS,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
  if not client.authenticated:
    client.login(email, password)
  request_started_at = datetime.now(UTC).isoformat()
  initial_response = client.read_car_status(state.last_running_cycle_time, refresh_dtc=refresh_dtc)
  response = initial_response
  login_result = int((response.get("login") or {}).get("success", -1))
  if login_result != 0:
    client.clear_session()
    client.login(email, password)
    request_started_at = datetime.now(UTC).isoformat()
    initial_response = client.read_car_status(state.last_running_cycle_time, refresh_dtc=refresh_dtc)
    response = initial_response
    login_result = int((response.get("login") or {}).get("success", -1))
    if login_result != 0:
      client.clear_session()
      raise AuthenticationError(f"GMOne session authentication failed: code_{login_result}")

  response, timing = resolve_async_response(
    client,
    initial_response,
    timeout_seconds=async_timeout_seconds,
    poll_seconds=result_poll_seconds,
  )
  timing.update({
    "operation": STATUS_OPERATION,
    "refresh_dtc": refresh_dtc,
    "request_started_at": request_started_at,
    "response_received_at": datetime.now(UTC).isoformat(),
  })
  if store is not None:
    store.save_snapshot("refresh_timing", "gmone-direct", timing, timing.get("response_server_time"))

  state.update_cycles(response)
  state.save()
  body = response.get("body") or {}
  cycles = body.get("running_cycles_data") or []
  if store is not None and isinstance(cycles, list):
    store.save_running_cycles(cycle for cycle in cycles if isinstance(cycle, dict))
  result_code = int(body.get("success", -1))
  timestamp = response.get("timestamp")
  diagnostic = collector_diagnostic(result_code, timestamp)
  diagnostic.update({
    "collector_request_status": CAR_CONTROL_RESULTS.get(
      int(timing.get("request_result_code", -1)),
      f"unknown_{timing.get('request_result_code', -1)}",
    ),
    "collector_result_poll_count": timing["result_poll_count"],
    "collector_result_timed_out": timing["result_timed_out"],
  })
  car_status = body.get("car_status")
  if result_code == 0 and isinstance(car_status, dict):
    if store is not None:
      store.save_snapshot("car_status", "gmone-direct", car_status, _timestamp_seconds(timestamp))
      dtc_records = car_status.get("dtc")
      if isinstance(dtc_records, list):
        store.save_snapshot(
          "dtc",
          "gmone-direct",
          {"count": car_status.get("dtcCnt"), "records": dtc_records},
          _timestamp_seconds(timestamp),
        )
    try:
      collect_running_cycles(client, state, store)
    except CollectorError as exc:
      LOG.warning("Running-cycle collection failed: %s", exc)
    if store is not None:
      collect_auxiliary_data(
        client,
        state,
        store,
        async_timeout_seconds=async_timeout_seconds,
        result_poll_seconds=result_poll_seconds,
      )
    return normalize_car_status(car_status, timestamp), diagnostic

  if official_firebase_client is not None and client.vin is not None:
    try:
      cached = official_firebase_client.read_cached_status(
        email,
        password,
        client.vin,
        expected_user_uuid=client.user_uuid,
      )
      cached_car_status = cached.get("car_status")
      if isinstance(cached_car_status, dict):
        cached_timestamp = _timestamp_seconds(cached.get("time"))
        now_timestamp = datetime.now(UTC).timestamp()
        if cached_timestamp is None or now_timestamp - cached_timestamp > max_cache_age_seconds:
          diagnostic["collector_cache_status"] = "stale"
          if cached_timestamp is not None:
            diagnostic["collector_cache_last_update"] = _timestamp_kst(cached_timestamp)
          return None, diagnostic
        if store is not None:
          store.save_snapshot("car_status", "gmone-official-cache", cached_car_status, cached_timestamp)
        normalized = normalize_car_status(
          cached_car_status,
          cached_timestamp,
          data_source="gmone-official-cache",
          collector_status="success_cached",
        )
        normalized["collector_direct_status"] = diagnostic["collector_status"]
        normalized["collector_last_attempt"] = diagnostic["collector_last_attempt"]
        return normalized, diagnostic
      diagnostic["collector_cache_status"] = "empty"
    except CollectorError as exc:
      diagnostic["collector_cache_status"] = "unavailable"
      LOG.warning("Official GMOne cache fallback unavailable: %s", exc)
  return None, diagnostic


def _default_state_path() -> Path:
  return Path.home() / ".local" / "state" / "wayon" / "gmone-collector.json"


def _default_database_path() -> Path:
  return Path.home() / ".local" / "share" / "wayon" / "gmone.sqlite3"


def _configure_logging(verbose: bool) -> None:
  logging.basicConfig(
    level=logging.DEBUG if verbose else logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
  )


def _parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description="Read-only GMOne vehicle status collector")
  parser.add_argument("--once", action="store_true", help="Fetch once and exit")
  parser.add_argument("--dry-run", action="store_true", help="Do not publish to Firebase")
  parser.add_argument("--json", action="store_true", help="Print the normalized result")
  parser.add_argument("--verbose", action="store_true")
  parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
  parser.add_argument("--server", default=os.environ.get("GMONE_SERVER", DEFAULT_SERVER))
  parser.add_argument("--firebase-url", default=os.environ.get("FIREBASE_CAR_STATUS_URL", DEFAULT_FIREBASE_URL))
  parser.add_argument("--keychain-service", default=DEFAULT_KEYCHAIN_SERVICE)
  parser.add_argument("--official-firebase-url", default=os.environ.get("GMONE_OFFICIAL_FIREBASE_URL", DEFAULT_OFFICIAL_FIREBASE_URL))
  parser.add_argument("--firebase-api-key-keychain-service", default=DEFAULT_FIREBASE_API_KEY_KEYCHAIN_SERVICE)
  parser.add_argument("--wayon-url", default=os.environ.get("WAYON_CLOUD_URL", ""))
  parser.add_argument(
    "--wayon-upload-token-keychain-service",
    default=DEFAULT_WAYON_UPLOAD_TOKEN_KEYCHAIN_SERVICE,
  )
  parser.add_argument(
    "--wayon-refresh-check-seconds",
    type=int,
    default=DEFAULT_WAYON_REFRESH_CHECK_SECONDS,
  )
  parser.add_argument("--no-firebase", action="store_true", help="Do not publish the legacy Firebase status")
  parser.add_argument("--no-official-cache", action="store_true", help="Disable the official GMOne Firebase cache fallback")
  parser.add_argument("--max-cache-age-hours", type=float, default=DEFAULT_MAX_CACHE_AGE_SECONDS / 3600)
  parser.add_argument("--state-file", type=Path, default=_default_state_path())
  parser.add_argument("--database", type=Path, default=_default_database_path())
  parser.add_argument("--no-local-store", action="store_true", help="Disable local status and cycle history storage")
  parser.add_argument("--refresh-dtc", action="store_true", help="Request a fresh DTC scan with the vehicle status")
  parser.add_argument("--async-timeout-seconds", type=float, default=DEFAULT_ASYNC_TIMEOUT_SECONDS)
  parser.add_argument("--result-poll-seconds", type=float, default=DEFAULT_RESULT_POLL_SECONDS)
  return parser


def main(argv: list[str] | None = None) -> int:
  args = _parser().parse_args(argv)
  _configure_logging(args.verbose)
  if args.poll_seconds < 60 and not args.once:
    raise SystemExit("--poll-seconds must be at least 60 for daemon mode")
  if args.max_cache_age_hours <= 0:
    raise SystemExit("--max-cache-age-hours must be greater than zero")
  if args.async_timeout_seconds <= 0:
    raise SystemExit("--async-timeout-seconds must be greater than zero")
  if args.result_poll_seconds <= 0:
    raise SystemExit("--result-poll-seconds must be greater than zero")
  if args.wayon_refresh_check_seconds < 15:
    raise SystemExit("--wayon-refresh-check-seconds must be at least 15")

  email, password = load_credentials(args.keychain_service)
  state = CollectorState(args.state_file.expanduser())
  state.load()
  store = None if args.no_local_store else GmoneStore(args.database.expanduser())
  stopping = False

  def stop(_signum: int, _frame: Any) -> None:
    nonlocal stopping
    stopping = True

  signal.signal(signal.SIGTERM, stop)
  signal.signal(signal.SIGINT, stop)
  client = GmoneClient(args.server)
  official_firebase_client = None
  if not args.no_official_cache:
    try:
      firebase_api_key = load_firebase_api_key(args.firebase_api_key_keychain_service)
      official_firebase_client = OfficialFirebaseClient(firebase_api_key, args.official_firebase_url)
    except AuthenticationError as exc:
      LOG.warning("Official GMOne cache fallback disabled: %s", exc)
  wayon_upload_token = None
  if args.wayon_url and not args.dry_run:
    wayon_upload_token = load_wayon_upload_token(args.wayon_upload_token_keychain_service)

  active_refresh_requested = args.once
  while not stopping:
    try:
      if active_refresh_requested:
        normalized, diagnostic = collect_once(
          client=client,
          state=state,
          email=email,
          password=password,
          official_firebase_client=official_firebase_client,
          max_cache_age_seconds=round(args.max_cache_age_hours * 3600),
          store=store,
          refresh_dtc=args.refresh_dtc,
          async_timeout_seconds=args.async_timeout_seconds,
          result_poll_seconds=args.result_poll_seconds,
        )
      else:
        normalized, diagnostic = collect_cached_once(
          client=client,
          email=email,
          password=password,
          official_firebase_client=official_firebase_client,
          max_cache_age_seconds=round(args.max_cache_age_hours * 3600),
          store=store,
        )
      wayon_payload = build_wayon_payload(normalized, diagnostic, store) if normalized is not None else None
      payload = wayon_payload["status"] if wayon_payload is not None else diagnostic
      if not args.dry_run and not args.no_firebase:
        publish_firebase(args.firebase_url, payload)
      if not args.dry_run and args.wayon_url and wayon_upload_token and normalized is not None:
        publish_wayon(
          args.wayon_url,
          wayon_upload_token,
          wayon_payload,
        )
      if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
      if normalized is None:
        LOG.info("Vehicle status unavailable: %s; retained prior vehicle values", diagnostic["collector_status"])
      else:
        LOG.info(
          "Vehicle status updated with %d normalized fields (%s)",
          len(normalized),
          "active" if active_refresh_requested else "passive",
        )
    except CollectorError as exc:
      client.clear_session()
      LOG.warning("Collection failed: %s", exc)
      if args.once:
        return 1
    except Exception:
      LOG.exception("Unexpected collector failure")
      if args.once:
        return 1

    if args.once:
      break
    active_refresh_requested = False
    deadline = time.monotonic() + args.poll_seconds
    next_refresh_check = time.monotonic() + args.wayon_refresh_check_seconds
    while not stopping and time.monotonic() < deadline:
      now = time.monotonic()
      if args.wayon_url and wayon_upload_token and now >= next_refresh_check:
        try:
          if wayon_refresh_pending(args.wayon_url, wayon_upload_token):
            LOG.info("Wayon requested an immediate GMOne refresh")
            active_refresh_requested = True
            break
        except CollectorError as exc:
          LOG.warning("Wayon refresh request check failed: %s", exc)
        next_refresh_check = now + args.wayon_refresh_check_seconds
      time.sleep(min(1, deadline - time.monotonic()))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
