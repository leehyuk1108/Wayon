from pathlib import Path

from openpilot.system.wayon_impact import (
  DoorLockTracker,
  ImpactDetector,
  append_impact_diagnostic,
  enqueue_impact_event,
  peek_impact_event,
  remove_impact_event,
  update_impact_event,
)

GRAVITY = (0.0, 0.0, 9.80665)
STILL_GYRO = (0.0, 0.0, 0.0)


def prime(detector: ImpactDetector, start: float = 0.0) -> float:
  now = start
  for _ in range(50):
    detector.update(GRAVITY, STILL_GYRO, now)
    now += 0.01
  return now


def test_detector_ignores_motion_before_arm_delay():
  detector = ImpactDetector(arm_delay_s=10.0, warmup_s=0.0)
  detector.update(GRAVITY, STILL_GYRO, 0.0)

  assert detector.update((8.0, 0.0, 9.80665), STILL_GYRO, 1.0) is None
  assert not detector.armed


def test_detector_ignores_small_vibration():
  detector = ImpactDetector(arm_delay_s=0.0, warmup_s=0.0)
  now = prime(detector)

  for index in range(100):
    vibration = 0.1 if index % 2 else -0.1
    assert detector.update((vibration, 0.0, 9.80665), STILL_GYRO, now) is None
    now += 0.01


def test_detector_ignores_measured_offroad_noise():
  detector = ImpactDetector(arm_delay_s=0.0, warmup_s=0.0)
  now = prime(detector)

  for index in range(200):
    noise = 0.02 if index % 2 else -0.02
    assert detector.update((noise, 0.0, 9.80665), (0.0, 0.01, 0.0), now) is None
    now += 0.01

  assert detector.last_dynamic_g < 0.01


def test_detector_confirms_two_sample_impact():
  detector = ImpactDetector(
    arm_delay_s=0.0,
    warmup_s=0.0,
    impulse_dynamic_g=2.0,
    strong_dynamic_g=2.0,
  )
  now = prime(detector)

  assert detector.update((4.5, 0.0, 9.80665), (0.0, 0.2, 0.0), now) is None
  event = detector.update((5.0, 0.0, 9.80665), (0.0, 0.3, 0.0), now + 0.01)

  assert event is not None
  assert event["severity"] == "light"
  assert event["peakDynamicG"] >= 0.45
  assert event["sampleCount"] == 2


def test_detector_catches_light_parking_impact_at_new_threshold():
  detector = ImpactDetector(arm_delay_s=0.0, warmup_s=0.0)
  now = prime(detector)

  event = detector.update((2.05, 0.0, 9.80665), STILL_GYRO, now)

  assert event is not None
  assert 0.20 <= event["peakDynamicG"] < 0.30


def test_detector_catches_measured_single_sample_parking_impact():
  detector = ImpactDetector(arm_delay_s=0.0, warmup_s=0.0)
  now = prime(detector)

  # The parked comma measured 0.0663 g and 11.49 g/s during a deliberate body impact.
  assert detector.update((-0.48, 0.0, 9.80665), STILL_GYRO, now) is None
  event = detector.update((0.65, 0.0, 9.80665), STILL_GYRO, now + 0.01)

  assert event is not None
  assert event["severity"] == "light"
  assert 0.06 <= event["peakDynamicG"] < 0.07
  assert event["peakJerkGPerSec"] >= 8.0


def test_detector_rejects_slow_body_motion_at_similar_dynamic_g():
  detector = ImpactDetector(arm_delay_s=0.0, warmup_s=0.0)
  now = prime(detector)

  assert detector.update((0.45, 0.0, 9.80665), STILL_GYRO, now) is None
  assert detector.update((0.55, 0.0, 9.80665), STILL_GYRO, now + 0.1) is None


def test_detector_suppresses_impact_while_detection_disabled():
  detector = ImpactDetector(arm_delay_s=0.0, warmup_s=0.0)
  now = prime(detector)

  assert detector.update((2.5, 0.0, 9.80665), STILL_GYRO, now, detection_enabled=False) is None
  assert detector.update((2.6, 0.0, 9.80665), STILL_GYRO, now + 0.01, detection_enabled=False) is None


def test_door_lock_tracker_requires_locked_state_and_persists(tmp_path: Path):
  state_path = tmp_path / "door_lock_status.json"
  tracker = DoorLockTracker(required=True, arm_delay_s=3.0, state_path=state_path)

  assert not tracker.detection_allowed(10.0)
  assert tracker.update(0, 0x130, bytes.fromhex("020000"), 10.0)
  assert tracker.locked is False
  assert not tracker.detection_allowed(20.0)

  assert tracker.update(0, 0x130, bytes.fromhex("040000"), 20.0)
  assert tracker.locked is True
  assert not tracker.update(0, 0x130, bytes.fromhex("010000"), 21.0)
  assert tracker.locked is True
  assert not tracker.detection_allowed(22.9)
  assert tracker.detection_allowed(23.0)

  restored = DoorLockTracker(required=True, arm_delay_s=3.0, state_path=state_path)
  assert restored.locked is True
  assert restored.detection_allowed(0.0)


def test_door_lock_tracker_ignores_other_can_frames(tmp_path: Path):
  tracker = DoorLockTracker(required=True, state_path=tmp_path / "state.json")

  assert not tracker.update(1, 0x130, bytes(8), 0.0)
  assert not tracker.update(0, 0x123, bytes(8), 0.0)
  assert not tracker.update(0, 0x130, bytes(0), 0.0)
  assert tracker.locked is None


def test_update_impact_event_preserves_queue_order(tmp_path: Path):
  queue = tmp_path / "impact_queue.jsonl"
  enqueue_impact_event({"id": "first", "severity": "light"}, queue)
  enqueue_impact_event({"id": "second", "severity": "moderate"}, queue)

  updated = update_impact_event("first", {"captureAttempts": 1}, queue)

  assert updated == {"id": "first", "severity": "light", "captureAttempts": 1}
  assert peek_impact_event(queue) == updated
  assert remove_impact_event("first", queue)
  assert peek_impact_event(queue) == {"id": "second", "severity": "moderate"}


def test_detector_uses_cooldown_after_strong_impact():
  detector = ImpactDetector(arm_delay_s=0.0, warmup_s=0.0, cooldown_s=30.0)
  now = prime(detector)

  first = detector.update((10.0, 0.0, 9.80665), STILL_GYRO, now)
  second = detector.update((-10.0, 0.0, 9.80665), STILL_GYRO, now + 1.0)

  assert first is not None
  assert second is None


def test_impact_queue_round_trip(tmp_path: Path):
  queue = tmp_path / "impact_queue.jsonl"
  first = {"id": "first", "peakDynamicG": 0.5}
  second = {"id": "second", "peakDynamicG": 0.8}

  enqueue_impact_event(first, queue)
  enqueue_impact_event(second, queue)
  assert peek_impact_event(queue) == first
  assert remove_impact_event("first", queue)
  assert peek_impact_event(queue) == second
  assert remove_impact_event("second", queue)
  assert peek_impact_event(queue) is None


def test_impact_diagnostics_append_and_rotate(tmp_path: Path):
  diagnostics = tmp_path / "impact_diagnostics.jsonl"
  for index in range(100):
    append_impact_diagnostic({"index": index, "peakDynamicG": index / 100.0}, diagnostics, max_bytes=1024)

  lines = diagnostics.read_text().splitlines()
  assert lines
  assert '"index":99' in lines[-1]
  assert diagnostics.stat().st_size <= 1024
