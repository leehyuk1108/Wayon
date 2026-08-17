from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any


SENSITIVE_KEYS = frozenset({
  "access_token",
  "api_key",
  "email",
  "firebase_auth_token",
  "iccid",
  "imei",
  "modem_phone_number",
  "password",
  "phone_number",
  "sub_email",
  "token_key",
  "user_uuid",
  "uuid",
  "vin",
})

SENSITIVE_KEY_FRAGMENTS = (
  "access_token",
  "api_key",
  "auth_token",
  "door_password",
  "firebase_auth",
  "iccid",
  "imei",
  "password",
  "phone_number",
  "secret",
  "session_token",
  "ticket_uuid",
  "token_key",
  "user_uuid",
)
VIN_PATTERN = re.compile(r"[A-HJ-NPR-Z0-9]{17}", re.IGNORECASE)
UUID_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", re.IGNORECASE)


def _is_sensitive_key(key: Any) -> bool:
  normalized = str(key).casefold()
  return normalized in SENSITIVE_KEYS or any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)


def _redact_identifier(value: str) -> str:
  if VIN_PATTERN.fullmatch(value) or UUID_PATTERN.fullmatch(value):
    return "<redacted>"
  return value


def _without_sensitive_fields(value: Any) -> Any:
  if isinstance(value, dict):
    safe = {}
    for key, item in value.items():
      if _is_sensitive_key(key):
        continue
      safe[_redact_identifier(str(key))] = _without_sensitive_fields(item)
    return safe
  if isinstance(value, list):
    return [_without_sensitive_fields(item) for item in value]
  if isinstance(value, str):
    return _redact_identifier(value)
  return value


class GmoneStore:
  """Local vehicle-data archive that never stores account or session secrets."""

  def __init__(self, path: Path):
    self.path = path
    parent_was_missing = not self.path.parent.exists()
    self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if parent_was_missing:
      os.chmod(self.path.parent, 0o700)
    self._initialize()

  def _connect(self) -> sqlite3.Connection:
    connection = sqlite3.connect(self.path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection

  def _initialize(self) -> None:
    with self._connect() as connection:
      connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS snapshots (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          kind TEXT NOT NULL,
          source TEXT NOT NULL,
          server_time REAL,
          collected_at TEXT NOT NULL,
          payload_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS snapshots_kind_time
          ON snapshots(kind, server_time DESC, id DESC);

        CREATE TABLE IF NOT EXISTS running_cycles (
          server_time INTEGER PRIMARY KEY,
          payload_json TEXT NOT NULL,
          collected_at TEXT NOT NULL
        );
        """
      )
    os.chmod(self.path, 0o600)

  def save_snapshot(
    self,
    kind: str,
    source: str,
    payload: dict[str, Any],
    server_time: float | None,
  ) -> None:
    collected_at = datetime.now(UTC).isoformat()
    safe_payload = _without_sensitive_fields(payload)
    encoded = json.dumps(safe_payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with self._connect() as connection:
      connection.execute(
        "INSERT INTO snapshots(kind, source, server_time, collected_at, payload_json) VALUES (?, ?, ?, ?, ?)",
        (kind, source, server_time, collected_at, encoded),
      )

  def save_running_cycles(self, cycles: Iterable[dict[str, Any]]) -> int:
    collected_at = datetime.now(UTC).isoformat()
    rows = []
    for cycle in cycles:
      timestamp = cycle.get("time")
      if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
        continue
      rows.append((
        int(timestamp),
        json.dumps(cycle, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        collected_at,
      ))
    if not rows:
      return 0
    with self._connect() as connection:
      before = connection.total_changes
      connection.executemany(
        "INSERT OR IGNORE INTO running_cycles(server_time, payload_json, collected_at) VALUES (?, ?, ?)",
        rows,
      )
      return connection.total_changes - before

  def latest_snapshot(self, kind: str) -> dict[str, Any] | None:
    with self._connect() as connection:
      row = connection.execute(
        "SELECT payload_json FROM snapshots WHERE kind = ? ORDER BY server_time DESC, id DESC LIMIT 1",
        (kind,),
      ).fetchone()
    if row is None:
      return None
    payload = json.loads(row["payload_json"])
    return payload if isinstance(payload, dict) else None

  def running_cycle_count(self) -> int:
    with self._connect() as connection:
      row = connection.execute("SELECT COUNT(*) AS count FROM running_cycles").fetchone()
    return int(row["count"])
