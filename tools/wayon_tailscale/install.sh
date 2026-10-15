#!/usr/bin/env bash
set -euo pipefail

[[ $EUID == 0 ]] || { echo 'Run with sudo.' >&2; exit 1; }
[[ $(cat /data/params/d/IsOnroad) == 0 && $(cat /data/params/d/IsOffroad) == 1 ]] || {
  echo 'Install only while offroad.' >&2; exit 1;
}
stage=$(cd -- "$(dirname -- "$0")" && pwd)
base=/data/wayon-tailscale
[[ ! -e $base ]] || { echo 'Existing installation found; inspect before updating.' >&2; exit 1; }
[[ $(sha256sum /data/continue.sh | cut -d ' ' -f 1) == 1258c4deaabf815a30a5763f977a74a76513c03702d3b591a78a7deff8b3507d ]] || {
  echo 'Boot script changed; refusing to replace it.' >&2; exit 1;
}
[[ $(sha256sum "$stage/tailscale_1.104.1_arm64.tgz" | cut -d ' ' -f 1) == f60294374967f3dfd8cf57bbbd474d6cfce32d123e3a8ddeab82a87940daa806 ]] || {
  echo 'Official archive checksum mismatch.' >&2; exit 1;
}
install -d -m 0755 "$base" "$base/bin"
install -d -m 0700 "$base/state" "$base/backup"
cp -a /data/continue.sh "$base/backup/continue.sh"
tar -xzf "$stage/tailscale_1.104.1_arm64.tgz" -C "$stage"
install -m 0755 "$stage/tailscale_1.104.1_arm64/tailscale" "$base/bin/tailscale"
install -m 0755 "$stage/tailscale_1.104.1_arm64/tailscaled" "$base/bin/tailscaled"
install -m 0755 "$stage/firewall.sh" "$stage/bootstrap.sh" "$base/"
install -m 0644 "$stage/wayon-tailscaled.service" "$base/"
install -m 0755 "$stage/continue.sh" /data/continue.sh.wayon-tailscale-new
chown --reference=/data/continue.sh /data/continue.sh.wayon-tailscale-new
bash -n /data/continue.sh.wayon-tailscale-new
mv /data/continue.sh.wayon-tailscale-new /data/continue.sh
"$base/bootstrap.sh"
echo 'Installed. Enrollment still required; no vehicle services were restarted.'
