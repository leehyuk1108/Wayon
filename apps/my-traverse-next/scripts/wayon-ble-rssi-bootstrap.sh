#!/usr/bin/env bash
set -euo pipefail

# AGNOS mounts /etc read-only. Recreate these runtime units at boot.
exec 9>/run/wayon-ble-rssi-bootstrap.lock
/usr/bin/flock -n 9 || exit 0
unit=/data/wayon-rssi/wayon-ble-rssi.service
if [[ ! -L /run/systemd/system/wayon-ble-rssi.service ]]; then
  /usr/bin/systemctl link --runtime "$unit"
fi
/usr/bin/systemctl start --no-block wayon-ble-rssi.service

unlock=/data/wayon-door-tools/system-cloud-v1/wayon-system-phone-unlock.service
if [[ -f /data/wayon-door/system-unlock-enabled && -s /data/wayon-door/system-unlock.json && -f "$unlock" ]]; then
  if [[ ! -L /run/systemd/system/wayon-system-phone-unlock.service ]]; then
    /usr/bin/systemctl link --runtime "$unlock"
  fi
  /usr/bin/systemctl start --no-block wayon-system-phone-unlock.service
fi
