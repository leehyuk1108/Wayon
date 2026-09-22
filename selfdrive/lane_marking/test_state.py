import json

from openpilot.selfdrive.lane_marking.state import OnnxLaneMarkingReader, lane_markings, read_state, write_state


def test_onnx_lane_state_rejects_stale_and_unknown_results() -> None:
  state = {"leftType": "dashed", "rightType": "solid", "laneUpdatedAtMonotonic": 10.0}
  assert lane_markings(state, 10.5) == {"navLaneLeftType": "dashed", "navLaneRightType": "solid"}
  assert lane_markings(state, 12.0) == {"navLaneLeftType": "unknown", "navLaneRightType": "unknown"}
  assert lane_markings({**state, "leftType": "centerDashed"}, 10.5)["navLaneLeftType"] == "unknown"


def test_onnx_lane_reader_is_inactive_until_enabled(tmp_path) -> None:
  path = tmp_path / "onnx.json"
  write_state({"leftType": "dashed", "rightType": "solid", "laneUpdatedAtMonotonic": 10.0}, path)
  reader = OnnxLaneMarkingReader(path)
  assert reader.snapshot(10.5)["navLaneLeftType"] == "unknown"
  reader.set_active(True)
  assert reader.snapshot(10.5)["navLaneLeftType"] == "dashed"
  assert read_state(path)["rightType"] == "solid"
  assert json.loads(path.read_text())["leftType"] == "dashed"
