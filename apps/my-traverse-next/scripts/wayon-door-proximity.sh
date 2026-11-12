#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/data/wayon-rssi:/data/openpilot/pydeps:/data/openpilot:/data/pythonpath
exec /usr/local/venv/bin/python3 "$(dirname -- "${BASH_SOURCE[0]}")/wayon_door_proximity.py" "$@"
