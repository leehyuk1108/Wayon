#!/usr/bin/env python3
"""Xiaoge vision service providing lane and gated blindspot results on comma."""

import argparse
import json
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

if __package__ in (None, ""):
  sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cereal import log
from openpilot.selfdrive.lane_marking.classifier import UNKNOWN_LANE_TYPES, score_to_type, update_score
from openpilot.selfdrive.lane_marking.inference import OnnxLaneInference, prepare_lane_gray, visible_y_plane
from openpilot.selfdrive.lane_marking.nv12 import pack_nv12
from openpilot.selfdrive.lane_marking.state import (
  BLINDSPOT_MAX_AGE_SEC,
  LANE_MARKING_MAX_AGE_SEC,
  publish_blindspot_state,
  publish_lane_marking_state,
)
from openpilot.selfdrive.lane_marking.vasm_inference import DEFAULT_MODEL_PATH, VASMInference
from openpilot.sunnypilot.selfdrive.controls.lib.lane_change_safety import target_lane_space_width

try:
  import cv2
  cv2.setNumThreads(1)
except ModuleNotFoundError as error:
  if error.name == "cv2":
    raise SystemExit(
        "V-ASM requires OpenCV. Restart openpilot through its normal launcher to install the bundled wheel into pydeps. " +
      "For development, install xiaoge/requirements.txt in a writable virtual environment."
    ) from None
  raise


HOST = "0.0.0.0"
PORT = 8082
CONFIG_PATH = Path(__file__).resolve().parent / "v_asm_config.json"
MIN_THRESHOLD = 0.25
MAX_THRESHOLD = 1.0
MIN_SMOOTHING_SECONDS = 0.1
MAX_SMOOTHING_SECONDS = 0.5
MIN_BASE_INTERVAL_SECONDS = 0.05
MAX_BASE_INTERVAL_SECONDS = 1.0
BASE_INTERVAL_SECONDS = 0.25
MIN_LANE_INTERVAL_SECONDS = 0.40
MAX_LANE_INTERVAL_SECONDS = 2.0
LANE_INTERVAL_SECONDS = 0.40
LANE_INFERENCE_YIELD_SECONDS = 0.03
FOLLOWUP_INTERVAL_SECONDS = 0.15
FOLLOWUP_WINDOW_SECONDS = 1.5
VASM_MIN_SPEED_MPS = 30.0 / 3.6
VASM_MAX_SPEED_MPS = 120.0 / 3.6
VASM_MIN_LANE_WIDTH_METERS = 3.0
CAMERA_TIMEOUT_SECONDS = 2.0
SNAPSHOT_TIMEOUT_SECONDS = 5.0
# VisionIPC recv holds the GIL while waiting. Poll without blocking, then sleep
# in Python so an idle camera cannot stall inference or HTTP on other threads.
CAMERA_POLL_INTERVAL_SECONDS = 0.005


DEFAULT_POLYGONS = {
  "width": 1928,
  "height": 1208,
  "poly_left": [
    [0, 550],
    [550, 480],
    [650, 950],
    [0, 1200],
  ],
  "poly_right": [
    [1378, 480],
    [1927, 550],
    [1927, 1200],
    [1278, 950],
  ],
}


def normalize_config(config: object) -> dict:
  if not isinstance(config, dict):
    raise ValueError("configuration must be a JSON object")
  try:
    width, height = int(config.get("width", 0)), int(config.get("height", 0))
  except (TypeError, ValueError) as error:
    raise ValueError("camera dimensions must be integers") from error
  if not 1 <= width <= 8192 or not 1 <= height <= 8192:
    raise ValueError("camera dimensions must be between 1 and 8192")

  normalized = {"width": width, "height": height}
  for side in ("left", "right"):
    polygon = config.get(f"poly_{side}", [])
    if not isinstance(polygon, list) or len(polygon) > 64:
      raise ValueError(f"poly_{side} must contain at most 64 points")
    if polygon and len(polygon) < 3:
      raise ValueError(f"poly_{side} requires at least 3 points")
    points = []
    for point in polygon:
      if not isinstance(point, (list, tuple)) or len(point) != 2:
        raise ValueError(f"poly_{side} points must be [x, y]")
      try:
        x, y = round(float(point[0])), round(float(point[1]))
      except (TypeError, ValueError) as error:
        raise ValueError(f"poly_{side} coordinates must be numbers") from error
      if not 0 <= x < width or not 0 <= y < height:
        raise ValueError(f"poly_{side} point is outside the image")
      points.append([x, y])
    normalized[f"poly_{side}"] = points
  if not normalized["poly_left"] and not normalized["poly_right"]:
    raise ValueError("annotate at least one side")
  return normalized


