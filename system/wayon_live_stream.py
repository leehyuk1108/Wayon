#!/usr/bin/env python3
import json
import os
import queue
import select
import socket
import struct
import subprocess
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openpilot.system.camera_lease import CameraLease
from openpilot.system.wayon_live_archive import (
  build_dual_h264_archive,
  frame_duration_s,
  select_recent_frames,
  upload_live_capture,
  utc_now,
)


CONFIG_PATH = Path(os.getenv("WAYON_CLOUD_CONFIG", "/data/wayon_cloud/config.json"))
LISTEN_HOST = os.getenv("WAYON_LIVE_HOST", "0.0.0.0")
LISTEN_PORT = int(os.getenv("WAYON_LIVE_PORT", "8765"))
LIVE_BITRATE = 5_000_000
DEFAULT_MAX_SESSION_S = 300.0
DEFAULT_CAMERA_WAIT_S = 30.0
DEFAULT_PROCESS_WAIT_S = 10.0
MIN_SESSION_S = 30.0
MAX_SESSION_S = 900.0
CLIENT_HEARTBEAT_TIMEOUT_S = 12.0
WAYON_LIVE_ACTIVE_PATH = Path(os.getenv("WAYON_LIVE_ACTIVE_PATH", "/tmp/wayon_live.active"))

CLIENT_HEARTBEAT_MAGIC = b"WLP1"
CLIENT_CONTROL_MAGIC = b"WLC1"
CLIENT_CONTROL_HEADER = struct.Struct(">4sBI")
CLIENT_CONTROL_PHOTO = 1
CLIENT_CONTROL_CLIP = 2
MAX_CONTROL_PAYLOAD = 8 * 1024 * 1024
MAX_CLIP_BUFFER_S = 36.0
MAX_PENDING_ARCHIVES = 3

FRAME_MAGIC = b"WLV1"
FRAME_HEADER = struct.Struct(">4sBBHIQI")
FRAME_TYPE_METADATA = 0
FRAME_TYPE_WIDE = 1
FRAME_TYPE_DRIVER = 2
FRAME_TYPE_STATUS = 3
FRAME_FLAG_KEY = 1

STREAM_SERVICES = {
  "livestreamWideRoadEncodeData": FRAME_TYPE_WIDE,
  "livestreamDriverEncodeData": FRAME_TYPE_DRIVER,
}

ARCHIVE_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="wayon-live-archive")


class ClientControlState:
  def __init__(self):
    self.heartbeat_seen = False
    self.last_heartbeat = time.monotonic()
    self.buffer = bytearray()
    self.commands = queue.SimpleQueue()

  def feed(self, data: bytes) -> None:
    if not data:
      return

    self.buffer.extend(data)
    while self.buffer:
      if self.buffer.startswith(CLIENT_HEARTBEAT_MAGIC):
        del self.buffer[:len(CLIENT_HEARTBEAT_MAGIC)]
        self.heartbeat_seen = True
        self.last_heartbeat = time.monotonic()
        continue

      if self.buffer.startswith(CLIENT_CONTROL_MAGIC):
        if len(self.buffer) < CLIENT_CONTROL_HEADER.size:
          return
        _magic, command_type, payload_size = CLIENT_CONTROL_HEADER.unpack_from(self.buffer)
        if payload_size > MAX_CONTROL_PAYLOAD:
          del self.buffer[:len(CLIENT_CONTROL_MAGIC)]
          continue
        frame_size = CLIENT_CONTROL_HEADER.size + payload_size
        if len(self.buffer) < frame_size:
          return
        payload = bytes(self.buffer[CLIENT_CONTROL_HEADER.size:frame_size])
        del self.buffer[:frame_size]
        self.commands.put((command_type, payload))
        continue

      marker_indexes = [
        index for index in (
          self.buffer.find(CLIENT_HEARTBEAT_MAGIC, 1),
          self.buffer.find(CLIENT_CONTROL_MAGIC, 1),
        ) if index >= 0
      ]
      if marker_indexes:
        del self.buffer[:min(marker_indexes)]
        continue

      keep = b""
      payload = bytes(self.buffer)
      for length in range(min(3, len(payload)), 0, -1):
        suffix = payload[-length:]
        if CLIENT_HEARTBEAT_MAGIC.startswith(suffix) or CLIENT_CONTROL_MAGIC.startswith(suffix):
          keep = suffix
          break
      self.buffer = bytearray(keep)
      return

  def pop_commands(self):
    commands = []
    while True:
      try:
        commands.append(self.commands.get_nowait())
      except queue.Empty:
        return commands


