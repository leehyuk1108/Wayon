import json
import os
from pathlib import Path
import socket
import threading

import pytest

import openpilot.system.gm_button_test_server as button_server
from openpilot.system.gm_button_test_server import GMButtonTestServer, build_button_command, is_allowed_client


def test_client_network_filter():
  assert is_allowed_client("127.0.0.1")
  assert is_allowed_client("10.110.240.173")
  assert is_allowed_client("192.168.35.69")
  assert not is_allowed_client("8.8.8.8")
  assert not is_allowed_client("invalid")


def test_button_command_payload():
  payload = build_button_command("res", "command-id")
  command = json.loads(payload)
  assert command["schema"] == "gm-button-test-v2"
  assert command["id"] == "command-id"
  assert command["button"] == "res"
  assert isinstance(command["issuedAtMono"], float)


def test_unsupported_button_rejected():
  with pytest.raises(ValueError):
    build_button_command("main", "command-id")


def test_controller_ack_round_trip(monkeypatch):
  command_path = f"/tmp/gmb-{os.getpid()}-controller.sock"
  ack_path = f"/tmp/gmb-{os.getpid()}-web.sock"
  monkeypatch.setattr(button_server, "BUTTON_SOCKET", command_path)
  monkeypatch.setattr(button_server, "ACK_SOCKET", ack_path)

  controller_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
  controller_socket.bind(command_path)

  def controller():
    command = json.loads(controller_socket.recv(1024))
    controller_socket.sendto(json.dumps({
      "schema": "gm-button-test-ack-v1",
      "id": command["id"],
      "state": "transmitted",
      "bus": 2,
      "counter": 1,
    }).encode(), ack_path)

  thread = threading.Thread(target=controller)
  thread.start()

  class FakeParams:
    def get_bool(self, _key):
      return True

  server = GMButtonTestServer(("127.0.0.1", 0), params=FakeParams())
  try:
    result = server.controller_request("res", 0.5)
    assert result["state"] == "transmitted"
    assert result["bus"] == 2
  finally:
    server.server_close()
    thread.join(timeout=1)
    controller_socket.close()
    Path(command_path).unlink(missing_ok=True)
