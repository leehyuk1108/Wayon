#!/usr/bin/env python3
import math
import subprocess
import time

import numpy as np
from PIL import Image

import cereal.messaging as messaging
from msgq.visionipc import VisionIpcClient, VisionStreamType
from openpilot.common.params import Params
from openpilot.common.realtime import DT_MDL
from openpilot.system.camera_lease import CameraLease
from openpilot.system.hardware import PC
from openpilot.selfdrive.selfdrived.alertmanager import set_offroad_alert
from openpilot.system.manager.process_config import managed_processes


VISION_STREAMS = {
  "roadCameraState": VisionStreamType.VISION_STREAM_ROAD,
  "driverCameraState": VisionStreamType.VISION_STREAM_DRIVER,
  "wideRoadCameraState": VisionStreamType.VISION_STREAM_WIDE_ROAD,
}

DEFAULT_SNAPSHOT_TIMEOUT_S = 30.0
SNAPSHOT_POLL_MS = 100


def jpeg_write(fn, dat):
  img = Image.fromarray(dat)
  img.save(fn, "JPEG")


def yuv_to_rgb(y, u, v):
  ul = np.repeat(np.repeat(u, 2).reshape(u.shape[0], y.shape[1]), 2, axis=0).reshape(y.shape)
  vl = np.repeat(np.repeat(v, 2).reshape(v.shape[0], y.shape[1]), 2, axis=0).reshape(y.shape)

  yuv = np.dstack((y, ul, vl)).astype(np.int16)
  yuv[:, :, 1:] -= 128

  m = np.array([
    [1.00000,  1.00000, 1.00000],
    [0.00000, -0.39465, 2.03211],
    [1.13983, -0.58060, 0.00000],
  ])
  rgb = np.dot(yuv, m).clip(0, 255)
  return rgb.astype(np.uint8)


