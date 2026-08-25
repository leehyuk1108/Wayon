from collections import deque

import pytest
from websocket import ABNF, WebSocketTimeoutException

from openpilot.system import wayon_remote_relay as relay


class FakeWebSocket:
  def __init__(self, events):
    self.events = deque(events)
    self.timeout = None
    self.pings = []

  def settimeout(self, timeout):
    self.timeout = timeout

  def recv_data(self, control_frame=False):
    event = self.events.popleft()
    if isinstance(event, Exception):
      raise event
    return event

  def ping(self, payload):
    self.pings.append(payload)


def test_idle_timeout_keeps_relay_connected_until_pong():
  websocket = FakeWebSocket([
    WebSocketTimeoutException("idle"),
    (ABNF.OPCODE_PONG, b"wayon-ssh"),
    (ABNF.OPCODE_CLOSE, b""),
  ])

  relay.RelayChannel("ssh", "https://wayon.test", "token").relay_connected(websocket)

  assert websocket.timeout == relay.HEARTBEAT_INTERVAL_SECONDS
  assert websocket.pings == [b"wayon-ssh"]


def test_idle_relay_does_not_reconnect_without_an_io_failure():
  websocket = FakeWebSocket([
    WebSocketTimeoutException("idle"),
    WebSocketTimeoutException("idle"),
    (ABNF.OPCODE_CLOSE, b""),
  ])

  relay.RelayChannel("live", "https://wayon.test", "token").relay_connected(websocket)

  assert websocket.pings == [b"wayon-live", b"wayon-live"]


def test_failed_heartbeat_reconnects_relay():
  websocket = FakeWebSocket([WebSocketTimeoutException("idle")])

  def fail_ping(payload):
    raise OSError("network down")

  websocket.ping = fail_ping

  with pytest.raises(OSError):
    relay.RelayChannel("ssh", "https://wayon.test", "token").relay_connected(websocket)
