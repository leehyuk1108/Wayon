#!/usr/bin/env python3
"""Read-only installed-service verification. Never include node credentials."""
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import time


def command(*args):
  return subprocess.check_output(args, text=True, timeout=15).strip()


def main():
  unit = "wayon-tailscaled.service"
  cli = ["/data/wayon-tailscale/bin/tailscale", "--socket=/run/wayon-tailscale/tailscaled.sock"]
  status = json.loads(command(*cli, "status", "--json"))
  prefs = json.loads(command(*cli, "debug", "prefs"))
  pid = int(command("systemctl", "show", unit, "--property=MainPID", "--value"))
  if pid <= 0:
    raise RuntimeError("Tailscale daemon is not running")

  def sample():
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    ticks = int(fields[11]) + int(fields[12])
    proc_status = dict(line.split(":", 1) for line in Path(f"/proc/{pid}/status").read_text().splitlines())
    return time.monotonic(), ticks, int(proc_status["VmRSS"].split()[0])

  samples = [sample()]
  for _ in range(30):
    time.sleep(1)
    samples.append(sample())
  hz = os.sysconf("SC_CLK_TCK")
  cpu = [(b[1] - a[1]) / hz / (b[0] - a[0]) * 100 for a, b in zip(samples, samples[1:])]
  hashes = {}
  for name in [
    "selfdrive/controls/lib/longcontrol.py",
    "sunnypilot/selfdrive/controls/lib/wayon_longitudinal_coordinator.py",
  ]:
    hashes[name] = hashlib.sha256((Path("/data/openpilot") / name).read_bytes()).hexdigest()
  result = {
    "timestamp": command("date", "-Is"),
    "backend_state": status["BackendState"],
    "ip": status["TailscaleIPs"],
    "health": status.get("Health", []),
    "tailnet": status.get("CurrentTailnet", {}).get("Name"),
    "key_expiry": status.get("Self", {}).get("KeyExpiry"),
    "cpu_percent_one_core": {"mean": statistics.mean(cpu), "max": max(cpu), "seconds": samples[-1][0] - samples[0][0]},
    "rss_mib": {"mean": statistics.mean(s[2] for s in samples) / 1024, "max": max(s[2] for s in samples) / 1024},
    "service": command("systemctl", "show", unit, "-p", "ActiveState", "-p", "MainPID", "-p", "NRestarts", "-p", "MemoryCurrent", "-p", "MemoryMax", "-p", "Nice", "-p", "CPUAffinity"),
    "preferences": {key: prefs.get(key) for key in ["CorpDNS", "RouteAll", "RunSSH", "RunWebClient", "AdvertiseRoutes", "ExitNodeID", "NetfilterMode"]},
    "ipv4_firewall": command("iptables-legacy", "-S"),
    "ipv6_firewall": command("ip6tables-legacy", "-S"),
    "default_routes": command("ip", "route", "show", "default"),
    "root_mount": command("findmnt", "-n", "-o", "OPTIONS", "/"),
    "onroad": Path("/data/params/d/IsOnroad").read_text(),
    "offroad": Path("/data/params/d/IsOffroad").read_text(),
    "controller_hashes": hashes,
    "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
    "boot_hook_present": "/data/wayon-tailscale/bootstrap.sh" in Path("/data/continue.sh").read_text(),
  }
  print(json.dumps(result, indent=2))


if __name__ == "__main__":
  main()
