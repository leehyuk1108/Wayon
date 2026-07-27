"""Manager entrypoint for comma -> Navdy bridge."""

from __future__ import annotations

import os
import sys
from multiprocessing import current_process

from openpilot.common.realtime import set_core_affinity
from selfdrive.navdy import navdy_op_bridge


DEFAULT_ARGS = [
  "--hz", "5",
  "--path-update-sec", "0.1",
  "--radar-overlay",
  "--lane-marking-classifier",
  "--lane-marking-interval-sec", "0.5",
  "--adb-path", "adb",
  "--adb-server-port", "5038",
  "--no-stdout",
  "--manage-navdy-power",
  "--socket-transport",
  "--heartbeat-sec", "5",
  "--power-on-ensure-sec", "60",
  "--power-off-delay-sec", "30",
  "--power-off-ensure-sec", "5",
]


def should_use_default_args(process_name: str, argv: list[str]) -> bool:
  if process_name == "navdy_bridge":
    return True
  if len(argv) <= 1:
    return True
  return os.path.basename(argv[0]) != "navdy_power_bridge.py"


def main() -> int:
  set_core_affinity([0, 1, 2, 3])
  if should_use_default_args(current_process().name, sys.argv):
    sys.argv = [sys.argv[0]] + DEFAULT_ARGS
  return navdy_op_bridge.main()


if __name__ == "__main__":
  raise SystemExit(main())
