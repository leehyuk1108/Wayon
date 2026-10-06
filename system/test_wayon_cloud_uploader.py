#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import requests

# Direct execution starts inside system/, so add openpilot root explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openpilot.system.wayon_cloud_uploader import (device_details_payload, enhance_wide_snapshot, gps_payload, openpilot_details_payload,
                                                   panda_details_payload, resolve_onroad_state,
                                                   upload_pending_impacts, upload_pending_vehicle_events,
                                                   vehicle_details_payload)
from openpilot.system.wayon_impact import enqueue_impact_event, peek_impact_event, peek_impact_events
from openpilot.system.wayon_vehicle_events import door_lock_event, enqueue_vehicle_event, peek_vehicle_event


class FakeSubMaster(dict):
  def __init__(self, gps=None, seen=True, receive_time=0.0):
    super().__init__(gpsLocation=gps, gpsLocationExternal=gps)
    self.seen = {"gpsLocation": seen, "gpsLocationExternal": seen}
    self.recv_time = {"gpsLocation": receive_time, "gpsLocationExternal": receive_time}


def test_wide_snapshot_enhancement_lifts_dark_frames_without_clipping():
  image = np.full((8, 12, 3), 32, dtype=np.uint8)
  image[0, 0] = 255

  enhanced = enhance_wide_snapshot(image)

  assert enhanced.dtype == np.uint8
  assert enhanced.shape == image.shape
  assert np.median(enhanced) >= 68
  assert np.array_equal(enhanced[0, 0], image[0, 0])


def test_wide_snapshot_enhancement_leaves_bright_frames_unchanged():
  image = np.full((8, 12, 3), 96, dtype=np.uint8)
  assert enhance_wide_snapshot(image) is image


def test_started_override_is_authoritative():
  assert resolve_onroad_state(True, False) is False
  assert resolve_onroad_state(False, True) is True
  assert resolve_onroad_state(True) is True


def test_missing_gps_clears_current_location():
  sm = FakeSubMaster(gps=None, seen=False)
  params = SimpleNamespace(get=lambda _key: None)
  assert gps_payload(sm, params) == {"fresh": False, "source": "unavailable"}


def test_stale_gps_clears_current_location():
  gps = SimpleNamespace(
    hasFix=True,
    latitude=37.5,
    longitude=127.0,
    unixTimestampMillis=1,
  )
  sm = FakeSubMaster(gps=gps, receive_time=0.0)
  params = SimpleNamespace(get=lambda _key: None)
  assert gps_payload(sm, params) == {"fresh": False, "source": "unavailable"}