def read_client_control(client: socket.socket, state: ClientControlState, timeout_s: float = 0.0) -> bool:
  try:
    readable, _, _ = select.select([client], [], [], max(0.0, timeout_s))
    while readable:
      data = client.recv(4096)
      if not data:
        return False
      state.feed(data)
      readable, _, _ = select.select([client], [], [], 0.0)
    return True
  except (ConnectionError, OSError, ValueError):
    return False


class ClientHeartbeatMonitor:
  def __init__(self, client: socket.socket, state: ClientControlState,
               timeout_s: float = CLIENT_HEARTBEAT_TIMEOUT_S, poll_s: float = 0.25):
    self.client = client
    self.state = state
    self.timeout_s = timeout_s
    self.poll_s = poll_s
    self.client_alive = True
    self.timed_out = False
    self.stop_event = threading.Event()
    self.thread = threading.Thread(target=self._run, name="wayon-live-heartbeat", daemon=True)

  def start(self) -> None:
    self.thread.start()

  def stop(self) -> None:
    self.stop_event.set()
    if self.thread.is_alive():
      self.thread.join(timeout=max(1.0, self.poll_s * 2.0))

  def _close_client(self) -> None:
    try:
      self.client.shutdown(socket.SHUT_RDWR)
    except OSError:
      pass

  def _run(self) -> None:
    while not self.stop_event.is_set():
      if not read_client_control(self.client, self.state, self.poll_s):
        self.client_alive = False
        self._close_client()
        return

      if time.monotonic() - self.state.last_heartbeat > self.timeout_s:
        self.client_alive = False
        self.timed_out = True
        print("Wayon live: viewer heartbeat timed out", flush=True)
        self._close_client()
        return


class ClipFrameStore:
  def __init__(self, max_buffer_s: float = MAX_CLIP_BUFFER_S):
    self.max_buffer_s = max_buffer_s
    self.lock = threading.Lock()
    self.buffers = {
      FRAME_TYPE_WIDE: deque(),
      FRAME_TYPE_DRIVER: deque(),
    }

  def append(self, frame_type: int, frame) -> None:
    received_at = frame[0]
    with self.lock:
      frame_buffer = self.buffers[frame_type]
      frame_buffer.append(frame)
      cutoff = received_at - self.max_buffer_s
      while frame_buffer and frame_buffer[0][0] < cutoff:
        frame_buffer.popleft()

  def recent_pair(self, duration_s: float, now_s: float):
    with self.lock:
      wide = list(self.buffers[FRAME_TYPE_WIDE])
      driver = list(self.buffers[FRAME_TYPE_DRIVER])
    return (
      select_recent_frames(wide, duration_s, now_s),
      select_recent_frames(driver, duration_s, now_s),
    )


