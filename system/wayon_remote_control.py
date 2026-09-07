#!/usr/bin/env python3
import ipaddress
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time
from typing import Protocol
from urllib.parse import urlparse

from openpilot.system.wayon_remote_auth import RemotePasswordAuthorizer


HOST = "0.0.0.0"
PORT = int(os.getenv("WAYON_REMOTE_CONTROL_PORT", "4444"))
HTML_PATH = Path(__file__).with_name("wayon_remote_control.html")
REMOTE_CONTROL_SESSION = Path("/data/RemoteControlNextDrive")
BOOT_ID_PATH = Path("/proc/sys/kernel/random/boot_id")
WATCHDOG_TIMEOUT = 0.25
MAX_BODY_BYTES = 1024
SESSION_HEADER = "X-Wayon-Control-Session"


class ParamsReader(Protocol):
  def get_bool(self, key: str) -> bool:
    ...

  def put_bool(self, key: str, value: bool, block: bool = False) -> None:
    ...


def is_allowed_client(host: str) -> bool:
  try:
    address = ipaddress.ip_address(host)
  except ValueError:
    return False
  return address.is_private or address.is_loopback or address.is_link_local


def clamp(value: float, low: float, high: float) -> float:
  return min(max(float(value), low), high)


class RemoteControlMode:
  """One-shot remote mode selected offroad for the next onroad cycle."""

  def __init__(self, path: Path = REMOTE_CONTROL_SESSION, params: ParamsReader | None = None,
               boot_id_path: Path = BOOT_ID_PATH):
    self.path = path
    self.params = params
    self.boot_id_path = boot_id_path
    self.lock = threading.Lock()
    self.last_onroad: bool | None = None

  def _boot_id(self) -> str:
    try:
      return self.boot_id_path.read_text(encoding="utf-8").strip()
    except OSError:
      return ""

  def enabled(self) -> bool:
    with self.lock:
      return self._enabled_unlocked()

  def _enabled_unlocked(self) -> bool:
    try:
      payload = json.loads(self.path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
      return False
    boot_id = self._boot_id()
    return bool(boot_id and payload.get("version") == 1 and payload.get("bootId") == boot_id)

  def activate(self, onroad: bool) -> None:
    if onroad:
      raise PermissionError("activation is only available while offroad")
    boot_id = self._boot_id()
    if not boot_id:
      raise OSError("vehicle boot identity is unavailable")
    payload = {"version": 1, "bootId": boot_id}
    temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
    with self.lock:
      self.path.parent.mkdir(parents=True, exist_ok=True)
      temporary.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
      os.replace(temporary, self.path)
      if self.params is not None:
        self.params.put_bool("JoystickDebugMode", False, block=True)

  def deactivate(self, onroad: bool = False) -> None:
    if onroad:
      raise PermissionError("remote mode cannot be changed while onroad")
    with self.lock:
      self.path.unlink(missing_ok=True)

  def observe(self, onroad: bool) -> bool:
    """Clear the one-shot selection on the onroad -> offroad edge."""
    with self.lock:
      if self.path.is_file() and not self._enabled_unlocked():
        self.path.unlink(missing_ok=True)
      if self.last_onroad is True and not onroad:
        self.path.unlink(missing_ok=True)
      self.last_onroad = onroad
      return self._enabled_unlocked()

  def status(self, onroad: bool) -> dict:
    enabled = self.enabled()
    phase = "active" if enabled and onroad else "pending" if enabled else "inactive"
    return {"phase": phase, "enabled": enabled, "onroad": onroad}


class RemoteWideCamera:
  """Latest-frame wide camera preview, isolated from the control watchdog."""

  def __init__(self, fps: float = 20.0, stale_after: float = 1.5):
    self.frame_interval = 1.0 / fps
    self.stale_after = stale_after
    self.lock = threading.Lock()
    self.start_lock = threading.Lock()
    self.latest = b""
    self.latest_at = 0.0
    self.requested_at = 0.0
    self.stopping = threading.Event()
    self.thread = threading.Thread(target=self._run, name="wayon-remote-wide-camera", daemon=True)

  def frame(self, now: float | None = None) -> bytes | None:
    now = time.monotonic() if now is None else now
    with self.lock:
      self.requested_at = now
      frame = self.latest if self.latest and now - self.latest_at <= self.stale_after else None
    with self.start_lock:
      if not self.thread.is_alive():
        self.thread.start()
    return frame

  def stop(self) -> None:
    self.stopping.set()
    if self.thread.is_alive():
      self.thread.join(timeout=1.0)

  @staticmethod
  def _jpeg(buffer) -> bytes:
    from io import BytesIO

    import numpy as np
    from PIL import Image

    # Downsample the NV12 planes before RGB conversion. This keeps the preview
    # below roughly 1,000 px wide and avoids loading the control CPU with a
    # full-resolution color conversion for every camera frame.
    uv_height = ((buffer.height // 2) + 15) // 16 * 16
    uv_size = buffer.stride * uv_height
    raw = np.frombuffer(buffer.data, dtype=np.uint8)
    y = raw[:buffer.uv_offset].reshape((-1, buffer.stride))[:buffer.height, :buffer.width]
    uv = raw[buffer.uv_offset:buffer.uv_offset + uv_size]
    u = uv[::2].reshape((-1, buffer.stride // 2))[:buffer.height // 2, :buffer.width // 2]
    v = uv[1::2].reshape((-1, buffer.stride // 2))[:buffer.height // 2, :buffer.width // 2]
    scale = 2 if buffer.width > 960 else 1
    y = y[::scale, ::scale]
    u = u[::scale, ::scale]
    v = v[::scale, ::scale]
    u = np.repeat(np.repeat(u, 2, axis=0), 2, axis=1)[:y.shape[0], :y.shape[1]].astype(np.float32) - 128.0
    v = np.repeat(np.repeat(v, 2, axis=0), 2, axis=1)[:y.shape[0], :y.shape[1]].astype(np.float32) - 128.0
    y = y.astype(np.float32)
    rgb = np.stack((y + 1.13983 * v,
                    y - 0.39465 * u - 0.58060 * v,
                    y + 2.03211 * u), axis=-1).clip(0, 255).astype(np.uint8)
    output = BytesIO()
    Image.fromarray(rgb).save(output, "JPEG", quality=62)
    return output.getvalue()

  def _run(self) -> None:
    from msgq.visionipc import VisionIpcClient, VisionStreamType

    client = None
    last_encoded_at = 0.0
    while not self.stopping.is_set():
      with self.lock:
        requested_recently = time.monotonic() - self.requested_at <= 2.0
      if not requested_recently:
        time.sleep(0.1)
        continue
      try:
        if client is None:
          candidate = VisionIpcClient("camerad", VisionStreamType.VISION_STREAM_WIDE_ROAD, True)
          if not candidate.connect(False):
            time.sleep(0.1)
            continue
          client = candidate
        buffer = client.recv(timeout_ms=250)
        now = time.monotonic()
        if buffer is None or now - last_encoded_at < self.frame_interval:
          continue
        jpeg = self._jpeg(buffer)
        with self.lock:
          self.latest = jpeg
          self.latest_at = now
        last_encoded_at = now
      except Exception:
        client = None
        time.sleep(0.1)


class RemoteControlState:
  def __init__(self, watchdog_timeout: float = WATCHDOG_TIMEOUT):
    self.watchdog_timeout = watchdog_timeout
    self.lock = threading.Lock()
    self.steering = 0.0
    self.accelerator = 0.0
    self.brake = 0.0
    self.sequence = 0
    self.owner = ""
    self.last_input_at = 0.0

  @staticmethod
  def valid_session(session: str) -> bool:
    return 16 <= len(session) <= 128 and session.isascii() and all(c.isalnum() or c in "-_" for c in session)

  def arm(self, session: str, now: float | None = None) -> dict:
    if not self.valid_session(session):
      raise ValueError("invalid control session")
    now = time.monotonic() if now is None else now
    with self.lock:
      if self.owner and self.owner != session and self._fresh(now):
        raise PermissionError("another controller is active")
      self.owner = session
      self.sequence = 0
      self.last_input_at = now
      self._zero()
      return self._snapshot(now)

  def update(self, session: str, steering: float, accelerator: float, brake: float,
             sequence: int, now: float | None = None) -> dict:
    now = time.monotonic() if now is None else now
    steering = clamp(steering, -1.0, 1.0)
    accelerator = clamp(accelerator, 0.0, 1.0)
    brake = clamp(brake, 0.0, 1.0)
    sequence = int(sequence)
    if brake > 0.0:
      accelerator = 0.0

    with self.lock:
      self._expire(now)
      if not self.owner or session != self.owner:
        raise PermissionError("control session is not armed")
      if sequence <= self.sequence:
        raise ValueError("stale control sequence")
      self.steering = steering
      self.accelerator = accelerator
      self.brake = brake
      self.sequence = sequence
      self.last_input_at = now
      return self._snapshot(now)

  def snapshot(self, now: float | None = None) -> dict:
    now = time.monotonic() if now is None else now
    with self.lock:
      self._expire(now)
      return self._snapshot(now)

  def reset(self, session: str = "", now: float | None = None, force: bool = False) -> dict:
    now = time.monotonic() if now is None else now
    with self.lock:
      if not force and self.owner and session != self.owner:
        raise PermissionError("control session is not armed")
      self._zero()
      self.owner = ""
      self.last_input_at = 0.0
      return self._snapshot(now)

  def axes(self, now: float | None = None) -> tuple[list[float], bool]:
    now = time.monotonic() if now is None else now
    with self.lock:
      self._expire(now)
      active = bool(self.owner and self._fresh(now))
      return [self.accelerator - self.brake, self.steering], active

  def owned_by(self, session: str, now: float | None = None) -> bool:
    now = time.monotonic() if now is None else now
    with self.lock:
      self._expire(now)
      return bool(self.owner and session == self.owner)

  def _fresh(self, now: float) -> bool:
    return bool(self.last_input_at and now - self.last_input_at <= self.watchdog_timeout)

  def _expire(self, now: float) -> None:
    if self.owner and not self._fresh(now):
      self._zero()
      self.owner = ""
      self.last_input_at = 0.0

  def _zero(self) -> None:
    self.steering = 0.0
    self.accelerator = 0.0
    self.brake = 0.0

  def _snapshot(self, now: float) -> dict:
    age_ms = None if not self.last_input_at else max(0, round((now - self.last_input_at) * 1000))
    return {
      "armed": bool(self.owner and self._fresh(now)),
      "steering": round(self.steering, 4),
      "accelerator": round(self.accelerator, 4),
      "brake": round(self.brake, 4),
      "sequence": self.sequence,
      "inputAgeMs": age_ms,
      "watchdogMs": round(self.watchdog_timeout * 1000),
    }


class RemoteControlBridge:
  def __init__(self, state: RemoteControlState, params: ParamsReader | None = None,
               mode: RemoteControlMode | None = None):
    self.params = params
    self.state = state
    self.mode = mode or RemoteControlMode(params=params)
    self.lock = threading.Lock()
    self.vehicle = {"onroad": False, "engaged": False, "armReady": False, "speedMps": 0.0, "gear": "—"}
    self.stopping = threading.Event()

  def available(self) -> bool:
    with self.lock:
      arm_ready = bool(self.vehicle["armReady"])
    return self.mode.enabled() and arm_ready

  def activate(self) -> dict:
    with self.lock:
      onroad = bool(self.vehicle["onroad"])
    self.state.reset(force=True)
    self.mode.activate(onroad)
    return self.mode.status(onroad)

  def deactivate(self) -> dict:
    with self.lock:
      onroad = bool(self.vehicle["onroad"])
    self.state.reset(force=True)
    self.mode.deactivate(onroad)
    return self.mode.status(onroad)

  def mode_status(self) -> dict:
    with self.lock:
      onroad = bool(self.vehicle["onroad"])
    return self.mode.status(onroad)

  def status(self) -> dict:
    with self.lock:
      return dict(self.vehicle)

  def run(self) -> None:
    from cereal import car, messaging
    from openpilot.common.params import Params
    from openpilot.common.realtime import Ratekeeper

    params = self.params or Params()
    if self.mode.params is None:
      self.mode.params = params
    pm = messaging.PubMaster(["testJoystick"])
    sm = messaging.SubMaster(["carState", "selfdriveState"])
    drivable_gears = (car.CarState.GearShifter.drive, car.CarState.GearShifter.low)
    gear_labels = {
      car.CarState.GearShifter.park: "P",
      car.CarState.GearShifter.reverse: "R",
      car.CarState.GearShifter.neutral: "N",
      car.CarState.GearShifter.drive: "D",
      car.CarState.GearShifter.low: "L",
    }
    rk = Ratekeeper(100, print_delay_threshold=None)
    while not self.stopping.is_set():
      sm.update(0)
      onroad = params.get_bool("IsOnroad")
      mode_enabled = self.mode.observe(onroad)
      if not mode_enabled:
        self.state.reset(force=True)
      engaged = bool(sm["selfdriveState"].enabled)
      car_state = sm["carState"]
      speed = float(car_state.vEgo)
      arm_ready = bool(onroad and car_state.gearShifter in drivable_gears and
                       not car_state.gasPressed and not car_state.brakePressed and not car_state.parkingBrake)
      with self.lock:
        self.vehicle = {"onroad": onroad, "engaged": engaged,
                        "armReady": arm_ready, "speedMps": round(speed, 3),
                        "gear": gear_labels.get(car_state.gearShifter, "—")}

      axes, active = self.state.axes()
      active = active and arm_ready and mode_enabled
      if not active:
        axes = [0.0, 0.0]
      message = messaging.new_message("testJoystick")
      message.valid = True
      message.testJoystick.axes = axes
      message.testJoystick.buttons = [active]
      pm.send("testJoystick", message)
      rk.keep_time()

  def stop(self) -> None:
    self.state.reset(force=True)
    self.stopping.set()


class RemoteControlHandler(BaseHTTPRequestHandler):
  server_version = "WayonRemoteControl/2"

  def log_message(self, _format: str, *_args) -> None:
    return

  def _write(self, status: int, content_type: str, body: bytes) -> None:
    self.send_response(status)
    self.send_header("Content-Type", content_type)
    self.send_header("Content-Length", str(len(body)))
    self.send_header("Cache-Control", "no-store")
    content_security_policy = "; ".join((
      "default-src 'self'",
      "img-src 'self' data: blob:",
      "style-src 'self' 'unsafe-inline'",
      "script-src 'self' 'unsafe-inline'",
    ))
    self.send_header("Content-Security-Policy", content_security_policy)
    self.send_header("X-Content-Type-Options", "nosniff")
    self.send_header("X-Frame-Options", "DENY")
    self.end_headers()
    self.wfile.write(body)

  def _json(self, status: int, payload: dict) -> None:
    self._write(status, "application/json; charset=utf-8", json.dumps(payload, separators=(",", ":")).encode())

  def _client_allowed(self) -> bool:
    if is_allowed_client(self.client_address[0]):
      return True
    self._json(403, {"ok": False, "error": "local network only"})
    return False

  def _origin_allowed(self) -> bool:
    origin = self.headers.get("Origin")
    if origin is None or urlparse(origin).netloc == self.headers.get("Host"):
      return True
    self._json(403, {"ok": False, "error": "origin rejected"})
    return False

  def _authorized(self) -> bool:
    if self.server.authorizer.authorized(self.headers.get("Authorization"), self._session(), self.client_address[0]):
      return True
    self._json(401, {"ok": False, "error": "remote control password login required"})
    return False

  def _session(self) -> str:
    return self.headers.get(SESSION_HEADER, "")

  def _read_json(self) -> dict:
    content_length = int(self.headers.get("Content-Length", "0"))
    if not 0 < content_length <= MAX_BODY_BYTES:
      raise ValueError("invalid body")
    payload = json.loads(self.rfile.read(content_length))
    if not isinstance(payload, dict):
      raise ValueError("invalid body")
    return payload

  def do_GET(self) -> None:
    if not self._client_allowed():
      return
    if self.path == "/":
      self._write(200, "text/html; charset=utf-8", self.server.html)
    elif self.path == "/api/camera.jpg":
      if not self._authorized():
        return
      if self.server.bridge.mode_status()["phase"] != "active":
        self._json(409, {"ok": False, "error": "wide camera is available during remote onroad mode only"})
        return
      frame = self.server.camera.frame()
      if frame is None:
        self._json(503, {"ok": False, "error": "wide camera is starting"})
        return
      self._write(200, "image/jpeg", frame)
    elif self.path == "/api/status":
      if not self._authorized():
        return
      state = self.server.state.snapshot()
      state["ownedBySession"] = self.server.state.owned_by(self._session())
      self._json(200, {
        "ok": True,
        "available": self.server.bridge.available(),
        "realVehicleControl": True,
        "limits": {"maxSpeedKph": 50.0, "minSteerSpeedKph": 10.0,
                   "maxAccelMps2": 0.8, "maxBrakeMps2": 1.5, "maxSteer": 0.25},
        "vehicle": self.server.bridge.status(),
        "mode": self.server.bridge.mode_status(),
        "state": state,
      })
    else:
      self._json(404, {"ok": False, "error": "not found"})

  def do_POST(self) -> None:
    if not self._client_allowed() or not self._origin_allowed():
      return
    if self.path == "/api/login":
      token = ""
      try:
        payload = self._read_json()
        token = self.server.authorizer.login(payload.get("password"), self._session(), self.client_address[0])
        mode = self.server.bridge.mode_status()
        if mode["onroad"]:
          raise PermissionError("remote control can only be activated while comma is offroad")
        if mode["phase"] != "pending":
          mode = self.server.bridge.activate()
      except FileNotFoundError as exc:
        self._json(409, {"ok": False, "error": str(exc)})
        return
      except RuntimeError as exc:
        self._json(429, {"ok": False, "error": str(exc)})
        return
      except PermissionError as exc:
        if token:
          self.server.authorizer.revoke(token)
        self._json(401 if not token else 409, {"ok": False, "error": str(exc)})
        return
      except OSError as exc:
        if token:
          self.server.authorizer.revoke(token)
        self._json(500, {"ok": False, "error": f"failed to activate remote mode: {exc}"})
        return
      except (TypeError, ValueError, json.JSONDecodeError) as exc:
        self._json(400, {"ok": False, "error": str(exc) or "invalid login"})
        return
      self._json(200, {"ok": True, "token": token, "realVehicleControl": True, "mode": mode})
      return
    if not self._authorized():
      return
    if self.path not in ("/api/activate", "/api/deactivate", "/api/arm", "/api/input", "/api/reset"):
      self._json(404, {"ok": False, "error": "not found"})
      return

    try:
      if self.path == "/api/activate":
        mode = self.server.bridge.activate()
        self._json(200, {"ok": True, "realVehicleControl": True, "mode": mode})
        return
      if self.path == "/api/deactivate":
        mode = self.server.bridge.deactivate()
        self._json(200, {"ok": True, "realVehicleControl": True, "mode": mode})
        return
    except PermissionError as exc:
      self._json(409, {"ok": False, "error": str(exc)})
      return
    except OSError as exc:
      self._json(500, {"ok": False, "error": f"failed to change remote mode: {exc}"})
      return

    if self.path == "/api/reset":
      try:
        state = self.server.state.reset(self._session())
      except PermissionError as exc:
        self._json(409, {"ok": False, "error": str(exc)})
        return
      self._json(200, {"ok": True, "realVehicleControl": True, "state": state})
      return

    if not self.server.bridge.available():
      self.server.state.reset(force=True)
      self._json(409, {"ok": False, "error": "remote control is unavailable"})
      return

    session = self._session()
    try:
      if self.path == "/api/arm":
        state = self.server.state.arm(session)
      else:
        payload = self._read_json()
        if (not self.server.bridge.status().get("engaged") and
            any(abs(float(payload[name])) > 1e-6 for name in ("steering", "accelerator", "brake"))):
          raise PermissionError("engage openpilot before applying control input")
        state = self.server.state.update(session, payload["steering"], payload["accelerator"],
                                         payload["brake"], payload["sequence"])
    except PermissionError as exc:
      self._json(409, {"ok": False, "error": str(exc)})
      return
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
      self._json(400, {"ok": False, "error": str(exc) or "invalid control input"})
      return
    self._json(200, {"ok": True, "realVehicleControl": True, "state": state})


class RemoteControlServer(ThreadingHTTPServer):
  daemon_threads = True
  allow_reuse_address = True

  def __init__(self, address=(HOST, PORT), params: ParamsReader | None = None,
               state: RemoteControlState | None = None, authorizer: RemotePasswordAuthorizer | None = None,
               bridge: RemoteControlBridge | None = None, camera: RemoteWideCamera | None = None):
    self.state = state or RemoteControlState()
    self.authorizer = authorizer or RemotePasswordAuthorizer()
    self.bridge = bridge or RemoteControlBridge(self.state, params)
    self.camera = camera or RemoteWideCamera()
    self.bridge_thread = threading.Thread(target=self.bridge.run, name="wayon-remote-control", daemon=True)
    super().__init__(address, RemoteControlHandler)
    self.html = HTML_PATH.read_bytes()

  def start_bridge(self) -> None:
    if not self.bridge_thread.is_alive():
      self.bridge_thread.start()

  def server_close(self) -> None:
    self.bridge.stop()
    self.camera.stop()
    if self.bridge_thread.is_alive():
      self.bridge_thread.join(timeout=1)
    super().server_close()


def main() -> None:
  server = RemoteControlServer()
  server.start_bridge()
  try:
    server.serve_forever(poll_interval=0.1)
  finally:
    server.server_close()


if __name__ == "__main__":
  main()