def test_ai_telemetry_helpers_expose_numeric_thermal_power_and_drive_state():
  device = SimpleNamespace(
    deviceType="tici", networkType="wifi", networkStrength="great", networkMetered=False,
    freeSpacePercent=71.5, memoryUsagePercent=42, gpuUsagePercent=5, cpuUsagePercent=[10, 20],
    powerDrawW=8.5, somPowerDrawW=4.2, offroadPowerUsageUwh=2_000_000,
    carBatteryCapacityUwh=18_000_000, cpuTempC=[55.0, 56.0], gpuTempC=[52.0], dspTempC=54.0,
    memoryTempC=50.0, modemTempC=[44.0], pmicTempC=[46.0], intakeTempC=38.0,
    exhaustTempC=42.0, gnssTempC=43.0, bottomSocTempC=51.0, maxTempC=56.0,
    thermalZones=[SimpleNamespace(name="cpu", temp=55.0)], thermalStatus="ok",
    fanSpeedPercentDesired=25, screenBrightnessPercent=60,
  )
  device_payload = device_details_payload(device)
  assert device_payload["thermal"]["temperaturesC"]["max"] == 56.0
  assert device_payload["power"]["offroadUsageWh"] == 2.0

  panda = SimpleNamespace(
    pandaType="tres", ignitionLine=True, ignitionCan=True, voltage=12_400,
    current=800, faultStatus="none", faults=[], uptime=60, heartbeatLost=False,
    interruptLoad=0.2, rxBufferOverflow=0, txBufferOverflow=0, spiErrorCount=0,
    harnessStatus="normal", controlsAllowed=True, controlsAllowedLateral=True,
    controlsAllowedLongitudinal=True, safetyModel="hyundaiCanfd", safetyParam=0,
    safetyRxInvalid=0, safetyTxBlocked=0, safetyRxChecksInvalid=False,
  )
  assert panda_details_payload(panda)["estimatedPowerW"] == 9.92

  cruise = SimpleNamespace(enabled=True, available=True, standstill=False, nonAdaptive=False,
                           speed=27.0, speedCluster=27.0)
  car = SimpleNamespace(
    vEgoCluster=20.0, vEgo=19.8, vEgoRaw=19.9, aEgo=0.1, yawRate=0.01, standstill=False,
    gearShifter="drive", steeringAngleDeg=1.2, steeringRateDeg=0.3, steeringPressed=False,
    gasPressed=False, brakePressed=False, parkingBrake=False, brakeHoldActive=False,
    leftBlinker=False, rightBlinker=True, leftBlindspot=False, rightBlindspot=True,
    doorOpen=False, seatbeltUnlatched=False, fuelGauge=0.6, charging=False,
    canValid=True, canTimeout=False, canErrorCounter=0, steerFaultTemporary=False,
    steerFaultPermanent=False, cruiseState=cruise,
  )
  vehicle = vehicle_details_payload({"carState": car}, True)
  assert vehicle["speedKph"] == 72.0
  assert vehicle["rightBlindspot"] is True

  selfdrive = SimpleNamespace(
    state="enabled", enabled=True, active=True, engageable=True, experimentalMode=False,
    personality="standard", alertText1="", alertText2="", alertType="",
    alertStatus="normal", alertSize="none", alertSound="none", alertHudVisual="none",
  )
  assert openpilot_details_payload({"selfdriveState": selfdrive})["active"] is True


def test_vehicle_event_upload_removes_only_after_success(tmp_path, monkeypatch):
  queue = tmp_path / "vehicle_events.jsonl"
  now = datetime(2026, 7, 20, tzinfo=timezone.utc)
  event = {
    **door_lock_event(False),
    "id": "unlock-event",
    "occurredAt": (now - timedelta(seconds=7)).isoformat().replace("+00:00", "Z"),
  }
  enqueue_vehicle_event(event, queue)
  posted = []

  def fake_post(config, path, payload):
    posted.append((path, payload))
    return {"ok": True}

  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json", fake_post)
  assert upload_pending_vehicle_events(
    {"endpoint": "test", "token": "test"}, "device", queue, now=now) == 1
  assert posted == [("/api/vehicle-event", {**event, "deviceId": "device"})]


def test_vehicle_event_upload_holds_unlock_for_six_seconds(tmp_path, monkeypatch):
  queue = tmp_path / "vehicle_events.jsonl"
  now = datetime(2026, 7, 20, tzinfo=timezone.utc)
  event = {
    **door_lock_event(False),
    "id": "unlock-event",
    "occurredAt": (now - timedelta(seconds=5.9)).isoformat().replace("+00:00", "Z"),
  }
  enqueue_vehicle_event(event, queue)
  posted = []
  monkeypatch.setattr(
    "openpilot.system.wayon_cloud_uploader.post_json",
    lambda config, path, payload: posted.append((path, payload)),
  )

  assert upload_pending_vehicle_events(
    {"endpoint": "test", "token": "test"}, "device", queue, now=now) == 0
  assert posted == []
  assert peek_vehicle_event(queue) == event


