import stat
import subprocess
from pathlib import Path

import pytest

from openpilot.system import wayon_remote_installer as installer


def test_file_sha256(tmp_path: Path):
  path = tmp_path / "payload"
  path.write_bytes(b"wayon")

  assert installer.file_sha256(path) == "7fdcb6fc008278770719cb0886ee3e967ad4a463483a1a04963ba17ff7a525e3"


def test_fetch_tunnel_token_rejects_short_token(monkeypatch):
  class Response:
    def raise_for_status(self):
      return None

    def json(self):
      return {"tunnelToken": "too-short"}

  monkeypatch.setattr(installer.requests, "get", lambda *args, **kwargs: Response())

  with pytest.raises(ValueError, match="invalid Cloudflare Tunnel token"):
    installer.fetch_tunnel_token({"endpoint": "https://wayon.test", "token": "device-token"})


def test_ensure_directories_uses_writable_data_partition(tmp_path: Path, monkeypatch):
  install_root = tmp_path / "wayon-remote"
  bin_dir = install_root / "bin"
  monkeypatch.setattr(installer, "INSTALL_ROOT", install_root)
  monkeypatch.setattr(installer, "BIN_DIR", bin_dir)

  installer.ensure_directories()

  assert stat.S_IMODE(install_root.stat().st_mode) == 0o750
  assert stat.S_IMODE(bin_dir.stat().st_mode) == 0o750


def test_run_supervisor_keeps_daemon_identity(tmp_path: Path, monkeypatch):
  supervisor = tmp_path / "wayon_remote_supervisor.sh"
  calls = []
  monkeypatch.setattr(installer, "SUPERVISOR_PATH", supervisor)
  monkeypatch.setattr(
    installer.subprocess,
    "run",
    lambda args, check: calls.append((args, check)) or subprocess.CompletedProcess(args, 0),
  )

  assert installer.run_supervisor() == 0

  assert calls == [([str(supervisor)], False)]


def test_supervisor_supports_cellular_transport_fallback():
  source = installer.SUPERVISOR_SOURCE.read_text(encoding="utf-8")

  assert "--protocol quic" not in source
  assert "cloudflared_tunnel_ha_connections" in source
  assert "HEALTH_FAILURES_TO_RESTART=6" in source
  assert "systemctl start ssh" in source


def test_supervisor_shell_syntax():
  subprocess.run(["sh", "-n", str(installer.SUPERVISOR_SOURCE)], check=True)


def test_main_keeps_retrying_while_offroad(monkeypatch):
  offroad = iter((True, True, True, False))
  attempts = []
  sleeps = []

  def fail_install():
    attempts.append(1)
    raise OSError("offline")

  monkeypatch.setattr(installer, "is_offroad", lambda: next(offroad))
  monkeypatch.setattr(installer, "install", fail_install)
  monkeypatch.setattr(installer.time, "sleep", sleeps.append)

  installer.main()

  assert len(attempts) == 2
  assert sleeps == [15]
