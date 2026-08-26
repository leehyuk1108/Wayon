import base64
from collections import deque
import json

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


class FakeParams:
  def __init__(self, keys=""):
    self.values = {"GithubSshKeys": keys} if keys else {}

  def get(self, key):
    return self.values.get(key)

  def put(self, key, value, block=False):
    self.values[key] = value

  def remove(self, key):
    self.values.pop(key, None)


class FakeTimer:
  instances = []

  def __init__(self, delay, callback, args=()):
    self.delay = delay
    self.callback = callback
    self.args = args
    self.daemon = False
    self.started = False
    self.__class__.instances.append(self)

  def start(self):
    self.started = True

  def fire(self):
    self.callback(*self.args)


def authorization_command(public_key, authorization_id="0123456789abcdef0123456789abcdef", ttl=90):
  payload = json.dumps({
    "publicKey": public_key,
    "authorizationId": authorization_id,
    "ttlSeconds": ttl,
  }).encode()
  encoded = base64.urlsafe_b64encode(payload).decode().rstrip("=")
  return relay.SSH_AUTHORIZE_PREFIX + encoded


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


def test_wayon_session_key_is_added_then_removed_without_touching_user_key():
  FakeTimer.instances.clear()
  user_key = f"ssh-ed25519 {base64.b64encode(bytes(range(48))).decode()} owner"
  session_key = f"ssh-rsa {base64.b64encode(bytes(range(96))).decode()} hylink-android"
  params = FakeParams(user_key + "\n")
  authorizer = relay.TemporarySshAuthorizer(params, FakeTimer)

  assert authorizer.authorize(authorization_command(session_key))
  lines = params.values["GithubSshKeys"].splitlines()
  assert lines[0] == user_key
  assert lines[1].endswith("wayon-session-0123456789abcdef0123456789abcdef")
  assert FakeTimer.instances[0].delay == 90
  assert FakeTimer.instances[0].daemon
  assert FakeTimer.instances[0].started

  FakeTimer.instances[0].fire()
  assert params.values["GithubSshKeys"].splitlines() == [user_key]


@pytest.mark.parametrize("command", [
  "wayon-ssh-authorize-v1.invalid",
  authorization_command("ssh-rsa not-base64"),
  authorization_command(f"ssh-rsa {base64.b64encode(bytes(range(96))).decode()}", ttl=121),
])
def test_invalid_wayon_session_key_is_rejected(command):
  params = FakeParams()
  assert not relay.TemporarySshAuthorizer(params, FakeTimer).authorize(command)
  assert "GithubSshKeys" not in params.values


def test_relay_installs_authorization_before_opening_local(monkeypatch):
  session_key = f"ssh-rsa {base64.b64encode(bytes(range(96))).decode()} hylink-android"
  params = FakeParams()
  authorizer = relay.TemporarySshAuthorizer(params, FakeTimer)
  opened = []
  websocket = FakeWebSocket([
    (ABNF.OPCODE_TEXT, authorization_command(session_key).encode()),
    (ABNF.OPCODE_TEXT, b"wayon-peer-open"),
    (ABNF.OPCODE_CLOSE, b""),
  ])
  channel = relay.RelayChannel("ssh", "https://wayon.test", "token", authorizer)
  monkeypatch.setattr(channel, "open_local", lambda ws: opened.append(ws))

  channel.relay_connected(websocket)

  assert "wayon-session-" in params.values["GithubSshKeys"]
  assert opened == [websocket]
