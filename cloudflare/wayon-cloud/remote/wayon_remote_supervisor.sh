#!/bin/sh
set -u

ROOT=/data/wayon-remote
CLOUDFLARED="$ROOT/bin/cloudflared"
TOKEN_FILE="$ROOT/tunnel.token"
PID_FILE="$ROOT/cloudflared.pid"
LOG_FILE="$ROOT/cloudflared.log"
PARAM_ONROAD=/data/params/d/IsOnroad
PARAM_SSH_ENABLED=/data/params/d/SshEnabled
SSH_ALIAS=172.31.255.254
METRICS_URL=http://127.0.0.1:49312/metrics
POLL_SECONDS=2
OFFROAD_SAMPLES_TO_START=3
HEALTH_CHECK_SAMPLES=5
HEALTH_FAILURES_TO_RESTART=6

child_pid=""
offroad_samples=0
health_samples=0
health_failures=0

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
  health_samples=0
  health_failures=0
  rm -f "$PID_FILE"
}

ensure_ssh() {
  ssh_enabled="$(tr -d '\r\n ' < "$PARAM_SSH_ENABLED" 2>/dev/null || true)"
  if [ "$ssh_enabled" != "1" ]; then
    log "SSH is disabled by SshEnabled"
    return
  fi
  if ! sudo -n systemctl is-active --quiet ssh; then
    if sudo -n systemctl start ssh; then
      log "started SSH service"
    else
      log "failed to start SSH service"
    fi
  fi
}

start_tunnel() {
  if [ ! -x "$CLOUDFLARED" ] || [ ! -r "$TOKEN_FILE" ]; then
    log "cloudflared binary or token missing"
    return
  fi

  ensure_ssh
  log "starting cloudflared"
  GOMAXPROCS=1 nice -n 15 "$CLOUDFLARED" tunnel \
    --no-autoupdate \
    --metrics 127.0.0.1:49312 \
    --loglevel warn \
    --transport-loglevel warn \
    --logfile "$LOG_FILE" \
    run \
    --token-file "$TOKEN_FILE" &
  child_pid=$!
  health_samples=0
  health_failures=0
  printf '%s\n' "$child_pid" > "$PID_FILE"
}

tunnel_connections() {
  curl -fsS --max-time 2 "$METRICS_URL" 2>/dev/null | awk '
    $1 == "cloudflared_tunnel_ha_connections" {
      print int($2)
      found = 1
      exit
    }
    END {
      if (!found) exit 1
    }
  '
}

check_tunnel_health() {
  connections="$(tunnel_connections || true)"
  case "$connections" in
    ""|*[!0-9]*) connections=0 ;;
  esac

  if [ "$connections" -gt 0 ]; then
    if [ "$health_failures" -gt 0 ]; then
      log "cloudflared recovered connections=$connections"
    fi
    health_failures=0
    return
  fi

  health_failures=$((health_failures + 1))
  if [ "$health_failures" -eq 1 ]; then
    log "cloudflared has no active connections"
  fi
  if [ "$health_failures" -ge "$HEALTH_FAILURES_TO_RESTART" ]; then
    log "restarting unhealthy cloudflared failures=$health_failures"
    stop_tunnel
    offroad_samples=$OFFROAD_SAMPLES_TO_START
    start_tunnel
  fi
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
      health_samples=0
      health_failures=0
      rm -f "$PID_FILE"
    fi
    if [ -z "$child_pid" ] && [ "$offroad_samples" -ge "$OFFROAD_SAMPLES_TO_START" ]; then
      start_tunnel
    elif [ -n "$child_pid" ]; then
      health_samples=$((health_samples + 1))
      if [ "$health_samples" -ge "$HEALTH_CHECK_SAMPLES" ]; then
        health_samples=0
        check_tunnel_health
      fi
    fi
  fi
  sleep "$POLL_SECONDS"
done
