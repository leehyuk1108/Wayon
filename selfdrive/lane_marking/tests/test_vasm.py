import math
import threading
from types import SimpleNamespace

import numpy as np
from cereal import log

from openpilot.selfdrive.lane_marking.nv12 import nv12_y_plane, pack_nv12
from openpilot.selfdrive.lane_marking.server import DEFAULT_POLYGONS, VASMService, normalize_config
from openpilot.selfdrive.lane_marking.vasm_inference import VASMInference


def test_default_polygons_are_valid_without_web_edits():
  assert normalize_config(DEFAULT_POLYGONS) == DEFAULT_POLYGONS


def test_padded_nv12_camera_frame_is_packed_without_padding():
  width, height, stride = 8, 4, 10
  uv_offset = stride * height + 6
  raw = np.full(uv_offset + stride * (height // 2) + 9, 255, dtype=np.uint8)
  expected_y = np.arange(width * height, dtype=np.uint8).reshape(height, width)
  expected_uv = np.arange(width * height // 2, dtype=np.uint8).reshape(height // 2, width) + 90
  raw[:stride * height].reshape(height, stride)[:, :width] = expected_y
  raw[uv_offset:uv_offset + stride * (height // 2)].reshape(height // 2, stride)[:, :width] = expected_uv

  np.testing.assert_array_equal(nv12_y_plane(raw, width, height, stride), expected_y)
  np.testing.assert_array_equal(pack_nv12(raw, width, height, stride, uv_offset), np.vstack((expected_y, expected_uv)))


def test_blindspot_model_loads_and_evaluates_only_requested_side():
  inference = VASMInference()
  assert inference.load(), inference.error
  inference.load_config({
    "width": 352,
    "height": 256,
    "poly_left": [[0, 0], [174, 0], [174, 254], [0, 254]],
    "poly_right": [[176, 0], [350, 0], [350, 254], [176, 254]],
  })
  frame = np.zeros((384, 352), dtype=np.uint8)
  frame[256:] = 128

  inference.update(frame, 352, 256, "left", 0.45, 0.2, 0.25)

  assert math.isfinite(inference.confidence["left"])
  assert 0.0 <= inference.confidence["left"] <= 1.0
  assert inference.confidence["right"] == 0.0
  assert not inference.active["right"]


def test_vasm_gate_uses_sunnypilot_lane_geometry():
  def line(y):
    return SimpleNamespace(x=[0.0, 8.0, 15.0, 25.0], y=[y] * 4)

  model = SimpleNamespace(
    meta=SimpleNamespace(laneChangeDirection=log.LaneChangeDirection.left),
    laneLines=[line(-4.7), line(-1.5), line(1.5), line(4.3)],
    laneLineProbs=[0.9, 0.9, 0.9, 0.9],
    roadEdges=[line(-5.2), line(5.2)],
    roadEdgeStds=[0.2, 0.2],
  )

  class FakeSubMaster:
    def update(self, _timeout):
      pass

    def all_alive(self, _services):
      return True

    def all_valid(self, _services):
      return True

    def __getitem__(self, service):
      return SimpleNamespace(vEgo=20.0) if service == "carState" else model

  service = VASMService.__new__(VASMService)
  service.lock = threading.Lock()
  service.sm = FakeSubMaster()
  assert service._update_vasm_gate() == (True, "left")

  model.meta.laneChangeDirection = log.LaneChangeDirection.right
  assert service._update_vasm_gate() == (False, "right")
  assert service.vasm_gate["reason"] == "target lane width below 3.0 m"
