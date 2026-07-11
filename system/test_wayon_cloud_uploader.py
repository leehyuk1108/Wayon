#!/usr/bin/env python3
import sys
from pathlib import Path
from types import SimpleNamespace

# Direct execution starts inside system/, so add openpilot root explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from system.wayon_cloud_uploader import gps_payload, resolve_onroad_state


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
  assert gps_payload(sm) == {"fresh": False, "source": "unavailable"}


def test_stale_gps_clears_current_location():
  gps = SimpleNamespace(
    hasFix=True,
    latitude=37.5,
    longitude=127.0,
    unixTimestampMillis=1,
  )
  sm = FakeSubMaster(gps=gps, receive_time=0.0)
  assert gps_payload(sm) == {"fresh": False, "source": "unavailable"}


if __name__ == "__main__":
  test_started_override_is_authoritative()
  test_missing_gps_clears_current_location()
  test_stale_gps_clears_current_location()
