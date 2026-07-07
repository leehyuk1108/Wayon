"""Manager entrypoint for comma -> Navdy bridge."""

from __future__ import annotations

import sys

from openpilot.common.realtime import set_core_affinity
from selfdrive.navdy import navdy_op_bridge


DEFAULT_ARGS = [
  "--adb-path", "adb",
  "--adb-server-port", "5038",
  "--no-stdout",
  "--manage-navdy-power",
  "--socket-transport",
  "--heartbeat-sec", "3",
  "--power-on-ensure-sec", "5",
  "--power-off-delay-sec", "30",
]


def main() -> int:
  set_core_affinity([0, 1, 2, 3])
  if "--adb-path" not in sys.argv and "--manage-navdy-power" not in sys.argv:
    sys.argv = [sys.argv[0]] + DEFAULT_ARGS
  return navdy_op_bridge.main()


if __name__ == "__main__":
  raise SystemExit(main())
