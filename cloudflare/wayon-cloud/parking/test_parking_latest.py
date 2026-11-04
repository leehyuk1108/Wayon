import io
import json
import logging
from contextlib import ExitStack
from http.client import HTTPResponse
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import quote

import service as s


class LatestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = {"dataDir": self.tmp.name, "codexExe": "unused", "token": "t" * 48}
        self.runner = Mock(side_effect=AssertionError("read must not run inference"))
        self.service = s.Service(self.config, self.runner)
        self.addCleanup(self.service.db.close)

    def job(self, number, *, device="device-a", event=None, parked=100, created=100,
            status="completed", result=None, error=None):
        job_id = f"{number:032x}"
        self.service.db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)",
                                (job_id, device, event or f"parking-{number}", parked, "test-signature",
                                 status, created, json.dumps(result) if result is not None else None, error))
        self.service.db.commit()
        return job_id

    def request(self, target, *, authorization=True, method="GET"):
        headers = "Host: localhost\r\n"
        if authorization:
            token = self.config["token"] if authorization is True else authorization
            headers += f"Authorization: Bearer {token}\r\n"
        request = f"{method} {target} HTTP/1.0\r\n{headers}\r\n".encode("ascii")
        wire = io.BytesIO()
        connection = Mock()
        connection.makefile.return_value = io.BytesIO(request)
        connection.sendall.side_effect = wire.write
        # Exercise the real HTTP parser and handler without opening a socket.
        s.handler(self.service)(connection, ("127.0.0.1", 0), Mock())
        response = HTTPResponse(SimpleNamespace(makefile=lambda *_: io.BytesIO(wire.getvalue())))
        response.begin()
        body = json.loads(response.read())
        return response.status, body, dict(response.getheaders())

    def test_no_job_is_null(self):
        self.assertIsNone(self.service.latest("device-a"))
        status, body, headers = self.request("/latest?device=device-a")
        self.assertEqual(status, 200)
        self.assertIsNone(body)
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_device_isolation(self):
        expected = self.job(1)
        other = self.job(2, device="device-b", parked=200)
        for device, job_id in (("device-a", expected), ("device-b", other)):
            with self.subTest(device=device):
                status, body, _ = self.request(f"/latest?device={device}")
                self.assertEqual(status, 200)
                self.assertEqual(body["deviceId"], device)
                self.assertEqual(body["jobId"], job_id)
        self.assertIsNone(self.service.latest("Device-a"))
        self.assertIsNone(self.request("/latest?device=device-c")[1])

    def test_latest_orders_by_parked_then_created_then_id(self):
        self.job(99, parked=100, created=900)
        self.job(98, parked=200, created=100)
        winner = self.job(2, parked=200, created=200)
        self.job(1, parked=200, created=200)
        for _ in range(3):
            self.assertEqual(self.service.latest("device-a")["jobId"], winner)

    def test_snapshot_events_are_excluded(self):
        self.job(1, event="snapshot-only", parked=500)
        self.assertIsNone(self.service.latest("device-a"))
        expected = self.job(2, event="parking-event", parked=100)
        self.job(3, event="snapshot-", parked=600)
        self.assertEqual(self.request("/latest?device=device-a")[1]["jobId"], expected)

    def test_snapshot_filter_is_only_a_literal_prefix(self):
        expected = self.job(1, event="parking-snapshot-example")
        self.assertEqual(self.service.latest("device-a")["jobId"], expected)

    def test_latest_failed_queued_and_running_do_not_fall_back(self):
        self.job(1, result={"analysis": {"old": True}})
        for number, state in enumerate(("failed", "queued", "running"), 2):
            with self.subTest(state=state):
                error = "model_timeout" if state == "failed" else None
                expected = self.job(number, parked=number * 100, status=state, error=error)
                status, body, _ = self.request("/latest?device=device-a")
                self.assertEqual(status, 200)
                self.assertEqual(body["jobId"], expected)
                self.assertEqual(body["status"], state)
                self.assertEqual(body["error"], error)
                self.assertIsNone(body["result"])

    def test_get_and_latest_preserve_scene_display(self):
        baseline = {"analysis": {"readings": [], "exactParkingSpotKnown": False}, "frames": []}
        job_id = self.job(1, result=baseline)
        job_dir = Path(self.tmp.name) / job_id
        job_dir.mkdir()
        (job_dir / "scene-comparison.json").write_text(json.dumps({"status": "skipped"}), encoding="utf-8")
        for enabled in (False, True):
            with self.subTest(sceneDisplay=enabled):
                self.config["sceneDisplay"] = enabled
                status, latest, _ = self.request("/latest?device=device-a")
                self.assertEqual(status, 200)
                self.assertEqual(latest, self.service.get(job_id))
                self.assertEqual(latest, self.request("/jobs/" + job_id)[1])
                self.assertEqual("inspection" in latest["result"], enabled)
                if enabled:
                    self.assertEqual(latest["result"]["inspection"]["status"], "skipped")

    def test_health_reports_scene_display_boolean(self):
        self.service.worker = Mock(is_alive=Mock(return_value=True))
        for value in (None, False, True, "true", 1):
            with self.subTest(value=value):
                self.config["sceneDisplay"] = value
                status, body, _ = self.request("/health")
                self.assertEqual(status, 200)
                self.assertIs(body["sceneDisplayConfigured"], value is True)

    def test_authentication_precedes_query_validation(self):
        for authorization in (False, "wrong-token"):
            for target in ("/latest?device=device-a", "/latest?unknown=x", "/health"):
                with self.subTest(authorization=authorization, target=target):
                    status, body, _ = self.request(target, authorization=authorization)
                    self.assertEqual((status, body), (401, {"error": "unauthorized"}))

    def test_exact_query_rejects_unknown_duplicate_and_malformed_fields(self):
        targets = ["/latest", "/latest?", "/latest?device", "/latest?device=",
                   "/latest?Device=device-a", "/latest?deviceId=device-a", "/latest?other=device-a",
                   "/latest?device=device-a&device=device-a", "/latest?device=device-a&device=device-b",
                   "/latest?device=device-a&other=x", "/latest?other=x&device=device-a",
                   "/latest?device=device-a&", "/latest?&device=device-a",
                   "/latest?device=device-a;other=x", "/latest?device=device-a#fragment",
                   "/latest?device=%FF", "/latest?device=%ZZ", "/latest?device=device-a%00"]
        for target in targets:
            with self.subTest(target=target):
                self.assertEqual(self.request(target)[:2], (400, {"error": "invalid_query"}))

    def test_safe96_device_validation(self):
        device = "A" + "z" * 92 + "_.-"
        expected = self.job(1, device=device)
        self.assertEqual(self.service.latest(device)["jobId"], expected)
        self.assertEqual(self.request("/latest?device=" + device)[1]["jobId"], expected)
        self.job(2, device="a-b.c_d")
        self.assertEqual(self.request("/latest?device=a%2Db.c_d")[0], 200)
        invalid = ["", "x" * 97, "-bad", "_bad", ".bad", "../bad", "a/b", "a b", "a\n", "\u00e9"]
        for device in invalid:
            with self.subTest(device=device):
                with self.assertRaisesRegex(ValueError, "invalid_id"):
                    self.service.latest(device)
                self.assertEqual(self.request("/latest?device=" + quote(device, safe=""))[0], 400)
        for device in (None, 123, True):
            with self.subTest(device=device), self.assertRaisesRegex(ValueError, "invalid_id"):
                self.service.latest(device)

    def test_sql_injection_is_rejected(self):
        self.job(1, device="device-b")
        before = list(self.service.db.iterdump())
        for device in ("' OR 1=1 --", "device-a'; DROP TABLE jobs;--", 'device-a" OR "1"="1'):
            with self.subTest(device=device):
                with self.assertRaisesRegex(ValueError, "invalid_id"):
                    self.service.latest(device)
                self.assertEqual(self.request("/latest?device=" + quote(device, safe=""))[0], 400)
        self.assertEqual(list(self.service.db.iterdump()), before)

    def test_latest_has_no_post_route(self):
        self.assertEqual(self.request("/latest?device=device-a", method="POST")[0], 404)

    def test_reads_do_not_mutate_or_start_work(self):
        job_id = self.job(1, status="queued")
        self.service.db.execute("INSERT INTO attempts VALUES (?,?)", (job_id, 2))
        self.service.db.execute("INSERT INTO cloud_frames VALUES (?,?,?,?)", ("frame", "event", 100, "received"))
        self.service.db.execute("CREATE TABLE parking_notify_outbox (job TEXT, state TEXT)")
        self.service.db.execute("INSERT INTO parking_notify_outbox VALUES (?,?)", (job_id, "pending"))
        self.service.db.commit()
        self.service.queue.put_nowait(job_id)
        self.service.worker = Mock(is_alive=Mock(return_value=True))
        self.service.parking_notify = Mock(thread=None)
        before = list(self.service.db.iterdump())
        changes = self.service.db.total_changes
        files = {p.relative_to(self.service.root): p.read_bytes()
                 for p in self.service.root.rglob("*") if p.is_file()}
        self.service.db.execute("PRAGMA query_only=ON")
        with ExitStack() as stack:
            stack.enter_context(patch.object(s.Service, "__init__", side_effect=AssertionError("new service")))
            for method in ("submit", "retry", "process_one", "work", "cleanup"):
                stack.enter_context(patch.object(self.service, method, side_effect=AssertionError("read started work")))
            for _ in range(3):
                self.assertEqual(self.service.latest("device-a")["status"], "queued")
                self.assertEqual(self.request("/latest?device=device-a")[1]["status"], "queued")
                self.assertEqual(self.request("/health")[0], 200)
        self.assertEqual(list(self.service.db.iterdump()), before)
        self.assertEqual(self.service.db.total_changes, changes)
        self.assertEqual(self.service.queue.get_nowait(), job_id)
        self.assertTrue(self.service.queue.empty())
        self.assertEqual(self.service.queue.unfinished_tasks, 1)
        self.runner.assert_not_called()
        self.service.parking_notify.enqueue_completed.assert_not_called()
        self.service.parking_notify.start.assert_not_called()
        self.assertEqual({p.relative_to(self.service.root): p.read_bytes()
                          for p in self.service.root.rglob("*") if p.is_file()}, files)


