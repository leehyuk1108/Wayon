"""Offline outbox tests and a real Python-produced fixture for the Cloud contract."""
import copy
from contextlib import closing
from datetime import datetime, timezone
import hashlib
from http.client import IncompleteRead
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import parking_notify as n
import service as s
from test_service import bundle, readable

NOW = s.timestamp("2026-11-02T00:10:00Z")


def iso(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def source_bundle(event="notify-1", now=NOW, phases=("approach", "parked", "parked")):
    value = bundle(event)
    value["parkedAt"] = iso(now - 180)
    for i, frame in enumerate(value["frames"]):
        frame.update(capturedAt=iso(now - 182 + i), phase=phases[i])
    return value


def source_result(now=NOW):
    manifest = s.prepare_bundle(source_bundle(now=now))[0]
    result = {"analysis": readable(), "frames": manifest["frames"], "completedAt": iso(now - 1)}
    return manifest, result


def wire_fixture(now=NOW):
    """No network or credential access: Cloud tests can JSON-encode this payload."""
    manifest, result = source_result(now)
    job = hashlib.sha256((manifest["deviceId"] + ":" + manifest["eventId"]).encode()).hexdigest()[:32]
    return n.make_payload(job, manifest, result, "test-device", now - 3600, now)[0]


class PayloadTests(unittest.TestCase):
    def prepare(self, manifest=None, result=None, now=NOW, before=NOW - 3600):
        original_manifest, original_result = source_result()
        return n.make_payload("a" * 32, manifest or original_manifest, result or original_result,
                              "test-device", before, now)

    def test_exact_wire_contract_and_source_provenance(self):
        payload = wire_fixture()
        self.assertEqual(set(payload), {"eventId", "jobId", "deviceId", "parkedAt", "completedAt", "readings", "phaseHint", "test"})
        self.assertIs(payload["test"], False)
        self.assertEqual(payload["phaseHint"], "mixed")
        manifest, _ = source_result()
        for reading in payload["readings"]:
            self.assertEqual(set(reading), {"kind", "text", "status", "evidence"})
            for evidence in reading["evidence"]:
                self.assertEqual(set(evidence), {"frameIndex", "box", "capturedAt", "sha256", "phase"})
                frame = manifest["frames"][evidence["frameIndex"]]
                for key in ("capturedAt", "sha256", "phase"):
                    self.assertEqual(evidence[key], frame[key])
        self.assertNotIn("imageBase64", json.dumps(payload))
        self.assertNotIn("alternatives", json.dumps(payload))

    def test_unknown_ambiguous_and_empty_never_notified(self):
        for change in ({"kind": "unknown"}, {"status": "ambiguous", "text": None, "alternatives": ["204"]}):
            manifest, result = source_result()
            result["analysis"]["readings"][0].update(change)
            self.assertIsNone(self.prepare(manifest, result))
        manifest, result = source_result()
        result["analysis"]["readings"] = []
        self.assertIsNone(self.prepare(manifest, result))

    def test_valid_reading_survives_unknown_but_not_invalid_result(self):
        manifest, result = source_result()
        unknown = copy.deepcopy(result["analysis"]["readings"][0])
        unknown["kind"] = "unknown"
        result["analysis"]["readings"].append(unknown)
        self.assertEqual(len(self.prepare(manifest, result)[0]["readings"]), 1)
        unknown["evidence"][1]["frameIndex"] = 0
        with self.assertRaisesRegex(ValueError, "invalid_evidence"):
            self.prepare(manifest, result)

    def test_controls_bidi_and_invisible_characters_rejected(self):
        for char in ("\x00", "\n", "\r", "\t", "\x7f", "\x85", "\u202e", "\u2066", "\u2069", "\u200b", "\ufeff", "\u2028", "\ud800"):
            with self.subTest(char=repr(char)):
                manifest, result = source_result()
                result["analysis"]["readings"][0]["text"] = "2" + char + "04"
                with self.assertRaisesRegex(ValueError, "unsafe_notify_text"):
                    self.prepare(manifest, result)

    def test_zone_and_pillar_are_independent_and_keep_separate_boxes(self):
        manifest, result = source_result()
        zone = copy.deepcopy(result["analysis"]["readings"][0])
        zone.update(kind="zone", text="C")
        for evidence in zone["evidence"]:
            evidence["box"] = [0.01, 0.2, 0.09, 0.8]
        result["analysis"]["readings"].insert(0, zone)
        payload = self.prepare(manifest, result)[0]
        self.assertEqual([(r["kind"], r["text"]) for r in payload["readings"]],
                         [("zone", "C"), ("pillar", "204")])
        self.assertNotEqual(payload["readings"][0]["evidence"][0]["box"],
                            payload["readings"][1]["evidence"][0]["box"])
        for alternatives in ([], ["C", "G"]):
            zone.update(text=None, status="ambiguous", alternatives=alternatives)
            self.assertEqual([(r["kind"], r["text"]) for r in self.prepare(manifest, result)[0]["readings"]],
                             [("pillar", "204")])

    def test_zone_cannot_borrow_pillar_temporal_or_image_corroboration(self):
        manifest, result = source_result()
        zone = copy.deepcopy(result["analysis"]["readings"][0])
        zone.update(kind="zone", text="AB", evidence=zone["evidence"][:1])
        result["analysis"]["readings"].append(zone)
        with self.assertRaisesRegex(ValueError, "uncorroborated"):
            self.prepare(manifest, result)


    def test_service_image_hash_and_temporal_validation_not_weakened(self):
        for mutation, error in (
                (lambda f: f[1].update(sha256=f[0]["sha256"]), "uncorroborated"),
                (lambda f: f[1].update(capturedAt=iso(NOW - 181.501)), "temporal"),
                (lambda f: f[1].update(sha256="bad"), "invalid_notify_source"),
                (lambda f: f[0].update(capturedAt=iso(NOW - 400)), "invalid_notify_source"),
                (lambda f: f[0].update(camera="driver"), "invalid_notify_source")):
            manifest, result = source_result()
            mutation(manifest["frames"])
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                self.prepare(manifest, result)
        manifest, result = source_result()
        manifest["frames"][1]["capturedAt"] = iso(NOW - 181.5)
        self.assertIsNotNone(self.prepare(manifest, result))

    def test_frame_binding_and_legacy_phase_fail_closed(self):
        manifest, result = source_result()
        result["frames"] = copy.deepcopy(result["frames"])
        result["frames"][0]["sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "provenance_mismatch"):
            self.prepare(manifest, result)
        manifest, result = source_result()
        del manifest["frames"][0]["phase"]
        self.assertIsNone(self.prepare(manifest, result))

    def test_phase_hint_uses_only_cited_evidence(self):
        for phases, expected in ((("parked", "parked", "approach"), "parked"),
                                 (("approach", "approach", "parked"), "approach"),
                                 (("approach", "parked", "parked"), "mixed")):
            manifest, result = source_result()
            for frame, phase in zip(manifest["frames"], phases):
                frame["phase"] = phase
            self.assertEqual(self.prepare(manifest, result)[0]["phaseHint"], expected)

    def test_freshness_activation_future_and_boundaries(self):
        self.assertIsNone(self.prepare(before=NOW - 179))
        self.assertIsNone(self.prepare(now=NOW - 2))
        manifest, result = source_result()
        result["completedAt"] = iso(NOW - 181)
        self.assertIsNone(self.prepare(manifest, result))
        manifest, result = source_result()
        manifest["deviceId"] = "other-device"
        self.assertIsNone(self.prepare(manifest, result))
        for parked_age, completed_age, allowed in ((1800, 600, True), (1800.001, 600, False), (1800, 600.001, False)):
            manifest, result = source_result()
            manifest["parkedAt"] = iso(NOW - parked_age)
            result["completedAt"] = iso(NOW - completed_age)
            for i, frame in enumerate(manifest["frames"]):
                frame["capturedAt"] = iso(NOW - parked_age - 2 + i)
            self.assertEqual(self.prepare(manifest, result) is not None, allowed)

    def test_identifiers_body_limit_and_content_normalization(self):
        manifest, result = source_result()
        for event in ("dot.event", "bad\n", "a" * 97):
            manifest["eventId"] = event
            with self.assertRaisesRegex(ValueError, "event_id"):
                self.prepare(manifest, result)
        with patch.object(n, "MAX_BODY", 1), self.assertRaisesRegex(ValueError, "body_too_large"):
            self.prepare()
        manifest, result = source_result()
        original = self.prepare(manifest, result)[2]
        result["analysis"]["readings"][0]["text"] = " \uff12\uff10\uff14 "
        result["analysis"]["readings"] *= 2
        self.assertEqual(self.prepare(manifest, result)[2], original)


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.credentials = self.root / "parking-notify.credentials.json"
        self.secret = "dedicated-notify-secret-" + "x" * 40
        self.write_credentials()
        self.config = {"dataDir": str(self.root / "data"), "codexExe": "never-run", "token": "local-" + "y" * 40,
                       "parkingNotify": {"enabled": True, "credentialsFile": str(self.credentials), "notBefore": iso(NOW - 3600)}}
        self.now = NOW
        self.service = s.Service(self.config, lambda *_: {"analysis": readable()})
        self.notifier = self.service.parking_notify
        self.assertIsNotNone(self.notifier)
        self.notifier.clock = lambda: self.now

    def write_credentials(self, **updates):
        credentials = {"endpoint": "https://example.invalid", "token": self.secret, "deviceId": "test-device"}
        credentials.update(updates)
        self.credentials.write_text(json.dumps(credentials), encoding="utf-8")
        self.credentials.chmod(0o600)

    def tearDown(self):
        if self.notifier and self.notifier.thread:
            self.notifier.stop_event.set()
            self.notifier.thread.join(3)
            self.assertFalse(self.notifier.thread.is_alive())
        self.service.db.close()
        self.tmp.cleanup()

    def complete(self, event="notify-1", phases=("parked", "parked", "parked"), text="204"):
        analysis = readable()
        analysis["readings"][0]["text"] = text
        self.service.runner = lambda *_: {"analysis": analysis}
        with patch("service.time.time", return_value=self.now), patch("service.utcnow", return_value=iso(self.now)):
            job, _ = self.service.submit(source_bundle(event, self.now, phases))
            self.service.process_one()
        self.assertEqual(self.service.get(job)["status"], "completed")
        return job

    def row(self, event="notify-1"):
        self.service.db.row_factory = sqlite3.Row
        try:
            row = self.service.db.execute("SELECT * FROM parking_notify_outbox WHERE event=?", (event,)).fetchone()
            return dict(row) if row else None
        finally:
            self.service.db.row_factory = None

    def restart(self):
        self.service.db.close()
        self.service = s.Service(self.config)
        self.notifier = self.service.parking_notify
        self.notifier.clock = lambda: self.now

    def test_new_completion_persists_without_network_and_no_backfill(self):
        self.service.parking_notify = None
        self.complete("old")
        self.service.parking_notify = self.notifier
        self.restart()
        self.assertFalse(self.notifier.once())
        self.assertIsNone(self.row("old"))
        with patch.object(self.notifier, "send") as send:
            self.complete()
            send.assert_not_called()
        self.assertEqual(self.row()["state"], "pending")
        self.restart()
        self.assertEqual(self.row()["state"], "pending")

    def test_job_created_before_activation_never_enqueued(self):
        self.notifier.not_before = self.now - 200
        with patch("service.time.time", return_value=self.now - 201):
            job, _ = self.service.submit(source_bundle())
        with patch("service.utcnow", return_value=iso(self.now)):
            self.service.process_one()
        self.assertEqual(self.service.get(job)["status"], "completed")
        self.assertIsNone(self.row())

    def test_completion_and_outbox_commit_together(self):
        enqueue = self.notifier._enqueue
        def inspect(*args):
            enqueue(*args)
            with closing(sqlite3.connect(self.service.root / "parking.sqlite")) as observer:
                self.assertEqual(observer.execute("SELECT status FROM jobs").fetchone()[0], "running")
                self.assertEqual(observer.execute("SELECT COUNT(*) FROM parking_notify_outbox").fetchone()[0], 0)
        with patch.object(self.notifier, "_enqueue", side_effect=inspect):
            self.complete()
        self.assertEqual(self.row()["state"], "pending")

    def test_enqueue_savepoint_and_hook_failures_do_not_fail_completed_job(self):
        enqueue = self.notifier._enqueue
        def fail(*args):
            enqueue(*args)
            raise RuntimeError("secret must not be logged")
        with patch.object(self.notifier, "_enqueue", side_effect=fail), self.assertLogs(level="WARNING") as logs:
            self.complete()
        self.assertIsNone(self.row())
        self.assertNotIn("secret", str(logs.output))
        with patch.object(self.notifier, "enqueue_completed", side_effect=RuntimeError("secret")):
            self.complete("second")
        self.assertIsNone(self.row("second"))

    def test_inference_failure_does_not_enqueue(self):
        self.service.runner = Mock(side_effect=RuntimeError("model_timeout"))
        job, _ = self.service.submit(source_bundle())
        self.service.process_one()
        self.assertEqual(self.service.get(job)["status"], "failed")
        self.assertIsNone(self.row())

    def test_content_cooldown_persists_and_suppression_does_not_extend_it(self):
        self.complete()
        self.restart()
        self.now += n.COOLDOWN / 2
        self.complete("second", text="\uff12\uff10\uff14")
        self.assertEqual(self.row("second")["reason"], "content_cooldown")
        self.assertIsNone(self.row("second")["payload"])
        self.now += n.COOLDOWN / 2
        self.complete("third")
        self.assertEqual(self.row("third")["state"], "pending")

    def test_new_approach_session_bypasses_content_not_event_dedup(self):
        first_job = self.complete()
        self.now += 300
        self.complete("second", ("approach", "parked", "parked"))
        self.assertEqual(self.row("second")["state"], "pending")
        record = self.service.get(first_job)
        manifest = json.loads((self.service.root / first_job / "manifest.json").read_text())
        manifest["frames"][0]["phase"] = "approach"
        with self.service.lock, self.service.db:
            self.notifier.enqueue_completed(first_job, manifest, record["result"])
        self.assertEqual(self.service.db.execute("SELECT COUNT(*) FROM parking_notify_outbox").fetchone()[0], 2)

    def test_uncited_or_recycled_approach_cannot_bypass(self):
        self.complete()
        self.now += 1
        self.complete("recycled", ("approach", "parked", "parked"))
        self.assertEqual(self.row("recycled")["state"], "suppressed")
        self.now += 300
        self.complete("uncited", ("parked", "parked", "approach"))
        self.assertEqual(self.row("uncited")["state"], "suppressed")

    def test_outbox_is_bounded_and_job_retention_keeps_event_tombstone(self):
        self.complete()
        with patch.object(n, "MAX_PENDING", 1):
            self.complete("second", text="205")
        self.assertEqual(self.row("second")["reason"], "outbox_full")
        self.service.db.execute("UPDATE jobs SET created=0")
        self.service.db.commit()
        self.service.cleanup()
        self.assertEqual(self.service.db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 0)
        self.assertEqual(self.service.db.execute("SELECT COUNT(*) FROM parking_notify_outbox").fetchone()[0], 2)

    def test_network_is_after_commit_and_outside_service_lock(self):
        job = self.complete()
        def send(payload):
            self.assertTrue(self.service.lock.acquire(blocking=False))
            self.service.lock.release()
            with closing(sqlite3.connect(self.service.root / "parking.sqlite")) as observer:
                self.assertEqual(observer.execute("SELECT status FROM jobs WHERE id=?", (job,)).fetchone()[0], "completed")
                self.assertEqual(observer.execute("SELECT state,attempts FROM parking_notify_outbox").fetchone(), ("sending", 1))
            return "acknowledged", "cloud_accepted"
        with patch.object(self.notifier, "send", side_effect=send):
            self.assertTrue(self.notifier.once())
        self.assertEqual(self.row()["state"], "acknowledged")
        self.assertIsNone(self.row()["payload"])
        self.assertEqual(self.service.get(job)["status"], "completed")

    def test_retry_backoff_exact_payload_restart_and_five_attempt_limit(self):
        self.complete()
        original = self.row()["payload"]
        for attempt, delay in enumerate((15, 30, 60, 60, 60), 1):
            with patch.object(self.notifier, "send", return_value=("retry", "network_failure")) as send:
                self.assertTrue(self.notifier.once())
                send.assert_called_once_with(original)
                self.assertFalse(self.notifier.once())
            row = self.row()
            self.assertEqual(row["attempts"], attempt)
            self.assertEqual(row["next_attempt"], self.now + delay)
            self.now += delay
            self.restart()
        self.assertEqual(self.row()["state"], "terminal")
        self.assertEqual(self.row()["reason"], "attempt_limit")
        self.assertIsNone(self.row()["payload"])
        self.assertFalse(self.notifier.once())

    def test_expired_restart_clock_rollback_and_changed_not_before_do_not_send(self):
        for mutation in ("expiry", "rollback", "activation"):
            with self.subTest(mutation=mutation):
                event = mutation
                self.complete(event, text=mutation)
                saved = self.now
                if mutation == "expiry":
                    self.now += 601
                elif mutation == "rollback":
                    self.now -= 1
                else:
                    self.notifier.not_before = self.now
                with patch.object(self.notifier, "send") as send:
                    self.assertFalse(self.notifier.once())
                    send.assert_not_called()
                self.assertEqual(self.row(event)["state"], "expired")
                self.now = saved

    def test_retry_that_would_cross_expiry_is_dropped(self):
        self.complete()
        self.now += 590
        with patch.object(self.notifier, "send", return_value=("retry", "http_retryable")):
            self.notifier.once()
        self.assertEqual(self.row()["state"], "expired")

    def test_unknown_delivery_after_crash_is_not_retried(self):
        self.complete()
        self.service.db.execute("UPDATE parking_notify_outbox SET state='sending',attempts=1,lease_until=?", (self.now + 60,))
        self.service.db.commit()
        self.restart()
        with patch.object(self.notifier, "send") as send:
            self.assertFalse(self.notifier.once())
            self.now += 61
            self.assertFalse(self.notifier.once())
            send.assert_not_called()
        self.assertEqual(self.row()["reason"], "delivery_unknown")

    def test_unexpected_push_error_is_terminal_and_never_job_failure(self):
        job = self.complete()
        with patch.object(self.notifier, "send", side_effect=RuntimeError("secret")), self.assertLogs(level="INFO") as logs:
            self.notifier.once()
        self.assertEqual(self.row()["state"], "terminal")
        self.assertEqual(self.service.get(job)["status"], "completed")
        self.assertNotIn("secret", str(logs.output))

    def test_single_daemon_and_concurrent_claim(self):
        self.complete()
        entered, release = threading.Event(), threading.Event()
        def send(_):
            entered.set()
            self.assertTrue(release.wait(3))
            return "acknowledged", "cloud_accepted"
        with patch.object(self.notifier, "send", side_effect=send) as sender:
            thread = self.notifier.start()
            self.assertIs(thread, self.notifier.start())
            self.assertTrue(thread.daemon)
            try:
                self.assertTrue(entered.wait(3))
                self.assertFalse(self.notifier.once())
                self.assertEqual(self.row()["attempts"], 1)
            finally:
                self.notifier.stop_event.set()
                release.set()
                thread.join(3)
            self.assertFalse(thread.is_alive())
            sender.assert_called_once()

    def test_private_config_https_and_dedicated_credentials(self):
        for endpoint in ("http://example.invalid", "https://example.invalid/path", "https://user:pass@example.invalid",
                         "https://example.invalid?x=1", "https://example.invalid#x", "https://", "https://example.invalid\n",
                         "https://example.invalid:0", "https://example.invalid:bad", "https://example.invalid\\other"):
            self.write_credentials(endpoint=endpoint)
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                n.load_settings(self.service)
        for token in ("short", "\n" + self.secret, self.config["token"]):
            self.write_credentials(token=token)
            with self.assertRaisesRegex(ValueError, "dedicated_token"):
                n.load_settings(self.service)
        self.write_credentials()
        self.config["cloud"] = {"credentialsFile": str(self.credentials)}
        with self.assertRaisesRegex(ValueError, "dedicated_credentials"):
            n.load_settings(self.service)
        del self.config["cloud"]
        self.config["parkingNotify"]["credentialsFile"] = str(self.root / "data" / "outside.json")
        with self.assertRaisesRegex(ValueError, "private_root"):
            n.load_settings(self.service)

    @unittest.skipIf(os.name == "nt", "Windows uses private-directory ACLs")
    def test_posix_public_credentials_rejected(self):
        self.credentials.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "private_permissions"):
            n.load_settings(self.service)

    def test_disabled_and_invalid_config_do_not_touch_inference(self):
        for enabled in (False, None, 1, "true"):
            self.config["parkingNotify"]["enabled"] = enabled
            self.assertIsNone(n.configure(self.service))
        self.config["parkingNotify"]["enabled"] = True
        self.credentials.write_text("invalid secret")
        with self.assertLogs(level="WARNING") as logs:
            self.assertIsNone(n.configure(self.service))
        self.assertNotIn("invalid secret", str(logs.output))
        for config in (None, [], True):
            self.config["parkingNotify"] = config
            self.assertIsNone(n.configure(self.service))

    def test_health_reports_positive_configuration_and_actual_thread_liveness(self):
        server = s.BoundedServer(("127.0.0.1", 0), s.handler(self.service))
        serving = threading.Thread(target=server.serve_forever, daemon=True)
        self.service.worker = Mock(is_alive=Mock(return_value=True))
        serving.start()
        def health():
            request = Request(f"http://127.0.0.1:{server.server_port}/health",
                              headers={"Authorization": "Bearer " + self.config["token"]})
            with urlopen(request, timeout=3) as response:
                return json.load(response)
        try:
            self.assertEqual((health()["parkingNotifyConfigured"], health()["parkingNotifyAlive"]), (True, False))
            self.notifier.start()
            self.assertEqual((health()["parkingNotifyConfigured"], health()["parkingNotifyAlive"]), (True, True))
            self.notifier.stop_event.set()
            self.notifier.thread.join(3)
            self.assertFalse(health()["parkingNotifyAlive"])
            self.service.parking_notify = None
            value = health()
            self.assertEqual((value["parkingNotifyConfigured"], value["parkingNotifyAlive"]), (False, False))
            self.assertTrue(value["workerAlive"])
            self.assertNotIn(self.secret, json.dumps(value))
        finally:
            server.shutdown()
            server.server_close()
            serving.join(3)

    def test_real_main_starts_daemon_and_authenticated_health(self):
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        config = dict(self.config, port=port)
        path = self.root / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        process = subprocess.Popen([sys.executable, str(Path(s.__file__).resolve()), "--config", str(path)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            request = Request(f"http://127.0.0.1:{port}/health",
                              headers={"Authorization": "Bearer " + config["token"]})
            deadline, health = time.monotonic() + 5, None
            while process.poll() is None and time.monotonic() < deadline:
                try:
                    with urlopen(request, timeout=0.3) as response:
                        health = json.load(response)
                    break
                except (URLError, TimeoutError):
                    time.sleep(0.02)
            self.assertIsNotNone(health)
            for key in ("workerAlive", "parkingNotifyConfigured", "parkingNotifyAlive"):
                self.assertIs(health[key], True)
        finally:
            process.terminate()
            try:
                process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=3)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.notifier = n.ParkingNotifier.__new__(n.ParkingNotifier)
        self.notifier.endpoint = "https://example.invalid"
        self.notifier.token = "fake-token-" + "x" * 40
        self.notifier.opener = Mock()
        self.payload = json.dumps(wire_fixture())

    def response(self, status=202, body=None):
        response = Mock(status=status)
        response.read.return_value = json.dumps(body or {"claimed": True, "status": "accepted", "eventId": "notify-1"}).encode()
        self.notifier.opener.open.return_value.__enter__ = Mock(return_value=response)
        self.notifier.opener.open.return_value.__exit__ = Mock(return_value=False)
        return response

    def test_https_post_headers_timeout_and_ack_not_phone_receipt(self):
        response = self.response()
        self.assertEqual(self.notifier.send(self.payload), ("acknowledged", "cloud_accepted"))
        request = self.notifier.opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.invalid/api/parking/recognition")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("User-agent"), "Wayon-ParkingVision/1.0")
        self.assertEqual(request.get_header("Authorization"), "Bearer " + self.notifier.token)
        self.assertEqual(self.notifier.opener.open.call_args.kwargs, {"timeout": 10})
        self.assertEqual(request.data, self.payload.encode())
        response.read.assert_called_once_with(n.MAX_RESPONSE + 1)
        self.response(body={"claimed": True, "status": "duplicate", "eventId": "notify-1"})
        self.assertEqual(self.notifier.send(self.payload), ("acknowledged", "cloud_duplicate"))

    def test_missing_malformed_and_oversized_ack_terminal(self):
        for body in (b"", b"not json", b"{}", b"[]", b"x" * (n.MAX_RESPONSE + 1),
                     b'{"claimed":true,"status":"accepted","eventId":"other"}',
                     b'{"claimed":true,"status":"accepted"}',
                     b'{"claimed":false,"status":"accepted","eventId":"notify-1"}',
                     b'{"claimed":true,"status":"sent","eventId":"notify-1"}'):
            self.response().read.return_value = body
            self.assertEqual(self.notifier.send(self.payload)[0], "terminal")

    def test_oversized_request_never_opens_network(self):
        self.assertEqual(self.notifier.send("x" * (n.MAX_BODY + 1)), ("terminal", "request_too_large"))
        self.notifier.opener.open.assert_not_called()

    def test_status_classification_both_response_and_http_error(self):
        for status in (200, 201, 204, 301, 302, 307, 308, 400, 401, 403, 404, 409, 422, 429, 500, 502, 503, 599):
            expected = "retry" if status == 429 or status >= 500 else "terminal"
            with self.subTest(status=status):
                self.response(status)
                self.assertEqual(self.notifier.send(self.payload)[0], expected)
                error = HTTPError("https://example.invalid", status, "secret", {}, io.BytesIO(b"private error"))
                self.notifier.opener.open.side_effect = error
                self.assertEqual(self.notifier.send(self.payload)[0], expected)
                self.assertTrue(error.fp.closed)
                self.notifier.opener.open.side_effect = None

    def test_only_confirmed_network_errors_retry(self):
        for error in (TimeoutError(), ConnectionResetError(), URLError(socket.gaierror()),
                      URLError(ConnectionRefusedError()), IncompleteRead(b"{")):
            self.notifier.opener.open.side_effect = error
            self.assertEqual(self.notifier.send(self.payload), ("retry", "network_failure"))
        for error in (ssl.SSLCertVerificationError(), URLError(ssl.SSLCertVerificationError()), URLError("unknown")):
            self.notifier.opener.open.side_effect = error
            self.assertEqual(self.notifier.send(self.payload)[0], "terminal")

    def test_no_redirect_and_no_proxy_policy(self):
        handler = n.NoRedirect()
        for status in (301, 302, 303, 307, 308):
            request = Request("https://example.invalid/api/parking/recognition", data=b"private")
            self.assertIsNone(handler.redirect_request(request, None, status, "", {}, "https://elsewhere.invalid"))
        opener = n.build_opener(n.NoRedirect(), n.ProxyHandler({}))
        self.assertTrue(any(isinstance(h, n.NoRedirect) for h in opener.handlers))
        self.assertFalse(any(isinstance(h, n.ProxyHandler) and h.proxies for h in opener.handlers))


if __name__ == "__main__":
    unittest.main()
