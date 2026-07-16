import stat
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


def test_run_supervisor_replaces_manager_process(tmp_path: Path, monkeypatch):
  supervisor = tmp_path / "wayon_remote_supervisor.sh"
  calls = []
  monkeypatch.setattr(installer, "SUPERVISOR_PATH", supervisor)
  monkeypatch.setattr(installer.os, "execv", lambda path, args: calls.append((path, args)))

  installer.run_supervisor()

  assert calls == [(str(supervisor), [str(supervisor)])]