def test_vehicle_event_upload_sends_unlock_after_six_seconds(tmp_path, monkeypatch):
  queue = tmp_path / "vehicle_events.jsonl"
  now = datetime(2026, 7, 20, tzinfo=timezone.utc)
  event = {
    **door_lock_event(False),
    "id": "unlock-event",
    "occurredAt": (now - timedelta(seconds=6.1)).isoformat().replace("+00:00", "Z"),
  }
  enqueue_vehicle_event(event, queue)
  posted = []
  monkeypatch.setattr(
    "openpilot.system.wayon_cloud_uploader.post_json",
    lambda config, path, payload: posted.append((path, payload)),
  )

  assert upload_pending_vehicle_events(
    {"endpoint": "test", "token": "test"}, "device", queue, now=now) == 1
  assert [payload["locked"] for _, payload in posted] == [False]
  assert peek_vehicle_event(queue) is None


def test_vehicle_event_upload_sends_pair_relocked_before_four_seconds(tmp_path, monkeypatch):
  queue = tmp_path / "vehicle_events.jsonl"
  now = datetime(2026, 7, 20, tzinfo=timezone.utc)
  unlocked = {
    **door_lock_event(False),
    "id": "unlock-event",
    "occurredAt": (now - timedelta(seconds=3.9)).isoformat().replace("+00:00", "Z"),
  }
  locked = {
    **door_lock_event(True),
    "id": "lock-event",
    "occurredAt": now.isoformat().replace("+00:00", "Z"),
  }
  enqueue_vehicle_event(unlocked, queue)
  enqueue_vehicle_event(locked, queue)
  posted = []
  monkeypatch.setattr(
    "openpilot.system.wayon_cloud_uploader.post_json",
    lambda config, path, payload: posted.append((path, payload)),
  )

  assert upload_pending_vehicle_events(
    {"endpoint": "test", "token": "test"}, "device", queue, now=now) == 2
  assert [payload["locked"] for _, payload in posted] == [False, True]
  assert peek_vehicle_event(queue) is None


def test_vehicle_event_upload_suppresses_pair_relocked_from_four_to_six_seconds(tmp_path, monkeypatch):
  for elapsed_s in (4.0, 4.98, 6.0):
    queue = tmp_path / f"vehicle_events_{elapsed_s}.jsonl"
    suppressed_state = tmp_path / f"suppressed_{elapsed_s}.json"
    now = datetime(2026, 7, 20, tzinfo=timezone.utc)
    unlocked = {
      **door_lock_event(False),
      "id": f"unlock-{elapsed_s}",
      "occurredAt": (now - timedelta(seconds=elapsed_s)).isoformat().replace("+00:00", "Z"),
    }
    locked = {
      **door_lock_event(True),
      "id": f"lock-{elapsed_s}",
      "occurredAt": now.isoformat().replace("+00:00", "Z"),
    }
    enqueue_vehicle_event(unlocked, queue)
    enqueue_vehicle_event(locked, queue)
    posted = []
    monkeypatch.setattr(
      "openpilot.system.wayon_cloud_uploader.post_json",
      lambda config, path, payload: posted.append((path, payload)),
    )
    marker_ms = int((now - timedelta(seconds=elapsed_s + 1.0)).timestamp() * 1000)

    assert upload_pending_vehicle_events(
      {"endpoint": "test", "token": "test"}, "device", queue, now=now,
      suppressed_state_path=suppressed_state,
      fetch_status_fn=lambda config: {"refresh_action": f"CLICKED_AT_{marker_ms}"}) == 0
    assert posted == []
    assert peek_vehicle_event(queue) is None
    suppressed = json.loads(suppressed_state.read_text())
    assert suppressed["elapsedSeconds"] == elapsed_s
    assert suppressed["reason"] == "vehicle_status_refresh"
    assert suppressed["refreshMarker"]["source"] == "refresh_action"


