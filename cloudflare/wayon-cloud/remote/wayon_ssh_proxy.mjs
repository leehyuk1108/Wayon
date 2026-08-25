#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const endpoint = process.env.WAYON_SSH_URL
  || "wss://wayon-cloud.hyuklee.workers.dev/api/remote/ssh";
const connectTimeoutMs = Number.parseInt(process.env.WAYON_SSH_CONNECT_TIMEOUT_MS || "30000", 10);
const credentialsPath = process.env.WAYON_SSH_CREDENTIALS_FILE
  || join(homedir(), ".config", "wayon", "ssh.credentials.json");
const debug = process.env.WAYON_SSH_DEBUG === "1";
const highWaterBytes = Number.parseInt(process.env.WAYON_SSH_HIGH_WATER_BYTES || "262144", 10);

function debugLog(message) {
  if (debug) process.stderr.write(`wayon ssh debug ${new Date().toISOString()}: ${message}\n`);
}

function exitWithError(message) {
  process.stderr.write(`wayon ssh: ${message}\n`);
  process.exit(1);
}

let credentials;
try {
  credentials = JSON.parse(readFileSync(credentialsPath, "utf8"));
} catch {
  exitWithError(`cannot read credentials: ${credentialsPath}`);
}
const wayonKey = String(credentials?.key || credentials?.token || "");
if (!wayonKey.startsWith("wayon_")) {
  exitWithError(`invalid credentials: ${credentialsPath}`);
}

const sessionEndpoint = new URL(endpoint);
sessionEndpoint.protocol = sessionEndpoint.protocol === "wss:" ? "https:" : "http:";
sessionEndpoint.pathname = sessionEndpoint.pathname.replace(/\/ssh$/, "/session");

let login;
try {
  login = await fetch(sessionEndpoint, {
    method: "POST",
    headers: {
      authorization: `Bearer ${wayonKey}`,
      accept: "application/json",
      "user-agent": "wayon-ssh-proxy/1.0",
    },
  });
} catch {
  exitWithError("login endpoint unavailable");
}
if (!login.ok) exitWithError(`login failed (${login.status})`);

const session = await login.json();
if (typeof session?.protocol !== "string" || !session.protocol.startsWith("wayon-ssh-v1.")) {
  exitWithError("invalid login response");
}

process.stdin.pause();
let stdinEnded = false;
let remoteReady = false;
const pendingInput = [];
let pumpTimer = null;
let retryTimer = null;
let originTimer = null;
let websocket = null;
const connectTimeout = setTimeout(() => exitWithError("connection timed out"), connectTimeoutMs);

function fail(message) {
  clearTimeout(connectTimeout);
  exitWithError(message);
}

function sendInput(chunk) {
  const bytes = Uint8Array.from(chunk);
  websocket.send(bytes.buffer);
  debugLog(`sent ${bytes.byteLength} bytes; buffered=${websocket.bufferedAmount}`);
  if (debug) setTimeout(() => debugLog(`buffered after send=${websocket.bufferedAmount}`), 100);
}

function scheduleInputPump() {
  if (pumpTimer === null) pumpTimer = setTimeout(pumpInput, 10);
}

function pumpInput() {
  pumpTimer = null;
  if (!remoteReady || websocket?.readyState !== 1) return;
  while (pendingInput.length && websocket.bufferedAmount < highWaterBytes) {
    sendInput(pendingInput.shift());
  }
  if (pendingInput.length || websocket.bufferedAmount >= highWaterBytes) {
    process.stdin.pause();
    scheduleInputPump();
  } else if (stdinEnded) {
    if (websocket.bufferedAmount === 0) websocket.close(1000, "stdin closed");
    else scheduleInputPump();
  } else {
    process.stdin.resume();
  }
}

function scheduleReconnect(ws, reason) {
  if (remoteReady) {
    fail(reason);
    return;
  }
  if (websocket !== ws) return;
  debugLog(`${reason}; retrying origin`);
  websocket = null;
  clearTimeout(originTimer);
  try { ws.close(1012, "retry origin"); } catch {}
  if (retryTimer === null) {
    retryTimer = setTimeout(() => {
      retryTimer = null;
      connectWebSocket();
    }, 1000);
  }
}

function connectWebSocket() {
  const ws = new WebSocket(endpoint, session.protocol);
  websocket = ws;
  ws.binaryType = "arraybuffer";

  ws.addEventListener("open", () => {
    if (websocket !== ws) return;
    debugLog("websocket open");
    clearTimeout(originTimer);
    originTimer = setTimeout(() => {
      if (!remoteReady) scheduleReconnect(ws, "origin banner timeout");
    }, 5000);
  });
  ws.addEventListener("message", (event) => {
    if (websocket !== ws) return;
    clearTimeout(originTimer);
    const bytes = event.data instanceof ArrayBuffer
      ? Buffer.from(event.data)
      : Buffer.from(event.data);
    process.stdout.write(bytes);
    if (!remoteReady) {
      debugLog(`origin ready; flushing ${pendingInput.length} chunks`);
      remoteReady = true;
      clearTimeout(connectTimeout);
      pumpInput();
    } else if (pendingInput.length || ws.bufferedAmount >= highWaterBytes) {
      scheduleInputPump();
    }
  });
  ws.addEventListener("error", () => scheduleReconnect(ws, "remote tunnel unavailable"));
  ws.addEventListener("close", (event) => {
    if (websocket !== ws) return;
    clearTimeout(originTimer);
    if (!remoteReady) scheduleReconnect(ws, `connection closed (${event.code})`);
    else if (event.code !== 1000 && !process.exitCode) fail(`connection closed (${event.code})`);
    else process.stdout.end();
  });
}

connectWebSocket();

process.stdin.on("data", (chunk) => {
  debugLog(`stdin ${chunk.length} bytes; ready=${remoteReady}`);
  pendingInput.push(Buffer.from(chunk));
  pumpInput();
});
process.stdin.on("end", () => {
  stdinEnded = true;
  pumpInput();
});
process.on("SIGTERM", () => process.exit(143));
process.on("SIGINT", () => process.exit(130));
