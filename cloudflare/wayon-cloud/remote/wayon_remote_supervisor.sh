#!/bin/sh
set -u

ROOT=/data/wayon-remote
CLOUDFLARED="$ROOT/bin/cloudflared"
TOKEN_FILE="$ROOT/tunnel.token"
PID_FILE="$ROOT/cloudflared.pid"
LOG_FILE="$ROOT/cloudflared.log"
PARAM_ONROAD=/data/params/d/IsOnroad
SSH_ALIAS=172.31.255.254
POLL_SECONDS=2
OFFROAD_SAMPLES_TO_START=3

child_pid=""
offroad_samples=0

log() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$ROOT/supervisor.log"
}

stop_tunnel() {
  if [ -n "$child_pid" ] && kill -0 "$child_pid" 2>/dev/null; then
    log "stopping cloudflared pid=$child_pid"
    kill "$child_pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$child_pid" 2>/dev/null; then
      kill -KILL "$child_pid" 2>/dev/null || true
    fi
    wait "$child_pid" 2>/dev/null || true
  fi
  child_pid=""
  rm -f "$PID_FILE"
}

start_tunnel() {
  if [ ! -x "$CLOUDFLARED" ] || [ ! -r "$TOKEN_FILE" ]; then
    log "cloudflared binary or token missing"
    return
  fi

  log "starting cloudflared"
  GOMAXPROCS=1 nice -n 15 "$CLOUDFLARED" tunnel \
    --no-autoupdate \
    --protocol quic \
    --metrics 127.0.0.1:49312 \
    --loglevel warn \
    --transport-loglevel warn \
    --logfile "$LOG_FILE" \
    run \
    --token-file "$TOKEN_FILE" &
  child_pid=$!
  printf '%s\n' "$child_pid" > "$PID_FILE"
}

trap 'stop_tunnel; exit 0' INT TERM EXIT
mkdir -p "$ROOT"
log "supervisor started"
if ! sudo -n ip address replace "$SSH_ALIAS/32" dev lo; then
  log "failed to configure SSH loopback alias"
  exit 1
fi

while :; do
  onroad="$(tr -d '\r\n ' < "$PARAM_ONROAD" 2>/dev/null || true)"
  if [ "$onroad" != "0" ]; then
    offroad_samples=0
    stop_tunnel
  else
    offroad_samples=$((offroad_samples + 1))
    if [ -n "$child_pid" ] && ! kill -0 "$child_pid" 2>/dev/null; then
      log "cloudflared exited pid=$child_pid"
      wait "$child_pid" 2>/dev/null || true
      child_pid=""
      rm -f "$PID_FILE"
    fi
    if [ -z "$child_pid" ] && [ "$offroad_samples" -ge "$OFFROAD_SAMPLES_TO_START" ]; then
      start_tunnel
    fi
  fi
  sleep "$POLL_SECONDS"
done
