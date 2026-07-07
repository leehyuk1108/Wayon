#!/usr/bin/env python3
import hashlib
import os
from pathlib import Path


SIMULATION_MODE_FLAG = Path(os.getenv("SIMULATION_MODE_FLAG", "/data/SimulationMode"))
TRUE_VALUES = {"1", "true", "on", "yes", "enabled"}
DEVICE_ONLY_RUNTIME_HASHES = {
  # comma 10.234.104.173 / serial db5ce68d
  "e6b2fee68627fc38d60c768f91ef165f8d299dc545f4665cd5525c4e88c7dc3e",
}


def simulation_runtime() -> bool:
  return "SIMULATION" in os.environ or "REPLAY" in os.environ


def raw_simulation_mode_enabled() -> bool:
  env_value = os.getenv("SIMULATION_MODE", "").strip().lower()
  if env_value in TRUE_VALUES:
    return True

  try:
    flag_value = SIMULATION_MODE_FLAG.read_text(encoding="utf-8").strip().lower()
  except OSError:
    return False
  return flag_value in TRUE_VALUES


def _value_hash(value: str | None) -> str:
  return hashlib.sha256((value or "").strip().encode("utf-8")).hexdigest()


def current_device_allowed() -> bool:
  device_ids: list[str | None] = []
  try:
    from openpilot.system.hardware import HARDWARE
    device_ids.append(HARDWARE.get_serial())
  except Exception:
    pass

  try:
    from openpilot.common.params import Params
    params = Params()
    device_ids.append(params.get("HardwareSerial"))
  except Exception:
    pass

  return any(_value_hash(device_id) in DEVICE_ONLY_RUNTIME_HASHES for device_id in device_ids)


def set_raw_simulation_mode_enabled(enabled: bool) -> None:
  if enabled:
    SIMULATION_MODE_FLAG.parent.mkdir(parents=True, exist_ok=True)
    SIMULATION_MODE_FLAG.write_text("1\n", encoding="utf-8")
    return

  try:
    SIMULATION_MODE_FLAG.unlink()
  except FileNotFoundError:
    pass


def simulation_mode_enabled() -> bool:
  return raw_simulation_mode_enabled() and (simulation_runtime() or current_device_allowed())
