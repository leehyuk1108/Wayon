#!/usr/bin/env bash

# Independent, nonblocking network service; failure must not delay openpilot startup.
if [[ -x /data/wayon-tailscale/bootstrap.sh ]]; then
  sudo -n /data/wayon-tailscale/bootstrap.sh >/dev/null 2>&1 &
fi

cd /data/openpilot
exec ./launch_openpilot.sh
