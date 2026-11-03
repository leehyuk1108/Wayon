"""Offline contract, capture-provenance, and collector replay tests."""
import base64
import copy
from datetime import datetime, timezone
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from cloud_collector import Collector, groups
import service as s
from test_service import StoreFixture, bundle, readable


BASE = s.timestamp("2026-10-30T12:00:00Z")


def iso(seconds):
    return datetime.fromtimestamp(BASE + seconds, timezone.utc).isoformat()


def snapshots(event="park-1", device="car", offsets=(0, 30, 60, 61, 62), phases=None):
    phases = phases or ["approach"] * (len(offsets) - 3) + ["parked"] * min(3, len(offsets))
    return [{"id": f"{event}-{i}", "deviceId": device, "camera": "wide", "capturedAt": iso(at),
             "parking": {"version": 1, "eventId": event, "parkedAt": iso(offsets[-1]),
                         "index": i, "count": len(offsets), "phase": phases[i]}}
            for i, at in enumerate(offsets)]


def tagged_bundle():
    value = bundle()
    for i, frame in enumerate(value["frames"]):
        frame["phase"] = "approach" if i == 0 else "parked"
    value["parkedAt"] = value["frames"][-1]["capturedAt"]
    return value


class ExplicitGroupTests(unittest.TestCase):
    def accept(self, frames, before=BASE, now=BASE + 300):
        return groups(frames, before, now)

    def test_out_of_order_listing_sorted_by_exact_indices(self):
        frames = snapshots()
        for permutation in itertools.permutations(frames):
            self.assertEqual(self.accept(list(permutation)), [frames])

    def test_wire_count_bounds_and_sender_nine_frame_shape(self):
        for count in range(2, 13):
            with self.subTest(count=count):
                frames = snapshots(offsets=tuple(range(count)), phases=["parked"] * count)
                self.assertEqual(self.accept(frames), [frames])
        frames = snapshots(offsets=(0, 20, 40, 60, 80, 100, 118, 119, 120),
                           phases=["approach"] * 6 + ["parked"] * 3)
        self.assertEqual(self.accept(frames), [frames])

    def test_each_partial_subset_is_rejected(self):
        frames = snapshots()
        for length in range(len(frames)):
            for subset in itertools.combinations(frames, length):
                with self.subTest(indices=[f["parking"]["index"] for f in subset]):
                    self.assertEqual(self.accept(list(subset)), [])

    def test_metadata_type_and_range_corruption(self):
        mutations = {
            "version": (None, True, 1.0, "1", 0, 2, [], {}),
            "eventId": (None, True, "", "x" * 97, "../bad", "with space", "bad\n", "\u00e9vent", [], {}),
            "parkedAt": (None, True, "bad", "2026-10-30T12:01:02", iso(61), iso(63), [], {}),
            "index": (None, True, 0.0, "0", -1, 5, 12, [], {}),
            "count": (None, True, 5.0, "5", 0, 1, 2, 4, 6, 13, [], {}),
            "phase": (None, True, "", "unknown", "APPROACH", [], {}),
        }
        for key, values in mutations.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    frames = snapshots()
                    frames[0]["parking"][key] = value
                    self.assertEqual(self.accept(frames), [])
        for key in snapshots()[0]["parking"]:
            frames = snapshots()
            del frames[0]["parking"][key]
            self.assertEqual(self.accept(frames), [])
        frames = snapshots()
        frames[0]["parking"]["extra"] = "bad"
        self.assertEqual(self.accept(frames), [])

    def test_snapshot_corruption_cannot_be_filtered_into_complete_group(self):
        mutations = {
            "deviceId": (None, True, "other", "../bad", [], {}),
            "id": (None, True, "", "../bad", [], {}),
            "capturedAt": (None, True, "bad", "2026-10-30T12:00:00", iso(-1), iso(301), [], {}),
            "camera": (None, True, "road", "driver", [], {}),
            "impact": ({"id": "collision"},),
        }
        for key, values in mutations.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    frames = snapshots()
                    frames[0][key] = value
                    self.assertEqual(self.accept(frames), [])
        for key in ("deviceId", "id", "capturedAt", "camera"):
            frames = snapshots()
            del frames[0][key]
            self.assertEqual(self.accept(frames), [])

    def test_extra_corrupt_claimant_poisons_session_but_not_other_event(self):
        for mutation in (
                lambda f: f.update(capturedAt=iso(-8000)),
                lambda f: f.update(capturedAt="bad"),
                lambda f: f.update(camera="driver"),
                lambda f: f.update(impact={"id": "crash"}),
                lambda f: f["parking"].update(version=2),
                lambda f: f["parking"].update(parkedAt=iso(-7998)),
                lambda f: f["parking"].pop("index")):
            frames = snapshots()
            extra = copy.deepcopy(frames[0])
            extra["id"] = "extra"
            mutation(extra)
            other = snapshots("good", offsets=(100, 101, 102))
            self.assertEqual(self.accept(frames + [extra] + other), [other])

    def test_exact_indices_unique_ids_and_timestamps(self):
        mutations = (
            lambda f: f[1]["parking"].update(index=0),
            lambda f: f[0].update(id=f[1]["id"]),
            lambda f: f[1].update(capturedAt=f[0]["capturedAt"]),
            lambda f: f[1].update(capturedAt=iso(60.5)),
            lambda f: f[0]["parking"].update(index=1),
        )
        for mutate in mutations:
            frames = snapshots()
            mutate(frames)
            self.assertEqual(self.accept(frames), [])
        frames = snapshots()
        self.assertEqual(self.accept(frames + [copy.deepcopy(frames[0])]), [])
        other = snapshots("other", offsets=(100, 101, 102))
        other[0]["id"] = frames[0]["id"]
        self.assertEqual(self.accept(frames + other), [])

    def test_phase_order_and_final_parked_reference(self):
        for phases in itertools.product(("approach", "parked"), repeat=5):
            frames = snapshots(phases=phases)
            valid = phases[-1] == "parked" and "approach" not in phases[phases.index("parked"):]
            self.assertEqual(self.accept(frames), [frames] if valid else [])
        for reference in (-1, 0, 60, 61, 62.001, 100, 8000):
            frames = snapshots()
            for frame in frames:
                frame["parking"]["parkedAt"] = iso(reference)
            self.assertEqual(self.accept(frames), [])

    def test_wait_window_activation_and_capture_span_boundaries(self):
        frames = snapshots(offsets=(0, 118, 120))
        for now, expected in ((239.999999, []), (240, [frames]), (7200, [frames]), (7200.000001, []), (-1, [])):
            with self.subTest(now=now):
                self.assertEqual(self.accept(frames, now=BASE + now), expected)
        self.assertEqual(self.accept(frames, before=BASE + 0.000001), [])
        self.assertEqual(self.accept(frames, before=BASE), [frames])
        too_long = snapshots(offsets=(0, 119, 120.000001))
        self.assertEqual(self.accept(too_long), [])
        future = snapshots(offsets=(0, 299, 301))
        self.assertEqual(self.accept(future), [])

    def test_equivalent_timezone_instants_and_maximum_ascii_id(self):
        frames = snapshots(event="e" * 94)  # Snapshot IDs also fit the 96-character bound.
        for frame in frames:
            frame["parking"]["eventId"] = "a" * 96
        frames[0]["parking"]["parkedAt"] = "2026-10-30T21:01:02+09:00"
        self.assertEqual(self.accept(frames), [frames])
        frames[1]["capturedAt"] = "2026-10-30T21:00:00+09:00"
        self.assertEqual(self.accept(frames), [])

    def test_device_and_session_separation_without_stale_member_mixing(self):
        first = snapshots("first")
        second = snapshots("second")
        other_device = snapshots("first", device="other")
        for frame in other_device:
            frame["id"] = "other-" + frame["id"]
        self.assertEqual(len(self.accept(first + second + other_device)), 3)
        self.assertEqual(self.accept(first[:2] + second[2:]), [])
        self.assertEqual(self.accept(first[:2] + other_device[2:]), [])
        stale = snapshots("first", offsets=(-8000, -7970, -7940, -7939, -7938))
        for frame in stale:
            frame["id"] = "stale-" + frame["id"]
        self.assertEqual(self.accept(stale[:2] + first[2:]), [])
        self.assertEqual(self.accept(stale + first), [])

    def test_legacy_compatibility_and_malformed_metadata_never_falls_back(self):
        legacy = snapshots(offsets=(0, 1, 2))
        for frame in legacy:
            del frame["parking"]
        self.assertEqual(self.accept(legacy), [legacy])
        for metadata in (None, False, 0, "", [], {}, {"eventId": "x"}, {"version": 2}):
            for index in range(3):
                frames = copy.deepcopy(legacy)
                frames[index]["parking"] = metadata
                self.assertEqual(self.accept(frames), [])
            frames = copy.deepcopy(legacy)
            for frame in frames:
                frame["parking"] = metadata
            self.assertEqual(self.accept(frames), [])
        explicit = snapshots("new", offsets=(100, 101, 102))
        self.assertEqual(self.accept([None, [], "bad"] + legacy + explicit), [legacy, explicit])


