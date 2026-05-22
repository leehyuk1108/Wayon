from pathlib import Path
import os
from typing import Any


SIMULATION_IGNORE_PHONE_DM = "SimulationIgnorePhoneDM"
DEFAULT_PARAMS_ROOT = Path("/data/params/d")


def _param_known(params: Any, key: str) -> bool:
  try:
    params.check_key(key)
    return True
  except Exception:
    return False


def _param_path(params: Any | None, key: str, root: Path | None) -> Path:
  if root is not None:
    return root / key

  if params is not None:
    try:
      return Path(params.get_param_path(key))
    except Exception:
      pass

  return DEFAULT_PARAMS_ROOT / key


def _raw_bool(path: Path, default: bool = False) -> bool:
  try:
    value = path.read_text(encoding="utf-8").strip().lower()
  except OSError:
    return default
  return value in {"1", "true", "on", "yes"}


def get_simulation_ignore_phone_dm(params: Any | None = None, root: Path | None = None) -> bool:
  if params is not None and _param_known(params, SIMULATION_IGNORE_PHONE_DM):
    try:
      return bool(params.get_bool(SIMULATION_IGNORE_PHONE_DM))
    except Exception:
      pass

  return _raw_bool(_param_path(params, SIMULATION_IGNORE_PHONE_DM, root))


def put_simulation_ignore_phone_dm(enabled: bool, params: Any | None = None, root: Path | None = None) -> None:
  if params is not None and _param_known(params, SIMULATION_IGNORE_PHONE_DM):
    try:
      params.put_bool(SIMULATION_IGNORE_PHONE_DM, enabled)
      return
    except Exception:
      pass

  path = _param_path(params, SIMULATION_IGNORE_PHONE_DM, root)
  tmp_path = path.with_name(f".tmp_{SIMULATION_IGNORE_PHONE_DM}_{os.getpid()}")
  try:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text("1" if enabled else "0", encoding="utf-8")
    os.replace(tmp_path, path)
  except OSError:
    try:
      tmp_path.unlink(missing_ok=True)
    except OSError:
      pass
