import json
import time
from types import SimpleNamespace

import pytest
from cereal import log

from openpilot.sunnypilot.selfdrive.controls.lib.lane_change_safety import (
  LaneBoundaryStateReader,
  LaneChangeSafetyGate,
  TARGET_LANE_WIDTH_CONFIRM_FRAMES,
  target_lane_space_width,
)


Direction = log.LaneChangeDirection


def line(y):
  return SimpleNamespace(x=[0.0, 8.0, 15.0, 25.0, 40.0], y=[y] * 5)


def model(left_width=3.2, right_width=3.2, outer_prob=0.9,
          left_edge=-5.2, right_edge=5.2, edge_std=0.2):
  return SimpleNamespace(
    laneLines=[line(-1.5 - left_width), line(-1.5), line(1.5), line(1.5 + right_width)],
    laneLineProbs=[outer_prob, 0.9, 0.9, outer_prob],
    roadEdges=[line(left_edge), line(right_edge)],
    roadEdgeStds=[edge_std, edge_std],
  )


def write_markings(path, left="dashed", right="dashed", updated_at=None):
  path.write_text(json.dumps({
    "leftType": left,
    "rightType": right,
    "updatedAtMonotonic": time.monotonic() if updated_at is None else updated_at,
  }))


def test_target_lane_width_uses_confident_outer_lane_lines():
  m = model(left_width=2.35, right_width=3.15)
  assert target_lane_space_width(m, Direction.left) == pytest.approx(2.35)
  assert target_lane_space_width(m, Direction.right) == pytest.approx(3.15)


def test_target_lane_width_falls_back_to_road_edge():
  m = model(outer_prob=0.1, left_edge=-3.7, right_edge=3.8)
  assert target_lane_space_width(m, Direction.left) == pytest.approx(2.2)
  assert target_lane_space_width(m, Direction.right) == pytest.approx(2.3)


def test_unreliable_geometry_does_not_report_a_width():
  m = model(outer_prob=0.1, edge_std=1.0)
  assert target_lane_space_width(m, Direction.left) is None
  assert target_lane_space_width(m, Direction.right) is None


def test_centerline_block_releases_on_explicit_dashed_line(tmp_path):
  state = tmp_path / "markings.json"
  write_markings(state, left="centerSolid")
  gate = LaneChangeSafetyGate(LaneBoundaryStateReader(str(state)))

  assert gate.update(Direction.left, model())
  write_markings(state, left="unknown")
  gate.boundary_reader.last_read_at = 0.0
  assert gate.update(Direction.left, model())

  write_markings(state, left="dashed")
  gate.boundary_reader.last_read_at = 0.0
  assert not gate.update(Direction.left, model())
  assert gate.block_reason == ""


def test_white_solid_line_blocks_and_releases_on_dashed_line(tmp_path):
  state = tmp_path / "markings.json"
  write_markings(state, right="solid")
  gate = LaneChangeSafetyGate(LaneBoundaryStateReader(str(state)))

  assert gate.update(Direction.right, model())
  assert gate.block_reason == "solidLine"

  write_markings(state, right="dashed")
  gate.boundary_reader.last_read_at = 0.0
  assert not gate.update(Direction.right, model())
  assert gate.block_reason == ""


def test_dashed_centerline_also_blocks_requested_direction(tmp_path):
  state = tmp_path / "markings.json"
  write_markings(state, right="centerDashed")
  gate = LaneChangeSafetyGate(LaneBoundaryStateReader(str(state)))

  assert gate.update(Direction.right, model())
  assert gate.block_reason == "centerline"
  gate.reset()
  assert not gate.update(Direction.left, model())


def test_narrow_target_requires_consecutive_frames_and_latches(tmp_path):
  state = tmp_path / "markings.json"
  write_markings(state)
  gate = LaneChangeSafetyGate(LaneBoundaryStateReader(str(state)))
  narrow = model(right_width=0.9)

  for _ in range(TARGET_LANE_WIDTH_CONFIRM_FRAMES - 1):
    assert not gate.update(Direction.right, narrow)
  assert gate.update(Direction.right, narrow)
  assert gate.block_reason == "narrowTargetLane"

  assert gate.update(Direction.right, model(right_width=1.0))
  gate.reset()
  assert not gate.update(Direction.right, model(right_width=1.0))


def test_stale_centerline_state_is_ignored(tmp_path):
  state = tmp_path / "markings.json"
  write_markings(state, left="centerSolid", updated_at=time.monotonic() - 10.0)
  gate = LaneChangeSafetyGate(LaneBoundaryStateReader(str(state)))

  assert not gate.update(Direction.left, model())