def extract_image(buf):
  # NV12 format: Y plane followed by interleaved UV plane
  # UV plane size is stride * uv_height, where uv_height = align(height/2, 16)
  uv_height = ((buf.height // 2) + 15) // 16 * 16
  uv_plane_size = buf.stride * uv_height

  y = np.array(buf.data[:buf.uv_offset], dtype=np.uint8).reshape((-1, buf.stride))[:buf.height, :buf.width]
  uv_data = buf.data[buf.uv_offset:buf.uv_offset + uv_plane_size]
  u = np.array(uv_data[::2], dtype=np.uint8).reshape((-1, buf.stride//2))[:buf.height//2, :buf.width//2]
  v = np.array(uv_data[1::2], dtype=np.uint8).reshape((-1, buf.stride//2))[:buf.height//2, :buf.width//2]

  return yuv_to_rgb(y, u, v)


def _remaining_timeout_ms(deadline: float, stage: str) -> int:
  remaining_s = deadline - time.monotonic()
  if remaining_s <= 0.0:
    raise TimeoutError(f"camera snapshot timed out while {stage}")
  return max(1, min(SNAPSHOT_POLL_MS, int(remaining_s * 1000)))


def exposure_near_target(frame_data, ready_ratio: float) -> bool:
  measured = float(frame_data.measuredGreyFraction)
  target = float(frame_data.targetGreyFraction)
  ratio = max(0.0, min(1.0, float(ready_ratio)))
  return (math.isfinite(measured) and math.isfinite(target) and target > 0.0 and
          measured >= target * ratio)


def get_snapshots(frame="roadCameraState", front_frame="driverCameraState",
                  warmup_s=4.0, front_warmup_s=None,
                  timeout_s: float = DEFAULT_SNAPSHOT_TIMEOUT_S,
                  exposure_ready_ratio: float | None = None,
                  exposure_stable_frames: int = 3,
                  exposure_max_wait_s: float = 5.0):
  sockets = [s for s in (frame, front_frame) if s is not None]
  if not sockets:
    return None, None

  deadline = time.monotonic() + max(1.0, float(timeout_s))
  sm = messaging.SubMaster(sockets)
  vipc_clients = {s: VisionIpcClient("camerad", VISION_STREAMS[s], True) for s in sockets}

  warmup_by_service = {
    frame: max(0.0, float(warmup_s)) if frame is not None else 0.0,
    front_frame: max(0.0, float(warmup_s if front_warmup_s is None else front_warmup_s)) if front_frame is not None else 0.0,
  }

  def wait_for_warmup():
    first_frame_ids = {}
    exposure_started_at = {}
    stable_counts = {service: 0 for service in sockets}
    ready = set()
    required_stable_frames = max(1, int(exposure_stable_frames))
    max_exposure_wait_s = max(0.0, float(exposure_max_wait_s))

    while len(ready) < len(sockets):
      pending = next(service for service in sockets if service not in ready)
      sm.update(_remaining_timeout_ms(deadline, f"waiting for {pending} exposure"))
      now = time.monotonic()

      for service in sockets:
        if service in ready:
          continue

        frame_id = int(sm[service].frameId)
        if frame_id <= 0:
          continue
        if service not in first_frame_ids:
          first_frame_ids[service] = frame_id
          exposure_started_at[service] = now

        minimum_frames = int(warmup_by_service[service] / DT_MDL)
        if frame_id - first_frame_ids[service] < minimum_frames:
          continue
        if exposure_ready_ratio is None:
          ready.add(service)
          continue

        if sm.updated[service]:
          if exposure_near_target(sm[service], exposure_ready_ratio):
            stable_counts[service] += 1
          else:
            stable_counts[service] = 0

        waited_s = now - exposure_started_at[service]
        if stable_counts[service] >= required_stable_frames or waited_s >= max_exposure_wait_s:
          ready.add(service)

  def connect(service):
    client = vipc_clients[service]
    while not client.connect(False):
      _remaining_timeout_ms(deadline, f"connecting to {service}")
      time.sleep(0.02)
    return client

  def receive(service):
    client = connect(service)
    buffer = None
    while buffer is None:
      buffer = client.recv(timeout_ms=_remaining_timeout_ms(deadline, f"receiving {service}"))
    return buffer

  rear, front = None, None
  wait_for_warmup()
  if frame is not None:
    rear = extract_image(receive(frame))
  if front_frame is not None:
    front = extract_image(receive(front_frame))
  return rear, front


def snapshot():
  params = Params()

  if not params.get_bool("IsOffroad"):
    print("Already taking snapshot")
    return None, None

  lease = CameraLease("snapshot", 45.0)
  if not lease.acquire():
    print("Camera is leased by another process")
    return None, None

  snapshot_flag_set = False
  try:
    if params.get_bool("IsTakingSnapshot"):
      print("Already taking snapshot")
      return None, None

    front_camera_allowed = params.get_bool("RecordFront")
    params.put_bool("IsTakingSnapshot", True, block=True)
    snapshot_flag_set = True
    set_offroad_alert("Offroad_IsTakingSnapshot", True)
    time.sleep(2.0)  # Give hardwared time to read the param, or if just started give camerad time to start

    try:
      subprocess.check_call(["pgrep", "camerad"])
      print("Camerad already running")
      return None, None
    except subprocess.CalledProcessError:
      pass

    started_camerad = False
    try:
      # Allow testing on replay on PC
      if not PC:
        managed_processes['camerad'].start()
        started_camerad = True

      frame = "wideRoadCameraState"
      front_frame = "driverCameraState" if front_camera_allowed else None
      rear, front = get_snapshots(frame, front_frame)
    finally:
      if started_camerad:
        managed_processes['camerad'].stop()

    if not front_camera_allowed:
      front = None

    return rear, front
  finally:
    if snapshot_flag_set:
      params.put_bool("IsTakingSnapshot", False, block=True)
      set_offroad_alert("Offroad_IsTakingSnapshot", False)
    lease.release()


if __name__ == "__main__":
  pic, fpic = snapshot()
  if pic is not None:
    print(pic.shape)
    jpeg_write("/tmp/back.jpg", pic)
    if fpic is not None:
      jpeg_write("/tmp/front.jpg", fpic)
  else:
    print("Error taking snapshot")
