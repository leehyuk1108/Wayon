import json
from types import SimpleNamespace

from openpilot.selfdrive.lane_marking.state import (
  BlindspotStateReader,
  publish_blindspot_state,
  publish_lane_marking_state,
  merge_visual_blindspot,
)


def test_lane_state_writer_preserves_actual_inference_time(tmp_path):
  path = tmp_path / "lane-state.json"
  publish_lane_marking_state(
    {"navLaneLeftType": "solid", "navLaneRightType": "dashed"},
    updated_at=25.0,
    path=str(path),
  )

  state = json.loads(path.read_text())
  assert state["source"] == "xiaoge"
  assert state["leftType"] == "solid"
  assert state["rightType"] == "dashed"
  assert state["updatedAtMonotonic"] == 25.0


def test_visual_blindspot_reader_accepts_only_fresh_evaluated_side(tmp_path):
  path = tmp_path / "blindspot-state.json"
  publish_blindspot_state(True, True, "left", updated_at=10.0, path=str(path))
  reader = BlindspotStateReader(str(path))

  state = reader.read(now=10.1)
  assert state.left is True
  assert state.right is False
  assert state.evaluated_side == "left"

  reader.last_read_at = 0.0
  stale = reader.read(now=12.0)
  assert stale.left is False
  assert stale.right is False


def test_visual_blindspot_is_or_merged_with_oem_bsd():
  car_state = SimpleNamespace(leftBlindspot=False, rightBlindspot=True)
  merge_visual_blindspot(
    car_state,
    SimpleNamespace(left=True, right=False),
  )

  assert car_state.leftBlindspot is True
  assert car_state.rightBlindspot is True
