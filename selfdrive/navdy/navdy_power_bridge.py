"""Manager entrypoint for comma -> Navdy bridge."""

from __future__ import annotations

import sys

from selfdrive.navdy import navdy_op_bridge


DEFAULT_ARGS = [
  "--adb-path", "adb",
  "--adb-server-port", "5038",
  "--no-stdout",
  "--manage-navdy-power",
  "--power-off-delay-sec", "30",
]


def main() -> int:
  if len(sys.argv) == 1:
    sys.argv = [sys.argv[0]] + DEFAULT_ARGS
  return navdy_op_bridge.main()


if __name__ == "__main__":
  raise SystemExit(main())