class PhaseInputTests(unittest.TestCase):
    def test_optional_phase_manual_compatibility_and_sorting(self):
        original, _, original_sig = s.prepare_bundle(bundle())
        value = bundle()
        value["frames"][0]["phase"] = "approach"
        value["frames"].reverse()
        metadata, frames, signature = s.prepare_bundle(value)
        self.assertEqual(frames[0]["phase"], "approach")
        self.assertNotIn("phase", frames[1])
        self.assertNotIn("phase", original["frames"][0])
        self.assertNotEqual(signature, original_sig)
        self.assertEqual(metadata["frames"][0]["phase"], "approach")

    def test_invalid_phase_and_unknown_fields(self):
        for phase in (None, False, 0, "", "unknown", [], {}, "parked\n"):
            value = bundle()
            value["frames"][0]["phase"] = phase
            with self.assertRaisesRegex(ValueError, "invalid_frame_phase"):
                s.prepare_bundle(value)
        value = tagged_bundle()
        value["frames"][0]["prompt"] = "instruction"
        with self.assertRaisesRegex(ValueError, "invalid_frame"):
            s.prepare_bundle(value)

    def test_duplicate_pixels_keep_tagged_capture_provenance(self):
        value = tagged_bundle()
        value["frames"][2]["imageBase64"] = value["frames"][0]["imageBase64"]
        metadata, frames, _ = s.prepare_bundle(value)
        self.assertEqual(len(frames), 3)
        self.assertEqual([f["phase"] for f in metadata["frames"]], ["approach", "parked", "parked"])
        self.assertEqual(frames[0]["sha256"], frames[2]["sha256"])
        self.assertNotEqual(frames[0]["capturedAt"], frames[2]["capturedAt"])
        for frame in value["frames"]:
            frame["imageBase64"] = value["frames"][0]["imageBase64"]
        with self.assertRaisesRegex(ValueError, "need_two_distinct_frames"):
            s.prepare_bundle(value)

    def test_signature_covers_duplicate_phase_and_timestamp(self):
        value = tagged_bundle()
        value["frames"][2]["imageBase64"] = value["frames"][0]["imageBase64"]
        signature = s.prepare_bundle(value)[2]
        changed = copy.deepcopy(value)
        changed["frames"][2]["phase"] = "approach"
        self.assertNotEqual(signature, s.prepare_bundle(changed)[2])
        changed = copy.deepcopy(value)
        changed["frames"][2]["capturedAt"] = "2026-10-30T12:13:03Z"
        self.assertNotEqual(signature, s.prepare_bundle(changed)[2])

    def test_prompt_has_attachment_provenance_and_location_caveat(self):
        frames = s.prepare_bundle(tagged_bundle())[0]["frames"]
        prompt = s.model_prompt(frames)
        self.assertIn("not the exact parked location", prompt)
        self.assertIn("no tools", prompt)
        provenance = json.loads(prompt.split("Per-attachment capture provenance: ", 1)[1])
        self.assertEqual([f["frameIndex"] for f in provenance], [0, 1, 2])
        self.assertEqual([f["phase"] for f in provenance], ["approach", "parked", "parked"])
        self.assertEqual(provenance[0]["capturedAt"], frames[0]["capturedAt"])
        self.assertEqual(provenance[0]["sha256"], frames[0]["sha256"])
        manual = s.prepare_bundle(bundle())[0]["frames"]
        self.assertIn('"phase": "unspecified"', s.model_prompt(manual))


