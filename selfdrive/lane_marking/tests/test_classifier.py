import threading
from types import SimpleNamespace

from openpilot.selfdrive.lane_marking import classifier


def worker(active=True):
  instance = object.__new__(classifier.OnnxLaneMarkingClassifier)
  instance._condition = threading.Condition()
  instance._active = active
  instance.stale_sec = 2.0
  instance._result = dict(classifier.UNKNOWN_LANE_TYPES)
  instance._result_at = 0.0
  instance._scores = {"Left": 0.0, "Right": 0.0}
  instance._last_duration_ms = 0.0
  instance._last_error = ""
  return instance


def test_result_timestamp_is_not_refreshed_by_reading_snapshot():
  instance = worker()
  instance._update_result(result(left="dashed", left_conf=1.0), 12.5, 30.0)

  assert instance.last_result_at() == 12.5
  instance.snapshot(12.6)
  assert instance.last_result_at() == 12.5


def result(left="unknown", right="unknown", left_conf=0.0, right_conf=0.0,
           valid=True, error=""):
  return {
    "leftType": left,
    "rightType": right,
    "leftConf": left_conf,
    "rightConf": right_conf,
    "valid": valid,
    "error": error,
  }


def test_request_keeps_model_frame_synchronization_contract():
  request = classifier.capture_request(
    SimpleNamespace(frameId=100), SimpleNamespace(rpyCalib=[0.0, 0.0, 0.0]))

  assert classifier.request_matches_frame(request, 100)
  assert classifier.request_matches_frame(request, 102)
  assert not classifier.request_matches_frame(request, 99)
  assert not classifier.request_matches_frame(request, 103)


def test_solid_enters_before_dashed_permission():
  instance = worker()

  instance._update_result(result(left="solid", left_conf=0.8), 10.0, 20.0)
  assert instance._result["navLaneLeftType"] == "solid"

  instance = worker()
  for now in (10.0, 10.5):
    instance._update_result(result(left="dashed", left_conf=0.9), now, 20.0)
    assert instance._result["navLaneLeftType"] == "unknown"
  instance._update_result(result(left="dashed", left_conf=0.9), 11.0, 20.0)
  assert instance._result["navLaneLeftType"] == "dashed"


def test_one_dashed_frame_cannot_release_stable_solid():
  instance = worker()
  instance._update_result(result(left="solid", left_conf=1.0), 10.0, 20.0)
  assert instance._result["navLaneLeftType"] == "solid"

  instance._update_result(result(left="dashed", left_conf=1.0), 10.5, 20.0)
  assert instance._result["navLaneLeftType"] != "dashed"


def test_only_adjacent_boundaries_are_published():
  instance = worker()
  for now in (10.0, 10.5, 11.0):
    instance._update_result(
      result(left="dashed", right="solid", left_conf=0.95, right_conf=0.85),
      now, 20.0)

  assert instance._result == {
    "navLaneFarLeftType": "unknown",
    "navLaneLeftType": "dashed",
    "navLaneRightType": "solid",
    "navLaneFarRightType": "unknown",
  }


def test_invalid_inference_does_not_refresh_or_clear_previous_state():
  instance = worker()
  instance._update_result(result(left="solid", left_conf=0.9), 10.0, 20.0)
  previous = dict(instance._result)

  instance._update_result(
    result(valid=False, error="camera unavailable"), 10.5, 1.0)

  assert instance._result == previous
  assert instance._result_at == 10.0
  assert instance.last_error() == "camera unavailable"


def test_snapshot_expires_and_disengagement_discards_finished_sample():
  instance = worker()
  instance.stale_sec = 2.0
  instance._update_result(result(right="solid", right_conf=0.9), 10.0, 20.0)
  assert instance.snapshot(11.9)["navLaneRightType"] == "solid"
  assert instance.snapshot(12.1) == classifier.UNKNOWN_LANE_TYPES

  inactive = worker(active=False)
  inactive._update_result(result(left="solid", left_conf=1.0), 20.0, 20.0)
  assert inactive._result == classifier.UNKNOWN_LANE_TYPES
  assert inactive._result_at == 0.0
