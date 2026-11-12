import asyncio
import json
from pathlib import Path
import ssl
import tempfile
from types import SimpleNamespace
import unittest
from uuid import uuid4

from aiohttp import ClientSession, TCPConnector, web
from aiohttp.test_utils import TestClient, TestServer
from jeepney import DBusAddress, HeaderFields, new_signal

import comma_rssi_receiver as rx


class CaptureTest(unittest.TestCase):
  def test_measurement_priority_is_visible_only_during_owned_capture(self):
    with tempfile.TemporaryDirectory() as temp:
      gate = Path(temp) / "radio.lock"
      self.assertFalse(rx.diagnostic_waiting(gate))
      with rx.diagnostic_priority(gate):
        self.assertTrue(rx.diagnostic_waiting(gate))
      self.assertFalse(rx.diagnostic_waiting(gate))

  def test_only_fresh_rssi_from_matched_phone(self):
    uuid = str(uuid4())
    capture = rx.Capture("INSIDE", uuid, started=100, wall=42)
    capture.receive("other", {"RSSI": ("n", -35)}, now=100)
    capture.receive("phone", {"UUIDs": ("as", [uuid]), "RSSI": ("n", -58)}, now=100)
    capture.receive("phone", {"RSSI": ("n", -59)}, now=100.125)
    capture.receive("other", {"RSSI": ("n", -99)}, now=101)
    capture.receive("phone", {"RSSI": ("n", -81)}, now=101)
    capture.receive("phone", {"UUIDs": ("as", [uuid])}, now=102)
    capture.receive("phone", {"RSSI": ("n", 127)}, now=103)
    capture.receive("phone", {"RSSI": ("n", -85)}, now=118)
    self.assertEqual(capture.row(), ["INSIDE", 42, [[125, -58], [1000, -81]]])
    self.assertEqual(capture.last_seen_ms, 1000)

  def test_denser_sampling_preserves_wire_limit_and_does_not_fill_missing_buckets(self):
    uuid = str(uuid4())
    capture = rx.Capture("DOOR", uuid, started=100, wall=42)
    for i in range(rx.CAPTURE_MS // rx.SAMPLE_MS):
      if 8 <= i < 16:
        continue
      capture.receive("phone", {"UUIDs": ("as", [uuid]), "RSSI": ("n", -100 if i % 2 else -60)},
                      now=100 + i * .125)
    self.assertEqual(len(capture.samples), 136)
    self.assertEqual(len(capture.series()), 68)
    self.assertEqual(capture.series()[0], [125, -80])
    self.assertFalse(any(1000 <= point[0] < 2000 for point in capture.series()))
    self.assertLessEqual(len(capture.series()), 72)

  def test_object_manager_root_signal_is_accepted_only_from_bluez(self):
    uuid = str(uuid4())
    capture = rx.Capture("DOOR", uuid)
    path = "/org/bluez/hci0/dev_01"
    signal = new_signal(DBusAddress("/", interface=rx.OBJECTS), "InterfacesAdded", "oa{sa{sv}}",
                        (path, {rx.DEVICE: {"UUIDs": ("as", [uuid]), "RSSI": ("n", -66)}}))
    signal.header.fields[HeaderFields.sender] = ":1.2"
    rx.consume(signal, ":1.3", "/org/bluez/hci0", capture)
    self.assertEqual(capture.samples, [])
    rx.consume(signal, ":1.2", "/org/bluez/hci1", capture)
    self.assertEqual(capture.samples, [])
    rx.consume(signal, ":1.2", "/org/bluez/hci0", capture)
    self.assertEqual([value for _, value in capture.samples], [-66])

  def test_ignition_guard_rejects_stale_invalid_and_missing_sources(self):
    off = SimpleNamespace(pandaType="c4", ignitionLine=False, ignitionCan=False)
    msg = SimpleNamespace(valid=True, logMonoTime=2_000_000_000, pandaStates=[off])
    now = 2_100_000_000
    offroad = True
    receive = msg
    guard = rx.IgnitionGuard(lambda: receive, lambda: now, lambda: offroad)
    self.assertTrue(guard())
    receive = None
    self.assertTrue(guard())
    now += 1_000_000_000
    self.assertFalse(guard())
    now = 2_100_000_000
    for field in ("ignitionLine", "ignitionCan"):
      setattr(off, field, True)
      self.assertFalse(guard())
      setattr(off, field, False)
    off.pandaType = "unknown"
    self.assertFalse(guard())
    off.pandaType = "c4"
    offroad = False
    self.assertFalse(guard())
    offroad = True
    msg.valid = False
    self.assertFalse(guard())


class ReceiverTest(unittest.IsolatedAsyncioTestCase):
  async def asyncSetUp(self):
    self.temp = tempfile.TemporaryDirectory()
    self.log = Path(self.temp.name) / "logs.json"
    self.finish = asyncio.Event()
    self.parked = True
    self.calls = 0

    async def fake_scan(capture, is_parked, ready):
      self.calls += 1
      capture.receive("phone", {"UUIDs": ("as", [capture.service]), "RSSI": ("n", -67)}, now=capture.started)
      ready.set_result(None)
      await self.finish.wait()
      if not is_parked():
        raise RuntimeError()

    self.rx = rx.Receiver("test-token", self.log, lambda: self.parked, fake_scan)
    self.client = TestClient(TestServer(self.rx.app()))
    await self.client.start_server()
    self.auth = {"Authorization": "Bearer test-token"}

  async def asyncTearDown(self):
    await self.client.close()
    self.temp.cleanup()

  async def test_start_live_and_log_without_connected_phone(self):
    result = await self.client.post(f"/capture/DOOR/{uuid4()}", headers=self.auth)
    self.assertEqual(result.status, 200)
    live = await self.client.get("/snapshot", headers=self.auth)
    active = (await live.json())["active"]
    self.assertEqual(active["samples"], [[0, -67]])
    self.assertEqual(active["received"], 1)
    self.finish.set()
    await self.rx.task
    self.assertEqual(json.loads(self.log.read_bytes())["runs"][0][2], [[0, -67]])
    self.assertEqual((self.log.stat().st_mode & 0o077), 0)
    result = await self.client.get("/snapshot", headers=self.auth)
    self.assertIsNone((await result.json())["active"])
    restarted = rx.Receiver("test-token", self.log, lambda: self.parked, self.rx.scanner)
    self.assertEqual(restarted.runs, self.rx.runs)

  async def test_scope_authorization_and_invalid_or_onroad_requests(self):
    self.assertEqual((await self.client.get("/snapshot")).status, 401)
    self.assertEqual((await self.client.post(f"/capture/DOOR/{uuid4()}")).status, 401)
    self.assertEqual((await self.client.post("/capture/DOOR/not-uuid", headers=self.auth)).status, 400)
    self.assertEqual((await self.client.post("/lock", headers=self.auth)).status, 404)
    self.parked = False
    self.assertEqual((await self.client.post(f"/capture/DOOR/{uuid4()}", headers=self.auth)).status, 409)
    self.assertEqual(self.calls, 0)

  async def test_relay_accepts_only_capture_and_snapshot_and_cancels_on_disconnect(self):
    replies = []

    async def send_json(message):
      replies.append(message)

    ws = SimpleNamespace(send_json=send_json)
    request = {"id": str(uuid4()), "stage": "DOOR", "service": str(uuid4())}
    await rx.reply_wayon(ws, self.rx, {**request, "op": "unlock"})
    await rx.reply_wayon(ws, self.rx, {**request, "op": "capture", "id": None})
    self.assertEqual(self.calls, 0)
    self.parked = False
    await rx.reply_wayon(ws, self.rx, {**request, "op": "capture"})
    self.assertEqual(replies.pop()["status"], 409)
    self.parked = True
    await rx.reply_wayon(ws, self.rx, {**request, "op": "capture"})
    self.assertEqual(replies.pop()["status"], 200)
    await rx.reply_wayon(ws, self.rx, {**request, "op": "snapshot"})
    self.assertEqual(replies.pop()["body"]["active"]["stage"], "DOOR")
    await self.rx.close(None)
    self.assertIsNone(self.rx.snapshot_data()["active"])
    self.assertEqual(self.rx.runs, [])

  async def test_managed_receiver_rate_limited(self):
    self.rx.limited = True
    now = 300.0
    self.rx.clock = lambda: now
    self.finish.set()
    for _ in range(6):
      _, status = await self.rx.begin("DOOR", str(uuid4()))
      self.assertEqual(status, 200)
      await self.rx.task
      now += 20
    _, status = await self.rx.begin("DOOR", str(uuid4()))
    self.assertEqual(status, 429)
    self.assertEqual(self.calls, 6)

  async def test_ignition_change_discards_partial_capture(self):
    _, status = await self.rx.begin("DOOR", str(uuid4()))
    self.assertEqual(status, 200)
    self.assertTrue(self.rx.snapshot_data()["active"]["samples"])
    self.parked = False
    self.finish.set()
    await self.rx.task
    self.assertIsNone(self.rx.snapshot_data()["active"])
    self.assertEqual(self.rx.snapshot_data()["error"], "capture_failed")
    self.assertEqual(self.rx.runs, [])

  async def test_receiver_tls_matches_certificate_and_does_not_accept_wrong_pin(self):
    directory = Path(self.temp.name)
    server_ssl, pin = rx.tls("127.0.0.1", directory)
    self.assertEqual(len(pin), 64)
    runner = web.AppRunner(self.rx.app())
    await runner.setup()
    try:
      site = web.TCPSite(runner, "127.0.0.1", 0, ssl_context=server_ssl)
      await site.start()
      url = f"https://127.0.0.1:{runner.addresses[0][1]}/snapshot"
      async with ClientSession(connector=TCPConnector()) as client:
        result = await client.get(url, headers=self.auth, ssl=ssl.create_default_context(cafile=directory / "cert.pem"))
        self.assertEqual((await result.json())["source"], "comma")
        with self.assertRaises(Exception):
          await client.get(url, headers=self.auth, ssl=__import__("aiohttp").Fingerprint(bytes(32)))
    finally:
      await runner.cleanup()


if __name__ == "__main__":
  unittest.main()