class VASMService:
  def __init__(self, model_path: Path):
    import cereal.messaging as messaging

    self.lock = threading.Lock()
    self.snapshot_condition = threading.Condition(self.lock)
    self.snapshot_requests = {"wide": 0, "road": 0}
    self.snapshot_responses = {"wide": 0, "road": 0}
    self.vasm_inference_lock = threading.Lock()
    self.publish_lock = threading.Lock()
    self.inference = VASMInference(model_path)
    self.inference.load()
    self.config = self._read_config()
    if self.config:
      self.inference.load_config(self.config)
    self.threshold = 0.45
    self.smoothing_seconds = 0.2
    self.base_interval_seconds = BASE_INTERVAL_SECONDS
    self.running = True
    self.last_jpeg: bytes | None = None
    self.last_frame_at = 0.0
    self.last_inference_at = 0.0
    self.last_inference_ms = 0.0
    self.last_inference_thread_cpu_ms = 0.0
    self.inference_count = 0
    self.inference_fps = 0.0
    self._fps_window_start = time.monotonic()
    self._fps_window_count = 0
    self.last_side_at = {"left": 0.0, "right": 0.0}
    self.next_side = "left"
    self.followup_until = 0.0
    self.camera_error = "waiting for wide road camera"
    self.sm = messaging.SubMaster(["carState", "modelV2"])
    self.vasm_gate = {
      "active": False,
      "side": "",
      "reason": "waiting for carState and modelV2",
      "laneWidth": 0.0,
    }
    self.vasm_result = {"left": False, "right": False, "side": "", "updatedMonoTimeNanos": 0}

    # Lane inference engine setup
    self.lane_inference = OnnxLaneInference()
    self.lane_inference.load()
    self.lane_threshold = 0.25
    self.lane_interval_seconds = LANE_INTERVAL_SECONDS
    self.lane_camera_error = "waiting for road camera"
    self.last_road_jpeg: bytes | None = None
    self.last_road_frame_at = 0.0
    self.last_lane_inference_at = 0.0
    self.last_lane_inference_ms = 0.0
    self.last_lane_inference_thread_cpu_ms = 0.0
    self.lane_inference_count = 0
    self.lane_inference_fps = 0.0
    self._lane_fps_window_start = time.monotonic()
    self._lane_fps_window_count = 0
    self.lane_result = {
      "leftLine": -1,
      "rightLine": -1,
      "leftConf": 0.0,
      "rightConf": 0.0,
      "candidatesCount": 0,
      "valid": False,
      "error": "",
      "updatedMonoTimeNanos": 0,
    }
    self.lane_scores = {"Left": 0.0, "Right": 0.0}
    self.lane_types = dict(UNKNOWN_LANE_TYPES)

  def _read_config(self) -> dict:
    try:
      return normalize_config(json.loads(CONFIG_PATH.read_text()))
    except (OSError, ValueError, json.JSONDecodeError):
      return DEFAULT_POLYGONS

  def _write_config(self, config: dict) -> None:
    temporary_path = CONFIG_PATH.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(config, separators=(",", ":")) + "\n")
    temporary_path.replace(CONFIG_PATH)

  def save_config(self, config: object) -> dict:
    normalized = normalize_config(config)
    self._write_config(normalized)
    with self.vasm_inference_lock:
      self.inference.load_config(normalized)
    with self.lock:
      self.config = normalized
    return normalized

  def clear_config(self) -> None:
    try:
      CONFIG_PATH.unlink()
    except FileNotFoundError:
      pass
    with self.vasm_inference_lock:
      self.inference.load_config(DEFAULT_POLYGONS)
    with self.lock:
      self.config = DEFAULT_POLYGONS

  def set_settings(self, settings: object) -> dict:
    if not isinstance(settings, dict):
      raise ValueError("settings must be a JSON object")
    try:
      threshold = float(settings.get("threshold", self.threshold))
      smoothing_seconds = float(settings.get("smoothingSeconds", self.smoothing_seconds))
      base_interval_seconds = float(settings.get("baseIntervalSeconds", self.base_interval_seconds))
      lane_threshold = float(settings.get("laneThreshold", self.lane_threshold))
      lane_interval_seconds = float(settings.get("laneIntervalSeconds", self.lane_interval_seconds))
    except (TypeError, ValueError) as error:
      raise ValueError("settings must be numeric") from error
    if not MIN_THRESHOLD <= threshold <= MAX_THRESHOLD:
      raise ValueError(f"threshold must be {MIN_THRESHOLD:.2f} to {MAX_THRESHOLD:.2f}")
    if not MIN_SMOOTHING_SECONDS <= smoothing_seconds <= MAX_SMOOTHING_SECONDS:
      raise ValueError(f"smoothingSeconds must be {MIN_SMOOTHING_SECONDS:.1f} to {MAX_SMOOTHING_SECONDS:.1f}")
    if not MIN_BASE_INTERVAL_SECONDS <= base_interval_seconds <= MAX_BASE_INTERVAL_SECONDS:
      raise ValueError(f"baseIntervalSeconds must be {MIN_BASE_INTERVAL_SECONDS:.2f} to {MAX_BASE_INTERVAL_SECONDS:.2f}")
    if not 0.05 <= lane_threshold <= 1.0:
      raise ValueError("laneThreshold must be 0.05 to 1.0")
    if not MIN_LANE_INTERVAL_SECONDS <= lane_interval_seconds <= MAX_LANE_INTERVAL_SECONDS:
      raise ValueError(
        f"laneIntervalSeconds must be {MIN_LANE_INTERVAL_SECONDS:.2f} to {MAX_LANE_INTERVAL_SECONDS:.1f}")

    with self.lock:
      self.threshold = threshold
      self.smoothing_seconds = smoothing_seconds
      self.base_interval_seconds = base_interval_seconds
      self.lane_threshold = lane_threshold
      self.lane_interval_seconds = lane_interval_seconds
    return self.status()

  def status(self) -> dict:
    with self.lock:
      now = time.monotonic()
      now_nanos = time.monotonic_ns()
      camera_age = now - self.last_frame_at if self.last_frame_at else None
      road_camera_age = now - self.last_road_frame_at if self.last_road_frame_at else None
      camera_available = camera_age is not None and camera_age <= CAMERA_TIMEOUT_SECONDS and not self.camera_error
      road_camera_available = road_camera_age is not None and road_camera_age <= CAMERA_TIMEOUT_SECONDS and not self.lane_camera_error
      vasm_timestamp = self.vasm_result["updatedMonoTimeNanos"]
      vasm_fresh = vasm_timestamp > 0 and 0 <= now_nanos - vasm_timestamp <= int(BLINDSPOT_MAX_AGE_SEC * 1e9)
      vehicle_sides = {}
      for side in ("left", "right"):
        valid = bool(camera_available and self.inference.valid and vasm_fresh and self.vasm_gate["active"] and
                     self.vasm_gate["side"] == side and self.vasm_result["side"] == side)
        vehicle_sides[side] = {
          "valid": valid,
          "active": self.vasm_result[side] if valid else False,
          "confidence": self.inference.confidence[side] if valid else 0.0,
        }
      lane_timestamp = self.lane_result["updatedMonoTimeNanos"]
      lane_fresh = bool(road_camera_available and self.lane_inference.valid and self.lane_result["valid"] and
                        lane_timestamp > 0 and 0 <= now_nanos - lane_timestamp <= int(LANE_MARKING_MAX_AGE_SEC * 1e9))
      return {
        "standalone": False,
        "integrated": True,
        "model": {
          "path": str(self.inference.model_path),
          "loaded": self.inference.valid,
          "error": self.inference.error,
        },
        "configured": bool(self.config),
        "configuredSides": list(self.inference.configured_sides),
        "gate": self.vasm_gate,
        "threshold": self.threshold,
        "smoothingSeconds": self.smoothing_seconds,
        "baseIntervalSeconds": self.base_interval_seconds,
        "camera": {
          "available": camera_available,
          "error": self.camera_error,
          "lastFrameAgeSeconds": camera_age,
        },
        "imageSide": vehicle_sides,
        "vehicleSide": vehicle_sides,
        "inference": {
          "latencyMs": round(self.last_inference_ms, 1),
          "threadCpuMs": round(self.last_inference_thread_cpu_ms, 1),
          "updatedMonoTimeNanos": vasm_timestamp,
          "fps": self.inference_fps,
          "count": self.inference_count,
          "lastAgeSeconds": round(time.monotonic() - self.last_inference_at, 2) if self.last_inference_at else None,
        },
        "lastInferenceAgeSeconds": time.monotonic() - self.last_inference_at if self.last_inference_at else None,
        "lane": {
          "enabled": True,
          "loaded": self.lane_inference.valid,
          "error": self.lane_inference.error,
          "threshold": self.lane_threshold,
          "intervalSeconds": self.lane_interval_seconds,
          "cameraAvailable": road_camera_available,
          "cameraError": self.lane_camera_error,
          "lastFrameAgeSeconds": road_camera_age,
          "resultFresh": lane_fresh,
          "result": self.lane_result,
          "inference": {
            "latencyMs": round(self.last_lane_inference_ms, 1),
            "threadCpuMs": round(self.last_lane_inference_thread_cpu_ms, 1),
            "fps": self.lane_inference_fps,
            "count": self.lane_inference_count,
            "lastAgeSeconds": round(time.monotonic() - self.last_lane_inference_at, 2) if self.last_lane_inference_at else None,
          },
        },
      }

  def snapshot(self, stream_type: str) -> bytes | None:
    with self.snapshot_condition:
      self.snapshot_requests[stream_type] += 1
      requested = self.snapshot_requests[stream_type]
      self.snapshot_condition.wait_for(
        lambda: self.snapshot_responses[stream_type] >= requested or not self.running,
        timeout=SNAPSHOT_TIMEOUT_SECONDS,
      )
      if self.snapshot_responses[stream_type] < requested:
        return None
      return self.last_road_jpeg if stream_type == "road" else self.last_jpeg

  def _update_vasm_gate(self) -> tuple[bool, str]:
    self.sm.update(0)
    services = ["carState", "modelV2"]
    if not (self.sm.all_alive(services) and self.sm.all_valid(services)):
      gate = {"active": False, "side": "", "reason": "carState or modelV2 is unavailable", "laneWidth": 0.0}
    else:
      speed = float(self.sm["carState"].vEgo)
      direction = self.sm["modelV2"].meta.laneChangeDirection
      if speed < VASM_MIN_SPEED_MPS or speed > VASM_MAX_SPEED_MPS:
        gate = {"active": False, "side": "", "reason": "speed outside 30-120 km/h", "laneWidth": 0.0}
      elif direction == log.LaneChangeDirection.left:
        width = target_lane_space_width(self.sm["modelV2"], direction) or 0.0
        gate = {"active": width >= VASM_MIN_LANE_WIDTH_METERS, "side": "left", "reason": "", "laneWidth": width}
      elif direction == log.LaneChangeDirection.right:
        width = target_lane_space_width(self.sm["modelV2"], direction) or 0.0
        gate = {"active": width >= VASM_MIN_LANE_WIDTH_METERS, "side": "right", "reason": "", "laneWidth": width}
      else:
        gate = {"active": False, "side": "", "reason": "no lane-change direction", "laneWidth": 0.0}
      if gate["side"] and not gate["active"]:
        gate["reason"] = "target lane width below 3.0 m"
    with self.lock:
      self.vasm_gate = gate
    return bool(gate["active"]), str(gate["side"])

  def publish_vision_result(self) -> None:
    status = self.status()
    lane = status["lane"]["result"]
    sides = status["vehicleSide"]
    blindspot_valid = any(side["valid"] for side in status["vehicleSide"].values())
    blindspot_side = next((side for side in ("left", "right") if sides[side]["valid"]), "")
    lane_updated_at = lane["updatedMonoTimeNanos"] * 1e-9
    markings = {
      "navLaneLeftType": "solid" if lane["leftLine"] == 1 else "dashed" if lane["leftLine"] == 0 else "unknown",
      "navLaneRightType": "solid" if lane["rightLine"] == 1 else "dashed" if lane["rightLine"] == 0 else "unknown",
    }
    with self.publish_lock:
      publish_lane_marking_state(
        markings,
        lane_updated_at,
        status["lane"]["inference"]["latencyMs"],
        str(status["lane"]["error"]),
      )
      blindspot_updated_at = status["inference"]["updatedMonoTimeNanos"] * 1e-9
      confidence = sides[blindspot_side]["confidence"] if blindspot_side else 0.0
      publish_blindspot_state(
        sides["left"]["active"] if blindspot_valid else False,
        sides["right"]["active"] if blindspot_valid else False,
        blindspot_side if blindspot_valid else "",
        blindspot_updated_at,
        confidence,
      )

  @staticmethod
  def _jpeg_from_nv12(data: bytes, width: int, height: int, stride: int, uv_offset: int) -> bytes:
    nv12 = pack_nv12(data, width, height, stride, uv_offset)
    rgb = cv2.cvtColor(nv12, cv2.COLOR_YUV2RGB_NV12)
    output = BytesIO()
    Image.fromarray(rgb).save(output, "JPEG", quality=85)
    return output.getvalue()

  @staticmethod
  def _lane_jpeg_from_nv12(data: bytes, width: int, height: int, stride: int) -> bytes:
    """Build the grayscale road-camera input expected by the lane model."""
    class Frame:
      pass
    frame = Frame()
    frame.data, frame.width, frame.height, frame.stride = data, width, height, stride
    gray = prepare_lane_gray(visible_y_plane(frame), cv2)
    output = BytesIO()
    Image.fromarray(gray).save(output, "JPEG", quality=50)
    return output.getvalue()

  def run_camera(self) -> None:
    from msgq.visionipc import VisionIpcClient, VisionStreamType

    client = None
    while self.running:
      try:
        if client is None or not client.is_connected():
          client = VisionIpcClient("camerad", VisionStreamType.VISION_STREAM_WIDE_ROAD, True)
          if not client.connect(False):
            with self.lock:
              self.camera_error = "wide road camera is unavailable; start openpilot/camerad first"
            time.sleep(1.0)
            continue

        buffer = client.recv(timeout_ms=0)
        if buffer is None:
          time.sleep(CAMERA_POLL_INTERVAL_SECONDS)
          continue
        now = time.monotonic()
        gate_active, side = self._update_vasm_gate()
        publish_clear = False
        with self.lock:
          self.last_frame_at = now
          self.camera_error = ""
          if self.snapshot_responses["wide"] < self.snapshot_requests["wide"]:
            self.last_jpeg = self._jpeg_from_nv12(buffer.data, buffer.width, buffer.height, buffer.stride, buffer.uv_offset)
            self.snapshot_responses["wide"] = self.snapshot_requests["wide"]
            self.snapshot_condition.notify_all()
          if not gate_active:
            publish_clear = self.vasm_result["left"] or self.vasm_result["right"]
            self.vasm_result = {"left": False, "right": False, "side": "", "updatedMonoTimeNanos": time.monotonic_ns()}
          else:
            interval = FOLLOWUP_INTERVAL_SECONDS if now < self.followup_until else self.base_interval_seconds
            if now - self.last_inference_at < interval:
              continue
        if not gate_active:
          if publish_clear:
            self.publish_vision_result()
          continue
        with self.vasm_inference_lock:
          configured_sides = self.inference.configured_sides
          if side not in configured_sides or not self.inference.valid:
            continue
          frame = pack_nv12(buffer.data, buffer.width, buffer.height, buffer.stride, buffer.uv_offset)
          previous = self.last_side_at[side]
          t0 = time.monotonic()
          cpu0 = time.thread_time()
          self.inference.update(frame, buffer.width, buffer.height, side, self.threshold, self.smoothing_seconds, now - previous if previous else interval)
          t1 = time.monotonic()
          thread_cpu_ms = (time.thread_time() - cpu0) * 1000.0
          active = self.inference.active[side]
        with self.lock:
          self.last_inference_ms = (t1 - t0) * 1000.0
          self.last_inference_thread_cpu_ms = thread_cpu_ms
          self.inference_count += 1
          self._fps_window_count += 1
          if t1 - self._fps_window_start >= 1.0:
            self.inference_fps = round(self._fps_window_count / (t1 - self._fps_window_start), 1)
            self._fps_window_start = t1
            self._fps_window_count = 0
          self.last_inference_at = self.last_side_at[side] = now
          if active:
            self.followup_until = now + FOLLOWUP_WINDOW_SECONDS
          self.vasm_result = {
            "left": self.inference.active["left"] if side == "left" else False,
            "right": self.inference.active["right"] if side == "right" else False,
            "side": side,
            "updatedMonoTimeNanos": time.monotonic_ns(),
          }
        self.publish_vision_result()
      except (OSError, ValueError, cv2.error) as error:
        with self.lock:
          self.camera_error = str(error)
        client = None
        time.sleep(1.0)

  def run_road_camera(self) -> None:
    from msgq.visionipc import VisionIpcClient, VisionStreamType

    client = None
    while self.running:
      try:
        if client is None or not client.is_connected():
          client = VisionIpcClient("camerad", VisionStreamType.VISION_STREAM_ROAD, True)
          if not client.connect(False):
            with self.lock:
              self.lane_camera_error = "road camera is unavailable; start openpilot/camerad first"
            time.sleep(1.0)
            continue

        buffer = client.recv(timeout_ms=0)
        if buffer is None:
          time.sleep(CAMERA_POLL_INTERVAL_SECONDS)
          continue
        now = time.monotonic()
        with self.lock:
          self.last_road_frame_at = now
          self.lane_camera_error = ""
          if self.snapshot_responses["road"] < self.snapshot_requests["road"]:
            self.last_road_jpeg = self._lane_jpeg_from_nv12(buffer.data, buffer.width, buffer.height, buffer.stride)
            self.snapshot_responses["road"] = self.snapshot_requests["road"]
            self.snapshot_condition.notify_all()
          if not self.lane_inference.valid:
            continue
          if now - self.last_lane_inference_at < self.lane_interval_seconds:
            continue

          lane_threshold = self.lane_threshold
        t0 = time.monotonic()
        cpu0 = time.thread_time()
        res = self.lane_inference.infer(buffer, confidence_threshold=lane_threshold)
        t1 = time.monotonic()
        thread_cpu_ms = (time.thread_time() - cpu0) * 1000.0
        with self.lock:
          self.last_lane_inference_ms = (t1 - t0) * 1000.0
          self.last_lane_inference_thread_cpu_ms = thread_cpu_ms
          self.lane_inference_count += 1
          self._lane_fps_window_count += 1
          if t1 - self._lane_fps_window_start >= 1.0:
            self.lane_inference_fps = round(self._lane_fps_window_count / (t1 - self._lane_fps_window_start), 1)
            self._lane_fps_window_start = t1
            self._lane_fps_window_count = 0

          self.last_lane_inference_at = now
          if res["valid"]:
            for side in ("Left", "Right"):
              raw_type = str(res.get(f"{side.lower()}Type", "unknown"))
              confidence = float(res.get(f"{side.lower()}Conf", 0.0))
              if confidence < lane_threshold:
                raw_type, confidence = "unknown", 0.0
              self.lane_scores[side] = update_score(self.lane_scores[side], raw_type, confidence)
              key = f"navLane{side}Type"
              self.lane_types[key] = score_to_type(self.lane_scores[side], self.lane_types[key])
            left_type = self.lane_types["navLaneLeftType"]
            right_type = self.lane_types["navLaneRightType"]
            self.lane_result = {
              "leftLine": 1 if left_type == "solid" else 0 if left_type == "dashed" else -1,
              "rightLine": 1 if right_type == "solid" else 0 if right_type == "dashed" else -1,
              "leftConf": float(res.get("leftConf", 0.0)),
              "rightConf": float(res.get("rightConf", 0.0)),
              "candidatesCount": int(res.get("candidatesCount", 0)),
              "valid": True,
              "error": "",
              "updatedMonoTimeNanos": time.monotonic_ns(),
            }
          else:
            self.lane_result["error"] = str(res.get("error", "lane inference failed"))
        self.publish_vision_result()
        # Let realtime planning work run between consecutive ONNX passes when
        # inference itself takes longer than the configured start interval.
        time.sleep(LANE_INFERENCE_YIELD_SECONDS)
      except (OSError, ValueError, cv2.error) as error:
        with self.lock:
          self.lane_camera_error = str(error)
        client = None
        time.sleep(1.0)


