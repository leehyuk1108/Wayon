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
