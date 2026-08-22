#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests


CONFIG_PATH = Path("/data/wayon_cloud/config.json")
INSTALL_ROOT = Path("/data/wayon-remote")
BIN_DIR = INSTALL_ROOT / "bin"
CLOUDFLARED_PATH = BIN_DIR / "cloudflared"
TOKEN_PATH = INSTALL_ROOT / "tunnel.token"
SUPERVISOR_PATH = INSTALL_ROOT / "wayon_remote_supervisor.sh"
PARAM_ONROAD = Path("/data/params/d/IsOnroad")

CLOUDFLARED_VERSION = "2026.7.2"
CLOUDFLARED_URL = (
  f"https://github.com/cloudflare/cloudflared/releases/download/{CLOUDFLARED_VERSION}/cloudflared-linux-arm64"
)
CLOUDFLARED_SHA256 = "405df476437e027fc6d18729a5a77155c0a33a6082aeee60a799a688f3052e66"
USER_AGENT = "wayon-remote-installer/1.0"

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "cloudflare/wayon-cloud/remote"
SUPERVISOR_SOURCE = SOURCE_ROOT / "wayon_remote_supervisor.sh"


def file_sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def read_config() -> dict:
  with CONFIG_PATH.open("r", encoding="utf-8") as f:
    config = json.load(f)

  endpoint = str(config.get("endpoint", "")).rstrip("/")
  token = str(config.get("token", ""))
  if not endpoint.startswith("https://") or not token:
    raise ValueError("invalid Wayon Cloud config")
  return {"endpoint": endpoint, "token": token}


def fetch_tunnel_token(config: dict) -> str:
  response = requests.get(
    f"{config['endpoint']}/api/remote/bootstrap",
    headers={
      "Authorization": f"Bearer {config['token']}",
      "Accept": "application/json",
      "User-Agent": USER_AGENT,
    },
    timeout=20,
  )
  response.raise_for_status()
  token = str(response.json().get("tunnelToken", ""))
  if len(token) < 100 or any(char.isspace() for char in token):
    raise ValueError("invalid Cloudflare Tunnel token")
  return token


def ensure_directories() -> None:
  INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
  BIN_DIR.mkdir(parents=True, exist_ok=True)
  os.chmod(INSTALL_ROOT, 0o750)
  os.chmod(BIN_DIR, 0o750)


def install_cloudflared() -> bool:
  if CLOUDFLARED_PATH.is_file() and file_sha256(CLOUDFLARED_PATH) == CLOUDFLARED_SHA256:
    return False

  download_path = BIN_DIR / ".cloudflared.download"
  digest = hashlib.sha256()
  try:
    with requests.get(CLOUDFLARED_URL, headers={"User-Agent": USER_AGENT}, stream=True, timeout=60) as response:
      response.raise_for_status()
      with download_path.open("wb") as f:
        for chunk in response.iter_content(1024 * 1024):
          if chunk:
            digest.update(chunk)
            f.write(chunk)
    if digest.hexdigest() != CLOUDFLARED_SHA256:
      raise ValueError("cloudflared checksum mismatch")
    os.chmod(download_path, 0o755)
    os.replace(download_path, CLOUDFLARED_PATH)
  finally:
    download_path.unlink(missing_ok=True)
  return True


def copy_if_changed(source: Path, destination: Path, mode: int) -> bool:
  if destination.is_file() and source.read_bytes() == destination.read_bytes():
    return False
  shutil.copyfile(source, destination)
  os.chmod(destination, mode)
  return True


def write_token(token: str) -> bool:
  content = f"{token}\n"
  if TOKEN_PATH.is_file() and TOKEN_PATH.read_text(encoding="utf-8") == content:
    return False
  temporary = TOKEN_PATH.with_suffix(".token.tmp")
  temporary.write_text(content, encoding="utf-8")
  os.chmod(temporary, 0o600)
  os.replace(temporary, TOKEN_PATH)
  return True


def install() -> None:
  config = read_config()
  token = fetch_tunnel_token(config)
  ensure_directories()

  install_cloudflared()
  copy_if_changed(SUPERVISOR_SOURCE, SUPERVISOR_PATH, 0o755)
  write_token(token)


def run_supervisor() -> int:
  supervisor = str(SUPERVISOR_PATH)
  return subprocess.run([supervisor], check=False).returncode


def is_offroad() -> bool:
  try:
    return PARAM_ONROAD.read_text(encoding="utf-8").strip() == "0"
  except OSError:
    return False


def main() -> None:
  attempt = 0
  while True:
    if not is_offroad():
      time.sleep(2)
      continue

    try:
      install()
      print("Wayon remote: installed; starting supervisor", flush=True)
      return_code = run_supervisor()
      raise RuntimeError(f"supervisor exited with code {return_code}")
    except Exception as exc:
      attempt += 1
      print(f"Wayon remote: install attempt {attempt} failed: {exc}", flush=True)
      time.sleep(2 if not is_offroad() else min(15 * attempt, 60))


if __name__ == "__main__":
  main()
