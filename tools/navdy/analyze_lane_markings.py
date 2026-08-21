#!/usr/bin/env python3
"""Replay the Navdy lane-marking classifier against local route segments."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import threading
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from openpilot.selfdrive.navdy import lane_marking_classifier as classifier
from openpilot.tools.lib.logreader import LogReader


FRAME_WIDTH = 1344
FRAME_HEIGHT = 760
FRAME_RATE = 20
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT * 3 // 2


def load_segment_messages(log_path: Path):
  encodes = {}
  models = {}
  calibrations = []
  speeds = []
  for msg in LogReader(str(log_path), only_union_types=True):
    which = msg.which()
    if which == "roadEncodeIdx":
      encode = msg.roadEncodeIdx
      encodes[int(encode.segmentId)] = int(encode.frameId)
    elif which == "modelV2":
      models[int(msg.modelV2.frameId)] = msg.modelV2.as_builder()
    elif which == "liveCalibration":
      calibrations.append((int(msg.logMonoTime), msg.liveCalibration.as_builder()))
    elif which == "carState":
      speeds.append((int(msg.logMonoTime), float(msg.carState.vEgo)))
  return encodes, models, calibrations, speeds


def value_at_or_before(samples, mono_time: int):
  result = None
  for sample_time, value in samples:
    if sample_time > mono_time:
      break
    result = value
  return result


def make_worker():
  worker = object.__new__(classifier.NavdyLaneMarkingClassifier)
  worker._condition = threading.Condition()
  worker._active = True
  worker._result = dict(classifier.UNKNOWN_LANE_TYPES)
  worker._result_at = 0.0
  worker._pattern_scores = np.zeros(4, dtype=np.float32)
  worker._center_scores = np.zeros(4, dtype=np.float32)
  worker._center_last_seen_at = np.zeros(4, dtype=np.float64)
  worker._last_duration_ms = 0.0
  return worker


def decode_sampled_frames(video_path: Path, sample_stride: int):
  if shutil.which("ffmpeg") is None:
    yield from decode_sampled_frames_with_av(video_path, sample_stride)
    return

  command = [
    "ffmpeg", "-v", "error", "-i", str(video_path),
    "-vf", f"select=not(mod(n\\,{sample_stride}))",
    "-fps_mode", "vfr", "-pix_fmt", "nv12", "-f", "rawvideo", "-",
  ]
  process = subprocess.Popen(command, stdout=subprocess.PIPE)
  assert process.stdout is not None
  frame_index = 0
  try:
    while True:
      data = process.stdout.read(FRAME_SIZE)
      if not data:
        break
      if len(data) != FRAME_SIZE:
        raise RuntimeError(f"short decoded frame: {len(data)} bytes")
      raw = np.frombuffer(data, dtype=np.uint8)
      yield frame_index * sample_stride, SimpleNamespace(
        width=FRAME_WIDTH,
        height=FRAME_HEIGHT,
        stride=FRAME_WIDTH,
        uv_offset=FRAME_WIDTH * FRAME_HEIGHT,
        data=memoryview(raw),
      )
      frame_index += 1
  finally:
    process.stdout.close()
    return_code = process.wait()
    if return_code:
      raise RuntimeError(f"ffmpeg exited with {return_code}")


def decode_sampled_frames_with_av(video_path: Path, sample_stride: int):
  import av

  with av.open(str(video_path)) as container:
    for frame_index, video_frame in enumerate(container.decode(video=0)):
      if frame_index % sample_stride:
        continue
      nv12 = np.ascontiguousarray(video_frame.to_ndarray(format="nv12"))
      if nv12.shape != (FRAME_HEIGHT * 3 // 2, FRAME_WIDTH):
        raise RuntimeError(f"unexpected decoded frame shape: {nv12.shape}")
      raw = nv12.reshape(-1)
      yield frame_index, SimpleNamespace(
        width=FRAME_WIDTH,
        height=FRAME_HEIGHT,
        stride=FRAME_WIDTH,
        uv_offset=FRAME_WIDTH * FRAME_HEIGHT,
        data=memoryview(raw),
      )


def frame_luma(frame) -> float:
  return float(np.mean(np.frombuffer(
    frame.data, dtype=np.uint8, count=frame.uv_offset)))


def analyze_segment(segment_dir: Path, sample_stride: int):
  encodes, models, calibrations, speeds = load_segment_messages(segment_dir / "rlog.zst")
  worker = make_worker()
  raw_counts = [Counter() for _ in classifier.LANE_SUFFIXES]
  stable_counts = [Counter() for _ in classifier.LANE_SUFFIXES]
  yellow_confidences = [[] for _ in classifier.LANE_SUFFIXES]
  pattern_confidences = [[] for _ in classifier.LANE_SUFFIXES]
  lumas = []
  samples = []
  missing_model = 0
  missing_calibration = 0

  for frame_index, frame in decode_sampled_frames(segment_dir / "fcamera.hevc", sample_stride):
    frame_id = encodes.get(frame_index)
    model = models.get(frame_id)
    if model is None:
      missing_model += 1
      continue
    calibration = value_at_or_before(calibrations, int(model.timestampEof))
    if calibration is None:
      missing_calibration += 1
      continue
    request = classifier.capture_request(model, calibration)
    if request is None:
      missing_model += 1
      continue

    profiles = classifier.classify_frame(request, frame)
    now = frame_index / FRAME_RATE
    worker._update_result(profiles, now=max(0.001, now), duration_ms=0.0)
    stable = dict(worker._result)
    luma = frame_luma(frame)
    lumas.append(luma)
    speed = value_at_or_before(speeds, int(model.timestampEof)) or 0.0
    row = {
      "frame": frame_index,
      "frameId": frame_id,
      "seconds": round(now, 2),
      "speedKph": round(speed * 3.6, 1),
      "luma": round(luma, 1),
      "raw": [],
      "stable": [],
    }
    for index, (suffix, profile) in enumerate(zip(classifier.LANE_SUFFIXES, profiles, strict=True)):
      raw_counts[index][profile.pattern] += 1
      stable_type = stable[f"navLane{suffix}Type"]
      stable_counts[index][stable_type] += 1
      yellow_confidences[index].append(profile.yellow_confidence)
      pattern_confidences[index].append(profile.confidence)
      row["raw"].append({
        "pattern": profile.pattern,
        "confidence": round(profile.confidence, 3),
        "yellow": round(profile.yellow_confidence, 3),
      })
      row["stable"].append(stable_type)
    samples.append(row)

  def percentile(values, percentile):
    return round(float(np.percentile(values, percentile)), 3) if values else 0.0

  return {
    "segment": segment_dir.name,
    "sampleStride": sample_stride,
    "sampleCount": len(samples),
    "missingModel": missing_model,
    "missingCalibration": missing_calibration,
    "luma": {
      "min": round(min(lumas), 1) if lumas else 0.0,
      "median": round(float(np.median(lumas)), 1) if lumas else 0.0,
      "max": round(max(lumas), 1) if lumas else 0.0,
    },
    "lanes": [
      {
        "name": suffix,
        "raw": dict(raw_counts[index]),
        "stable": dict(stable_counts[index]),
        "patternConfidenceP50": percentile(pattern_confidences[index], 50),
        "patternConfidenceP90": percentile(pattern_confidences[index], 90),
        "yellowConfidenceP50": percentile(yellow_confidences[index], 50),
        "yellowConfidenceP90": percentile(yellow_confidences[index], 90),
        "yellowConfidenceMax": round(max(yellow_confidences[index], default=0.0), 3),
      }
      for index, suffix in enumerate(classifier.LANE_SUFFIXES)
    ],
    "samples": samples,
  }


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("segments", nargs="+", type=Path)
  parser.add_argument("--sample-stride", type=int, default=10)
  parser.add_argument("--output", type=Path)
  args = parser.parse_args()

  reports = [analyze_segment(path, max(1, args.sample_stride)) for path in args.segments]
  output = json.dumps(reports, ensure_ascii=True, indent=2)
  if args.output:
    args.output.write_text(output + "\n")
  else:
    print(output)


if __name__ == "__main__":
  main()
