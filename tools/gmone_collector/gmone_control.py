from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import time
from typing import Any

from openpilot.tools.gmone_collector.gmone_collector import (
  AuthenticationError,
  CAR_CONTROL_RESULTS,
  DEFAULT_SERVER,
  ProtocolError,
  _json_request,
)


LOGIN_OPERATION = 8
CONTROL_OPERATION = 19
RESULT_FETCH_OPERATION = 66


class ControlDisabledError(ProtocolError):
  pass


class DuplicateControlError(ProtocolError):
  pass


class ControlRateLimitError(ProtocolError):
  pass


class VehicleCommand(Enum):
  REMOTE_START_ON = (0, 2)
  REMOTE_START_OFF = (0, 0)
  DOOR_LOCK = (1, 0)
  DOOR_UNLOCK = (1, 1)
  TRUNK_CLOSE = (2, 0)
  TRUNK_OPEN = (2, 1)
  PANIC_ON = (3, 1)
  WINDOWS_CLOSE = (5, 0)
  WINDOWS_OPEN = (5, 1)
  SUNROOF_CLOSE = (6, 0)
  SUNROOF_OPEN = (6, 1)
  SUNROOF_TILT = (6, 3)

  @property
  def control_type(self) -> int:
    return self.value[0]

  @property
  def request_option(self) -> int:
    return self.value[1]


@dataclass(frozen=True)
class ControlResult:
  command: str
  idempotency_key: str
  result_code: int
  result_name: str
  ticket_uuid: str | None
  wait_response: bool
  timestamp: int | float | None


class GmoneControlClient:
  """Explicitly enabled GMOne command client, isolated from the collector."""

  def __init__(
    self,
    server: str = DEFAULT_SERVER,
    *,
    enabled: bool = False,
    minimum_interval_seconds: float = 2.0,
    timeout: float = 20,
  ):
    self.server = server.rstrip("/")
    self.enabled = enabled
    self.minimum_interval_seconds = minimum_interval_seconds
    self.timeout = timeout
    self.ticket_id = 0
    self._uuid: str | None = None
    self._token: str | None = None
    self._used_idempotency_keys: set[str] = set()
    self._last_command_time: float | None = None

  @property
  def authenticated(self) -> bool:
    return self._uuid is not None and self._token is not None

  def clear_session(self) -> None:
    self._uuid = None
    self._token = None

  def _next_ticket(self) -> int:
    ticket = self.ticket_id
    self.ticket_id = (self.ticket_id + 1) % 256
    return ticket

  def _post(self, operation: int, login: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    if operation not in (LOGIN_OPERATION, CONTROL_OPERATION, RESULT_FETCH_OPERATION):
      raise ProtocolError(f"Operation {operation} is blocked by the command allowlist")
    path = "/b1_init" if operation == LOGIN_OPERATION else "/b1_connect_m"
    return _json_request(
      f"{self.server}{path}",
      {
        "header": {"id": operation, "ticket_id": self._next_ticket(), "revision": 0},
        "login": login,
        "body": body,
      },
      timeout=self.timeout,
    )

  def login(self, email: str, password: str) -> None:
    response = self._post(LOGIN_OPERATION, {"email": email, "password": password}, {})
    login = response.get("login") or {}
    body = response.get("body") or {}
    if int(login.get("success", -1)) != 0 or int(body.get("success", -1)) != 0:
      raise AuthenticationError("GMOne command login failed")
    user_uuid = (login.get("user_info") or {}).get("user_uuid")
    token = login.get("token_key")
    if not isinstance(user_uuid, str) or not user_uuid or not isinstance(token, str) or not token:
      raise ProtocolError("GMOne command login response did not include a session token")
    self._uuid = user_uuid
    self._token = token

  def send(
    self,
    command: VehicleCommand,
    idempotency_key: str,
  ) -> ControlResult:
    if not self.enabled:
      raise ControlDisabledError("GMOne vehicle controls are disabled")
    if not self.authenticated:
      raise AuthenticationError("GMOne command login is required")
    if not idempotency_key.strip():
      raise ProtocolError("A non-empty idempotency key is required")
    if idempotency_key in self._used_idempotency_keys:
      raise DuplicateControlError("The idempotency key has already been used")

    now = time.monotonic()
    if self._last_command_time is not None and now - self._last_command_time < self.minimum_interval_seconds:
      raise ControlRateLimitError("Vehicle commands are rate limited")

    assert self._uuid is not None and self._token is not None
    response = self._post(
      CONTROL_OPERATION,
      {"uuid": self._uuid, "token_key": self._token},
      {"control_type": command.control_type, "request_option": command.request_option},
    )
    self._last_command_time = now
    self._used_idempotency_keys.add(idempotency_key)
    return self._parse_result(response, command.name, idempotency_key)

  def fetch_result(self, ticket_uuid: str) -> ControlResult:
    if not self.enabled:
      raise ControlDisabledError("GMOne vehicle controls are disabled")
    if not self.authenticated:
      raise AuthenticationError("GMOne command login is required")
    if not ticket_uuid.strip():
      raise ProtocolError("A non-empty command ticket is required")
    assert self._uuid is not None and self._token is not None
    response = self._post(
      RESULT_FETCH_OPERATION,
      {"uuid": self._uuid, "token_key": self._token},
      {"ticket_uuid": ticket_uuid},
    )
    return self._parse_result(response, "RESULT_FETCH", ticket_uuid)

  @staticmethod
  def _parse_result(response: dict[str, Any], command: str, idempotency_key: str) -> ControlResult:
    login_result = int((response.get("login") or {}).get("success", -1))
    if login_result != 0:
      raise AuthenticationError(f"GMOne command session failed: code_{login_result}")
    body = response.get("body") or {}
    result_code = int(body.get("success", -1))
    ticket_uuid = body.get("ticket_uuid")
    return ControlResult(
      command=command,
      idempotency_key=idempotency_key,
      result_code=result_code,
      result_name=CAR_CONTROL_RESULTS.get(result_code, f"unknown_{result_code}"),
      ticket_uuid=ticket_uuid if isinstance(ticket_uuid, str) and ticket_uuid else None,
      wait_response=bool(body.get("wait_response", False)),
      timestamp=response.get("timestamp") if isinstance(response.get("timestamp"), (int, float)) else None,
    )