class ClipFrameCollector:
  def __init__(self, messaging, frame_store: ClipFrameStore):
    self.messaging = messaging
    self.frame_store = frame_store
    self.stop_event = threading.Event()
    self.thread = threading.Thread(target=self._run, name="wayon-live-clip-buffer", daemon=True)

  def start(self) -> None:
    self.thread.start()

  def stop(self) -> None:
    self.stop_event.set()
    if self.thread.is_alive():
      self.thread.join(timeout=2.0)

  def _run(self) -> None:
    poller = self.messaging.Poller()
    _stream_sockets = [
      self.messaging.sub_sock(service, poller=poller, conflate=False)
      for service in STREAM_SERVICES
    ]
    try:
      while not self.stop_event.is_set():
        for stream_socket in poller.poll(250):
          event = self.messaging.recv_one_or_none(stream_socket)
          if event is None:
            continue
          service = event.which()
          encoded = getattr(event, service)
          payload, key_frame = encoded_payload(encoded)
          frame_type = STREAM_SERVICES[service]
          timestamp_us = int(encoded.idx.timestampEof // 1000)
          self.frame_store.append(
            frame_type,
            (time.monotonic(), payload, key_frame, timestamp_us),
          )
    except Exception as exc:
      print(f"Wayon live: clip collector failed: {exc}", flush=True)


def read_config(path: Path = CONFIG_PATH) -> dict:
  try:
    with path.open("r", encoding="utf-8") as handle:
      config = json.load(handle)
      return config if isinstance(config, dict) else {}
  except (OSError, ValueError):
    return {}


def bounded_number(value, fallback: float, minimum: float, maximum: float) -> float:
  try:
    return min(maximum, max(minimum, float(value)))
  except (TypeError, ValueError):
    return fallback


def pack_frame(frame_type: int, payload: bytes, sequence: int = 0,
               timestamp_us: int = 0, key_frame: bool = False) -> bytes:
  flags = FRAME_FLAG_KEY if key_frame else 0
  header = FRAME_HEADER.pack(
    FRAME_MAGIC,
    frame_type,
    flags,
    0,
    sequence & 0xFFFFFFFF,
    timestamp_us & 0xFFFFFFFFFFFFFFFF,
    len(payload),
  )
  return header + payload


def json_frame(frame_type: int, data: dict) -> bytes:
  return pack_frame(frame_type, json.dumps(data, separators=(",", ":")).encode("utf-8"))


def encoded_payload(encoded) -> tuple[bytes, bool]:
  codec_header = bytes(encoded.header)
  return codec_header + bytes(encoded.data), bool(codec_header)


def process_running(name: str, proc_root: Path = Path("/proc")) -> bool:
  try:
    entries = os.scandir(proc_root)
  except OSError:
    return subprocess.run(
      ["pgrep", "-x", name],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      check=False,
    ).returncode == 0

  with entries:
    for entry in entries:
      if not entry.name.isdigit():
        continue
      try:
        with open(os.path.join(entry.path, "comm"), encoding="utf-8") as handle:
          if handle.read().strip() == name:
            return True
      except OSError:
        continue
  return False


def wait_for_processes(names: tuple[str, ...], timeout_s: float = DEFAULT_PROCESS_WAIT_S,
                       poll_s: float = 0.05) -> bool:
  deadline = time.monotonic() + timeout_s
  while not all(process_running(name) for name in names):
    if time.monotonic() >= deadline:
      return False
    time.sleep(poll_s)
  return True


def set_live_active(active: bool, path: Path = WAYON_LIVE_ACTIVE_PATH) -> None:
  if active:
    path.write_text(str(os.getpid()), encoding="ascii")
    return
  try:
    path.unlink()
  except FileNotFoundError:
    pass


def camera_busy(params) -> bool:
  return params.get_bool("IsTakingSnapshot") or process_running("encoderd")


def wait_for_camera(params, timeout_s: float = DEFAULT_CAMERA_WAIT_S,
                    poll_s: float = 0.25) -> bool:
  deadline = time.monotonic() + timeout_s
  while is_offroad(params) and camera_busy(params):
    if time.monotonic() >= deadline:
      return False
    time.sleep(poll_s)
  return is_offroad(params) and not camera_busy(params)


def is_offroad(params) -> bool:
  return params.get_bool("IsOffroad") and not params.get_bool("IsOnroad")


def stream_metadata(bitrate: int, max_session_s: float) -> dict:
  return {
    "schema": "wayon-live-v1",
    "codec": "avc1.640020",
    "annexB": True,
    "width": 1344,
    "height": 760,
    "fps": 20,
    "bitratePerCamera": bitrate,
    "maxSessionSeconds": int(max_session_s),
    "cameras": ["wide", "driver"],
    "panorama": {
      "wideYawDeg": 0.0,
      "wideFovDeg": 205.0,
      "widePitchDeg": -4.0,
      "driverYawDeg": 180.0,
      "driverFovDeg": 205.0,
      "driverPitchDeg": -20.0,
      "driverMirror": False,
      "wideVerticalFovDeg": 128.0,
      "driverVerticalFovDeg": 128.0,
      "wideRadialDistortion": [-0.018, 0.006],
      "driverRadialDistortion": [-0.018, 0.006],
      "wideOpticalCenter": [0.5, 0.5],
      "driverOpticalCenter": [0.5, 0.5],
      "wideVignetteCompensation": 0.045,
      "driverVignetteCompensation": 0.045,
      "blendDeg": 24.0,
    },
  }


def send_terminal(client: socket.socket, state: str, message: str = "") -> None:
  payload = {"state": state}
  if message:
    payload["message"] = message
  client.sendall(json_frame(FRAME_TYPE_STATUS, payload))
  # Give the TCP/WebSocket bridge time to forward a short final frame before EOF.
  time.sleep(0.25)


def param_text(params, key: str) -> str:
  value = params.get(key)
  return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value or "")


