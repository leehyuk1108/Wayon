"""ONNX lane-marking inference used by comma lane-change safety.

The model and output decoder originate from jixiexiaoge's CarrotPilot ONNX
lane detector.  Only solid/dashed classification is consumed here; lane
geometry continues to come from modelV2.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "lane.onnx"
INPUT_SIZE = 416
PROTO_SIZE = 104
CONFIDENCE_THRESHOLD = 0.25
IOU_THRESHOLD = 0.5
CENTER_X = PROTO_SIZE / 2.0

# Model classes 0, 2 and 5 are solid; class 1 is dashed. Classes 3 and 4
# are deliberately ignored. Yellow/center-line semantics are out of scope.
SOLID_CLASSES = frozenset((0, 2, 5))
DASHED_CLASSES = frozenset((1,))
IGNORED_CLASSES = frozenset((3, 4))


def class_to_type(class_id: int) -> str:
  if class_id in SOLID_CLASSES:
    return "solid"
  if class_id in DASHED_CLASSES:
    return "dashed"
  return "unknown"


def visible_y_plane(frame: Any) -> np.ndarray:
  """Return a zero-copy view of the visible NV12 luma plane."""
  width = int(frame.width)
  height = int(frame.height)
  stride = int(frame.stride)
  if width <= 0 or height <= 0 or stride < width:
    raise ValueError("invalid road-camera dimensions")
  raw = np.frombuffer(frame.data, dtype=np.uint8)
  if raw.size < stride * height:
    raise ValueError("short road-camera luma plane")
  return raw[:stride * height].reshape((height, stride))[:, :width]


def prepare_lane_image(y_plane: np.ndarray, cv2_module: Any) -> np.ndarray:
  """Center-crop luma, resize to 416x416, and create normalized NCHW input."""
  if y_plane.ndim != 2 or min(y_plane.shape) <= 0:
    raise ValueError(f"unsupported lane image shape: {y_plane.shape}")
  height, width = y_plane.shape
  crop_size = min(width, height)
  start_x = (width - crop_size) // 2
  start_y = (height - crop_size) // 2
  gray = np.ascontiguousarray(
    y_plane[start_y:start_y + crop_size, start_x:start_x + crop_size])
  if gray.shape != (INPUT_SIZE, INPUT_SIZE):
    gray = cv2_module.resize(
      gray, (INPUT_SIZE, INPUT_SIZE), interpolation=cv2_module.INTER_LINEAR)
  normalized = gray.astype(np.float32) / 255.0
  return np.broadcast_to(
    normalized, (3, INPUT_SIZE, INPUT_SIZE)).copy()[np.newaxis, ...]


@dataclass(frozen=True)
class LaneCandidate:
  class_id: int
  score: float
  bottom: int
  center_at_bottom: float


def non_maximum_suppression(
  boxes_left: np.ndarray,
  boxes_top: np.ndarray,
  boxes_right: np.ndarray,
  boxes_bottom: np.ndarray,
  scores: np.ndarray,
  class_ids: np.ndarray,
  iou_threshold: float,
) -> np.ndarray:
  areas = (boxes_right - boxes_left) * (boxes_bottom - boxes_top)
  kept: list[int] = []
  for class_id in np.unique(class_ids):
    indices = np.flatnonzero(class_ids == class_id)
    order = indices[np.argsort(-scores[indices], kind="stable")]
    while len(order):
      current = int(order[0])
      kept.append(current)
      remaining = order[1:]
      if not len(remaining):
        break
      intersection_width = np.maximum(
        0.0,
        np.minimum(boxes_right[current], boxes_right[remaining]) -
        np.maximum(boxes_left[current], boxes_left[remaining]),
      )
      intersection_height = np.maximum(
        0.0,
        np.minimum(boxes_bottom[current], boxes_bottom[remaining]) -
        np.maximum(boxes_top[current], boxes_top[remaining]),
      )
      intersection = intersection_width * intersection_height
      union = areas[current] + areas[remaining] - intersection + 1e-6
      order = remaining[(intersection / union) <= iou_threshold]
  return np.asarray(
    sorted(kept, key=lambda index: scores[index], reverse=True), dtype=np.intp)


def select_lane_results(candidates: list[LaneCandidate]) -> dict[str, float | str]:
  left = [candidate for candidate in candidates if candidate.center_at_bottom < CENTER_X]
  right = [candidate for candidate in candidates if candidate.center_at_bottom >= CENTER_X]

  def nearest(side: list[LaneCandidate]) -> tuple[str, float]:
    if not side:
      return "unknown", 0.0
    candidate = min(
      side,
      key=lambda item: (
        (item.center_at_bottom - CENTER_X) ** 2 +
        2.0 * (item.bottom - (PROTO_SIZE - 1)) ** 2
      ),
    )
    return class_to_type(candidate.class_id), candidate.score

  left_type, left_confidence = nearest(left)
  right_type, right_confidence = nearest(right)
  return {
    "leftType": left_type,
    "rightType": right_type,
    "leftConf": round(float(left_confidence), 3),
    "rightConf": round(float(right_confidence), 3),
  }


def decode_outputs(
  predictions: np.ndarray,
  prototypes: np.ndarray,
  confidence_threshold: float = CONFIDENCE_THRESHOLD,
  iou_threshold: float = IOU_THRESHOLD,
) -> dict[str, float | str]:
  if predictions.ndim == 3:
    predictions = predictions[0]
  if prototypes.ndim == 4:
    prototypes = prototypes[0]
  if predictions.shape[0] != 42 or prototypes.shape != (32, PROTO_SIZE, PROTO_SIZE):
    raise ValueError(
      f"unexpected ONNX outputs: predictions={predictions.shape}, prototypes={prototypes.shape}")

  class_scores = predictions[4:10, :]
  max_scores = np.max(class_scores, axis=0)
  class_ids = np.argmax(class_scores, axis=0)
  valid = max_scores >= confidence_threshold
  if not np.any(valid):
    return select_lane_results([])

  valid_indices = np.flatnonzero(valid)
  boxes_cx = predictions[0, valid_indices]
  boxes_cy = predictions[1, valid_indices]
  boxes_w = predictions[2, valid_indices]
  boxes_h = predictions[3, valid_indices]
  scores = max_scores[valid_indices]
  filtered_classes = class_ids[valid_indices]
  coefficients = predictions[10:42, valid_indices].T

  boxes_left = boxes_cx - boxes_w * 0.5
  boxes_top = boxes_cy - boxes_h * 0.5
  boxes_right = boxes_cx + boxes_w * 0.5
  boxes_bottom = boxes_cy + boxes_h * 0.5
  kept = non_maximum_suppression(
    boxes_left, boxes_top, boxes_right, boxes_bottom,
    scores, filtered_classes, iou_threshold,
  )

  candidates: list[LaneCandidate] = []
  for index in kept:
    class_id = int(filtered_classes[index])
    if class_id in IGNORED_CLASSES:
      continue
    left = int(np.clip(boxes_left[index] / INPUT_SIZE * PROTO_SIZE, 0, PROTO_SIZE - 1))
    top = int(np.clip(boxes_top[index] / INPUT_SIZE * PROTO_SIZE, 0, PROTO_SIZE - 1))
    right = int(np.clip(boxes_right[index] / INPUT_SIZE * PROTO_SIZE, 0, PROTO_SIZE - 1))
    bottom = int(np.clip(boxes_bottom[index] / INPUT_SIZE * PROTO_SIZE, 0, PROTO_SIZE - 1))
    if right <= left or bottom <= top:
      continue

    prototype_crop = prototypes[:, top:bottom + 1, left:right + 1]
    mask = np.tensordot(
      coefficients[index], prototype_crop, axes=(0, 0)) > 0.0
    if not np.any(mask):
      continue
    rows = np.flatnonzero(np.any(mask, axis=1))
    if not len(rows):
      continue
    lowest_row = int(rows[-1])
    bottom_y = top + lowest_row
    if bottom_y < PROTO_SIZE // 2:
      continue
    columns = np.flatnonzero(mask[lowest_row])
    if not len(columns):
      continue
    candidates.append(LaneCandidate(
      class_id=class_id,
      score=float(scores[index]),
      bottom=bottom_y,
      center_at_bottom=left + float(np.mean(columns)),
    ))

  return select_lane_results(candidates)


class OnnxLaneInference:
  def __init__(self, model_path: Path = DEFAULT_MODEL_PATH, cv2_module: Any = None):
    self.model_path = Path(model_path)
    self.cv2 = cv2_module
    self.net = None
    self.error = ""

  @property
  def valid(self) -> bool:
    return self.net is not None

  def load(self) -> bool:
    try:
      if self.cv2 is None:
        import cv2  # type: ignore[import-not-found]
        self.cv2 = cv2
      if not self.model_path.is_file():
        raise FileNotFoundError(f"ONNX model not found: {self.model_path}")
      self.cv2.setNumThreads(2)
      self.net = self.cv2.dnn.readNetFromONNX(str(self.model_path))
      self.error = ""
      return True
    except Exception as error:
      self.net = None
      self.error = str(error)
      return False

  def infer(self, frame: Any) -> dict[str, float | str | bool]:
    if self.net is None or self.cv2 is None:
      return {
        **select_lane_results([]), "valid": False,
        "error": self.error or "ONNX model is not loaded",
      }
    try:
      blob = prepare_lane_image(visible_y_plane(frame), self.cv2)
      self.net.setInput(blob)
      output_names = self.net.getUnconnectedOutLayersNames()
      outputs = dict(zip(output_names, self.net.forward(output_names), strict=True))
      result = decode_outputs(outputs["output0"], outputs["output1"])
      return {**result, "valid": True, "error": ""}
    except Exception as error:
      return {
        **select_lane_results([]), "valid": False, "error": str(error),
      }
