import pytest

from openpilot.tools.gmone_collector.gmone_control import (
  ControlDisabledError,
  DuplicateControlError,
  GmoneControlClient,
  VehicleCommand,
)


EXPECTED_COMMANDS = {
  "REMOTE_START_ON": (0, 2),
  "REMOTE_START_OFF": (0, 0),
  "DOOR_LOCK": (1, 0),
  "DOOR_UNLOCK": (1, 1),
  "TRUNK_CLOSE": (2, 0),
  "TRUNK_OPEN": (2, 1),
  "PANIC_ON": (3, 1),
  "WINDOWS_CLOSE": (5, 0),
  "WINDOWS_OPEN": (5, 1),
  "SUNROOF_CLOSE": (6, 0),
  "SUNROOF_OPEN": (6, 1),
  "SUNROOF_TILT": (6, 3),
}


def test_official_command_mapping_is_complete():
  assert {command.name: command.value for command in VehicleCommand} == EXPECTED_COMMANDS


def test_control_is_disabled_by_default():
  client = GmoneControlClient()
  with pytest.raises(ControlDisabledError):
    client.send(VehicleCommand.DOOR_LOCK, "request-1")


def test_control_request_uses_named_mapping_and_idempotency(monkeypatch):
  captured = {}

  def fake_json_request(url, payload, **_kwargs):
    captured["url"] = url
    captured["payload"] = payload
    return {
      "login": {"success": 0},
      "body": {"success": 13, "ticket_uuid": "ticket-1", "wait_response": True},
      "timestamp": 1234,
    }

  monkeypatch.setattr("openpilot.tools.gmone_collector.gmone_control._json_request", fake_json_request)
  client = GmoneControlClient(enabled=True, minimum_interval_seconds=0)
  client._uuid = "user-uuid"
  client._token = "session-token"
  result = client.send(VehicleCommand.DOOR_UNLOCK, "request-1")
  assert captured["url"].endswith("/b1_connect_m")
  assert captured["payload"]["header"]["id"] == 19
  assert captured["payload"]["body"] == {"control_type": 1, "request_option": 1}
  assert result.result_name == "request_success"
  assert result.ticket_uuid == "ticket-1"
  assert result.wait_response is True

  with pytest.raises(DuplicateControlError):
    client.send(VehicleCommand.DOOR_UNLOCK, "request-1")


def test_result_fetch_uses_command_ticket(monkeypatch):
  captured = {}

  def fake_json_request(_url, payload, **_kwargs):
    captured["payload"] = payload
    return {"login": {"success": 0}, "body": {"success": 0}}

  monkeypatch.setattr("openpilot.tools.gmone_collector.gmone_control._json_request", fake_json_request)
  client = GmoneControlClient(enabled=True)
  client._uuid = "user-uuid"
  client._token = "session-token"
  result = client.fetch_result("ticket-1")
  assert captured["payload"]["header"]["id"] == 66
  assert captured["payload"]["body"] == {"ticket_uuid": "ticket-1"}
  assert result.result_name == "success"