def send_capture_status(client: socket.socket, capture_state: str, kind: str,
                        message: str = "", duration_s: float | None = None,
                        capture_id: str | None = None) -> None:
  payload = {
    "state": "capture",
    "captureState": capture_state,
    "kind": kind,
  }
  if message:
    payload["message"] = message
  if duration_s is not None:
    payload["durationSeconds"] = round(duration_s, 3)
  if capture_id:
    payload["captureId"] = capture_id
  client.sendall(json_frame(FRAME_TYPE_STATUS, payload))


def upload_clip_archive(config: dict, device_id: str, captured_at: str, duration_s: float,
                        requested_duration_s: int, wide_frames, driver_frames,
                        metadata: dict) -> dict:
  archive = build_dual_h264_archive(
    wide_frames,
    driver_frames,
    captured_at,
    requested_duration_s,
    metadata,
  )
  try:
    return upload_live_capture(
      config,
      device_id,
      "clip",
      captured_at,
      "application/zip",
      "dual_h264_360",
      archive,
      duration_s,
    )
  except Exception as exc:
    raise RuntimeError(f"archive_bytes={len(archive)} {type(exc).__name__}: {exc}") from exc


def process_capture_commands(client: socket.socket, control: ClientControlState,
                             config: dict, device_id: str, frame_store: ClipFrameStore,
                             metadata: dict, pending_archives: list) -> None:
  for command_type, payload in control.pop_commands():
    if len(pending_archives) >= MAX_PENDING_ARCHIVES:
      send_capture_status(client, "error", "unknown", "archive_queue_full")
      continue

    captured_at = utc_now()
    if command_type == CLIENT_CONTROL_PHOTO:
      if len(payload) < 4 or not payload.startswith(b"\xff\xd8") or not payload.endswith(b"\xff\xd9"):
        send_capture_status(client, "error", "photo", "invalid_jpeg")
        continue
      future = ARCHIVE_EXECUTOR.submit(
        upload_live_capture,
        config,
        device_id,
        "photo",
        captured_at,
        "image/jpeg",
        "equirectangular_360",
        payload,
      )
      pending_archives.append((future, {"kind": "photo", "duration": None}))
      send_capture_status(client, "uploading", "photo")
      continue

    if command_type != CLIENT_CONTROL_CLIP or len(payload) != 1 or payload[0] not in (10, 30):
      send_capture_status(client, "error", "unknown", "invalid_capture_command")
      continue

    requested_duration = int(payload[0])
    now = time.monotonic()
    wide_frames, driver_frames = frame_store.recent_pair(requested_duration, now)
    actual_duration = min(
      frame_duration_s(wide_frames),
      frame_duration_s(driver_frames),
    ) if wide_frames and driver_frames else 0.0
    if actual_duration < requested_duration * 0.9:
      send_capture_status(client, "buffering", "clip", duration_s=actual_duration)
      continue

    future = ARCHIVE_EXECUTOR.submit(
      upload_clip_archive,
      config,
      device_id,
      captured_at,
      actual_duration,
      requested_duration,
      wide_frames,
      driver_frames,
      metadata,
    )
    pending_archives.append((future, {"kind": "clip", "duration": actual_duration}))
    send_capture_status(client, "uploading", "clip", duration_s=actual_duration)


def process_archive_results(client: socket.socket, pending_archives: list) -> None:
  remaining = []
  for future, info in pending_archives:
    if not future.done():
      remaining.append((future, info))
      continue
    try:
      result = future.result()
      send_capture_status(
        client,
        "saved",
        info["kind"],
        duration_s=info["duration"],
        capture_id=str(result.get("id") or ""),
      )
    except Exception as exc:
      print(f"Wayon live: archive upload failed: {exc}", flush=True)
      send_capture_status(client, "error", info["kind"], str(exc)[:220], duration_s=info["duration"])
  pending_archives[:] = remaining