class PhaseResultTests(unittest.TestCase):
    def test_duplicate_images_cannot_corroborate_but_can_be_ambiguous(self):
        frames = s.prepare_bundle(tagged_bundle())[0]["frames"]
        frames[1]["sha256"] = frames[0]["sha256"]
        with self.assertRaisesRegex(ValueError, "uncorroborated_reading"):
            s.validate_result(readable(), 3, frames)
        value = readable()
        value["readings"][0].update(status="ambiguous", text=None, alternatives=["204", "304"])
        value["readings"][0]["evidence"] = value["readings"][0]["evidence"][:1]
        s.validate_result(value, 3, frames)
        s.validate_result({"readings": [], "exactParkingSpotKnown": False}, 3, frames)

    def test_temporal_boundary_requires_different_pixels(self):
        frames = s.prepare_bundle(tagged_bundle())[0]["frames"]
        frames[0]["capturedAt"] = iso(0)
        for delta, accepted in ((0, False), (0.499999, False), (0.5, True)):
            frames[1]["capturedAt"] = iso(delta)
            if accepted:
                s.validate_result(readable(), 3, frames)
            else:
                with self.assertRaisesRegex(ValueError, "insufficient_temporal_evidence"):
                    s.validate_result(readable(), 3, frames)


class PromptRunnerTests(unittest.TestCase):
    def test_actual_runner_passes_phase_to_model_without_tools(self):
        metadata, frames, _ = s.prepare_bundle(tagged_bundle())
        answer = {"readings": [], "exactParkingSpotKnown": False}
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp)
            (job / "manifest.json").write_text(json.dumps(metadata))
            for i, frame in enumerate(frames):
                (job / f"frame-{i:02d}.jpg").write_bytes(frame["bytes"])
            process = Mock(returncode=0)
            def communicate(prompt, timeout):
                self.assertEqual(timeout, 150)
                self.assertIn(b'"phase": "approach"', prompt)
                self.assertIn(b'"phase": "parked"', prompt)
                self.assertIn(b"not the exact parked location", prompt)
                (job / "answer.json").write_text(json.dumps(answer))
                (job / "codex-events.jsonl").write_text(json.dumps({"type": "turn.completed", "usage": {}}) + "\n")
            process.communicate.side_effect = communicate
            with patch.object(s.subprocess, "Popen", return_value=process) as popen, \
                    patch.object(s, "validate_result", return_value=answer) as validate:
                result = s.run_codex("not-executed", job, len(frames))
            validate.assert_called_once_with(answer, len(frames), metadata["frames"])
            args = popen.call_args.args[0]
            self.assertIn("read-only", args)
            self.assertIn("shell_tool", args)
            self.assertIn("mcp_servers={}", args)
            self.assertEqual(args.count("--image"), 3)
            self.assertEqual(result["analysis"], answer)


