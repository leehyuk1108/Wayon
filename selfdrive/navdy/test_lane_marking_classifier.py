import threading
from types import SimpleNamespace

import numpy as np

try:
  from openpilot.selfdrive.navdy import lane_marking_classifier as classifier
except ModuleNotFoundError:
  import lane_marking_classifier as classifier


def model_line(lateral_m: float, probability: float = 0.9):
  x = np.linspace(0.0, 80.0, 81, dtype=np.float32)
  return SimpleNamespace(
    x=x.tolist(),
    y=np.full_like(x, lateral_m).tolist(),
    z=np.full_like(x, 1.5).tolist(),
    probability=probability,
  )


def request_for_lines(frame_id: int = -1):
  model = SimpleNamespace(
    frameId=frame_id,
    laneLines=[
      model_line(-5.4),
      model_line(-1.8),
      model_line(1.8),
      model_line(5.4),
    ],
    laneLineProbs=[0.9, 0.9, 0.9, 0.9],
  )
  calibration = SimpleNamespace(rpyCalib=[0.0, 0.0, 0.0])
  return classifier.capture_request(model, calibration)


def synthetic_nv12_frame(request, lane_patterns, yellow_lanes):
  width, height, stride = 1344, 760, 1344
  uv_offset = stride * height
  raw = np.empty(uv_offset + stride * (height // 2), dtype=np.uint8)
  raw[:uv_offset] = 58
  raw[uv_offset:] = 128

  for lane_index, line in enumerate(request.lines):
    distances, pixels = classifier.project_line(
      line, request.rpy_calib, width, height)
    for distance, pixel in zip(distances, pixels, strict=True):
      pattern = lane_patterns[lane_index]
      painted = pattern == "solid" or int(distance // 3.0) % 2 == 0
      if not painted:
        continue
      center_x = int(round(float(pixel[0])))
      center_y = int(round(float(pixel[1])))
      for y in range(max(0, center_y - 1), min(height, center_y + 2)):
        for x in range(max(0, center_x - 2), min(width, center_x + 3)):
          raw[y * stride + x] = 225
          uv_index = uv_offset + (y // 2) * stride + (x & ~1)
          if lane_index in yellow_lanes:
            raw[uv_index] = 96
            raw[uv_index + 1] = 148

  return SimpleNamespace(
    width=width,
    height=height,
    stride=stride,
    uv_offset=uv_offset,
    data=memoryview(raw),
  )


def test_profile_classifier_distinguishes_solid_and_dashed():
  solid = np.ones(48, dtype=np.float32)
  dashed = np.tile(np.concatenate((
    np.ones(4, dtype=np.float32),
    np.zeros(4, dtype=np.float32),
  )), 6)
  no_yellow = np.zeros(48, dtype=np.float32)

  assert classifier.classify_profile(solid, no_yellow).pattern == "solid"
  assert classifier.classify_profile(dashed, no_yellow).pattern == "dashed"


def test_profile_classifier_keeps_partially_occluded_solid():
  occluded_solid = np.zeros(48, dtype=np.float32)
  occluded_solid[4:18] = 1.0
  occluded_solid[25:28] = 1.0
  no_yellow = np.zeros(48, dtype=np.float32)

  profile = classifier.classify_profile(occluded_solid, no_yellow)

  assert profile.pattern == "solid"
  assert profile.confidence >= 0.32


def test_profile_classifier_does_not_promote_repeating_dashes():
  repeating_dashes = np.zeros(48, dtype=np.float32)
  repeating_dashes[1:5] = 1.0
  repeating_dashes[10:22] = 1.0
  repeating_dashes[28:33] = 1.0
  repeating_dashes[39:43] = 1.0
  no_yellow = np.zeros(48, dtype=np.float32)

  assert classifier.classify_profile(repeating_dashes, no_yellow).pattern == "dashed"


def test_frame_classifier_reads_white_yellow_solid_and_dashed_lines():
  request = request_for_lines()
  assert request is not None
  frame = synthetic_nv12_frame(
    request,
    lane_patterns=("dashed", "solid", "solid", "dashed"),
    yellow_lanes={1, 3},
  )

  profiles = classifier.classify_frame(request, frame)

  assert [profile.pattern for profile in profiles] == [
    "dashed", "solid", "solid", "dashed",
  ]
  assert profiles[0].yellow_confidence < 0.2
  assert profiles[1].yellow_confidence > 0.48
  assert profiles[2].yellow_confidence < 0.2
  assert profiles[3].yellow_confidence > 0.48


def test_lane_type_keeps_unknown_white_but_preserves_detected_yellow():
  assert classifier.lane_type("solid", False) == "solid"
  assert classifier.lane_type("dashed", True) == "centerDashed"
  assert classifier.lane_type("unknown", False) == "unknown"
  assert classifier.lane_type("unknown", True) == "centerSolid"


def test_yellow_profile_requires_longitudinal_coverage():
  sustained = np.zeros(48, dtype=np.float32)
  sustained[4:14] = 0.8
  sustained[18:28] = 0.8
  sustained[32:42] = 0.8
  transverse = np.zeros(48, dtype=np.float32)
  transverse[18:26] = 1.0

  assert classifier.classify_yellow_profile(sustained) > 0.48
  assert classifier.classify_yellow_profile(transverse) < 0.48


def test_continuous_yellow_pixels_override_false_dashed_luma_pattern():
  dashed_luma = np.tile(np.concatenate((
    np.ones(4, dtype=np.float32),
    np.zeros(4, dtype=np.float32),
  )), 6)
  continuous_yellow = np.ones(48, dtype=np.float32)

  profile = classifier.classify_profile(dashed_luma, continuous_yellow)

  assert profile.pattern == "solid"
  assert profile.yellow_confidence > 0.9


def test_gapped_yellow_pixels_remain_dashed():
  weak_luma = np.zeros(48, dtype=np.float32)
  dashed_yellow = np.tile(np.concatenate((
    np.ones(8, dtype=np.float32),
    np.zeros(4, dtype=np.float32),
  )), 4)

  profile = classifier.classify_profile(weak_luma, dashed_yellow)

  assert profile.pattern == "dashed"
  assert profile.yellow_confidence > 0.48


def test_single_occlusion_does_not_turn_solid_yellow_into_dashes():
  weak_luma = np.zeros(48, dtype=np.float32)
  occluded_yellow = np.concatenate((
    np.ones(18, dtype=np.float32),
    np.zeros(7, dtype=np.float32),
    np.ones(15, dtype=np.float32),
    np.zeros(8, dtype=np.float32),
  ))

  profile = classifier.classify_profile(weak_luma, occluded_yellow)

  assert profile.pattern == "solid"
  assert profile.yellow_confidence > 0.48


def test_unknown_pattern_with_sustained_yellow_renders_solid_yellow():
  worker = object.__new__(classifier.NavdyLaneMarkingClassifier)
  worker._condition = threading.Condition()
  worker._active = True
  worker._result = dict(classifier.UNKNOWN_LANE_TYPES)
  worker._result_at = 0.0
  worker._pattern_scores = np.zeros(4, dtype=np.float32)
  worker._center_scores = np.zeros(4, dtype=np.float32)
  worker._center_last_seen_at = np.zeros(4, dtype=np.float64)
  worker._last_duration_ms = 0.0
  yellow = classifier.LaneProfile("unknown", 0.0, 0.8)
  unknown = classifier.LaneProfile("unknown", 0.0, 0.0)

  for now in (10.0, 10.5, 11.0):
    worker._update_result((unknown, yellow, unknown, unknown), now=now, duration_ms=2.0)

  assert worker._result["navLaneLeftType"] == "centerSolid"


def test_yellow_centerline_survives_short_color_detection_gaps():
  worker = object.__new__(classifier.NavdyLaneMarkingClassifier)
  worker._condition = threading.Condition()
  worker._active = True
  worker._result = dict(classifier.UNKNOWN_LANE_TYPES)
  worker._result_at = 0.0
  worker._pattern_scores = np.zeros(4, dtype=np.float32)
  worker._center_scores = np.zeros(4, dtype=np.float32)
  worker._center_last_seen_at = np.zeros(4, dtype=np.float64)
  worker._last_duration_ms = 0.0
  yellow_solid = classifier.LaneProfile("solid", 1.0, 0.8)
  white_dashed = classifier.LaneProfile("dashed", 1.0, 0.0)
  unknown = classifier.LaneProfile("unknown", 0.0, 0.0)

  for now in (10.0, 10.5, 11.0):
    worker._update_result(
      (unknown, yellow_solid, unknown, unknown), now=now, duration_ms=2.0)
  for now in (11.5, 12.0, 12.5, 13.0):
    worker._update_result(
      (unknown, white_dashed, unknown, unknown), now=now, duration_ms=2.0)
    assert worker._result["navLaneLeftType"] == "centerSolid"

  worker._update_result(
    (unknown, white_dashed, unknown, unknown), now=14.0, duration_ms=2.0)
  assert not worker._result["navLaneLeftType"].startswith("center")


def test_warm_global_color_cast_does_not_turn_white_lines_yellow():
  request = request_for_lines()
  assert request is not None
  frame = synthetic_nv12_frame(
    request,
    lane_patterns=("solid", "solid", "solid", "solid"),
    yellow_lanes=set(),
  )
  raw = np.frombuffer(frame.data, dtype=np.uint8)
  uv = raw[frame.uv_offset:].reshape((-1, frame.stride))
  uv[:, 0::2] = 102
  uv[:, 1::2] = 142

  profiles = classifier.classify_frame(request, frame)

  assert all(profile.yellow_confidence < 0.2 for profile in profiles)


def test_local_contrast_keeps_markings_across_dark_and_bright_exposure():
  request = request_for_lines()
  assert request is not None

  for background, paint in ((25, 47), (160, 190)):
    frame = synthetic_nv12_frame(
      request,
      lane_patterns=("solid", "solid", "solid", "solid"),
      yellow_lanes=set(),
    )
    y_plane = np.frombuffer(
      frame.data, dtype=np.uint8, count=frame.uv_offset)
    y_plane[y_plane == 58] = background
    y_plane[y_plane == 225] = paint

    profiles = classifier.classify_frame(request, frame)

    assert all(profile.pattern == "solid" for profile in profiles)


def test_lane_request_rejects_stale_or_older_camera_frames():
  request = request_for_lines(frame_id=100)
  assert request is not None

  assert classifier.request_matches_frame(request, 100)
  assert classifier.request_matches_frame(request, 102)
  assert not classifier.request_matches_frame(request, 99)
  assert not classifier.request_matches_frame(request, 103)


def test_pattern_hysteresis_ignores_one_conflicting_frame():
  worker = object.__new__(classifier.NavdyLaneMarkingClassifier)
  worker._condition = threading.Condition()
  worker._active = True
  worker._result = dict(classifier.UNKNOWN_LANE_TYPES)
  worker._result_at = 0.0
  worker._pattern_scores = np.zeros(4, dtype=np.float32)
  worker._center_scores = np.zeros(4, dtype=np.float32)
  worker._center_last_seen_at = np.zeros(4, dtype=np.float64)
  worker._last_duration_ms = 0.0
  solid = classifier.LaneProfile("solid", 1.0, 0.0)
  dashed = classifier.LaneProfile("dashed", 1.0, 0.0)
  unknown = classifier.LaneProfile("unknown", 0.0, 0.0)

  for now in (10.0, 10.5, 11.0):
    worker._update_result((unknown, solid, unknown, unknown), now, 2.0)
  assert worker._result["navLaneLeftType"] == "solid"

  worker._update_result((unknown, dashed, unknown, unknown), 11.5, 2.0)
  assert worker._result["navLaneLeftType"] == "solid"


def test_centerline_requires_repeated_color_evidence():
  worker = object.__new__(classifier.NavdyLaneMarkingClassifier)
  worker._condition = threading.Condition()
  worker._active = True
  worker._result = dict(classifier.UNKNOWN_LANE_TYPES)
  worker._result_at = 0.0
  worker._pattern_scores = np.zeros(4, dtype=np.float32)
  worker._center_scores = np.zeros(4, dtype=np.float32)
  worker._center_last_seen_at = np.zeros(4, dtype=np.float64)
  worker._last_duration_ms = 0.0
  yellow = classifier.LaneProfile("solid", 1.0, 0.8)
  unknown = classifier.LaneProfile("unknown", 0.0, 0.0)

  worker._update_result((unknown, yellow, unknown, unknown), 10.0, 2.0)
  assert worker._result["navLaneLeftType"] == "unknown"
  worker._update_result((unknown, yellow, unknown, unknown), 10.5, 2.0)
  assert worker._result["navLaneLeftType"] == "unknown"
  worker._update_result((unknown, yellow, unknown, unknown), 11.0, 2.0)
  assert worker._result["navLaneLeftType"] == "centerSolid"


def test_projection_uses_c4_road_camera_without_full_frame_copy():
  request = request_for_lines()
  assert request is not None
  distances, pixels = classifier.project_line(
    request.lines[1], request.rpy_calib, 1344, 760)

  assert distances.size >= 40
  assert np.isfinite(pixels).all()
  assert np.all((pixels[:, 0] > 0.0) & (pixels[:, 0] < 1344.0))
  assert np.all((pixels[:, 1] > 0.0) & (pixels[:, 1] < 760.0))


def test_finished_sample_cannot_restore_result_after_disengagement():
  worker = object.__new__(classifier.NavdyLaneMarkingClassifier)
  worker._condition = threading.Condition()
  worker._active = False
  worker._result = dict(classifier.UNKNOWN_LANE_TYPES)
  worker._result_at = 0.0
  worker._pattern_scores = np.zeros(4, dtype=np.float32)
  worker._center_scores = np.zeros(4, dtype=np.float32)
  worker._center_last_seen_at = np.zeros(4, dtype=np.float64)
  worker._last_duration_ms = 0.0
  solid = classifier.LaneProfile("solid", 1.0, 0.0)

  worker._update_result((solid, solid, solid, solid), now=10.0, duration_ms=2.0)

  assert worker._result == classifier.UNKNOWN_LANE_TYPES
  assert worker._result_at == 0.0
