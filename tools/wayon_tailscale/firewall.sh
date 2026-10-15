#!/usr/bin/env bash
set -euo pipefail

# Only this interface is filtered; existing LAN, modem and vehicle traffic is untouched.
for family in 4 6; do
  if [[ $family == 4 ]]; then
    ipt=/usr/sbin/iptables-legacy
    peer=100.64.0.0/10
    protocol=icmp
  else
    ipt=/usr/sbin/ip6tables-legacy
    peer=fd7a:115c:a1e0::/48
    protocol=ipv6-icmp
  fi
  if ! "$ipt" -w 5 -S WAYON_TS_IN >/dev/null 2>&1; then
    "$ipt" -w 5 -N WAYON_TS_IN
  fi
  # Fail closed while refreshing rules, even when the interface already exists.
  "$ipt" -w 5 -I INPUT 1 -i tailscale0 -j DROP
  "$ipt" -w 5 -F WAYON_TS_IN
  "$ipt" -w 5 -A WAYON_TS_IN -s "$peer" -p tcp --dport 22 -j ACCEPT
  "$ipt" -w 5 -A WAYON_TS_IN -s "$peer" -p "$protocol" -j ACCEPT
  "$ipt" -w 5 -A WAYON_TS_IN -j DROP
  if ! "$ipt" -w 5 -C INPUT -i tailscale0 -j WAYON_TS_IN 2>/dev/null; then
    "$ipt" -w 5 -I INPUT 2 -i tailscale0 -j WAYON_TS_IN
  fi
  for direction in -i -o; do
    if ! "$ipt" -w 5 -C FORWARD "$direction" tailscale0 -j DROP 2>/dev/null; then
      "$ipt" -w 5 -I FORWARD 1 "$direction" tailscale0 -j DROP
    fi
  done
  while "$ipt" -w 5 -C INPUT -i tailscale0 -j DROP 2>/dev/null; do
    "$ipt" -w 5 -D INPUT -i tailscale0 -j DROP
  done
done
