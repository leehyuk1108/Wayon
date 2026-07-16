#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const endpoint = process.env.WAYON_SSH_URL
  || "wss://wayon-cloud.leehyuk1108-comma.workers.dev/api/remote/ssh";
const connectTimeoutMs = Number.parseInt(process.env.WAYON_SSH_CONNECT_TIMEOUT_MS || "15000", 10);
const credentialsPath = process.env.WAYON_SSH_CREDENTIALS_FILE
  || join(homedir(), ".config", "wayon", "ssh.credentials.json");

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
if (typeof credentials?.username !== "string" || typeof credentials?.password !== "string"
    || !credentials.username || !credentials.password) {
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
      authorization: `Basic ${Buffer.from(`${credentials.username}:${credentials.password}`, "utf8").toString("base64")}`,
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

const websocket = new WebSocket(endpoint, session.protocol);
websocket.binaryType = "arraybuffer";
process.stdin.pause();
let stdinEnded = false;
const connectTimeout = setTimeout(() => exitWithError("connection timed out"), connectTimeoutMs);

function fail(message) {
  clearTimeout(connectTimeout);
  exitWithError(message);
}

websocket.addEventListener("open", () => {
  clearTimeout(connectTimeout);
  if (stdinEnded) websocket.close(1000, "stdin closed");
  else process.stdin.resume();
});
websocket.addEventListener("message", (event) => {
  const bytes = event.data instanceof ArrayBuffer
    ? Buffer.from(event.data)
    : Buffer.from(event.data);
  process.stdout.write(bytes);
});
websocket.addEventListener("error", () => fail("remote tunnel unavailable"));
websocket.addEventListener("close", (event) => {
  clearTimeout(connectTimeout);
  if (event.code !== 1000 && !process.exitCode) fail(`connection closed (${event.code})`);
  else process.stdout.end();
});

process.stdin.on("data", (chunk) => {
  if (websocket.readyState === 1) websocket.send(chunk);
});
process.stdin.on("end", () => {
  stdinEnded = true;
  if (websocket.readyState === 1) websocket.close(1000, "stdin closed");
});
process.on("SIGTERM", () => process.exit(143));
process.on("SIGINT", () => process.exit(130));
