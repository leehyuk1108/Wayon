#!/usr/bin/env python3
import os
from pathlib import Path


SIMULATION_MODE_FLAG = Path(os.getenv("SIMULATION_MODE_FLAG", "/data/SimulationMode"))
TRUE_VALUES = {"1", "true", "on", "yes", "enabled"}


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
  return simulation_runtime() and raw_simulation_mode_enabled()
