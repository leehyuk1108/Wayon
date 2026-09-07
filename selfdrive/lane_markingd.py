#!/usr/bin/env python3
"""Managed Xiaoge ONNX lane and visual blindspot service."""

import os

from openpilot.selfdrive.lane_marking.server import create_server


def main() -> None:
  # Lane classification is advisory. Keep control and planning processes ahead
  # of this CPU-heavy ONNX worker when all four C4 cores are busy.
  try:
    os.nice(10)
  except OSError:
    pass
  service, server = create_server()
  print(f"Xiaoge vision server: http://0.0.0.0:{server.server_port}")
  try:
    server.serve_forever()
  finally:
    server.server_close()
    service.running = False


if __name__ == "__main__":
  main()
