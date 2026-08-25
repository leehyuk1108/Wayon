import ipaddress
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
from typing import Protocol
from urllib.parse import urlparse


HOST = "0.0.0.0"
PORT = int(os.getenv("REMOTE_SIMULATION_PORT", "4444"))
HTML_PATH = Path(__file__).with_name("remote_simulation.html")
WATCHDOG_TIMEOUT = 0.3
MAX_BODY_BYTES = 1024
REMOTE_SIMULATION_FLAG = "/data/RemoteSimulation"


class ParamsReader(Protocol):
  def get_bool(self, key: str) -> bool:
    ...


def is_allowed_client(host: str) -> bool:
  try:
    address = ipaddress.ip_address(host)
  except ValueError:
    return False
  return address.is_private or address.is_loopback or address.is_link_local


def clamp(value: float, low: float, high: float) -> float:
  return min(max(float(value), low), high)


class SimulationState:
  def __init__(self, watchdog_timeout: float = WATCHDOG_TIMEOUT):
    self.watchdog_timeout = watchdog_timeout
    self.lock = threading.Lock()
    self.steering = 0.0
    self.accelerator = 0.0
    self.brake = 0.0
    self.sequence = 0
    self.last_input_at = 0.0

  def update(self, steering: float, accelerator: float, brake: float, sequence: int, now: float | None = None) -> dict:
    now = time.monotonic() if now is None else now
    steering = clamp(steering, -1.0, 1.0)
    accelerator = clamp(accelerator, 0.0, 1.0)
    brake = clamp(brake, 0.0, 1.0)
    if brake > 0.0:
      accelerator = 0.0

    with self.lock:
      self.steering = steering
      self.accelerator = accelerator
      self.brake = brake
      self.sequence = max(int(sequence), self.sequence)
      self.last_input_at = now
      return self._snapshot(now)

  def snapshot(self, now: float | None = None) -> dict:
    now = time.monotonic() if now is None else now
    with self.lock:
      if self.last_input_at and now - self.last_input_at > self.watchdog_timeout:
        self.steering = 0.0
        self.accelerator = 0.0
        self.brake = 0.0
      return self._snapshot(now)

  def reset(self, now: float | None = None) -> dict:
    now = time.monotonic() if now is None else now
    with self.lock:
      self.steering = 0.0
      self.accelerator = 0.0
      self.brake = 0.0
      self.last_input_at = 0.0
      return self._snapshot(now)

  def _snapshot(self, now: float) -> dict:
    age_ms = None if not self.last_input_at else max(0, round((now - self.last_input_at) * 1000))
    return {
      "steering": round(self.steering, 4),
      "accelerator": round(self.accelerator, 4),
      "brake": round(self.brake, 4),
      "sequence": self.sequence,
      "inputAgeMs": age_ms,
      "watchdogMs": round(self.watchdog_timeout * 1000),
    }


class RemoteSimulationHandler(BaseHTTPRequestHandler):
  server_version = "RemoteSimulation/1"

  def log_message(self, _format: str, *_args) -> None:
    return

  def _write(self, status: int, content_type: str, body: bytes) -> None:
    self.send_response(status)
    self.send_header("Content-Type", content_type)
    self.send_header("Content-Length", str(len(body)))
    self.send_header("Cache-Control", "no-store")
    self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
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

  def _available(self) -> bool:
    return os.path.isfile(REMOTE_SIMULATION_FLAG) and not self.server.params.get_bool("IsOnroad")

  def do_GET(self) -> None:
    if not self._client_allowed():
      return
    if self.path == "/":
      self._write(200, "text/html; charset=utf-8", self.server.html)
    elif self.path == "/api/status":
      self._json(200, {
        "ok": True,
        "available": self._available(),
        "simulationOnly": True,
        "vehicleOutputBlocked": True,
        "onroad": self.server.params.get_bool("IsOnroad"),
        "state": self.server.state.snapshot(),
      })
    else:
      self._json(404, {"ok": False, "error": "not found"})

  def do_POST(self) -> None:
    if not self._client_allowed() or not self._origin_allowed():
      return
    if self.path not in ("/api/input", "/api/reset"):
      self._json(404, {"ok": False, "error": "not found"})
      return
    if not self._available():
      self.server.state.reset()
      self._json(409, {"ok": False, "error": "remote simulation is unavailable"})
      return
    if self.path == "/api/reset":
      self._json(200, {"ok": True, "state": self.server.state.reset()})
      return

    try:
      content_length = int(self.headers.get("Content-Length", "0"))
      if not 0 < content_length <= MAX_BODY_BYTES:
        raise ValueError
      payload = json.loads(self.rfile.read(content_length))
      state = self.server.state.update(payload["steering"], payload["accelerator"], payload["brake"], payload["sequence"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
      self._json(400, {"ok": False, "error": "invalid simulation input"})
      return
    self._json(200, {"ok": True, "simulationOnly": True, "state": state})


class RemoteSimulationServer(ThreadingHTTPServer):
  daemon_threads = True
  allow_reuse_address = True

  def __init__(self, address=(HOST, PORT), params: ParamsReader | None = None, state: SimulationState | None = None):
    super().__init__(address, RemoteSimulationHandler)
    self.html = HTML_PATH.read_bytes()
    if params is None:
      from openpilot.common.params import Params
      params = Params()
    self.params = params
    self.state = state or SimulationState()


def main() -> None:
  server = RemoteSimulationServer()
  try:
    server.serve_forever(poll_interval=0.1)
  finally:
    server.state.reset()
    server.server_close()


if __name__ == "__main__":
  main()
