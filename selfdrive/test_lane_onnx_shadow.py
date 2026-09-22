from openpilot.selfdrive.lane_onnx_shadow import MAX_CPU_FRACTION, MIN_INTERVAL_SEC, has_headroom, next_inference_at, v_asm_side


def test_minimum_interval() -> None:
  assert next_inference_at(10.0, 0.05) == 10.0 + MIN_INTERVAL_SEC


def test_cpu_budget_extends_interval() -> None:
  assert next_inference_at(10.0, 0.5) == 10.0 + 0.5 / MAX_CPU_FRACTION


def test_negative_cpu_time_does_not_shorten_interval() -> None:
  assert next_inference_at(10.0, -1.0) == 10.0 + MIN_INTERVAL_SEC


def test_headroom_requires_background_cores_below_limit() -> None:
  assert has_headroom([55, 60, 65, 70, 90, 90, 90, 90], [68, 69])
  assert not has_headroom([55, 60, 75, 70], [68])
  assert not has_headroom([55, 60, 65, 70], [80])
  assert not has_headroom([], [])


def test_v_asm_runs_only_for_a_real_target_lane() -> None:
  assert v_asm_side(15.0, True, False, 3.2, None) == "left"
  assert v_asm_side(15.0, False, True, None, 3.2) == "right"
  assert v_asm_side(15.0, True, True, 3.2, 3.2) is None
  assert v_asm_side(15.0, True, False, 2.4, None) is None
  assert v_asm_side(5.0, True, False, 3.2, None) is None