def run_stream(client: socket.socket) -> None:
  from cereal import messaging
  from openpilot.common.params import Params
  from openpilot.selfdrive.selfdrived.alertmanager import set_offroad_alert

  params = Params()
  if not is_offroad(params):
    send_terminal(client, "onroad", "Offroad only")
    return

  control = ClientControlState()
  config = read_config()
  bitrate = LIVE_BITRATE
  max_session_s = bounded_number(
    config.get("live_stream_max_session_s", DEFAULT_MAX_SESSION_S),
    DEFAULT_MAX_SESSION_S,
    MIN_SESSION_S,
    MAX_SESSION_S,
  )
  metadata = stream_metadata(bitrate, max_session_s)
  device_id = str(config.get("device_id") or param_text(params, "DongleId") or "unknown")

  lease = CameraLease("wayon_live", max_session_s + DEFAULT_CAMERA_WAIT_S + 30.0)
  if not lease.acquire():
    send_terminal(client, "busy", "Camera is busy")
    return

  snapshot_flag_set = False
  live_flag_set = False
  monitor = None
  collector = None
  try:
    if not wait_for_camera(params):
      state = "onroad" if not is_offroad(params) else "busy"
      send_terminal(client, state, "Offroad only" if state == "onroad" else "Camera is busy")
      return

    monitor = ClientHeartbeatMonitor(client, control)
    monitor.start()
    params.put_bool("IsTakingSnapshot", True, block=True)
    snapshot_flag_set = True
    set_offroad_alert("Offroad_IsTakingSnapshot", True)

    try:
      client.sendall(json_frame(FRAME_TYPE_METADATA, {
        **metadata,
        "state": "starting",
      }))

      poller = messaging.Poller()
      _stream_sockets = [
        messaging.sub_sock(service, poller=poller, conflate=True)
        for service in STREAM_SERVICES
      ]
      frame_store = ClipFrameStore()
      collector = ClipFrameCollector(messaging, frame_store)
      collector.start()

      set_live_active(True)
      live_flag_set = True
      if not wait_for_processes(("camerad", "encoderd")):
        send_terminal(client, "error", "Camera startup timed out")
        return

      client.sendall(json_frame(FRAME_TYPE_STATUS, {"state": "live"}))
      started_at = time.monotonic()
      sequence = 0
      pending_archives = []
      while monitor.client_alive and is_offroad(params) and time.monotonic() - started_at < max_session_s:
        process_archive_results(client, pending_archives)
        process_capture_commands(client, control, config, device_id, frame_store, metadata, pending_archives)
        for stream_socket in poller.poll(1000):
          event = messaging.recv_one_or_none(stream_socket)
          if event is None:
            continue
          service = event.which()
          encoded = getattr(event, service)
          payload, key_frame = encoded_payload(encoded)
          frame_type = STREAM_SERVICES[service]
          timestamp_us = int(encoded.idx.timestampEof // 1000)
          client.sendall(pack_frame(
            frame_type,
            payload,
            sequence=sequence,
            timestamp_us=timestamp_us,
            key_frame=key_frame,
          ))
          sequence += 1
        process_archive_results(client, pending_archives)
        process_capture_commands(client, control, config, device_id, frame_store, metadata, pending_archives)

      if monitor.client_alive and not monitor.timed_out:
        state = "onroad" if not is_offroad(params) else "expired"
        client.sendall(json_frame(FRAME_TYPE_STATUS, {"state": state}))
    except (BrokenPipeError, ConnectionError, OSError) as exc:
      print(f"Wayon live: stream transport failed: {type(exc).__name__}: {exc}", flush=True)
    finally:
      if collector is not None:
        collector.stop()
  finally:
    if live_flag_set:
      set_live_active(False)
    if monitor is not None:
      monitor.stop()
    if snapshot_flag_set:
      params.put_bool("IsTakingSnapshot", False, block=True)
      set_offroad_alert("Offroad_IsTakingSnapshot", False)
    lease.release()


def main() -> None:
  set_live_active(False)
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(1)
    server.settimeout(1.0)
    print(f"Wayon live: listening on {LISTEN_HOST}:{LISTEN_PORT}", flush=True)

    while True:
      try:
        client, address = server.accept()
      except TimeoutError:
        continue

      print(f"Wayon live: viewer connected from {address[0]}", flush=True)
      with client:
        client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        client.settimeout(10.0)
        try:
          run_stream(client)
        except Exception as exc:
          print(f"Wayon live: session failed: {exc}", flush=True)
          try:
            send_terminal(client, "error")
          except OSError:
            pass
      print("Wayon live: viewer disconnected", flush=True)


if __name__ == "__main__":
  main()
