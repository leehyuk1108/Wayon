#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/data/wayon-rssi:/data/openpilot/pydeps:/data/openpilot:/data/pythonpath
exec /usr/local/venv/bin/python3 /data/wayon-door-tools/gmone_door_control.py "$@"
