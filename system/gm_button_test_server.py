import ipaddress
import json
import os
from pathlib import Path
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import time
from typing import Protocol
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = int(os.getenv("GM_BUTTON_TEST_PORT", "8844"))
BUTTON_SOCKET = "/tmp/gm_button_test.sock"
HTML_PATH = Path(__file__).with_name("gm_button_test.html")
ALLOWED_BUTTONS = frozenset(("res", "set", "cancel", "unpress"))
COMMAND_INTERVAL = 0.2


class ParamsReader(Protocol):
  def get_bool(self, key: str) -> bool:
    ...


def is_allowed_client(host: str) -> bool:
  try:
    address = ipaddress.ip_address(host)
  except ValueError:
    return False
  return address.is_private or address.is_loopback or address.is_link_local


def send_button_command(button: str, socket_path: str = BUTTON_SOCKET) -> None:
  if button not in ALLOWED_BUTTONS:
    raise ValueError("unsupported button")

  payload = json.dumps({
    "schema": "gm-button-test-v1",
    "button": button,
    "issuedAtMono": time.monotonic(),
  }, separators=(",", ":")).encode()

  with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as command_socket:
    command_socket.sendto(payload, socket_path)


class GMButtonTestHandler(BaseHTTPRequestHandler):
  server_version = "GMButtonTest/1"

  def log_message(self, _format, *_args):
    return

  def _write(self, status: int, content_type: str, body: bytes) -> None:
    self.send_response(status)
    self.send_header("Content-Type", content_type)
    self.send_header("Content-Length", str(len(body)))
    self.send_header("Cache-Control", "no-store")
    self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
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

  def do_GET(self) -> None:
    if not self._client_allowed():
      return

    if self.path == "/":
      self._write(200, "text/html; charset=utf-8", self.server.html)
    elif self.path == "/api/status":
      onroad = self.server.params.get_bool("IsOnroad")
      socket_ready = os.path.exists(BUTTON_SOCKET)
      self._json(200, {
        "ok": True,
        "onroad": onroad,
        "socketReady": socket_ready,
        "ready": onroad and socket_ready,
        "port": self.server.server_port,
      })
    else:
      self._json(404, {"ok": False, "error": "not found"})

  def do_POST(self) -> None:
    if not self._client_allowed() or not self._origin_allowed():
      return
    if self.path != "/api/command":
      self._json(404, {"ok": False, "error": "not found"})
      return

    try:
      content_length = int(self.headers.get("Content-Length", "0"))
      if not 0 < content_length <= 256:
        raise ValueError
      payload = json.loads(self.rfile.read(content_length))
      button = str(payload["button"]).lower()
      if button not in ALLOWED_BUTTONS:
        raise ValueError
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
      self._json(400, {"ok": False, "error": "invalid command"})
      return

    now = time.monotonic()
    if now - self.server.last_command_at < COMMAND_INTERVAL:
      self._json(429, {"ok": False, "error": "command rate limited"})
      return
    if not self.server.params.get_bool("IsOnroad") or not os.path.exists(BUTTON_SOCKET):
      self._json(409, {"ok": False, "error": "vehicle control is not ready"})
      return

    try:
      send_button_command(button)
    except OSError:
      self._json(503, {"ok": False, "error": "control socket unavailable"})
      return

    self.server.last_command_at = now
    self._json(202, {"ok": True, "button": button, "queued": True})


class GMButtonTestServer(ThreadingHTTPServer):
  daemon_threads = True
  allow_reuse_address = True

  def __init__(self, address=(HOST, PORT), params: ParamsReader | None = None):
    super().__init__(address, GMButtonTestHandler)
    self.html = HTML_PATH.read_bytes()
    if params is None:
      from openpilot.common.params import Params
      params = Params()
    self.params = params
    self.last_command_at = 0.0


def main() -> None:
  server = GMButtonTestServer()
  try:
    server.serve_forever(poll_interval=0.25)
  finally:
    server.server_close()


if __name__ == "__main__":
  main()
