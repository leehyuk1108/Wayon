#!/usr/bin/env python3
import json
import os
import secrets
from pathlib import Path

import requests

from openpilot.common.params import Params


DEFAULT_ENDPOINT = "https://wayon-cloud.hyuklee.workers.dev"
DEFAULT_CONFIG_PATH = Path("/data/wayon_cloud/config.json")
USER_AGENT = "wayon-device-identity/1.0"


def _read_json(path: Path) -> dict:
  try:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}
  except (OSError, TypeError, ValueError):
    return {}


def _param_text(params: Params, key: str) -> str:
  value = params.get(key)
  if isinstance(value, bytes):
    return value.decode("utf-8", "replace").strip()
  return str(value or "").strip()


def _write_json_atomic(path: Path, value: dict) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  temporary = path.with_suffix(path.suffix + ".tmp")
  temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
  os.chmod(temporary, 0o600)
  os.replace(temporary, path)


def ensure_wayon_identity(config_path: Path = DEFAULT_CONFIG_PATH, params: Params | None = None) -> dict | None:
  params = params or Params()
  config = _read_json(config_path)
  endpoint = str(config.get("endpoint") or DEFAULT_ENDPOINT).rstrip("/")
  device_id = str(config.get("device_id") or _param_text(params, "DongleId"))
  old_token = str(config.get("token") or "")
  if not endpoint.startswith("https://") or not device_id or device_id == "UnregisteredDevice":
    return None
  if old_token.startswith("wayon_"):
    config.update(endpoint=endpoint, device_id=device_id)
    return config

  key = f"wayon_{secrets.token_urlsafe(32)}"
  headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
  if old_token:
    headers["Authorization"] = f"Bearer {old_token}"
  response = requests.post(
    f"{endpoint}/api/devices/register",
    json={"deviceId": device_id, "key": key},
    headers=headers,
    timeout=20,
  )
  response.raise_for_status()

  config.update(endpoint=endpoint, device_id=device_id, token=key)
  _write_json_atomic(config_path, config)
  print(f"Wayon identity: registered device {device_id}", flush=True)
  return config

