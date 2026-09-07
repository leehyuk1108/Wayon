"""ONNX-backed lane-marking classification for HUD and lane-change safety."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

from openpilot.selfdrive.lane_marking.inference import OnnxLaneInference


LANE_SUFFIXES = ("FarLeft", "Left", "Right", "FarRight")
UNKNOWN_LANE_TYPES = {
  f"navLane{suffix}Type": "unknown" for suffix in LANE_SUFFIXES
}
MAX_FRAME_ID_DELTA = 2
VISION_FRAME_TIMEOUT_MS = 120
VISION_IMPORT_RETRY_SEC = 1.0
MODEL_LOAD_RETRY_SEC = 5.0
SCORE_DECAY = 0.70
SOLID_ALPHA = 0.50
DASHED_ALPHA = 0.30
SOLID_ENTER_THRESHOLD = 0.30
DASHED_ENTER_THRESHOLD = -0.50
SOLID_HOLD_THRESHOLD = 0.10
DASHED_HOLD_THRESHOLD = -0.18


@dataclass(frozen=True)
class LaneMarkingRequest:
  frame_id: int = -1


def capture_request(model_v2: Any, _live_calibration: Any) -> LaneMarkingRequest:
  """Keep the bridge API while ONNX consumes only the synchronized road frame."""
  return LaneMarkingRequest(int(getattr(model_v2, "frameId", -1)))


def request_matches_frame(request: LaneMarkingRequest, frame_id: int) -> bool:
  if request.frame_id < 0 or frame_id < 0:
    return True
  delta = frame_id - request.frame_id
  return 0 <= delta <= MAX_FRAME_ID_DELTA


def _observation(result: dict[str, Any], side: str) -> tuple[str, float]:
  lane_type = str(result.get(f"{side}Type", "unknown"))
  confidence = max(0.0, min(1.0, float(result.get(f"{side}Conf", 0.0))))
  if lane_type not in ("solid", "dashed"):
    return "unknown", 0.0
  return lane_type, confidence


def update_score(score: float, lane_type: str, confidence: float) -> float:
  """Bias temporal filtering toward blocking solid and confirmed dashed."""
  if lane_type == "solid":
    return (1.0 - SOLID_ALPHA) * score + SOLID_ALPHA * confidence
  if lane_type == "dashed":
    return (1.0 - DASHED_ALPHA) * score - DASHED_ALPHA * confidence
  return SCORE_DECAY * score


def score_to_type(score: float, previous: str) -> str:
  if score >= SOLID_ENTER_THRESHOLD:
    return "solid"
  if score <= DASHED_ENTER_THRESHOLD:
    return "dashed"
  if previous == "solid" and score >= SOLID_HOLD_THRESHOLD:
    return "solid"
  if previous == "dashed" and score <= DASHED_HOLD_THRESHOLD:
    return "dashed"
  return "unknown"


class OnnxLaneMarkingClassifier:
  """Latest-only ONNX worker capped to a low fixed inference rate."""

  def __init__(self, interval_sec: float = 0.5, stale_sec: float = 2.0,
               stdout: bool = False, inference_factory=OnnxLaneInference):
    self.interval_sec = max(0.2, float(interval_sec))
    self.stale_sec = max(self.interval_sec * 2.0, float(stale_sec))
    self.stdout = stdout
    self._inference_factory = inference_factory
    self._condition = threading.Condition()
    self._active = False
    self._pending: LaneMarkingRequest | None = None
    self._last_submit_at = 0.0
    self._result = dict(UNKNOWN_LANE_TYPES)
    self._result_at = 0.0
    self._scores = {"Left": 0.0, "Right": 0.0}
    self._last_duration_ms = 0.0
    self._last_error = ""
    self._thread = threading.Thread(
      target=self._run, name="lane_marking_onnx", daemon=True)
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
        self._scores = {"Left": 0.0, "Right": 0.0}
      self._condition.notify()

  def submit(self, model_v2: Any, live_calibration: Any,
             now: float | None = None) -> bool:
    now = time.monotonic() if now is None else now
    with self._condition:
      if not self._active or now - self._last_submit_at < self.interval_sec:
        return False
      self._last_submit_at = now
      self._pending = capture_request(model_v2, live_calibration)
      self._condition.notify()
    return True

  def snapshot(self, now: float | None = None) -> dict[str, str]:
    now = time.monotonic() if now is None else now
    with self._condition:
      if (not self._active or self._result_at <= 0.0 or
          now - self._result_at > self.stale_sec):
        return dict(UNKNOWN_LANE_TYPES)
      return dict(self._result)

  def last_duration_ms(self) -> float:
    with self._condition:
      return self._last_duration_ms

  def last_result_at(self) -> float:
    with self._condition:
      return self._result_at

  def last_error(self) -> str:
    with self._condition:
      return self._last_error

  def _record_error(self, error: str) -> None:
    with self._condition:
      self._last_error = str(error)

  def _update_result(self, result: dict[str, Any], now: float,
                     duration_ms: float) -> None:
    if not bool(result.get("valid", False)):
      self._record_error(str(result.get("error", "ONNX inference failed")))
      return
    with self._condition:
      if not self._active:
        return
      updated = dict(UNKNOWN_LANE_TYPES)
      for side in ("Left", "Right"):
        lane_type, confidence = _observation(result, side.lower())
        score = update_score(self._scores[side], lane_type, confidence)
        self._scores[side] = score
        key = f"navLane{side}Type"
        updated[key] = score_to_type(score, self._result.get(key, "unknown"))
      self._result = updated
      self._result_at = now
      self._last_duration_ms = duration_ms
      self._last_error = ""

  def _run(self) -> None:
    while True:
      try:
        from msgq.visionipc import VisionIpcClient, VisionStreamType
        break
      except Exception as error:
        self._record_error(f"VisionIPC unavailable: {error}")
        if self.stdout:
          print(f"ONNX lane classifier unavailable: {error}", flush=True)
        time.sleep(VISION_IMPORT_RETRY_SEC)

    inference = self._inference_factory()
    client = None
    next_model_load_at = 0.0
    while True:
      with self._condition:
        while not self._active or self._pending is None:
          self._condition.wait()
        request = self._pending
        self._pending = None

      try:
        now = time.monotonic()
        if not inference.valid:
          if now < next_model_load_at:
            continue
          if not inference.load():
            next_model_load_at = now + MODEL_LOAD_RETRY_SEC
            self._record_error(inference.error)
            if self.stdout:
              print(f"ONNX lane model load failed: {inference.error}", flush=True)
            continue
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
        if not request_matches_frame(
            request, int(getattr(client, "frame_id", -1))):
          continue
        started_at = time.monotonic()
        result = inference.infer(frame)
        finished_at = time.monotonic()
        self._update_result(
          result, finished_at, (finished_at - started_at) * 1000.0)
      except Exception as error:
        client = None
        self._record_error(str(error))
        if self.stdout:
          print(f"ONNX lane sample failed: {error}", flush=True)
        time.sleep(0.1)
