#!/usr/bin/env python3
import socket
import subprocess
import threading
import time

from websocket import ABNF, WebSocketException, WebSocketTimeoutException, create_connection

from openpilot.system.wayon_identity import DEFAULT_CONFIG_PATH, ensure_wayon_identity


USER_AGENT = "wayon-device-relay/1.0"
RELAY_TARGETS = {"ssh": ("127.0.0.1", 22), "live": ("127.0.0.1", 8765)}
HEARTBEAT_INTERVAL_SECONDS = 20
MAX_MISSED_HEARTBEATS = 3
RECONNECT_DELAY_SECONDS = 1


class RelayChannel:
  def __init__(self, kind: str, endpoint: str, token: str):
    self.kind = kind
    self.endpoint = endpoint
    self.token = token
    self.local: socket.socket | None = None
    self.local_lock = threading.Lock()

  def close_local(self) -> None:
    with self.local_lock:
      local, self.local = self.local, None
    if local is not None:
      try:
        local.shutdown(socket.SHUT_RDWR)
      except OSError:
        pass
      local.close()

  def open_local(self, websocket) -> None:
    self.close_local()
    if self.kind == "ssh":
      subprocess.run(["sudo", "-n", "systemctl", "start", "ssh"], check=False,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    local = socket.create_connection(RELAY_TARGETS[self.kind], timeout=10)
    local.settimeout(1.0)
    with self.local_lock:
      self.local = local

    def forward() -> None:
      try:
        while True:
          try:
            data = local.recv(64 * 1024)
          except TimeoutError:
            continue
          if not data:
            break
          websocket.send(data, opcode=ABNF.OPCODE_BINARY)
      except (OSError, WebSocketException):
        pass
      finally:
        self.close_local()

    threading.Thread(target=forward, name=f"wayon-{self.kind}-local", daemon=True).start()

  def relay_connected(self, websocket) -> None:
    missed_heartbeats = 0
    websocket.settimeout(HEARTBEAT_INTERVAL_SECONDS)

    while True:
      try:
        opcode, data = websocket.recv_data(control_frame=True)
      except WebSocketTimeoutException:
        missed_heartbeats += 1
        if missed_heartbeats >= MAX_MISSED_HEARTBEATS:
          raise
        # An idle relay is healthy. Ping it instead of tearing it down on every
        # receive timeout; the next pong resets the missed-heartbeat counter.
        websocket.ping(f"wayon-{self.kind}".encode())
        continue

      missed_heartbeats = 0
      if opcode == ABNF.OPCODE_TEXT:
        command = data.decode("utf-8", "replace") if isinstance(data, bytes) else str(data)
        if command == "wayon-peer-open":
          self.open_local(websocket)
        elif command == "wayon-peer-close":
          self.close_local()
      elif opcode == ABNF.OPCODE_BINARY:
        with self.local_lock:
          local = self.local
        if local is not None:
          local.sendall(data)
      elif opcode == ABNF.OPCODE_CLOSE:
        return

  def run(self) -> None:
    websocket_url = self.endpoint.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
    websocket_url = f"{websocket_url}/api/device/relay/{self.kind}"
    while True:
      websocket = None
      try:
        websocket = create_connection(
          websocket_url,
          header=[f"Authorization: Bearer {self.token}", f"User-Agent: {USER_AGENT}"],
          timeout=30,
          enable_multithread=True,
        )
        self.relay_connected(websocket)
      except (OSError, WebSocketException) as exc:
        print(f"Wayon relay {self.kind}: reconnecting after {type(exc).__name__}", flush=True)
      finally:
        self.close_local()
        try:
          websocket.close()
        except Exception:
          pass
      time.sleep(RECONNECT_DELAY_SECONDS)


def main() -> None:
  while True:
    try:
      config = ensure_wayon_identity(DEFAULT_CONFIG_PATH)
      if config is None:
        raise RuntimeError("Wayon identity unavailable")
      endpoint = str(config["endpoint"]).rstrip("/")
      token = str(config["token"])
      channels = [RelayChannel(kind, endpoint, token) for kind in RELAY_TARGETS]
      threads = [threading.Thread(target=channel.run, name=f"wayon-relay-{channel.kind}") for channel in channels]
      for thread in threads:
        thread.start()
      for thread in threads:
        thread.join()
    except Exception as exc:
      print(f"Wayon relay: startup failed: {exc}", flush=True)
      time.sleep(10)


if __name__ == "__main__":
  main()
