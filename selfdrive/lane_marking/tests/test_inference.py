from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from openpilot.selfdrive.lane_marking import inference as lane


def synthetic_outputs():
  predictions = np.zeros((42, 3549), dtype=np.float32)
  prototypes = np.zeros((32, lane.PROTO_SIZE, lane.PROTO_SIZE), dtype=np.float32)
  prototypes[0] = 1.0

  for anchor, center_x, class_id, confidence in (
      (0, 120.0, 0, 0.91),
      (1, 300.0, 1, 0.88),
  ):
    predictions[0, anchor] = center_x
    predictions[1, anchor] = 300.0
    predictions[2, anchor] = 60.0
    predictions[3, anchor] = 180.0
    predictions[4 + class_id, anchor] = confidence
    predictions[10, anchor] = 1.0
  return predictions, prototypes


def test_model_class_mapping_drops_unhandled_and_yellow_semantics():
  assert lane.class_to_type(0) == "solid"
  assert lane.class_to_type(1) == "dashed"
  assert lane.class_to_type(2) == "solid"
  assert lane.class_to_type(3) == "unknown"
  assert lane.class_to_type(4) == "unknown"
  assert lane.class_to_type(5) == "solid"


def test_visible_luma_handles_padded_c4_camera_allocation():
  width, height, stride = 1344, 760, 1408
  raw = np.arange(stride * height + stride * (height // 2), dtype=np.uint8)
  frame = SimpleNamespace(
    width=width, height=height, stride=stride,
    uv_offset=stride * height, data=memoryview(raw),
  )

  y_plane = lane.visible_y_plane(frame)

  assert y_plane.shape == (height, width)
  assert np.shares_memory(y_plane, raw)
  assert y_plane[1, 0] == raw[stride]


def test_decoder_selects_nearest_left_solid_and_right_dashed():
  predictions, prototypes = synthetic_outputs()

  result = lane.decode_outputs(predictions, prototypes)

  assert result == {
    "leftType": "solid",
    "rightType": "dashed",
    "leftConf": 0.91,
    "rightConf": 0.88,
  }


def test_decoder_rejects_unexpected_model_contract():
  with pytest.raises(ValueError, match="unexpected ONNX outputs"):
    lane.decode_outputs(
      np.zeros((1, 10), dtype=np.float32),
      np.zeros((32, lane.PROTO_SIZE, lane.PROTO_SIZE), dtype=np.float32),
    )


def test_bundled_model_loads_with_opencv_when_available():
  cv2 = pytest.importorskip("cv2")
  inference = lane.OnnxLaneInference(cv2_module=cv2)

  assert inference.model_path == Path(lane.__file__).resolve().parent / "models" / "lane.onnx"
  assert inference.load(), inference.error
  assert inference.valid

  width, height, stride = 1344, 760, 1408
  raw = np.full(stride * height + stride * (height // 2), 96, dtype=np.uint8)
  frame = SimpleNamespace(
    width=width, height=height, stride=stride,
    uv_offset=stride * height, data=memoryview(raw),
  )
  result = inference.infer(frame)
  assert result["valid"], result["error"]
  assert result["leftType"] in ("solid", "dashed", "unknown")
  assert result["rightType"] in ("solid", "dashed", "unknown")
