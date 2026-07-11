#!/usr/bin/env python3
import os
from pathlib import Path
from typing import Any


SIMULATION_IGNORE_PHONE_DM = "SimulationIgnorePhoneDM"
DEFAULT_FALLBACK_ROOT = Path("/data/sunnypilot/params")
LEGACY_SIMULATION_MODE_FLAG = Path("/data/SimulationMode")


def _param_known(params: Any, key: str) -> bool:
  try:
    params.check_key(key)
    return True
  except Exception:
    return False


def _fallback_root(params: Any | None, root: Path | None) -> Path:
  if root is not None:
    return root
  if params is not None:
    try:
      return Path(params.get_param_path()).parent / "sunnypilot_fallback"
    except Exception:
      pass
  return DEFAULT_FALLBACK_ROOT


def _fallback_path(params: Any | None, root: Path | None) -> Path:
  return _fallback_root(params, root) / SIMULATION_IGNORE_PHONE_DM


def _read_bool(path: Path) -> bool:
  try:
    return path.read_text(encoding="utf-8").strip().lower() in {"1", "true", "on", "yes"}
  except OSError:
    return False


def get_simulation_ignore_phone_dm(params: Any | None = None, root: Path | None = None) -> bool:
  if params is not None and _param_known(params, SIMULATION_IGNORE_PHONE_DM):
    try:
      return bool(params.get_bool(SIMULATION_IGNORE_PHONE_DM))
    except Exception:
      pass

  fallback_path = _fallback_path(params, root)
  if fallback_path.exists():
    return _read_bool(fallback_path)

  # Preserve the existing device setting while narrowing its behavior to phone DM.
  return _read_bool(LEGACY_SIMULATION_MODE_FLAG)


def put_simulation_ignore_phone_dm(enabled: bool, params: Any | None = None, root: Path | None = None) -> None:
  if params is not None and _param_known(params, SIMULATION_IGNORE_PHONE_DM):
    try:
      params.put_bool(SIMULATION_IGNORE_PHONE_DM, enabled)
      return
    except Exception:
      pass

  path = _fallback_path(params, root)
  tmp_path = path.with_name(f".tmp_{SIMULATION_IGNORE_PHONE_DM}_{os.getpid()}")
  try:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text("1" if enabled else "0", encoding="utf-8")
    os.replace(tmp_path, path)
  finally:
    if not enabled:
      try:
        LEGACY_SIMULATION_MODE_FLAG.unlink()
      except FileNotFoundError:
        pass
