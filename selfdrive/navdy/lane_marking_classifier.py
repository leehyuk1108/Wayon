"""Low-rate lane-marking classification for the Navdy HUD.

This module only reads existing model geometry and a shared VisionIPC road
frame. It never publishes into controls or planning services.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import Any

import numpy as np


LANE_SUFFIXES = ("FarLeft", "Left", "Right", "FarRight")
UNKNOWN_LANE_TYPES = {f"navLane{suffix}Type": "unknown" for suffix in LANE_SUFFIXES}

MIN_MODEL_PROBABILITY = 0.05
SAMPLE_START_M = 7.0
SAMPLE_END_M = 42.0
SAMPLE_STEP_M = 0.75
PROFILE_HIT_THRESHOLD = 0.42
YELLOW_HIT_THRESHOLD = 0.1
VISION_FRAME_TIMEOUT_MS = 120

VIEW_FROM_DEVICE = np.array([
  [0.0, 1.0, 0.0],
  [0.0, 0.0, 1.0],
  [1.0, 0.0, 0.0],
], dtype=np.float32)

# Raw road-camera VisionIPC dimensions and focal lengths.
CAMERA_FOCAL_LENGTHS = {
  (1928, 1208): 2648.0,
  (1344, 760): 1522.0 * 0.75,
  (1164, 874): 910.0,
}


@dataclass(frozen=True)
class LaneModelLine:
  x: np.ndarray
  y: np.ndarray
  z: np.ndarray
  probability: float


@dataclass(frozen=True)
class LaneMarkingRequest:
  lines: tuple[LaneModelLine, ...]
  rpy_calib: np.ndarray


@dataclass(frozen=True)
class LaneProfile:
  pattern: str
  confidence: float
  yellow_confidence: float


def clamp01(value: float) -> float:
  return max(0.0, min(1.0, float(value)))


def lane_type(pattern: str, centerline: bool) -> str:
  if centerline:
    return "centerDashed" if pattern == "dashed" else "centerSolid"
  return pattern if pattern in ("solid", "dashed") else "unknown"


def euler_rotation(rpy: np.ndarray) -> np.ndarray:
  roll, pitch, yaw = (float(value) for value in rpy)
  cx, sx = math.cos(roll), math.sin(roll)
  cy, sy = math.cos(pitch), math.sin(pitch)
  cz, sz = math.cos(yaw), math.sin(yaw)
  rx = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]], dtype=np.float32)
  ry = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=np.float32)
  rz = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)
  return rz @ ry @ rx


def camera_intrinsics(width: int, height: int) -> np.ndarray:
  focal_length = CAMERA_FOCAL_LENGTHS.get((width, height))
  if focal_length is None:
    # Preserve both known camera families when a scaled stream is exposed.
    focal_length = width * (0.85 if width / max(height, 1) > 1.7 else 1.37)
  return np.array([
    [focal_length, 0.0, width * 0.5],
    [0.0, focal_length, height * 0.5],
    [0.0, 0.0, 1.0],
  ], dtype=np.float32)


def capture_request(model_v2: Any, live_calibration: Any) -> LaneMarkingRequest | None:
  rpy = np.asarray(list(getattr(live_calibration, "rpyCalib", [])), dtype=np.float32)
  lane_lines = list(getattr(model_v2, "laneLines", []))
  lane_probs = list(getattr(model_v2, "laneLineProbs", []))
  if rpy.shape != (3,) or not np.isfinite(rpy).all() or len(lane_lines) < 4:
    return None

  output = []
  for index, line in enumerate(lane_lines[:4]):
    x = np.asarray(list(getattr(line, "x", [])), dtype=np.float32)
    y = np.asarray(list(getattr(line, "y", [])), dtype=np.float32)
    z = np.asarray(list(getattr(line, "z", [])), dtype=np.float32)
    size = min(x.size, y.size, z.size)
    if size < 4:
      return None
    points = np.column_stack((x[:size], y[:size], z[:size]))
    points = points[np.isfinite(points).all(axis=1)]
    points = points[(points[:, 0] >= 0.0) & (points[:, 0] <= 80.0)]
    if points.shape[0] < 4:
      return None
    order = np.argsort(points[:, 0])
    points = points[order]
    unique_x, unique_indices = np.unique(points[:, 0], return_index=True)
    if unique_x.size < 4:
      return None
    points = points[unique_indices]
    probability = float(lane_probs[index]) if index < len(lane_probs) else 0.0
    output.append(LaneModelLine(
      x=points[:, 0].copy(),
      y=points[:, 1].copy(),
      z=points[:, 2].copy(),
      probability=clamp01(probability),
    ))
  return LaneMarkingRequest(tuple(output), rpy.copy())


def project_line(line: LaneModelLine, rpy_calib: np.ndarray,
                 width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
  sample_end = min(SAMPLE_END_M, float(line.x[-1]))
  if sample_end < SAMPLE_START_M + 6.0:
    return np.empty((0,), dtype=np.float32), np.empty((0, 2), dtype=np.float32)
  distances = np.arange(SAMPLE_START_M, sample_end + 0.01, SAMPLE_STEP_M, dtype=np.float32)
  y = np.interp(distances, line.x, line.y)
  z = np.interp(distances, line.x, line.z)
  points = np.column_stack((distances, y, z)).astype(np.float32)

  transform = camera_intrinsics(width, height) @ VIEW_FROM_DEVICE @ euler_rotation(rpy_calib)
  projected = transform @ points.T
  depth = projected[2]
  valid = depth > 1e-3
  pixels = np.empty((distances.size, 2), dtype=np.float32)
  pixels.fill(np.nan)
  pixels[valid] = (projected[:2, valid] / depth[valid]).T
  valid &= (
    (pixels[:, 0] >= 3.0) & (pixels[:, 0] < width - 3.0) &
    (pixels[:, 1] >= 2.0) & (pixels[:, 1] < height - 2.0)
  )
  return distances[valid], pixels[valid]


def clean_occupancy(mask: np.ndarray) -> np.ndarray:
  if mask.size < 3:
    return mask.copy()
  cleaned = mask.copy()
  cleaned[1:-1] |= mask[:-2] & mask[2:]
  joined = cleaned.copy()
  cleaned[1:-1] &= joined[:-2] | joined[2:]
  return cleaned


def boolean_runs(mask: np.ndarray) -> list[tuple[bool, int]]:
  if mask.size == 0:
    return []
  runs = []
  value = bool(mask[0])
  length = 1
  for current in mask[1:]:
    current_value = bool(current)
    if current_value == value:
      length += 1
    else:
      runs.append((value, length))
      value = current_value
      length = 1
  runs.append((value, length))
  return runs


def classify_yellow_marking(yellow_scores: np.ndarray) -> tuple[str, float]:
  yellow_scores = np.asarray(yellow_scores, dtype=np.float32)
  if yellow_scores.size < 12:
    return "unknown", 0.0

  occupancy = clean_occupancy(yellow_scores >= YELLOW_HIT_THRESHOLD)
  hit_count = int(np.count_nonzero(occupancy))
  runs = boolean_runs(occupancy)
  hit_runs = [length for value, length in runs if value]
  internal_gap_runs = [
    length for index, (value, length) in enumerate(runs)
    if not value and 0 < index < len(runs) - 1
  ]
  longest_hit = max(
    hit_runs,
    default=0,
  )

  # A longitudinal marking covers many distance samples and has at least one
  # sustained run. Short transverse markings such as crosswalk bars do not.
  coverage_score = clamp01((hit_count - 12) / 12.0)
  continuity_score = clamp01((longest_hit - 5) / 5.0)
  confidence = coverage_score * continuity_score
  if confidence <= 0.0:
    return "unknown", 0.0

  longest_gap = max(internal_gap_runs, default=0)
  # One interrupted solid line commonly becomes two runs when a lead vehicle,
  # shadow, or road repair hides part of it. Require a repeating pattern before
  # declaring a yellow marking dashed.
  if len(hit_runs) <= 2 or longest_gap <= 2:
    return "solid", confidence
  if len(hit_runs) >= 3 and longest_gap >= 3:
    return "dashed", confidence
  return "unknown", confidence


def classify_yellow_profile(yellow_scores: np.ndarray) -> float:
  return classify_yellow_marking(yellow_scores)[1]


def classify_profile(strengths: np.ndarray, yellow_scores: np.ndarray) -> LaneProfile:
  strengths = np.asarray(strengths, dtype=np.float32)
  yellow_scores = np.asarray(yellow_scores, dtype=np.float32)
  if strengths.size < 12 or yellow_scores.size != strengths.size:
    return LaneProfile("unknown", 0.0, 0.0)

  occupancy = clean_occupancy(strengths >= PROFILE_HIT_THRESHOLD)
  runs = boolean_runs(occupancy)
  hit_runs = [length for value, length in runs if value]
  internal_gap_runs = [
    length for index, (value, length) in enumerate(runs)
    if not value and 0 < index < len(runs) - 1
  ]
  occupancy_ratio = float(np.mean(occupancy))
  longest_gap = max(internal_gap_runs, default=0)

  pattern = "unknown"
  confidence = 0.0
  if occupancy_ratio >= 0.68 and (
      longest_gap <= 3 or (occupancy_ratio >= 0.8 and len(internal_gap_runs) <= 1)):
    pattern = "solid"
    confidence = clamp01((occupancy_ratio - 0.58) / 0.32)
  elif (0.16 <= occupancy_ratio <= 0.76 and len(hit_runs) >= 2 and
        longest_gap >= 2 and len(runs) >= 4):
    pattern = "dashed"
    periodicity = min(1.0, (len(hit_runs) - 1) / 3.0)
    gap_strength = min(1.0, longest_gap / 4.0)
    confidence = clamp01(0.35 + 0.35 * periodicity + 0.3 * gap_strength)

  yellow_pattern, yellow_confidence = classify_yellow_marking(yellow_scores)
  if yellow_confidence >= 0.48 and yellow_pattern in ("solid", "dashed"):
    pattern = yellow_pattern
    confidence = max(confidence, yellow_confidence)
  return LaneProfile(pattern, confidence, yellow_confidence)


def sample_profile(frame: Any, line: LaneModelLine,
                   rpy_calib: np.ndarray) -> LaneProfile:
  if line.probability < MIN_MODEL_PROBABILITY:
    return LaneProfile("unknown", 0.0, 0.0)

  width = int(frame.width)
  height = int(frame.height)
  stride = int(frame.stride)
  uv_offset = int(frame.uv_offset)
  raw = np.frombuffer(frame.data, dtype=np.uint8)
  uv_height = (height + 1) // 2
  if (width <= 0 or height <= 0 or stride < width or
      raw.size < uv_offset + stride * uv_height):
    return LaneProfile("unknown", 0.0, 0.0)
  y_plane_size = stride * height
  if raw.size < y_plane_size:
    return LaneProfile("unknown", 0.0, 0.0)
  y_plane = raw[:y_plane_size].reshape((height, stride))
  uv_plane = raw[uv_offset:uv_offset + stride * uv_height].reshape((uv_height, stride))

  distances, pixels = project_line(line, rpy_calib, width, height)
  if distances.size < 12:
    return LaneProfile("unknown", 0.0, 0.0)

  strengths = np.zeros(distances.size, dtype=np.float32)
  yellow_scores = np.zeros(distances.size, dtype=np.float32)
  for index, (distance, pixel) in enumerate(zip(distances, pixels, strict=True)):
    center_x = int(round(float(pixel[0])))
    center_y = int(round(float(pixel[1])))
    search_half = int(round(np.interp(distance, [SAMPLE_START_M, SAMPLE_END_M], [16.0, 5.0])))
    left = max(0, center_x - search_half)
    right = min(width, center_x + search_half + 1)
    top = max(0, center_y - 1)
    bottom = min(height, center_y + 2)
    patch = y_plane[top:bottom, left:right]
    if patch.size < 6:
      continue

    flat_index = int(np.argmax(patch))
    patch_y, patch_x = np.unravel_index(flat_index, patch.shape)
    max_luma = float(patch[patch_y, patch_x])
    background = float(np.median(patch))
    contrast_score = clamp01((max_luma - background - 10.0) / 35.0)
    brightness_score = clamp01((max_luma - 55.0) / 110.0)
    strengths[index] = 0.78 * contrast_score + 0.22 * brightness_score

    # Yellow paint is often darker than white paint at night, so inspect its
    # chroma independently instead of only checking the brightest pixel.
    yellow_half = int(round(np.interp(
      distance, [SAMPLE_START_M, SAMPLE_END_M], [28.0, 8.0])))
    yellow_left = max(0, center_x - yellow_half)
    yellow_right = min(width, center_x + yellow_half + 1)
    yellow_top = max(0, center_y - 2)
    yellow_bottom = min(height, center_y + 3)
    pair_left = yellow_left & ~1
    pair_right = min(width - 2, (yellow_right - 1) & ~1)
    if pair_right < pair_left or yellow_bottom <= yellow_top:
      continue

    pair_x = np.arange(pair_left, pair_right + 1, 2)
    yellow_patch = y_plane[yellow_top:yellow_bottom, yellow_left:yellow_right]
    yellow_background = float(np.median(yellow_patch))
    pair_luma = np.maximum(
      np.max(y_plane[yellow_top:yellow_bottom, pair_x], axis=0),
      np.max(y_plane[yellow_top:yellow_bottom, pair_x + 1], axis=0),
    ).astype(np.float32)
    uv_rows = np.arange(
      yellow_top // 2,
      min(uv_height - 1, (yellow_bottom - 1) // 2) + 1,
    )
    u = uv_plane[uv_rows[:, None], pair_x[None, :]].astype(np.float32)
    v = uv_plane[uv_rows[:, None], (pair_x + 1)[None, :]].astype(np.float32)
    chroma = np.max(
      np.clip((v - u - 8.0) / 30.0, 0.0, 1.0) *
      np.clip((132.0 - u) / 28.0, 0.0, 1.0),
      axis=0,
    )
    yellow_luma = np.clip(
      (pair_luma - yellow_background - 2.0) / 20.0, 0.0, 1.0)
    yellow_scores[index] = float(np.max(chroma * yellow_luma))

  return classify_profile(strengths, yellow_scores)


def classify_frame(request: LaneMarkingRequest, frame: Any) -> tuple[LaneProfile, ...]:
  return tuple(sample_profile(frame, line, request.rpy_calib) for line in request.lines)


class NavdyLaneMarkingClassifier:
  """Latest-only asynchronous VisionIPC sampler capped to a low fixed rate."""

  def __init__(self, interval_sec: float = 0.5, stale_sec: float = 2.0,
               stdout: bool = False):
    self.interval_sec = max(0.2, float(interval_sec))
    self.stale_sec = max(self.interval_sec * 2.0, float(stale_sec))
    self.stdout = stdout
    self._condition = threading.Condition()
    self._active = False
    self._pending: LaneMarkingRequest | None = None
    self._last_submit_at = 0.0
    self._result = dict(UNKNOWN_LANE_TYPES)
    self._result_at = 0.0
    self._pattern_scores = np.zeros(4, dtype=np.float32)
    self._center_scores = np.zeros(4, dtype=np.float32)
    self._last_duration_ms = 0.0
    self._thread = threading.Thread(
      target=self._run, name="navdy_lane_marking", daemon=True)
    self._thread.start()

  def is_alive(self) -> bool:
    return self._thread.is_alive()

  def set_active(self, active: bool) -> None:
    with self._condition:
      active = bool(active)
      if self._active == active:
        return
      self._active = active
      if not active:
        self._pending = None
        self._result = dict(UNKNOWN_LANE_TYPES)
        self._result_at = 0.0
        self._pattern_scores.fill(0.0)
        self._center_scores.fill(0.0)
      self._condition.notify()

  def submit(self, model_v2: Any, live_calibration: Any,
             now: float | None = None) -> bool:
    now = time.monotonic() if now is None else now
    with self._condition:
      if not self._active or now - self._last_submit_at < self.interval_sec:
        return False
      self._last_submit_at = now
    request = capture_request(model_v2, live_calibration)
    if request is None:
      return False
    with self._condition:
      if not self._active:
        return False
      self._pending = request
      self._condition.notify()
    return True

  def snapshot(self, now: float | None = None) -> dict[str, str]:
    now = time.monotonic() if now is None else now
    with self._condition:
      if not self._active or self._result_at <= 0.0 or now - self._result_at > self.stale_sec:
        return dict(UNKNOWN_LANE_TYPES)
      return dict(self._result)

  def last_duration_ms(self) -> float:
    with self._condition:
      return self._last_duration_ms

  def _update_result(self, profiles: tuple[LaneProfile, ...], now: float,
                     duration_ms: float) -> None:
    with self._condition:
      if not self._active:
        return
      result = {}
      alpha = 0.45
      for index, suffix in enumerate(LANE_SUFFIXES):
        profile = profiles[index] if index < len(profiles) else LaneProfile("unknown", 0.0, 0.0)
        if profile.pattern == "solid":
          pattern_target = profile.confidence
        elif profile.pattern == "dashed":
          pattern_target = -profile.confidence
        else:
          pattern_target = None
        if pattern_target is None:
          self._pattern_scores[index] *= 0.88
        else:
          self._pattern_scores[index] = (
            (1.0 - alpha) * self._pattern_scores[index] + alpha * pattern_target)

        if profile.yellow_confidence >= 0.48:
          center_target = profile.yellow_confidence
        elif profile.pattern != "unknown":
          center_target = -profile.confidence
        else:
          center_target = None
        if center_target is None:
          self._center_scores[index] *= 0.88
        else:
          self._center_scores[index] = (
            (1.0 - alpha) * self._center_scores[index] + alpha * center_target)

        pattern_score = float(self._pattern_scores[index])
        pattern = "solid" if pattern_score >= 0.24 else (
          "dashed" if pattern_score <= -0.24 else "unknown")
        centerline = float(self._center_scores[index]) >= 0.28
        result[f"navLane{suffix}Type"] = lane_type(pattern, centerline)

      self._result = result
      self._result_at = now
      self._last_duration_ms = duration_ms

  def _run(self) -> None:
    try:
      from msgq.visionipc import VisionIpcClient, VisionStreamType
    except Exception as error:
      if self.stdout:
        print(f"navdy lane classifier unavailable: {error}", flush=True)
      return

    client = None
    while True:
      with self._condition:
        while not self._active or self._pending is None:
          self._condition.wait()
        request = self._pending
        self._pending = None

      try:
        if client is None:
          client = VisionIpcClient(
            "camerad", VisionStreamType.VISION_STREAM_ROAD, conflate=True)
          if not client.connect(False):
            client = None
            time.sleep(0.1)
            continue
        frame = client.recv(timeout_ms=VISION_FRAME_TIMEOUT_MS)
        if frame is None:
          continue
        started_at = time.monotonic()
        profiles = classify_frame(request, frame)
        finished_at = time.monotonic()
        self._update_result(
          profiles, finished_at, (finished_at - started_at) * 1000.0)
      except Exception as error:
        client = None
        if self.stdout:
          print(f"navdy lane classifier sample failed: {error}", flush=True)
        time.sleep(0.1)