class Handler(BaseHTTPRequestHandler):
  service: VASMService
  index_path = Path(__file__).resolve().parent / "web.html"

  def handle_one_request(self) -> None:
    try:
      super().handle_one_request()
    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
      return

  def _json(self, status: HTTPStatus, payload: object) -> None:
    body = json.dumps(payload).encode()
    self.send_response(status)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(body)))
    self.send_header("Cache-Control", "no-store")
    self.end_headers()
    self.wfile.write(body)

  def do_GET(self) -> None:
    path = urlparse(self.path).path
    if path == "/":
      body = self.index_path.read_bytes()
      self.send_response(HTTPStatus.OK)
      self.send_header("Content-Type", "text/html; charset=utf-8")
      self.send_header("Content-Length", str(len(body)))
      self.end_headers()
      self.wfile.write(body)
    elif path == "/api/status":
      self._json(HTTPStatus.OK, self.service.status())
    elif path == "/api/config":
      self._json(HTTPStatus.OK, self.service.config)
    elif path == "/api/snapshot":
      parsed_url = urlparse(self.path)
      stream_type = "wide"
      if "stream=road" in parsed_url.query:
        stream_type = "road"
      jpeg = self.service.snapshot(stream_type)
      if jpeg is None:
        self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": f"no {stream_type} camera frame available"})
        return
      self.send_response(HTTPStatus.OK)
      self.send_header("Content-Type", "image/jpeg")
      self.send_header("Content-Length", str(len(jpeg)))
      self.send_header("Cache-Control", "no-store")
      self.end_headers()
      self.wfile.write(jpeg)
    else:
      self.send_error(HTTPStatus.NOT_FOUND)

  def do_POST(self) -> None:
    path = urlparse(self.path).path
    try:
      length = int(self.headers.get("Content-Length", "0"))
      if not 0 < length <= 65536:
        raise ValueError("request body must be 1 to 65536 bytes")
      payload = json.loads(self.rfile.read(length))
      if path == "/api/config":
        self._json(HTTPStatus.OK, self.service.save_config(payload))
      elif path == "/api/settings":
        self._json(HTTPStatus.OK, self.service.set_settings(payload))
      else:
        self.send_error(HTTPStatus.NOT_FOUND)
    except (ValueError, json.JSONDecodeError) as error:
      self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})

  def do_DELETE(self) -> None:
    if urlparse(self.path).path != "/api/config":
      self.send_error(HTTPStatus.NOT_FOUND)
      return
    self.service.clear_config()
    self._json(HTTPStatus.OK, {"success": True})

  def log_message(self, _format: str, *_args) -> None:
    return