class ExplicitCollectorTests(StoreFixture):
    def setUp(self):
        super().setUp()
        self.collector = Collector.__new__(Collector)
        self.collector.service = self.service
        self.collector.not_before = BASE
        self.collector.device = "car"
        self.collector.deferred = {}
        self.frames = snapshots(offsets=(0, 1, 2), phases=["approach", "parked", "parked"])
        self.images = [base64.b64decode(f["imageBase64"]) for f in bundle()["frames"]]
        self.calls = []
        self.transfer_error = None
        self.collector.get = self.get

    def get(self, path, limit):
        if "snapshots?" in path:
            return json.dumps({"snapshots": self.frames}).encode()
        self.calls.append(path)
        if self.transfer_error is not None:
            raise self.transfer_error
        return self.images[int(path[-1]) % len(self.images)]

    def poll(self, offset=300):
        with patch("cloud_collector.time.time", return_value=BASE + offset):
            self.collector.once()

    def count(self, table):
        return self.service.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]

    def test_collection_preserves_event_phase_capture_and_parked_reference(self):
        self.frames.reverse()
        self.poll()
        row = self.service.db.execute("SELECT id,event FROM jobs").fetchone()
        self.assertEqual(row[1], "park-1")
        manifest = json.loads((self.service.root / row[0] / "manifest.json").read_text())
        self.assertEqual(manifest["parkedAt"], iso(2))
        self.assertEqual([f["capturedAt"] for f in manifest["frames"]], [iso(i) for i in range(3)])
        self.assertEqual([f["phase"] for f in manifest["frames"]], ["approach", "parked", "parked"])
        self.service.process_one()
        self.assertEqual(self.service.get(row[0])["result"]["frames"], manifest["frames"])
        self.assertEqual(self.service.get(row[0])["result"]["interpretation"], "nearby_signs_not_exact_parking_space")
        self.poll()
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.count("cloud_frames"), 3)

    def test_partial_then_complete_does_not_consume_early(self):
        full = self.frames
        self.frames = full[:2]
        self.poll()
        self.assertEqual(self.calls, [])
        self.assertEqual(self.count("cloud_frames"), 0)
        self.frames = full
        self.poll()
        self.assertEqual(self.count("jobs"), 1)
        self.assertEqual(self.count("cloud_frames"), 3)

    def test_producer_nine_frames_partial_parked_tail_never_becomes_legacy(self):
        full = snapshots(offsets=(0, 2, 4, 6, 8, 10, 118, 119, 120),
                         phases=["approach"] * 6 + ["parked"] * 3)
        for frame in full:
            frame["capturedAt"] = frame["capturedAt"].replace("+00:00", "Z")
            frame["parking"]["parkedAt"] = frame["parking"]["parkedAt"].replace("+00:00", "Z")
        self.frames = full[-3:]
        self.poll()
        self.assertEqual(self.calls, [])
        self.assertEqual(self.count("jobs"), 0)
        self.assertEqual(self.count("cloud_frames"), 0)
        self.frames = list(reversed(full))
        self.poll()
        job = self.service.db.execute("SELECT id FROM jobs").fetchone()[0]
        manifest = json.loads((self.service.root / job / "manifest.json").read_text())
        self.assertEqual(manifest["parkedAt"], iso(120))
        self.assertEqual([f["phase"] for f in manifest["frames"]], ["approach"] * 6 + ["parked"] * 3)
        self.assertEqual([f["capturedAt"] for f in manifest["frames"]],
                         [iso(i) for i in (0, 2, 4, 6, 8, 10, 118, 119, 120)])
        self.assertEqual(self.count("cloud_frames"), 9)
        self.assertEqual(len(self.calls), 9)
        self.poll()
        self.assertEqual(self.count("jobs"), 1)
        self.assertEqual(len(self.calls), 9)

    def test_malformed_group_skipped_without_blocking_next(self):
        self.frames[0]["parking"]["phase"] = None
        self.frames += snapshots("good", offsets=(100, 101, 102))
        self.poll()
        self.assertEqual(self.count("jobs"), 1)
        self.assertEqual(self.count("cloud_frames"), 3)
        self.assertTrue(all("good-" in path for path in self.calls))

    def test_other_devices_are_never_fetched(self):
        self.frames = snapshots(device="other")
        self.poll()
        self.assertEqual(self.calls, [])
        self.assertEqual(self.count("jobs"), 0)

    def test_changed_event_or_first_member_cannot_reuse_consumed_ids(self):
        self.poll()
        self.frames[0]["id"] = "changed-first-0"
        for frame in self.frames:
            frame["parking"]["eventId"] = "new-event"
        self.poll()
        self.assertEqual(self.count("jobs"), 1)
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.count("cloud_frames"), 4)

    def test_existing_job_after_mark_failure_is_not_submitted_again(self):
        mark = self.collector.mark
        self.collector.mark = Mock(side_effect=RuntimeError("local_write_failure"))
        self.poll()
        self.assertEqual(self.count("jobs"), 1)
        self.assertEqual(self.count("cloud_frames"), 0)
        self.collector.mark = mark
        self.poll(420)
        self.assertEqual(self.count("cloud_frames"), 3)
        self.assertEqual(len(self.calls), 3)

    def test_consumed_ids_survive_restart_and_job_removal(self):
        self.poll()
        self.service.db.execute("DELETE FROM jobs")
        self.service.db.commit()
        self.service.db.close()
        self.service = s.Service(self.config)
        self.collector.service = self.service
        self.collector.deferred = {}
        self.poll()
        self.assertEqual(self.count("jobs"), 0)
        self.assertEqual(len(self.calls), 3)

    def test_transient_fetch_retries_exact_backoff_and_success(self):
        self.transfer_error = TimeoutError()
        self.poll()
        self.poll(419.999999)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.count("cloud_frames"), 0)
        self.transfer_error = None
        self.poll(420)
        self.assertEqual(self.count("jobs"), 1)
        self.assertEqual(self.count("cloud_frames"), 3)

    def test_transient_failures_stop_after_five_attempts(self):
        self.transfer_error = TimeoutError()
        now = 300
        for attempt in range(1, 6):
            self.poll(now)
            self.poll(now)
            self.assertEqual(len(self.calls), attempt)
            now += min(1800, 60 * 2 ** attempt)
        self.assertEqual(self.count("cloud_frames"), 3)
        self.poll(now)
        self.assertEqual(len(self.calls), 5)
        self.assertEqual(self.count("jobs"), 0)

    def test_missing_or_corrupt_image_fails_whole_group_once(self):
        for failure in ("404", "invalid_image", "identical"):
            with self.subTest(failure=failure):
                self.service.db.execute("DELETE FROM cloud_frames")
                self.service.db.commit()
                self.calls.clear()
                self.transfer_error = HTTPError("https://example.invalid", 404, "missing", None, None) if failure == "404" else None
                self.images = [b"not_an_image"] * 3 if failure == "invalid_image" else [self.images[0]] * 3
                if failure == "identical":
                    self.images = [base64.b64decode(bundle()["frames"][0]["imageBase64"])] * 3
                self.poll()
                calls = len(self.calls)
                self.poll(600)
                self.assertEqual(len(self.calls), calls)
                self.assertEqual(self.count("jobs"), 0)
                self.assertEqual(self.count("cloud_frames"), 3)

    def test_queue_daily_limit_retry_and_permanent_conflict(self):
        submit = self.service.submit
        for error in ("queue_full", "daily_limit"):
            with self.subTest(error=error):
                self.collector.deferred.clear()
                self.service.submit = Mock(side_effect=ValueError(error))
                self.poll()
                self.assertEqual(self.count("cloud_frames"), 0)
                self.assertEqual(self.collector.deferred["park-1"][1], 1)
        self.collector.deferred.clear()
        self.service.submit = Mock(side_effect=ValueError("event_conflict"))
        self.poll()
        self.assertEqual(self.count("cloud_frames"), 3)
        self.assertEqual(self.count("jobs"), 0)
        self.service.submit = submit

    def test_phase_changes_conflict_and_manual_retry_keeps_provenance(self):
        value = tagged_bundle()
        job, _ = self.service.submit(value)
        self.assertEqual(self.service.submit(copy.deepcopy(value)), (job, False))
        changed = copy.deepcopy(value)
        changed["frames"][0]["phase"] = "parked"
        with self.assertRaisesRegex(ValueError, "event_conflict"):
            self.service.submit(changed)
        self.service.runner = Mock(side_effect=RuntimeError("model_timeout"))
        self.service.process_one()
        self.assertIsNone(self.service.get(job)["result"])
        self.service.retry(job)
        self.service.runner = lambda *args: {"analysis": {"readings": [], "exactParkingSpotKnown": False}}
        self.service.process_one()
        self.assertEqual([f["phase"] for f in self.service.get(job)["result"]["frames"]],
                         ["approach", "parked", "parked"])


if __name__ == "__main__":
    unittest.main()
