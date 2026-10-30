import base64
import copy
import io
import json
from pathlib import Path
import tempfile
import os
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from PIL import Image

import service as s


def bundle(event="test"):
    frames = []
    for i in range(3):
        image = Image.new("RGB", (128, 96), (i * 70, 50, 100))
        out = io.BytesIO()
        image.save(out, "PNG")
        frames.append({"capturedAt": f"2026-10-30T12:13:0{i}+00:00", "camera": "road",
                       "imageBase64": base64.b64encode(out.getvalue()).decode()})
    return {"eventId": event, "deviceId": "test-device", "parkedAt": "2026-10-30T12:13:10Z", "frames": frames}


def readable():
    return {"readings": [{"kind": "pillar", "text": "204", "status": "readable", "alternatives": [],
                           "evidence": [{"frameIndex": i, "box": [0.1, 0.2, 0.4, 0.8]} for i in (0, 1)]}],
            "exactParkingSpotKnown": False}


class InputTests(unittest.TestCase):
    def test_valid_and_metadata(self):
        meta, frames, sig = s.prepare_bundle(bundle())
        self.assertEqual(len(frames), 3)
        self.assertEqual(len(sig), 64)
        self.assertNotIn("imageBase64", json.dumps(meta))
        with Image.open(io.BytesIO(frames[0]["bytes"])) as im:
            self.assertEqual(im.format, "JPEG")
            self.assertFalse(im.getexif())

    def test_reject_invalid_cases(self):
        mutations = [
            lambda b: b.update(eventId="../bad"),
            lambda b: b.update(parkedAt="2026-10-30T12:13:10"),
            lambda b: b.update(parkedAt="2100-01-01T00:00:00Z"),
            lambda b: b.update(frames=b["frames"][:1]),
            lambda b: b.update(frames=b["frames"] * 5),
            lambda b: b["frames"][0].update(camera="driver"),
            lambda b: b["frames"][0].update(imageBase64="!!!!"),
            lambda b: b["frames"][0].update(imageBase64="eHl6"),
            lambda b: b["frames"][0].update(capturedAt="2026-10-29T12:13:10Z"),
            lambda b: b["frames"][0].update(imageBase64="A" * (3 * 1024 * 1024)),
            lambda b: b.update(prompt="run command"),
            lambda b: b.update(frames=[b["frames"][0]] * 3),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                value = bundle()
                mutate(value)
                with self.assertRaises(ValueError):
                    s.prepare_bundle(value)

    def test_order_and_duplicates(self):
        value = bundle()
        value["frames"] = [value["frames"][2], value["frames"][0], value["frames"][0], value["frames"][1]]
        metadata, frames, _ = s.prepare_bundle(value)
        self.assertEqual(len(frames), 3)
        self.assertEqual(metadata["frames"][0]["capturedAt"], "2026-10-30T12:13:00+00:00")


class ResultTests(unittest.TestCase):
    def test_readable_and_unknown(self):
        self.assertEqual(s.validate_result(readable(), 3)["readings"][0]["text"], "204")
        s.validate_result({"readings": [], "exactParkingSpotKnown": False}, 3)
        value = readable()
        value["readings"][0].update(status="ambiguous", text=None, alternatives=["204", "304"])
        s.validate_result(value, 3)

    def test_reject_unsupported_claims(self):
        mutations = [
            lambda r: r.update(exactParkingSpotKnown=True),
            lambda r: r["readings"][0].update(evidence=[{"frameIndex": 0, "box": [0, 0, 1, 1]}]),
            lambda r: r["readings"][0]["evidence"][1].update(frameIndex=9),
            lambda r: r["readings"][0]["evidence"][1].update(frameIndex=0),
            lambda r: r["readings"][0]["evidence"][0].update(box=[0.5, 0, 0.1, 1]),
            lambda r: r["readings"][0].update(status="ambiguous"),
            lambda r: r["readings"][0].update(kind="floor"),
            lambda r: r["readings"][0].update(alternatives=["304"]),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                value = readable()
                mutate(value)
                with self.assertRaises(Exception):
                    s.validate_result(value, 3)

    def test_codex_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            for i in range(3):
                (job / f"frame-{i:02d}.jpg").touch()
            args = s.codex_args("codex.exe", job)
            self.assertEqual(args.count("--image"), 3)
            self.assertIn("read-only", args)
            self.assertIn("--ignore-user-config", args)
            self.assertIn("tools.view_image=false", args)
            self.assertIn('forced_login_method="chatgpt"', args)
            self.assertIn("shell_tool", args)
            self.assertIn("apps", args)
            self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", args)

    def test_unicode_floor_and_temporal_evidence(self):
        value = readable()
        value["readings"][0].update(kind="floor", text="２")
        with self.assertRaisesRegex(ValueError, "numeric_floor"):
            s.validate_result(value, 3)
        frames = [{"capturedAt": "2026-10-30T12:00:00Z"}] * 3
        with self.assertRaisesRegex(ValueError, "temporal"):
            s.validate_result(readable(), 3, frames)


class StoreFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = {"dataDir": self.tmp.name, "codexExe": "unused", "token": "t" * 48}
        self.service = s.Service(self.config, lambda *args: {"analysis": readable()})

    def tearDown(self):
        self.service.db.close()
        self.tmp.cleanup()


class StoreTests(StoreFixture):
    def test_completion_dedup_and_conflict(self):
        job, created = self.service.submit(bundle())
        self.assertTrue(created)
        self.assertEqual(self.service.submit(bundle()), (job, False))
        self.service.process_one()
        record = self.service.get(job)
        self.assertEqual(record["status"], "completed")
        self.assertEqual(len(record["result"]["frames"]), 3)
        changed = bundle()
        changed["parkedAt"] = "2026-10-30T12:13:11Z"
        with self.assertRaisesRegex(ValueError, "event_conflict"):
            self.service.submit(changed)

    def test_failure_no_false_result(self):
        def fail(*args):
            raise RuntimeError("model_timeout")
        self.service.runner = fail
        job, _ = self.service.submit(bundle())
        self.service.process_one()
        record = self.service.get(job)
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["error"], "model_timeout")
        self.assertIsNone(record["result"])

    def test_restart_and_retention(self):
        job, _ = self.service.submit(bundle())
        other = s.Service(self.config)
        self.assertEqual(other.get(job)["error"], "service_restarted")
        other.db.execute("UPDATE jobs SET created=0")
        other.db.commit()
        other.cleanup()
        self.assertIsNone(other.get(job))
        self.assertFalse((Path(self.tmp.name) / job).exists())
        orphan = Path(self.tmp.name) / ("f" * 32)
        orphan.mkdir()
        os.utime(orphan, (0, 0))
        other.cleanup()
        self.assertFalse(orphan.exists())
        other.db.close()

    def test_failed_event_bounded_retry(self):
        self.service.runner = lambda *args: (_ for _ in ()).throw(RuntimeError("model_timeout"))
        job, _ = self.service.submit(bundle())
        self.service.process_one()
        for _ in range(2):
            self.service.retry(job)
            self.service.process_one()
        with self.assertRaisesRegex(ValueError, "retry_limit"):
            self.service.retry(job)


class CollectorTests(StoreFixture):
    def test_only_new_distinct_exterior_bursts(self):
        from cloud_collector import groups
        before = s.timestamp("2026-10-30T12:00:00Z")
        frames = [{"id": str(i), "deviceId": "car", "camera": "wide", "impact": None,
                   "capturedAt": f"2026-10-30T12:01:0{i}Z"} for i in range(3)]
        self.assertEqual(len(groups(frames, before, before + 300)), 1)
        self.assertEqual(groups(frames, before, before + 100), [])
        self.assertEqual(groups(frames, before + 100, before + 300), [])
        self.assertEqual(groups(frames, before, before + 8000), [])
        self.assertEqual(len(groups(frames, before, before + 7260)), 1)
        self.assertEqual(groups(frames, before, before + 7260.5), [])
        self.assertEqual(groups(frames[1:], before, before + 7261), [])
        self.assertEqual(groups(frames[:2], before, before + 300), [])
        frames[1]["camera"] = "driver"
        frames[2]["impact"] = {"id": "impact"}
        self.assertEqual(groups(frames, before, before + 300), [])

    def collector(self):
        from cloud_collector import Collector
        collector = Collector.__new__(Collector)
        collector.service = self.service
        collector.not_before = 0
        collector.device = "car"
        collector.deferred = {}
        return collector

    def test_bad_group_does_not_block_later_and_persisted_frame_ids(self):
        from unittest.mock import patch
        collector = self.collector()
        value = bundle()
        frames = [{"id": f"{prefix}-{i}", "deviceId": "car", "camera": "wide",
                   "capturedAt": f"2026-10-30T12:0{minute}:0{i}Z"}
                  for prefix, minute in [("bad", 0), ("good", 1)] for i in range(3)]
        def get(path, limit):
            if "snapshots?" in path:
                return json.dumps({"snapshots": frames}).encode()
            if "/bad-" in path:
                raise HTTPError("https://example.invalid", 404, "missing", None, None)
            return base64.b64decode(value["frames"][int(path[-1])]["imageBase64"])
        collector.get = get
        with patch('cloud_collector.time.time', return_value=s.timestamp("2026-10-30T12:10:00Z")):
            collector.once()
            collector.once()
        self.assertEqual(self.service.db.execute("SELECT count(*) FROM jobs").fetchone()[0], 1)
        self.assertEqual(self.service.db.execute("SELECT count(*) FROM cloud_frames").fetchone()[0], 6)
        # Even a changed first member cannot cause already-consumed snapshots to reappear.
        frames = frames[3:]
        frames[0]["id"] = "new-first"
        with patch('cloud_collector.time.time', return_value=s.timestamp("2026-10-30T12:10:00Z")):
            collector.once()
        self.assertEqual(self.service.db.execute("SELECT count(*) FROM jobs").fetchone()[0], 1)

    def test_private_credentials_and_https_origin(self):
        from cloud_collector import Collector
        from types import SimpleNamespace
        root = Path(self.tmp.name)
        credentials = root / 'credentials.json'
        credentials.write_text(json.dumps({'endpoint': 'https://example.invalid', 'token': 'test'}))
        service = SimpleNamespace(root=root / 'data', config={'cloud': {
            'credentialsFile': str(credentials), 'deviceId': 'car', 'notBefore': '2026-10-30T00:00:00Z'}})
        self.assertEqual(Collector(service).endpoint, 'https://example.invalid')
        for endpoint in ['http://example.invalid', 'https://example.invalid/path', 'https://user:pass@example.invalid']:
            credentials.write_text(json.dumps({'endpoint': endpoint, 'token': 'test'}))
            with self.assertRaisesRegex(ValueError, 'https_origin'):
                Collector(service)
        service.config['cloud']['credentialsFile'] = str(root.parent / 'outside.json')
        with self.assertRaisesRegex(ValueError, 'private_root'):
            Collector(service)

    def test_transfer_retries_are_bounded_and_spaced(self):
        from unittest.mock import patch
        collector = self.collector()
        start = s.timestamp('2026-10-30T12:10:00Z')
        frames = [{'id': str(i), 'deviceId': 'car', 'camera': 'wide',
                   'capturedAt': f'2026-10-30T12:09:0{i}Z'} for i in range(3)]
        calls = []
        def get(path, limit):
            if 'snapshots?' in path:
                return json.dumps({'snapshots': frames}).encode()
            calls.append(path)
            raise TimeoutError()
        collector.get = get
        now = start + 120
        for attempt in range(1, 6):
            with patch('cloud_collector.time.time', return_value=now):
                collector.once()
                collector.once()
            self.assertEqual(len(calls), attempt)
            now += min(1800, 60 * 2 ** attempt) + 1
        self.assertEqual(self.service.db.execute('SELECT count(*) FROM cloud_frames').fetchone()[0], 3)


class HttpTests(StoreFixture):
    def test_limits(self):
        self.service.config["maxJobsPerDay"] = 1
        self.service.submit(bundle())
        with self.assertRaisesRegex(ValueError, "daily_limit"):
            self.service.submit(bundle("two"))

    def test_authenticated_http(self):
        server = s.BoundedServer(("127.0.0.1", 0), s.handler(self.service))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with self.assertRaises(HTTPError) as caught:
                urlopen(base + "/health")
            self.assertEqual(caught.exception.code, 401)
            headers = {"Authorization": "Bearer " + self.config["token"], "Content-Type": "application/json"}
            req = Request(base + "/events", json.dumps(bundle()).encode(), headers)
            with urlopen(req) as response:
                self.assertEqual(response.status, 202)
                job = json.load(response)["jobId"]
            with urlopen(Request(base + "/jobs/" + job, headers=headers)) as response:
                self.assertEqual(json.load(response)["status"], "queued")
            headers["Content-Length"] = str(s.MAX_BODY + 1)
            with self.assertRaises(HTTPError) as caught:
                urlopen(Request(base + "/events", b"", headers))
            self.assertEqual(caught.exception.code, 413)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