def test_vehicle_event_upload_sends_five_second_pair_without_refresh_marker(tmp_path, monkeypatch):
  queue = tmp_path / "vehicle_events.jsonl"
  now = datetime(2026, 7, 20, tzinfo=timezone.utc)
  unlocked = {
    **door_lock_event(False),
    "id": "unlock-event",
    "occurredAt": (now - timedelta(seconds=4.98)).isoformat().replace("+00:00", "Z"),
  }
  locked = {
    **door_lock_event(True),
    "id": "lock-event",
    "occurredAt": now.isoformat().replace("+00:00", "Z"),
  }
  enqueue_vehicle_event(unlocked, queue)
  enqueue_vehicle_event(locked, queue)
  posted = []
  monkeypatch.setattr(
    "openpilot.system.wayon_cloud_uploader.post_json",
    lambda config, path, payload: posted.append((path, payload)),
  )

  assert upload_pending_vehicle_events(
    {"endpoint": "test", "token": "test"}, "device", queue, now=now,
    fetch_status_fn=lambda config: {}) == 2
  assert [payload["locked"] for _, payload in posted] == [False, True]
  assert peek_vehicle_event(queue) is None


def test_vehicle_event_upload_sends_pair_relocked_after_six_seconds(tmp_path, monkeypatch):
  queue = tmp_path / "vehicle_events.jsonl"
  now = datetime(2026, 7, 20, tzinfo=timezone.utc)
  unlocked = {
    **door_lock_event(False),
    "id": "unlock-event",
    "occurredAt": (now - timedelta(seconds=6.1)).isoformat().replace("+00:00", "Z"),
  }
  locked = {
    **door_lock_event(True),
    "id": "lock-event",
    "occurredAt": now.isoformat().replace("+00:00", "Z"),
  }
  enqueue_vehicle_event(unlocked, queue)
  enqueue_vehicle_event(locked, queue)
  posted = []
  monkeypatch.setattr(
    "openpilot.system.wayon_cloud_uploader.post_json",
    lambda config, path, payload: posted.append((path, payload)),
  )

  assert upload_pending_vehicle_events(
    {"endpoint": "test", "token": "test"}, "device", queue, now=now) == 2
  assert [payload["locked"] for _, payload in posted] == [False, True]
  assert peek_vehicle_event(queue) is None


def test_impact_upload_captures_both_cameras_and_cleans_local_media(tmp_path, monkeypatch):
  queue = tmp_path / "impact_queue.jsonl"
  media_root = tmp_path / "impact_media"
  event = {
    "id": "impact-with-cameras",
    "detectedAt": "2026-07-19T00:00:00Z",
    "severity": "light",
    "captureRequested": True,
  }
  enqueue_impact_event(event, queue)
  posted = []
  operations = []

  def fake_post(config, path, payload):
    operations.append(path)
    posted.append((path, payload))
    return {"ok": True}

  image = np.zeros((8, 12, 3), dtype=np.uint8)
  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json", fake_post)

  def capture():
    operations.append("capture")
    return image, image

  assert upload_pending_impacts(
    {"endpoint": "test", "token": "test"},
    "device",
    queue,
    media_root=media_root,
    capture_fn=capture,
    now=datetime(2026, 7, 19, tzinfo=timezone.utc),
  ) == 1
  assert operations == ["/api/impact", "capture", "/api/impact-media"]
  assert [path for path, _ in posted] == ["/api/impact", "/api/impact-media"]
  assert posted[1][1]["captureStatus"] == "complete"
  assert posted[1][1]["wideJpegBase64"]
  assert posted[1][1]["driverJpegBase64"]
  assert peek_impact_event(queue) is None
  assert not (media_root / "impact-with-cameras").exists()