class MainExportTests(unittest.TestCase):
    def run_main(self, config, exporter_factory):
        class StopLoop(Exception):
            pass

        with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
            path = Path(tmp) / "config.json"
            path.write_text(json.dumps({"token": "t" * 48, **config}), encoding="utf-8")
            service = Mock(root=Path(tmp), parking_notify=None)
            server = Mock()
            now = [0]
            ticks = iter((0, 29, 30, 59, 60))

            def handle_request():
                try:
                    now[0] = next(ticks)
                except StopIteration:
                    raise StopLoop

            server.handle_request.side_effect = handle_request
            stack.enter_context(patch.object(sys, "argv", ["service.py", "--config", str(path)]))
            stack.enter_context(patch.object(s, "Service", return_value=service))
            stack.enter_context(patch.object(s, "BoundedServer", return_value=server))
            stack.enter_context(patch.object(s.threading, "Thread"))
            stack.enter_context(patch.object(s.time, "monotonic", side_effect=lambda: now[0]))
            stack.enter_context(patch.object(s, "RotatingFileHandler", return_value=logging.NullHandler()))
            stack.enter_context(patch.object(s.logging, "basicConfig"))
            warning = stack.enter_context(patch.object(s.logging, "warning"))
            stack.enter_context(patch.dict(sys.modules, parking_export=SimpleNamespace(ParkingExport=exporter_factory)))
            with self.assertRaises(StopLoop):
                s.main()
            self.assertEqual(server.handle_request.call_count, 6)
            service.worker.start.assert_called_once()
            return service, warning

    def test_export_is_optional(self):
        factory = Mock()
        for config in ({}, {"inspectionExportDir": ""}):
            with self.subTest(config=config):
                _, warning = self.run_main(config, factory)
                factory.assert_not_called()
                warning.assert_not_called()

    def test_export_runs_every_30_seconds_on_existing_service(self):
        exporter = Mock()
        factory = Mock(return_value=exporter)
        service, warning = self.run_main({"inspectionExportDir": "private-export"}, factory)
        factory.assert_called_once_with(service, Path("private-export"))
        self.assertEqual(exporter.update.call_count, 3)
        warning.assert_not_called()

    def test_export_failure_is_isolated_and_does_not_hot_loop(self):
        exporter = Mock()
        exporter.update.side_effect = RuntimeError("sensitive detail must not be logged")
        _, warning = self.run_main({"inspectionExportDir": "private-export"}, Mock(return_value=exporter))
        self.assertEqual(exporter.update.call_count, 3)
        self.assertEqual(warning.call_count, 3)
        warning.assert_called_with("parking_export_update_failed class=%s", "RuntimeError")
        self.assertNotIn("sensitive", str(warning.call_args_list))

    def test_export_initialization_failure_does_not_stop_baseline(self):
        factory = Mock(side_effect=RuntimeError("sensitive detail must not be logged"))
        _, warning = self.run_main({"inspectionExportDir": "private-export"}, factory)
        factory.assert_called_once()
        warning.assert_called_once_with("parking_export_init_failed class=%s", "RuntimeError")

    def test_service_init_does_not_start_export(self):
        factory = Mock(side_effect=AssertionError("export must only start in main"))
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, parking_export=SimpleNamespace(ParkingExport=factory)):
            service = s.Service({"dataDir": tmp, "inspectionExportDir": "private-export"}, Mock())
            try:
                factory.assert_not_called()
            finally:
                service.db.close()


if __name__ == "__main__":
    unittest.main()
