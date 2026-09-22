#!/usr/bin/env python3
"""Opt-in, resource-limited CarrotPilot lane and blindspot observation.

This process has no control output. It records performance and classifications
so the model can be evaluated before it is considered for driving decisions.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

MODEL_PATH = Path(__file__).parent / "lane_marking" / "models" / "lane.onnx"
V_ASM_MODEL_PATH = Path(__file__).parent / "lane_marking" / "models" / "v_asm_model.onnx"
MIN_INTERVAL_SEC = 1.0
MAX_CPU_FRACTION = 0.20
REPORT_INTERVAL_SEC = 30.0
MAX_BACKGROUND_CORE_PCT = 75.0
MAX_CPU_TEMP_C = 80.0
V_ASM_MIN_SPEED_MPS = 30.0 / 3.6
V_ASM_MAX_SPEED_MPS = 120.0 / 3.6
V_ASM_MIN_LANE_WIDTH_M = 3.0
V_ASM_ROI = {
  "width": 1928, "height": 1208,
  "poly_left": [[0, 550], [550, 480], [650, 950], [0, 1200]],
  "poly_right": [[1378, 480], [1927, 550], [1927, 1200], [1278, 950]],
}


def next_inference_at(start: float, cpu_seconds: float) -> float:
  return start + max(MIN_INTERVAL_SEC, max(0.0, cpu_seconds) / MAX_CPU_FRACTION)


def has_headroom(cpu_percent: list[float], cpu_temp_c: list[float]) -> bool:
  return (len(cpu_percent) >= 4 and
          all(0.0 <= usage < MAX_BACKGROUND_CORE_PCT for usage in cpu_percent[:4]) and
          (not cpu_temp_c or max(cpu_temp_c) < MAX_CPU_TEMP_C))


def configure_background() -> None:
  os.environ["OPENBLAS_NUM_THREADS"] = "1"
  os.environ["OMP_NUM_THREADS"] = "1"
  os.environ["MKL_NUM_THREADS"] = "1"
  if sys.platform == "linux" and Path("/data/wayon_pydeps/cv2").is_dir():
    sys.path.insert(0, "/data/wayon_pydeps")
  os.nice(10)
  if sys.platform == "linux":
    from openpilot.common.realtime import set_core_affinity
    from openpilot.system.hardware import TICI
    if TICI:
      set_core_affinity([0, 1, 2, 3])


def load_inference(model_path: Path):
  import cv2
  from openpilot.selfdrive.lane_marking.inference import OnnxLaneInference

  cv2.setNumThreads(1)
  inference = OnnxLaneInference(model_path, cv2_module=cv2)
  if not inference.load():
    raise RuntimeError(inference.error)
  return inference


def v_asm_side(v_ego: float, left_blinker: bool, right_blinker: bool,
               left_width: float | None, right_width: float | None) -> str | None:
  if not V_ASM_MIN_SPEED_MPS <= v_ego <= V_ASM_MAX_SPEED_MPS or left_blinker == right_blinker:
    return None
  side = "left" if left_blinker else "right"
  width = left_width if left_blinker else right_width
  return side if width is not None and width >= V_ASM_MIN_LANE_WIDTH_M else None


def benchmark(model_path: Path, count: int) -> None:
  configure_background()
  inference = load_inference(model_path)
  frame = SimpleNamespace(data=bytes([128]) * (416 * 416), width=416, height=416, stride=416)
  samples = []
  for _ in range(count + 1):
    started = time.monotonic()
    cpu_started = time.process_time()
    result = inference.infer(frame)
    wall_seconds = time.monotonic() - started
    cpu_seconds = time.process_time() - cpu_started
    if not result["valid"]:
      raise RuntimeError(str(result["error"]))
    samples.append((wall_seconds, cpu_seconds))
  measured = samples[1:]
  print(json.dumps({
    "model": str(model_path), "samples": count,
    "wall_ms": [round(wall * 1000, 1) for wall, _ in measured],
    "cpu_ms": [round(cpu * 1000, 1) for _, cpu in measured],
    "estimated_interval_sec": [round(max(MIN_INTERVAL_SEC, cpu / MAX_CPU_FRACTION), 2)
                               for _, cpu in measured],
  }))


def run_shadow(model_path: Path, v_asm_model_path: Path = V_ASM_MODEL_PATH) -> None:
  configure_background()

  from cereal import messaging
  from msgq.visionipc import VisionIpcClient, VisionStreamType
  from openpilot.common.swaglog import cloudlog
  from openpilot.selfdrive.lane_marking.nv12 import pack_nv12
  from openpilot.selfdrive.lane_marking.state import write_state
  from openpilot.selfdrive.lane_marking.v_asm_inference import VASMInference
  from openpilot.sunnypilot.selfdrive.controls.lib.lane_change_safety import target_lane_space_width
  from cereal import log

  inference = load_inference(model_path)
  v_asm = VASMInference(v_asm_model_path)
  if not v_asm.load():
    raise RuntimeError(v_asm.error)
  v_asm.load_config(V_ASM_ROI)
  sm = messaging.SubMaster(["deviceState", "carState", "modelV2"])
  clients = {}
  next_budget_due = next_lane_due = next_v_asm_due = 0.0
  report_at = time.monotonic() + REPORT_INTERVAL_SEC
  count = v_asm_count = failures = skipped = 0
  cpu_total = wall_total = 0.0
  last_result = "unknown/unknown"
  state_data = {"leftType": "unknown", "rightType": "unknown",
                "laneUpdatedAtMonotonic": 0.0, "blindspotUpdatedAtMonotonic": 0.0,
                "leftBlindspot": False, "rightBlindspot": False}

  def report_if_due(now: float) -> None:
    nonlocal count, v_asm_count, failures, skipped, cpu_total, wall_total, report_at
    if now < report_at:
      return
    total = count + v_asm_count
    report = {"lane_samples": count, "v_asm_samples": v_asm_count,
              "failures": failures, "skipped": skipped,
              "cpu_ms": round(cpu_total / max(total, 1) * 1000, 1),
              "wall_ms": round(wall_total / max(total, 1) * 1000, 1),
              "last": last_result}
    cloudlog.info("ONNX_VISION_SHADOW " + json.dumps(report))
    count = v_asm_count = failures = skipped = 0
    cpu_total = wall_total = 0.0
    report_at = now + REPORT_INTERVAL_SEC

  while True:
    time.sleep(0.1)
    sm.update(0)
    now = time.monotonic()
    if now < next_budget_due:
      report_if_due(now)
      continue
    state = sm["deviceState"]
    if not sm.alive["deviceState"] or not has_headroom(list(state.cpuUsagePercent), list(state.cpuTempC)):
      skipped += 1
      next_budget_due = now + MIN_INTERVAL_SEC
      report_if_due(now)
      continue

    side = None
    if sm.alive["carState"] and sm.alive["modelV2"]:
      car_state = sm["carState"]
      model = sm["modelV2"]
      left_width = target_lane_space_width(model, log.LaneChangeDirection.left)
      right_width = target_lane_space_width(model, log.LaneChangeDirection.right)
      side = v_asm_side(float(car_state.vEgo), bool(car_state.leftBlinker),
                        bool(car_state.rightBlinker), left_width, right_width)
    if side is None and (state_data["leftBlindspot"] or state_data["rightBlindspot"]):
      v_asm.reset()
      state_data.update(leftBlindspot=False, rightBlindspot=False,
                        blindspotUpdatedAtMonotonic=0.0)
      write_state(state_data)

    task = "v_asm" if side is not None and now >= next_v_asm_due else "lane" if now >= next_lane_due else None
    if task is None:
      report_if_due(now)
      continue
    stream = VisionStreamType.VISION_STREAM_WIDE_ROAD if task == "v_asm" else VisionStreamType.VISION_STREAM_ROAD
    client = clients.get(task)
    if client is None or not client.is_connected():
      client = VisionIpcClient("camerad", stream, True)
      if not client.connect(False):
        clients.pop(task, None)
        next_budget_due = now + 1.0
        continue
      clients[task] = client
    frame = client.recv(timeout_ms=1000)
    if frame is None:
      clients.pop(task, None)
      continue

    started = time.monotonic()
    cpu_started = time.process_time()
    try:
      if task == "lane":
        result = inference.infer(frame)
        if not result["valid"]:
          raise RuntimeError(str(result["error"]))
        state_data.update(leftType=result["leftType"], rightType=result["rightType"],
                          laneUpdatedAtMonotonic=time.monotonic())
        last_result = f"{result['leftType']}/{result['rightType']}"
        count += 1
      else:
        nv12 = pack_nv12(frame.data, int(frame.width), int(frame.height),
                         int(frame.stride), int(frame.uv_offset))
        v_asm.update(nv12, int(frame.width), int(frame.height), side,
                     threshold=0.45, smoothing_seconds=0.2, dt=max(0.25, now - next_v_asm_due + 0.25))
        state_data.update(leftBlindspot=bool(v_asm.active["left"]),
                          rightBlindspot=bool(v_asm.active["right"]),
                          blindspotUpdatedAtMonotonic=time.monotonic())
        last_result = f"v_asm_{side}:{v_asm.confidence[side]:.2f}"
        v_asm_count += 1
      write_state(state_data)
    except Exception as error:
      failures += 1
      cloudlog.warning(f"ONNX_VISION_SHADOW {task} failed: {error}")
    wall_seconds = time.monotonic() - started
    cpu_seconds = time.process_time() - cpu_started
    next_budget_due = next_inference_at(started, cpu_seconds)
    if task == "lane":
      next_lane_due = started + MIN_INTERVAL_SEC
    else:
      next_v_asm_due = started + 0.25
    cpu_total += cpu_seconds
    wall_total += wall_seconds
    report_if_due(time.monotonic())


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("--model", type=Path, default=MODEL_PATH)
  parser.add_argument("--v-asm-model", type=Path, default=V_ASM_MODEL_PATH)
  parser.add_argument("--benchmark", type=int, metavar="COUNT")
  args = parser.parse_args()
  if args.benchmark is not None:
    if args.benchmark < 1:
      parser.error("--benchmark must be positive")
    benchmark(args.model, args.benchmark)
  else:
    run_shadow(args.model, args.v_asm_model)


if __name__ == "__main__":
  main()