def test_impact_media_retry_does_not_repost_impact(tmp_path, monkeypatch):
  queue = tmp_path / "impact_queue.jsonl"
  media_root = tmp_path / "impact_media"
  event = {
    "id": "impact-media-retry",
    "detectedAt": "2026-07-19T00:00:00Z",
    "severity": "light",
    "captureRequested": True,
  }
  enqueue_impact_event(event, queue)
  calls = []
  image = np.zeros((8, 12, 3), dtype=np.uint8)

  def failing_media(config, path, payload):
    calls.append(path)
    if path == "/api/impact-media":
      raise RuntimeError("temporary media failure")
    return {"ok": True}

  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json", failing_media)
  now = datetime(2026, 7, 19, tzinfo=timezone.utc)
  try:
    upload_pending_impacts(
      {"endpoint": "test", "token": "test"}, "device", queue,
      media_root=media_root, capture_fn=lambda: (image, image), now=now,
    )
    assert False, "media upload should fail"
  except RuntimeError:
    pass

  queued = peek_impact_event(queue)
  assert queued["impactUploaded"] is True
  assert queued["uploadAttempts"] == 1
  assert queued["nextUploadAt"] == "2026-07-19T00:01:00Z"
  assert calls == ["/api/impact", "/api/impact-media"]

  assert upload_pending_impacts(
    {"endpoint": "test", "token": "test"}, "device", queue,
    media_root=media_root, capture_fn=lambda: (image, image), now=now,
  ) == 0
  assert calls == ["/api/impact", "/api/impact-media"]


def test_suppressed_impact_skips_capture_and_media(tmp_path, monkeypatch):
  queue = tmp_path / "queue.jsonl"
  enqueue_impact_event({"id": "suppressed", "captureRequested": True}, queue)
  calls = []

  def post(config, path, payload):
    calls.append(path)
    return {"ok": True, "suppressed": True}

  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json", post)
  assert upload_pending_impacts({}, "device", queue, media_root=tmp_path / "media",
                               capture_fn=lambda: pytest.fail("suppressed impact must not capture")) == 1
  assert calls == ["/api/impact"]
  assert peek_impact_event(queue) is None


def test_deferred_media_head_cannot_block_new_impact(tmp_path, monkeypatch):
  queue = tmp_path / "queue.jsonl"
  enqueue_impact_event({"id": "old", "impactUploaded": True, "nextUploadAt": "2026-07-19T06:00:00Z"}, queue)
  enqueue_impact_event({"id": "new", "detectedAt": "2026-07-19T00:00:00Z"}, queue)
  calls = []
  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json",
                      lambda config, path, payload: calls.append((path, payload["id"])) or {"ok": True})
  assert upload_pending_impacts({}, "device", queue, limit=1, media_root=tmp_path / "media",
                               now=datetime(2026, 7, 19, tzinfo=timezone.utc)) == 1
  assert calls == [("/api/impact", "new")]
  assert [event["id"] for event in peek_impact_events(queue)] == ["old"]


def test_all_notifications_precede_camera_work(tmp_path, monkeypatch):
  queue = tmp_path / "queue.jsonl"
  now = datetime(2026, 7, 19, tzinfo=timezone.utc)
  for event_id in ("first", "second"):
    enqueue_impact_event({"id": event_id, "detectedAt": now.isoformat(), "captureRequested": True}, queue)
  calls = []
  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json",
                      lambda config, path, payload: calls.append(path) or {"ok": True})

  def capture():
    calls.append("capture")
    return np.zeros((4, 4, 3), dtype=np.uint8), np.zeros((4, 4, 3), dtype=np.uint8)

  assert upload_pending_impacts({}, "device", queue, media_root=tmp_path / "media", capture_fn=capture, now=now) == 2
  assert calls == ["/api/impact", "/api/impact", "capture", "/api/impact-media", "capture", "/api/impact-media"]


def test_failed_event_does_not_block_other_notifications(tmp_path, monkeypatch):
  queue = tmp_path / "queue.jsonl"
  for event_id in ("bad", "good"):
    enqueue_impact_event({"id": event_id}, queue)
  calls = []

  def post(config, path, payload):
    calls.append(payload["id"])
    if payload["id"] == "bad":
      raise RuntimeError("temporary failure")
    return {"ok": True}

  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json", post)
  with pytest.raises(RuntimeError, match="temporary failure"):
    upload_pending_impacts({}, "device", queue, media_root=tmp_path / "media")
  assert calls == ["bad", "good"]
  assert [event["id"] for event in peek_impact_events(queue)] == ["bad"]


