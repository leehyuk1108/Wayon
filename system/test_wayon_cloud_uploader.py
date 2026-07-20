#!/usr/bin/env python3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np

# Direct execution starts inside system/, so add openpilot root explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openpilot.system.wayon_cloud_uploader import (device_details_payload, gps_payload, openpilot_details_payload,
                                                   panda_details_payload, resolve_onroad_state,
                                                   upload_pending_impacts, upload_pending_vehicle_events,
                                                   vehicle_details_payload)
from openpilot.system.wayon_impact import enqueue_impact_event, peek_impact_event
from openpilot.system.wayon_vehicle_events import door_lock_event, enqueue_vehicle_event, peek_vehicle_event


class FakeSubMaster(dict):
  def __init__(self, gps=None, seen=True, receive_time=0.0):
    super().__init__(gpsLocation=gps, gpsLocationExternal=gps)
    self.seen = {"gpsLocation": seen, "gpsLocationExternal": seen}
    self.recv_time = {"gpsLocation": receive_time, "gpsLocationExternal": receive_time}


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
    "occurredAt": (now - timedelta(seconds=6)).isoformat().replace("+00:00", "Z"),
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


def test_vehicle_event_upload_holds_recent_unlock_for_wake_pair(tmp_path, monkeypatch):
  queue = tmp_path / "vehicle_events.jsonl"
  now = datetime(2026, 7, 20, tzinfo=timezone.utc)
  event = {
    **door_lock_event(False),
    "id": "unlock-event",
    "occurredAt": (now - timedelta(seconds=4)).isoformat().replace("+00:00", "Z"),
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


def test_vehicle_event_upload_suppresses_five_second_telemetry_wake_pair(tmp_path, monkeypatch):
  queue = tmp_path / "vehicle_events.jsonl"
  now = datetime(2026, 7, 20, tzinfo=timezone.utc)
  unlocked = {
    **door_lock_event(False),
    "id": "unlock-event",
    "occurredAt": (now - timedelta(seconds=7)).isoformat().replace("+00:00", "Z"),
  }
  locked = {
    **door_lock_event(True),
    "id": "lock-event",
    "occurredAt": (now - timedelta(seconds=2.02)).isoformat().replace("+00:00", "Z"),
  }
  enqueue_vehicle_event(unlocked, queue)
  enqueue_vehicle_event(locked, queue)
  posted = []
  monkeypatch.setattr(
    "openpilot.system.wayon_cloud_uploader.post_json",
    lambda config, path, payload: posted.append((path, payload)),
  )

  assert upload_pending_vehicle_events(
    {"endpoint": "test", "token": "test"}, "device", queue, now=now) == 0
  assert posted == []
  assert peek_vehicle_event(queue) is None


def test_vehicle_event_upload_keeps_manual_pair_outside_wake_signature(tmp_path, monkeypatch):
  queue = tmp_path / "vehicle_events.jsonl"
  now = datetime(2026, 7, 20, tzinfo=timezone.utc)
  unlocked = {
    **door_lock_event(False),
    "id": "unlock-event",
    "occurredAt": (now - timedelta(seconds=12)).isoformat().replace("+00:00", "Z"),
  }
  locked = {
    **door_lock_event(True),
    "id": "lock-event",
    "occurredAt": (now - timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
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


def test_vehicle_event_upload_keeps_short_manual_pair(tmp_path, monkeypatch):
  queue = tmp_path / "vehicle_events.jsonl"
  now = datetime(2026, 7, 20, tzinfo=timezone.utc)
  unlocked = {
    **door_lock_event(False),
    "id": "unlock-event",
    "occurredAt": (now - timedelta(seconds=8)).isoformat().replace("+00:00", "Z"),
  }
  locked = {
    **door_lock_event(True),
    "id": "lock-event",
    "occurredAt": (now - timedelta(seconds=3.865)).isoformat().replace("+00:00", "Z"),
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

  def fake_post(config, path, payload):
    posted.append((path, payload))
    return {"ok": True}

  image = np.zeros((8, 12, 3), dtype=np.uint8)
  monkeypatch.setattr("openpilot.system.wayon_cloud_uploader.post_json", fake_post)

  assert upload_pending_impacts(
    {"endpoint": "test", "token": "test"},
    "device",
    queue,
    media_root=media_root,
    capture_fn=lambda: (image, image),
  ) == 1
  assert [path for path, _ in posted] == ["/api/impact", "/api/impact-media"]
  assert posted[1][1]["captureStatus"] == "complete"
  assert posted[1][1]["wideJpegBase64"]
  assert posted[1][1]["driverJpegBase64"]
  assert peek_impact_event(queue) is None
  assert not (media_root / "impact-with-cameras").exists()


if __name__ == "__main__":
  test_started_override_is_authoritative()
  test_missing_gps_clears_current_location()
  test_stale_gps_clears_current_location()
