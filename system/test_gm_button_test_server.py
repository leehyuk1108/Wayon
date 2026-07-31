import json
import socket

import pytest

from openpilot.system.gm_button_test_server import is_allowed_client, send_button_command


def test_client_network_filter():
  assert is_allowed_client("127.0.0.1")
  assert is_allowed_client("10.110.240.173")
  assert is_allowed_client("192.168.35.69")
  assert not is_allowed_client("8.8.8.8")
  assert not is_allowed_client("invalid")


def test_button_command_payload(monkeypatch):
  sent = []

  class FakeSocket:
    def __enter__(self):
      return self

    def __exit__(self, *_args):
      return None

    def sendto(self, payload, path):
      sent.append((payload, path))

  monkeypatch.setattr(socket, "socket", lambda *_args: FakeSocket())
  send_button_command("res", "/tmp/test.sock")

  payload, path = sent[0]
  command = json.loads(payload)
  assert path == "/tmp/test.sock"
  assert command["schema"] == "gm-button-test-v1"
  assert command["button"] == "res"
  assert isinstance(command["issuedAtMono"], float)


def test_unsupported_button_rejected():
  with pytest.raises(ValueError):
    send_button_command("main")
