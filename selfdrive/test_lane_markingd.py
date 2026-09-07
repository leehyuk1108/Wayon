import json

from openpilot.selfdrive import lane_markingd


def test_state_payload_is_explicitly_onnx_and_adjacent_only():
  payload = lane_markingd.state_payload({
    "navLaneFarLeftType": "solid",
    "navLaneLeftType": "dashed",
    "navLaneRightType": "solid",
    "navLaneFarRightType": "dashed",
  }, now=12.5, duration_ms=34.26)

  assert payload == {
    "version": 2,
    "source": "onnx",
    "leftType": "dashed",
    "rightType": "solid",
    "updatedAtMonotonic": 12.5,
    "inferenceMs": 34.3,
    "error": "",
  }


def test_state_writer_replaces_file_atomically(tmp_path):
  path = tmp_path / "lane-state.json"
  lane_markingd.publish_lane_marking_state(
    {"navLaneLeftType": "solid", "navLaneRightType": "dashed"},
    now=25.0,
    path=str(path),
  )

  state = json.loads(path.read_text())
  assert state["source"] == "onnx"
  assert state["leftType"] == "solid"
  assert state["rightType"] == "dashed"
  assert state["updatedAtMonotonic"] == 25.0
  assert not (tmp_path / "lane-state.json.tmp").exists()