def main() -> None:
  parser = argparse.ArgumentParser(description="Xiaoge vision server")
  parser.add_argument("--host", default=HOST)
  parser.add_argument("--port", type=int, default=PORT)
  parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
  args = parser.parse_args()
  if not 1 <= args.port <= 65535:
    parser.error("port must be 1 through 65535")

  service, server = create_server(args.host, args.port, args.model)
  print(f"Xiaoge vision server: http://{args.host}:{args.port}")
  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass
  finally:
    server.server_close()
    service.running = False


def create_server(host: str = HOST, port: int = PORT, model_path: Path = DEFAULT_MODEL_PATH) -> tuple[VASMService, ThreadingHTTPServer]:
  # Camera wakeups can leave receivers on camerad's isolated CPU, where realtime
  # driving tasks take precedence. Set affinity before OpenCV creates workers so
  # both inference and camera threads stay on the background cores.
  if sys.platform == "linux":
    from openpilot.common.realtime import set_core_affinity
    set_core_affinity([0, 1, 2, 3])
  cv2.setNumThreads(1)
  service = VASMService(model_path)
  Handler.service = service
  server = ThreadingHTTPServer((host, port), Handler)
  threading.Thread(target=service.run_camera, daemon=True).start()
  threading.Thread(target=service.run_road_camera, daemon=True).start()
  return service, server


if __name__ == "__main__":
  main()
