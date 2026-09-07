#!/usr/bin/env python3
"""System ONNX lane-marking service for lane-change safety and HUD consumers."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from openpilot.common.realtime import set_core_affinity
from openpilot.selfdrive.lane_marking.classifier import OnnxLaneMarkingClassifier
from openpilot.selfdrive.lane_marking.state import LANE_MARKING_STATE_PATH


SERVICE_HZ = 10.0
INFERENCE_INTERVAL_SEC = 0.5
RESULT_STALE_SEC = 2.0


def state_payload(markings: dict[str, str], now: float, duration_ms: float = 0.0,
                  error: str = "") -> dict[str, Any]:
  return {
    "version": 2,
    "source": "onnx",
    "leftType": str(markings.get("navLaneLeftType", "unknown")),
    "rightType": str(markings.get("navLaneRightType", "unknown")),
    "updatedAtMonotonic": float(now),
    "inferenceMs": round(max(0.0, float(duration_ms)), 1),
    "error": str(error),
  }


def publish_lane_marking_state(markings: dict[str, str], now: float | None = None,
                               duration_ms: float = 0.0, error: str = "",
                               path: str = LANE_MARKING_STATE_PATH) -> None:
  now = time.monotonic() if now is None else now
  temp_path = path + ".tmp"
  try:
    with open(temp_path, "w", encoding="utf-8") as state_file:
      json.dump(
        state_payload(markings, now, duration_ms, error), state_file,
        separators=(",", ":"),
      )
    os.replace(temp_path, path)
  except OSError:
    try:
      os.unlink(temp_path)
    except OSError:
      pass


def main() -> None:
  from cereal import messaging

  set_core_affinity([0, 1, 2, 3])
  classifier = OnnxLaneMarkingClassifier(
    interval_sec=INFERENCE_INTERVAL_SEC,
    stale_sec=RESULT_STALE_SEC,
    stdout=True,
  )
  classifier.set_active(True)
  sm = messaging.SubMaster(["modelV2"])
  period = 1.0 / SERVICE_HZ
  next_tick = time.monotonic()

  while True:
    sm.update(max(0, int((next_tick - time.monotonic()) * 1000)))
    now = time.monotonic()
    if sm.updated["modelV2"] and sm.alive["modelV2"] and sm.valid["modelV2"]:
      classifier.submit(sm["modelV2"], None, now)

    markings = classifier.snapshot(now)
    publish_lane_marking_state(
      markings,
      # Preserve the time of the actual camera inference. Merely keeping this
      # daemon alive must not keep an old dashed-line decision fresh.
      now=classifier.last_result_at(),
      duration_ms=classifier.last_duration_ms(),
      error=classifier.last_error(),
    )
    next_tick = max(next_tick + period, now)


if __name__ == "__main__":
  main()
