#!/usr/bin/env bash
set -euo pipefail

# /run is writable on AGNOS. Recreate registration after each boot without remounting /.
exec 9>/run/wayon-tailscale-bootstrap.lock
/usr/bin/flock -n 9 || exit 0
touch /run/xtables.lock
unit=/data/wayon-tailscale/wayon-tailscaled.service
if [[ ! -L /run/systemd/system/wayon-tailscaled.service ]]; then
  /usr/bin/systemctl link --runtime "$unit"
fi
/usr/bin/systemctl start --no-block wayon-tailscaled.service
