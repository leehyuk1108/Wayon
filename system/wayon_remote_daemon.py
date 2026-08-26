#!/usr/bin/env python3
import signal
import subprocess
import sys
import time

from openpilot.common.params import Params
from openpilot.system.wayon_ssh_keys import ensure_persistent_ssh_keys


POLL_INTERVAL_SECONDS = 1
RESTART_DELAY_SECONDS = 2
RELAY_MODULE = "system.wayon_remote_relay"


def is_offroad(params: Params) -> bool:
  return params.get_bool("IsOffroad") and not params.get_bool("IsOnroad")


class RelaySupervisor:
  def __init__(self, process_factory=subprocess.Popen):
    self.process_factory = process_factory
    self.child = None
    self.last_exit_at = 0.0

  def start(self) -> None:
    if self.child is not None and self.child.poll() is None:
      return
    if time.monotonic() - self.last_exit_at < RESTART_DELAY_SECONDS:
      return
    self.child = self.process_factory([sys.executable, "-m", RELAY_MODULE])

  def stop(self) -> None:
    if self.child is None:
      return
    if self.child.poll() is None:
      self.child.terminate()
      try:
        self.child.wait(timeout=5)
      except subprocess.TimeoutExpired:
        self.child.kill()
        self.child.wait()
    self.child = None

  def update(self, offroad: bool) -> None:
    if self.child is not None and self.child.poll() is not None:
      self.child = None
      self.last_exit_at = time.monotonic()
    if offroad:
      self.start()
    else:
      self.stop()


def main() -> None:
  params = Params()
  supervisor = RelaySupervisor()
  stopping = False

  def request_stop(signum, frame) -> None:
    nonlocal stopping
    stopping = True

  signal.signal(signal.SIGINT, request_stop)
  signal.signal(signal.SIGTERM, request_stop)

  try:
    while not stopping:
      ensure_persistent_ssh_keys(params)
      supervisor.update(is_offroad(params))
      time.sleep(POLL_INTERVAL_SECONDS)
  finally:
    supervisor.stop()


if __name__ == "__main__":
  main()
