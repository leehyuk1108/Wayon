# Private SSH access on AGNOS

This directory preserves the Tailscale installation used on the Wayon Comma.
It does not enable Tailscale SSH, expose a public service, change vehicle control,
or store node credentials in Git. Connections use the existing OpenSSH daemon
and its authorized keys. Tailnet access policy still applies.

## Installation contract

- Install only while offroad. `install.sh` refuses an existing installation or
  an unexpected `/data/continue.sh`; inspect either case instead of bypassing it.
- Put the official `tailscale_1.104.1_arm64.tgz` from
  <https://pkgs.tailscale.com/stable/> beside these files. The installer checks
  its pinned SHA-256 before extraction. Binaries are not included in Git.
- Run `sudo ./install.sh` on the device. Enroll interactively in the intended
  tailnet using `/data/wayon-tailscale/bin/tailscale` with
  `--socket=/run/wayon-tailscale/tailscaled.sock` and `up --accept-dns=false
  --accept-routes=false --ssh=false --netfilter-mode=off --hostname=wayon-comma`.
- Do not commit an authentication URL, auth key, node state, SSH key, or anything
  under `/data/wayon-tailscale/state`.

## Persistence and resource limits

Files and node state live under `/data/wayon-tailscale`, outside the openpilot
checkout. `/data/continue.sh` starts the bootstrap asynchronously, then launches
openpilot normally. The bootstrap recreates the runtime systemd registration
after boot without remounting the read-only root filesystem.

The daemon uses CPUs 0-3, nice 15, at most 128 MiB of cgroup memory, and a bounded
restart policy. The firewall only filters `tailscale0`: SSH and ICMP are allowed,
other inbound ports and forwarding are denied for IPv4 and IPv6. LAN and modem
rules are not changed. This is not an exit node or a subnet router.

An installer that replaces `/data/continue.sh`, wipes `/data`, or deletes the
node from the tailnet requires inspection/re-enrollment. A Git pull alone does
not install or update the external service. Node authorization can expire.

## Verification

`sudo python3 verify.py` reads service state, hashes, firewall rules, routes,
and 30 seconds of CPU/RSS samples; it does not actuate the vehicle. Keep its
output private because it contains device and network identifiers.

On 2026-10-15, SSH was verified over the cellular default route with Wi-Fi down,
from another tailnet peer, and after a daemon restart. Non-SSH application ports
were blocked. Offroad daemon CPU averaged 0.37% of one core and RSS was about
26.8 MiB during that sample. Full-device reboot persistence and onroad transfer
load were not verified in that test.