def test_capture_exceptions_are_bounded_and_do_not_resend_notification(tmp_path, monkeypatch):
  queue = tmp_path / "queue.jsonl"
  now = datetime(2026, 7, 19, tzinfo=timezone.utc)
  enqueue_impact_event({"id": "camera-fails", "detectedAt": now.isoformat(), "captureRequested": True}, queue)
  calls, captures = [], []
  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json",
                      lambda config, path, payload: calls.append((path, payload)) or {"ok": True})

  def capture():
    captures.append(True)
    raise RuntimeError("camera unavailable")

  for attempt, elapsed in enumerate((0, 60), start=1):
    with pytest.raises(RuntimeError, match="capture incomplete"):
      upload_pending_impacts({}, "device", queue, media_root=tmp_path / "media", capture_fn=capture,
                             now=now + timedelta(seconds=elapsed))
    assert peek_impact_event(queue)["captureAttempts"] == attempt
    assert peek_impact_event(queue)["impactUploaded"] is True

  assert upload_pending_impacts({}, "device", queue, media_root=tmp_path / "media", capture_fn=capture,
                               now=now + timedelta(seconds=360)) == 1
  assert len(captures) == 3
  assert [path for path, _ in calls] == ["/api/impact", "/api/impact-media"]
  assert calls[-1][1]["captureStatus"] == "failed"
  assert calls[-1][1]["captureAttempts"] == 3
  assert peek_impact_event(queue) is None


def test_old_backlog_is_saved_without_taking_misleading_current_photo(tmp_path, monkeypatch):
  queue = tmp_path / "queue.jsonl"
  enqueue_impact_event({"id": "old", "detectedAt": "2026-07-18T00:00:00Z", "captureRequested": True}, queue)
  calls = []
  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json",
                      lambda config, path, payload: calls.append((path, payload)) or {"ok": True, "stale": True})
  assert upload_pending_impacts({}, "device", queue, media_root=tmp_path / "media",
                               capture_fn=lambda: pytest.fail("old impact must not take a current photo"),
                               now=datetime(2026, 7, 19, tzinfo=timezone.utc)) == 1
  assert calls[-1][1]["captureStatus"] == "failed"
  assert calls[-1][1]["captureAttempts"] == 0


@pytest.mark.parametrize("status,error,reset", [(404, "impact_not_found", True), (403, "unauthorized", False),
                                               (404, "other_error", False)])
def test_missing_legacy_record_revalidates_same_event_without_bypassing_auth(tmp_path, monkeypatch, status, error, reset):
  queue = tmp_path / "queue.jsonl"
  now = datetime(2026, 7, 19, tzinfo=timezone.utc)
  enqueue_impact_event({"id": "legacy", "detectedAt": "2026-07-18T00:00:00Z", "impactUploaded": True,
                        "captureRequested": True, "uploadAttempts": 12}, queue)
  response = requests.Response()
  response.status_code = status
  response._content = json.dumps({"error": error}).encode()

  def post(config, path, payload):
    assert path == "/api/impact-media"
    raise requests.HTTPError(response=response)

  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json", post)
  with pytest.raises(requests.HTTPError):
    upload_pending_impacts({}, "device", queue, media_root=tmp_path / "media", now=now)
  event = peek_impact_event(queue)
  assert event["impactUploaded"] is (not reset)
  assert event["uploadAttempts"] == (1 if reset else 13)
  assert event["id"] == "legacy"


if __name__ == "__main__":
  test_started_override_is_authoritative()
  test_missing_gps_clears_current_location()
  test_stale_gps_clears_current_location()
