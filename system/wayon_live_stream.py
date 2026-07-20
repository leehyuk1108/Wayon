#!/usr/bin/env python3
import json
import os
import socket
import struct
import subprocess
import time
from pathlib import Path


CONFIG_PATH = Path(os.getenv("WAYON_CLOUD_CONFIG", "/data/wayon_cloud/config.json"))
LISTEN_HOST = os.getenv("WAYON_LIVE_HOST", "0.0.0.0")
LISTEN_PORT = int(os.getenv("WAYON_LIVE_PORT", "8765"))
DEFAULT_BITRATE = 800_000
DEFAULT_MAX_SESSION_S = 300.0
MIN_BITRATE = 250_000
MAX_BITRATE = 2_000_000
MIN_SESSION_S = 30.0
MAX_SESSION_S = 900.0

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


def process_running(name: str) -> bool:
  return subprocess.run(
    ["pgrep", "-x", name],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=False,
  ).returncode == 0


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
      "driverMirror": True,
      "blendDeg": 16.0,
    },
  }


def run_stream(client: socket.socket) -> None:
  from cereal import messaging
  from openpilot.common.params import Params
  from openpilot.selfdrive.selfdrived.alertmanager import set_offroad_alert
  from openpilot.system.manager.process_config import managed_processes

  params = Params()
  if not is_offroad(params):
    client.sendall(json_frame(FRAME_TYPE_STATUS, {"state": "onroad", "message": "Offroad only"}))
    return
  if params.get_bool("IsTakingSnapshot") or process_running("encoderd"):
    client.sendall(json_frame(FRAME_TYPE_STATUS, {"state": "busy", "message": "Camera is busy"}))
    return

  config = read_config()
  bitrate = int(bounded_number(
    config.get("live_stream_bitrate", DEFAULT_BITRATE),
    DEFAULT_BITRATE,
    MIN_BITRATE,
    MAX_BITRATE,
  ))
  max_session_s = bounded_number(
    config.get("live_stream_max_session_s", DEFAULT_MAX_SESSION_S),
    DEFAULT_MAX_SESSION_S,
    MIN_SESSION_S,
    MAX_SESSION_S,
  )

  started_processes = []
  params.put_bool("IsTakingSnapshot", True, block=True)
  set_offroad_alert("Offroad_IsTakingSnapshot", True)
  client.sendall(json_frame(FRAME_TYPE_METADATA, {
    **stream_metadata(bitrate, max_session_s),
    "state": "starting",
  }))

  try:
    poller = messaging.Poller()
    _stream_sockets = [
      messaging.sub_sock(service, poller=poller, conflate=True)
      for service in STREAM_SERVICES
    ]

    os.environ["STREAM_BITRATE"] = str(bitrate)
    for process_name in ("camerad", "stream_encoderd"):
      if process_name == "camerad" and process_running("camerad"):
        continue
      managed_processes[process_name].start()
      started_processes.append(process_name)

    client.sendall(json_frame(FRAME_TYPE_STATUS, {"state": "live"}))
    started_at = time.monotonic()
    sequence = 0
    while is_offroad(params) and time.monotonic() - started_at < max_session_s:
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

    state = "onroad" if not is_offroad(params) else "expired"
    client.sendall(json_frame(FRAME_TYPE_STATUS, {"state": state}))
  except (BrokenPipeError, ConnectionError, OSError):
    pass
  finally:
    for process_name in reversed(started_processes):
      managed_processes[process_name].stop()
    params.put_bool("IsTakingSnapshot", False, block=True)
    set_offroad_alert("Offroad_IsTakingSnapshot", False)


def main() -> None:
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
            client.sendall(json_frame(FRAME_TYPE_STATUS, {"state": "error"}))
          except OSError:
            pass
      print("Wayon live: viewer disconnected", flush=True)


if __name__ == "__main__":
  main()
