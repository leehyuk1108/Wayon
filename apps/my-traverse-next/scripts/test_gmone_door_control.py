from contextlib import contextmanager
from http.client import BadStatusLine
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
from threading import Thread
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch
from urllib.parse import parse_qs, urlsplit

import gmone_door_control as door
from comma_rssi_receiver import IgnitionGuard


ACCOUNT = "owner+test@example.invalid"
KEY = "fixture+/=" * 4


class DoorControlTest(unittest.TestCase):
  @contextmanager
  def fake_server(self, status):
    seen = []

    class Handler(BaseHTTPRequestHandler):
      def do_GET(self):
        seen.append(urlsplit(self.path))
        self.send_response(status)
        if 300 <= status < 400:
          self.send_header("Location", "/redirected")
        self.end_headers()

      def log_message(self, *_args):
        pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
      worker = Thread(target=server.serve_forever, kwargs={"poll_interval": .02})
      worker.start()
      try:
        with patch.object(door, "ENDPOINT", f"http://127.0.0.1:{server.server_port}/api"):
          yield seen
      finally:
        server.shutdown()
        worker.join()

  def test_both_commands_use_the_expected_http_contract(self):
    with self.fake_server(200) as seen:
      credentials = door.Credentials.from_values(ACCOUNT, KEY)
      for command in door.DoorCommand:
        self.assertEqual(door.send_command(command, credentials), door.Result("http_response", 200))
      self.assertEqual([request.path for request in seen], ["/api", "/api"])
      self.assertEqual([parse_qs(request.query) for request in seen], [
        {"id": [ACCOUNT], "key": [KEY], "cmd": ["DOOR_LOCK"]},
        {"id": [ACCOUNT], "key": [KEY], "cmd": ["DOOR_UNLOCK"]},
      ])

  def test_redirect_and_http_failure_are_not_followed_or_retried(self):
    credentials = door.Credentials.from_values(ACCOUNT, KEY)
    for status in (302, 403, 503):
      with self.fake_server(status) as seen:
        self.assertEqual(door.send_command(door.DoorCommand.UNLOCK, credentials), door.Result("not_confirmed", status))
        self.assertEqual(len(seen), 1)

  def test_timeout_is_unknown_without_retry_or_secret_in_result(self):
    opener = Mock()
    opener.open.side_effect = TimeoutError(KEY)
    result = door.send_command(door.DoorCommand.LOCK, door.Credentials.from_values(ACCOUNT, KEY), opener=opener)
    self.assertEqual(result, door.Result("unknown"))
    self.assertNotIn(KEY, repr(result))
    opener.open.assert_called_once()
    with self.assertRaises(ValueError):
      door.send_command("REMOTE_START", door.Credentials.from_values(ACCOUNT, KEY), opener=opener)
    opener.reset_mock()
    opener.open.side_effect = BadStatusLine("unexpected reply")
    self.assertEqual(door.send_command(door.DoorCommand.LOCK, door.Credentials.from_values(ACCOUNT, KEY), opener=opener),
                     door.Result("unknown"))
    opener.open.assert_called_once()

  def test_dry_run_and_interlock_change_do_not_send(self):
    command = door.DoorCommand.LOCK
    credentials = Mock(return_value=door.Credentials.from_values(ACCOUNT, KEY))
    send = Mock(return_value=door.Result("http_response", 202))
    self.assertEqual(door.run_command(command, False, check=lambda _: None, credentials=credentials, send=send).state, "dry_run")
    self.assertEqual(door.run_command(command, True, check=lambda _: "door_closed_not_confirmed",
                                      credentials=credentials, send=send).state, "door_closed_not_confirmed")
    credentials.assert_not_called()
    check = Mock(side_effect=[None, "ignition_not_confirmed_off"])
    self.assertEqual(door.run_command(command, True, check=check, credentials=credentials, send=send).state,
                     "ignition_not_confirmed_off")
    send.assert_not_called()
    self.assertEqual(door.run_command(command, True, check=lambda _: None, credentials=credentials, send=send).status, 202)
    send.assert_called_once()

  def test_lock_requires_a_fresh_valid_closed_door_switch_sample(self):
    observation = door.DoorObservation()
    stamp = 8_000_000_000

    def event(payload, *, time=stamp, valid=True, bus=0):
      return SimpleNamespace(valid=valid, logMonoTime=time,
                             can=[SimpleNamespace(src=bus, address=0x12A, dat=payload)])

    self.assertFalse(observation.confirmed(stamp))
    observation.update(event(bytes(8), bus=1), stamp)
    self.assertFalse(observation.confirmed(stamp))
    observation.update(event(bytes(8)), stamp)
    self.assertTrue(observation.confirmed(stamp + 500_000_000))
    self.assertFalse(observation.confirmed(stamp + 1_100_000_000))
    observation.update(event(bytes([0, 0, 0x80, 0, 0, 0, 0, 0]), time=stamp + 1), stamp + 1)
    observation.update(event(bytes(8)), stamp + 1)
    self.assertFalse(observation.confirmed(stamp + 1))
    observation.update(event(bytes(8), time=stamp + 2), stamp + 2)
    observation.update(event(bytes(8), time=stamp + 3, valid=False), stamp + 3)
    self.assertFalse(observation.confirmed(stamp + 3))
    observation.update(event(b"\0", time=stamp + 4), stamp + 4)
    self.assertFalse(observation.confirmed(stamp + 4))

  def test_private_credentials_and_concurrent_requests(self):
    with tempfile.TemporaryDirectory() as temp:
      directory = Path(temp) / "private"
      expected = door.Credentials.from_values(ACCOUNT, KEY)
      door.provision(directory, expected)
      self.assertEqual(door.read_credentials(directory), expected)
      self.assertNotIn(KEY, repr(expected))
      self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
      path = directory / "multipack.json"
      self.assertEqual(path.stat().st_mode & 0o777, 0o600)
      with door.one_request(directory):
        with self.assertRaises(BlockingIOError), door.one_request(directory):
          self.fail("an overlapping operation must not proceed")
      path.chmod(0o644)
      with self.assertRaises(ValueError):
        door.read_credentials(directory)
      path.unlink()
      path.symlink_to("/dev/null")
      with self.assertRaises(OSError):
        door.read_credentials(directory)

  def test_wait_for_vehicle_checks_ignition_and_requires_fresh_door_state_for_lock(self):
    now = 4.
    panda = SimpleNamespace(pandaType="cuatro", ignitionLine=False, ignitionCan=False)
    message = SimpleNamespace(valid=True, logMonoTime=4_000_000_000, pandaStates=[panda])
    ns = lambda: int(now * 1e9)
    guard = IgnitionGuard(lambda: door.c4_panda_message(message), ns, lambda: True)

    def step(dt):
      nonlocal now
      now += dt
      message.logMonoTime = ns()

    def check(receive_can=None):
      return door.wait_for_vehicle(guard, receive_can, ns, lambda: now, step)

    self.assertIsNone(check())
    self.assertEqual(check(lambda: None), "door_closed_not_confirmed")
    can = SimpleNamespace(valid=True, logMonoTime=ns(), can=[
      SimpleNamespace(src=0, address=0x12A, dat=bytes(8)),
    ])
    events = iter((can, None))
    self.assertIsNone(check(lambda: next(events)))
    for name in ("ignitionLine", "ignitionCan"):
      setattr(panda, name, True)
      self.assertEqual(check(), "ignition_not_confirmed_off")
      setattr(panda, name, False)
    message.pandaStates = []
    self.assertEqual(check(), "ignition_not_confirmed_off")
    message.pandaStates = [panda, panda]
    self.assertEqual(check(), "ignition_not_confirmed_off")
    message.pandaStates = [panda]
    message.logMonoTime = 1

    def advance(dt):
      nonlocal now
      now += dt

    self.assertEqual(door.wait_for_vehicle(guard, None, ns, lambda: now, advance), "ignition_not_confirmed_off")

  def test_vehicle_check_preserves_manual_lock_and_explicit_closure_paths(self):
    params = MagicMock()
    params.__enter__.return_value.carFingerprint = "CHEVROLET_TRAVERSE"
    car = SimpleNamespace(CarParams=SimpleNamespace(from_bytes=Mock(return_value=params)))
    messaging = SimpleNamespace(sub_sock=Mock(), recv_one_or_none=Mock())
    with patch.dict(sys.modules, {"openpilot.cereal": SimpleNamespace(car=car, messaging=messaging)}), \
         patch.object(Path, "read_bytes", return_value=b"fixture"), \
         patch.object(door, "wait_for_vehicle", return_value=None) as wait:
      for action, options, needs_can in (
          (door.DoorCommand.LOCK, {}, True),
          (door.DoorCommand.LOCK, {"require_closed": False}, False),
          (door.DoorCommand.UNLOCK, {}, False),
          (door.DoorCommand.UNLOCK, {"require_closed": True}, True)):
        messaging.sub_sock.reset_mock()
        self.assertIsNone(door.vehicle_check(action, **options))
        names = [call.args[0] for call in messaging.sub_sock.call_args_list]
        self.assertEqual(names, ["pandaStates", "can"] if needs_can else ["pandaStates"])
        self.assertEqual(wait.call_args.args[1] is not None, needs_can)


if __name__ == "__main__":
  unittest.main()
