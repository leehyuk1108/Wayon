import {
  attachPandaCounterHealth,
  buildAiPandaInterface,
} from "./panda_counter_health.mjs";

const CORS_HEADERS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-allow-headers": "authorization, content-type",
  "access-control-max-age": "86400",
};

const JSON_HEADERS = {
  ...CORS_HEADERS,
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

const FIREBASE_CAR_STATUS_URL = "https://mycarserver-fb85e-default-rtdb.firebaseio.com/car_status.json";
const REMOTE_SESSION_PATH = "/api/remote/session";
const REMOTE_SSH_PATH = "/api/remote/ssh";
const REMOTE_SSH_PROTOCOL_PREFIX = "wayon-ssh-v1";
const REMOTE_SSH_MAX_AGE_SECONDS = 60;
const REMOTE_SSH_KEY_TTL_SECONDS = 90;
const REMOTE_SSH_AUTHORIZE_PREFIX = "wayon-ssh-authorize-v1";
const LIVE_SESSION_PATH = "/api/live/session";
const LIVE_STREAM_PATH = "/api/live/stream";
const LIVE_PROTOCOL_PREFIX = "wayon-live-v1";
const LIVE_MAX_AGE_SECONDS = 30;
const DEVICE_REGISTER_PATH = "/api/devices/register";
const DEVICE_RELAY_PREFIX = "/api/device/relay/";
const AUTH_DEVICE_HEADER = "x-wayon-auth-device";
const LIVE_FRAME_HEADER_SIZE = 24;
const LIVE_FRAME_MAX_PAYLOAD_SIZE = 4 * 1024 * 1024;
const SERVER_API_TIMEOUT_MS = 5000;
const FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging";
const FCM_TOKEN_URL = "https://oauth2.googleapis.com/token";
const GMONE_MAX_PAYLOAD_BYTES = 256 * 1024;
const GMONE_STALE_AFTER_SECONDS = 24 * 60 * 60;
const REMOTE_START_IMPACT_SUPPRESSION_SECONDS = 45;
const DEFAULT_HEALTH_BRIDGE_URL = "https://health-bridge-api.hyuklee.workers.dev";
const TRIP_HEALTH_CACHE_SECONDS = 6 * 60 * 60;
let cachedFcmAccessToken = null;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: JSON_HEADERS,
  });
}

function historyJson(data, source) {
  return new Response(JSON.stringify(data), {
    headers: {
      ...JSON_HEADERS,
      "x-wayon-history-source": source,
    },
  });
}

function getBearerToken(request) {
  const header = request.headers.get("authorization") || "";
  if (header.toLowerCase().startsWith("bearer ")) {
    return header.slice(7).trim();
  }
  return "";
}

function constantTimeEqual(a, b) {
  if (!a || !b || a.length !== b.length) return false;

  let diff = 0;
  for (let i = 0; i < a.length; i += 1) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

function bytesToBase64Url(bytes) {
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function textToBase64Url(value) {
  return bytesToBase64Url(new TextEncoder().encode(value));
}

function base64UrlToText(value) {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) throw new Error("invalid_base64url");
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
  const binary = atob(padded);
  return new TextDecoder().decode(Uint8Array.from(binary, (character) => character.charCodeAt(0)));
}

function pemToBytes(pem) {
  const normalized = String(pem || "").replace(/\\n/g, "\n");
  const body = normalized.replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s/g, "");
  if (!body) throw new Error("FCM private key is missing");
  const binary = atob(body);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

async function createGoogleServiceJwt(env, nowSeconds = Math.floor(Date.now() / 1000)) {
  if (!env.FCM_CLIENT_EMAIL || !env.FCM_PRIVATE_KEY) {
    throw new Error("FCM service account bindings are missing");
  }

  const header = textToBase64Url(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const claims = textToBase64Url(JSON.stringify({
    iss: env.FCM_CLIENT_EMAIL,
    scope: FCM_SCOPE,
    aud: FCM_TOKEN_URL,
    iat: nowSeconds,
    exp: nowSeconds + 3600,
  }));
  const unsigned = `${header}.${claims}`;
  const key = await crypto.subtle.importKey(
    "pkcs8",
    pemToBytes(env.FCM_PRIVATE_KEY),
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    key,
    new TextEncoder().encode(unsigned),
  );
  return `${unsigned}.${bytesToBase64Url(new Uint8Array(signature))}`;
}

async function getFcmAccessToken(env) {
  const now = Date.now();
  if (cachedFcmAccessToken && cachedFcmAccessToken.expiresAt > now + 60_000) {
    return cachedFcmAccessToken.token;
  }

  const assertion = await createGoogleServiceJwt(env);
  const response = await fetch(FCM_TOKEN_URL, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion,
    }),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok || !result.access_token) {
    throw new Error(`FCM OAuth failed (${response.status})`);
  }

  cachedFcmAccessToken = {
    token: result.access_token,
    expiresAt: now + Math.max(60, Number(result.expires_in || 3600)) * 1000,
  };
  return cachedFcmAccessToken.token;
}

function hexToBytes(value) {
  if (!/^[0-9a-f]+$/i.test(value) || value.length % 2 !== 0) return null;
  const bytes = new Uint8Array(value.length / 2);
  for (let i = 0; i < bytes.length; i += 1) {
    bytes[i] = Number.parseInt(value.slice(i * 2, i * 2 + 2), 16);
  }
  return bytes;
}

function bytesToHex(bytes) {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function importHmacKey(secret, usage) {
  return crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    [usage],
  );
}

async function sha256Hex(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return bytesToHex(new Uint8Array(digest));
}

function validDeviceId(value) {
  return /^[A-Za-z0-9._:-]{4,128}$/.test(String(value || ""));
}

function validWayonKey(value) {
  return /^wayon_[A-Za-z0-9_-]{40,96}$/.test(String(value || ""));
}

function validSshPublicKey(value) {
  const match = String(value || "").trim().match(
    /^(ssh-rsa|ssh-ed25519) ([A-Za-z0-9+/]{40,4096}={0,2})(?: [A-Za-z0-9@._-]{1,128})?$/,
  );
  if (!match) return false;
  try {
    atob(match[2]);
    return true;
  } catch {
    return false;
  }
}

async function issueSignedProtocol(prefix, sessionSecret, deviceId, nowSeconds) {
  const nonceBytes = new Uint8Array(16);
  crypto.getRandomValues(nonceBytes);
  const nonce = bytesToHex(nonceBytes);
  const encodedDeviceId = textToBase64Url(deviceId);
  const signedValue = `${nowSeconds}:${nonce}:${encodedDeviceId}`;
  const key = await importHmacKey(sessionSecret, "sign");
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(signedValue),
  );
  return `${prefix}.${nowSeconds}.${nonce}.${encodedDeviceId}.${bytesToHex(new Uint8Array(signature))}`;
}

async function verifySignedProtocol(prefix, maxAgeSeconds, header, sessionSecret, nowSeconds) {
  if (!header || !sessionSecret) return null;

  const protocol = header.split(",").map((value) => value.trim())
    .find((value) => value.startsWith(`${prefix}.`));
  if (!protocol) return null;

  const parts = protocol.split(".");
  if (parts.length !== 5 || parts[0] !== prefix) return null;
  const timestamp = Number.parseInt(parts[1], 10);
  const nonce = parts[2];
  const encodedDeviceId = parts[3];
  const signature = hexToBytes(parts[4]);
  if (!Number.isFinite(timestamp) || Math.abs(nowSeconds - timestamp) > maxAgeSeconds) return null;
  if (!/^[0-9a-f]{32}$/i.test(nonce) || !signature || signature.length !== 32) return null;

  let deviceId;
  try {
    deviceId = base64UrlToText(encodedDeviceId);
  } catch {
    return null;
  }
  if (!validDeviceId(deviceId)) return null;

  const encoder = new TextEncoder();
  const key = await importHmacKey(sessionSecret, "verify");
  const valid = await crypto.subtle.verify(
    "HMAC",
    key,
    signature,
    encoder.encode(`${timestamp}:${nonce}:${encodedDeviceId}`),
  );
  return valid ? { protocol, deviceId } : null;
}

export async function issueRemoteSshProtocol(
  sessionSecret,
  deviceId = "test-device",
  nowSeconds = Math.floor(Date.now() / 1000),
) {
  return issueSignedProtocol(REMOTE_SSH_PROTOCOL_PREFIX, sessionSecret, deviceId, nowSeconds);
}

export async function verifyRemoteSshProtocol(
  header,
  sessionSecret,
  nowSeconds = Math.floor(Date.now() / 1000),
) {
  return verifySignedProtocol(
    REMOTE_SSH_PROTOCOL_PREFIX,
    REMOTE_SSH_MAX_AGE_SECONDS,
    header,
    sessionSecret,
    nowSeconds,
  );
}

export async function issueLiveProtocol(
  sessionSecret,
  deviceId = "test-device",
  nowSeconds = Math.floor(Date.now() / 1000),
) {
  return issueSignedProtocol(LIVE_PROTOCOL_PREFIX, sessionSecret, deviceId, nowSeconds);
}

export async function verifyLiveProtocol(
  header,
  sessionSecret,
  nowSeconds = Math.floor(Date.now() / 1000),
) {
  return verifySignedProtocol(
    LIVE_PROTOCOL_PREFIX,
    LIVE_MAX_AGE_SECONDS,
    header,
    sessionSecret,
    nowSeconds,
  );
}

async function authenticateDeviceKey(request, env) {
  const token = getBearerToken(request);
  if (!validWayonKey(token)) return null;

  const keyHash = await sha256Hex(token);
  const device = await env.DB.prepare(`
    SELECT device_id FROM wayon_devices
    WHERE key_hash = ? AND revoked_at IS NULL
  `).bind(keyHash).first();
  if (!device || !validDeviceId(device.device_id)) return null;

  // Authentication is also used by high-frequency read endpoints such as the
  // ambient command poll. Writing last_seen_at here turns every read into D1
  // write amplification and can exhaust the daily quota. Freshness is already
  // represented by latest_state.updated_at, while registration maintains the
  // device metadata timestamps.
  return { deviceId: device.device_id };
}

async function handleDeviceRegistration(request, env) {
  const payload = await request.json().catch(() => ({}));
  const deviceId = String(payload.deviceId || "").trim();
  const key = String(payload.key || "").trim();
  if (!validDeviceId(deviceId) || !validWayonKey(key)) {
    return json({ error: "invalid_device_registration" }, 400);
  }

  const legacyToken = getBearerToken(request);
  const legacyAuthorized = constantTimeEqual(legacyToken, env.WAYON_UPLOAD_TOKEN || "");
  const existing = await env.DB.prepare(`
    SELECT key_hash, revoked_at FROM wayon_devices WHERE device_id = ?
  `).bind(deviceId).first();
  const keyHash = await sha256Hex(key);
  if (existing && !constantTimeEqual(existing.key_hash || "", keyHash) && !legacyAuthorized) {
    return json({ error: "device_already_registered" }, 409);
  }

  const now = nowIso();
  await env.DB.prepare(`
    INSERT INTO wayon_devices (
      device_id, key_hash, created_at, updated_at, last_seen_at, revoked_at
    ) VALUES (?, ?, ?, ?, ?, NULL)
    ON CONFLICT(device_id) DO UPDATE SET
      key_hash = excluded.key_hash,
      updated_at = excluded.updated_at,
      last_seen_at = excluded.last_seen_at,
      revoked_at = NULL
  `).bind(deviceId, keyHash, now, now, now).run();
  return json({ ok: true, deviceId });
}

function scopedDeviceRequest(request, deviceId) {
  const url = new URL(request.url);
  url.searchParams.set("deviceId", deviceId);
  const headers = new Headers(request.headers);
  headers.set(AUTH_DEVICE_HEADER, deviceId);
  headers.set("x-wayon-device-id", deviceId);
  return new Request(url.toString(), {
    method: request.method,
    headers,
    body: request.body,
    redirect: request.redirect,
  });
}

function authenticatedDeviceId(request) {
  const deviceId = String(request.headers.get(AUTH_DEVICE_HEADER) || "");
  return validDeviceId(deviceId) ? deviceId : "";
}

function connectDeviceRelay(request, env, deviceId, kind, role, protocol = "") {
  const id = env.DEVICE_RELAY.idFromName(`${deviceId}:${kind}`);
  const headers = new Headers(request.headers);
  headers.set("x-wayon-relay-role", role);
  headers.set("x-wayon-relay-kind", kind);
  headers.set("x-wayon-relay-device", deviceId);
  if (protocol) headers.set("x-wayon-relay-protocol", protocol);
  return env.DEVICE_RELAY.get(id).fetch(new Request(request.url, { headers }));
}

async function authorizeDeviceSshKey(env, deviceId, publicKey, authorizationId) {
  try {
    const id = env.DEVICE_RELAY.idFromName(`${deviceId}:ssh`);
    const response = await env.DEVICE_RELAY.get(id).fetch(new Request(
      "https://wayon.internal/authorize-ssh-key",
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          publicKey,
          authorizationId,
          ttlSeconds: REMOTE_SSH_KEY_TTL_SECONDS,
        }),
      },
    ));
    return response.ok;
  } catch {
    return false;
  }
}

async function handleDeviceRelay(request, env, kind) {
  if ((request.headers.get("upgrade") || "").toLowerCase() !== "websocket") {
    return json({ error: "websocket_required" }, 426);
  }
  if (!env.DEVICE_RELAY || !["ssh", "live"].includes(kind)) {
    return json({ error: "relay_unavailable" }, 503);
  }
  const identity = await authenticateDeviceKey(request, env);
  if (!identity) return json({ error: "unauthorized" }, 401);
  return connectDeviceRelay(request, env, identity.deviceId, kind, "device");
}

export class WayonDeviceRelay {
  constructor(state) {
    this.state = state;
  }

  async fetch(request) {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/authorize-ssh-key") {
      const payload = await request.json().catch(() => ({}));
      const publicKey = String(payload.publicKey || "").trim();
      const authorizationId = String(payload.authorizationId || "");
      const ttlSeconds = Number(payload.ttlSeconds);
      if (!validSshPublicKey(publicKey)
          || !/^[0-9a-f]{32}$/i.test(authorizationId)
          || ttlSeconds < REMOTE_SSH_MAX_AGE_SECONDS
          || ttlSeconds > 120) {
        return new Response("invalid authorization", { status: 400 });
      }
      const device = this.state.getWebSockets("device")[0];
      if (!device) return new Response("device offline", { status: 409 });
      device.send(`${REMOTE_SSH_AUTHORIZE_PREFIX}.${textToBase64Url(JSON.stringify({
        publicKey,
        authorizationId,
        ttlSeconds,
      }))}`);
      return new Response(null, { status: 204 });
    }

    if ((request.headers.get("upgrade") || "").toLowerCase() !== "websocket") {
      return new Response("websocket required", { status: 426 });
    }
    const role = request.headers.get("x-wayon-relay-role");
    if (!['device', 'client'].includes(role)) {
      return new Response("invalid relay role", { status: 400 });
    }

    for (const socket of this.state.getWebSockets(role)) {
      try { socket.close(1000, "replaced"); } catch {}
    }

    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    server.serializeAttachment({ role });
    this.state.acceptWebSocket(server, [role]);

    if (role === "client") {
      const device = this.state.getWebSockets("device")[0];
      if (!device) {
        server.close(1013, "device offline");
      } else {
        device.send("wayon-peer-open");
      }
    } else {
      // A device relay can reconnect while an SSH client is still waiting for
      // its local socket. Re-open the peer instead of leaving that client with
      // an idle WebSocket until its SSH banner timeout expires.
      const client = this.state.getWebSockets("client")[0];
      if (client) server.send("wayon-peer-open");
    }

    const protocol = request.headers.get("x-wayon-relay-protocol") || "";
    return new Response(null, {
      status: 101,
      webSocket: client,
      headers: protocol ? { "Sec-WebSocket-Protocol": protocol } : {},
    });
  }

  webSocketMessage(socket, message) {
    const role = socket.deserializeAttachment()?.role;
    // Relay control messages are text. SSH and camera payloads are binary, so
    // never allow an authenticated client to impersonate Durable Object
    // control messages sent to the device.
    if (role === "client" && typeof message === "string") return;
    const destination = role === "device" ? "client" : "device";
    for (const peer of this.state.getWebSockets(destination)) {
      try { peer.send(message); } catch {}
    }
  }

  webSocketClose(socket) {
    const role = socket.deserializeAttachment()?.role;
    if (role === "client") {
      // fetch() replaces an older client before accepting the new one. Its
      // delayed close callback must not tear down the local SSH socket that
      // was just opened for the replacement client.
      if (this.state.getWebSockets("client").length === 0) {
        for (const device of this.state.getWebSockets("device")) {
          try { device.send("wayon-peer-close"); } catch {}
        }
      }
    } else if (role === "device") {
      // Device relay reconnects use the same replacement flow. Ignore the
      // delayed close callback from the old socket when its replacement is
      // already registered, or it will tear down an otherwise healthy SSH.
      if (this.state.getWebSockets("device").length === 0) {
        for (const client of this.state.getWebSockets("client")) {
          try { client.close(1012, "device offline"); } catch {}
        }
      }
    }
  }

  webSocketError(socket) {
    this.webSocketClose(socket);
  }
}

async function handleRemoteSession(request, env) {
  if (!env.DEVICE_RELAY || !env.WAYON_SSH_SESSION_SECRET) {
    return json({ error: "remote_access_unavailable" }, 503);
  }
  const identity = await authenticateDeviceKey(request, env);
  if (!identity) return json({ error: "unauthorized" }, 401);

  const payload = await request.json().catch(() => ({}));
  const publicKey = String(payload.publicKey || "").trim();
  if (publicKey && !validSshPublicKey(publicKey)) {
    return json({ error: "invalid_ssh_public_key" }, 400);
  }

  const issuedAt = Math.floor(Date.now() / 1000);
  const protocol = await issueRemoteSshProtocol(
    env.WAYON_SSH_SESSION_SECRET,
    identity.deviceId,
    issuedAt,
  );
  if (publicKey) {
    const authorizationId = protocol.split(".")[2];
    if (!await authorizeDeviceSshKey(env, identity.deviceId, publicKey, authorizationId)) {
      return json({ error: "device_offline" }, 409);
    }
  }
  return json({
    protocol,
    deviceId: identity.deviceId,
    expiresAt: issuedAt + REMOTE_SSH_MAX_AGE_SECONDS,
    credentialMode: publicKey ? "wayon_key_ephemeral" : "existing_ssh_key",
  });
}

async function handleLiveSession(request, env) {
  if (!env.DEVICE_RELAY || !env.WAYON_SSH_SESSION_SECRET) {
    return json({ error: "live_access_unavailable" }, 503);
  }
  const identity = await authenticateDeviceKey(request, env);
  if (!identity) return json({ error: "unauthorized" }, 401);

  const issuedAt = Math.floor(Date.now() / 1000);
  const websocketUrl = new URL(LIVE_STREAM_PATH, request.url);
  websocketUrl.protocol = websocketUrl.protocol === "https:" ? "wss:" : "ws:";
  return json({
    protocol: await issueLiveProtocol(env.WAYON_SSH_SESSION_SECRET, identity.deviceId, issuedAt),
    websocketUrl: websocketUrl.toString(),
    deviceId: identity.deviceId,
    expiresAt: issuedAt + LIVE_MAX_AGE_SECONDS,
  });
}

export async function websocketBytes(data) {
  if (data instanceof ArrayBuffer) return new Uint8Array(data.slice(0));
  if (ArrayBuffer.isView(data)) {
    return new Uint8Array(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength));
  }
  if (data instanceof Blob) return new Uint8Array(await data.arrayBuffer());
  if (typeof data === "string") return new TextEncoder().encode(data);
  return null;
}

export class WayonLiveFrameAssembler {
  constructor() {
    this.header = new Uint8Array(LIVE_FRAME_HEADER_SIZE);
    this.headerLength = 0;
    this.frame = null;
    this.frameLength = 0;
  }

  push(chunk) {
    const complete = [];
    let offset = 0;

    while (offset < chunk.byteLength) {
      if (!this.frame) {
        const headerBytes = Math.min(
          LIVE_FRAME_HEADER_SIZE - this.headerLength,
          chunk.byteLength - offset,
        );
        this.header.set(chunk.subarray(offset, offset + headerBytes), this.headerLength);
        this.headerLength += headerBytes;
        offset += headerBytes;
        if (this.headerLength < LIVE_FRAME_HEADER_SIZE) continue;

        if (this.header[0] !== 87 || this.header[1] !== 76
            || this.header[2] !== 86 || this.header[3] !== 49) {
          throw new TypeError("invalid Wayon Live frame");
        }
        const payloadSize = new DataView(
          this.header.buffer,
          this.header.byteOffset,
          this.header.byteLength,
        ).getUint32(20);
        if (payloadSize > LIVE_FRAME_MAX_PAYLOAD_SIZE) {
          throw new RangeError("Wayon Live frame too large");
        }

        this.frame = new Uint8Array(LIVE_FRAME_HEADER_SIZE + payloadSize);
        this.frame.set(this.header);
        this.frameLength = LIVE_FRAME_HEADER_SIZE;
      }

      const frameBytes = Math.min(
        this.frame.byteLength - this.frameLength,
        chunk.byteLength - offset,
      );
      this.frame.set(chunk.subarray(offset, offset + frameBytes), this.frameLength);
      this.frameLength += frameBytes;
      offset += frameBytes;

      if (this.frameLength === this.frame.byteLength) {
        complete.push(this.frame);
        this.frame = null;
        this.frameLength = 0;
        this.headerLength = 0;
      }
    }
    return complete;
  }
}

async function handleRemoteSsh(request, env, ctx) {
  if ((request.headers.get("upgrade") || "").toLowerCase() !== "websocket") {
    return json({ error: "websocket_required" }, 426);
  }
  if (!env.DEVICE_RELAY || !env.WAYON_SSH_SESSION_SECRET) {
    return json({ error: "remote_access_unavailable" }, 503);
  }

  const session = await verifyRemoteSshProtocol(
    request.headers.get("sec-websocket-protocol") || "",
    env.WAYON_SSH_SESSION_SECRET,
  );
  if (!session) return json({ error: "unauthorized" }, 401);

  return connectDeviceRelay(request, env, session.deviceId, "ssh", "client", session.protocol);
}

async function handleLiveStream(request, env, ctx) {
  if ((request.headers.get("upgrade") || "").toLowerCase() !== "websocket") {
    return json({ error: "websocket_required" }, 426);
  }
  if (!env.DEVICE_RELAY || !env.WAYON_SSH_SESSION_SECRET) {
    return json({ error: "live_access_unavailable" }, 503);
  }

  const session = await verifyLiveProtocol(
    request.headers.get("sec-websocket-protocol") || "",
    env.WAYON_SSH_SESSION_SECRET,
  );
  if (!session) return json({ error: "unauthorized" }, 401);

  return connectDeviceRelay(request, env, session.deviceId, "live", "client", session.protocol);
}

function authorize(request, env, write = false) {
  return validDeviceId(request.headers.get(AUTH_DEVICE_HEADER));
}

function authorizePushRegistration(request, env) {
  return authorize(request, env, true);
}

function authorizeGmoneUpload(request, env) {
  return authorize(request, env, true)
    || constantTimeEqual(getBearerToken(request), env.WAYON_GMONE_TOKEN || "");
}

export function authorizeGmoneRefreshPoll(request, env) {
  return authorizeGmoneUpload(request, env);
}

export function impactSuppressedByRemoteStart(detectedAt, suppression) {
  const detectedAtMs = Date.parse(String(detectedAt || ""));
  const suppressFromMs = Date.parse(String(suppression?.suppress_from || ""));
  const suppressUntilMs = Date.parse(String(suppression?.suppress_until || ""));
  return Number.isFinite(detectedAtMs) && Number.isFinite(suppressFromMs)
    && Number.isFinite(suppressUntilMs)
    && detectedAtMs >= suppressFromMs && detectedAtMs <= suppressUntilMs;
}

async function handleImpactSuppression(request, env) {
  if (!authorizePushRegistration(request, env)) return json({ error: "unauthorized" }, 401);

  const payload = await request.json().catch(() => ({}));
  const deviceId = authenticatedDeviceId(request);
  const requestId = String(payload.requestId || "").trim().slice(0, 128);
  if (!deviceId || !requestId) return json({ error: "invalid_suppression" }, 400);

  if (payload.action === "cancel") {
    await env.DB.prepare(
      "DELETE FROM impact_suppressions WHERE device_id = ? AND request_id = ?",
    ).bind(deviceId, requestId).run();
    return json({ ok: true, active: false, deviceId, requestId });
  }

  const suppressFrom = new Date();
  const suppressUntil = new Date(
    suppressFrom.getTime() + REMOTE_START_IMPACT_SUPPRESSION_SECONDS * 1000,
  );
  await env.DB.prepare(`
    INSERT INTO impact_suppressions (
      device_id, request_id, suppress_from, suppress_until, reason, updated_at
    ) VALUES (?, ?, ?, ?, 'remote_start_request', ?)
    ON CONFLICT(device_id) DO UPDATE SET
      request_id = excluded.request_id,
      suppress_from = excluded.suppress_from,
      suppress_until = excluded.suppress_until,
      reason = excluded.reason,
      updated_at = excluded.updated_at
  `).bind(
    deviceId, requestId, suppressFrom.toISOString(), suppressUntil.toISOString(), nowIso(),
  ).run();
  return json({
    ok: true,
    active: true,
    deviceId,
    requestId,
    suppressFrom: suppressFrom.toISOString(),
    suppressUntil: suppressUntil.toISOString(),
  });
}

function authorizeAi(request, env) {
  return constantTimeEqual(getBearerToken(request), env.WAYON_AI_READ_TOKEN || "");
}

function authorizeServerSync(request, env) {
  return constantTimeEqual(getBearerToken(request), env.WAYON_SERVER_SYNC_TOKEN || "");
}

function requireBindings(env) {
  return Boolean(env.DB && env.SNAPSHOTS);
}

function toInt(value) {
  return value ? 1 : 0;
}

function nullableNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function objectWithValues(value) {
  return value && typeof value === "object" && !Array.isArray(value) && Object.keys(value).length > 0;
}

export function normalizeTripAnalysis(payload) {
  if (objectWithValues(payload?.analysis)) return payload.analysis;

  const report = payload?.report;
  if (!objectWithValues(report) || !report.schemaVersion) return {};
  if (String(report.schemaVersion).startsWith("wayon-drive-report-v1")) return report;

  const durationS = Math.max(0, nullableNumber(payload.durationS ?? payload.duration_s) ?? 0);
  const openpilot = report.openpilot || {};
  const stopQuality = report.stopQuality || {};
  const cutInRisk = report.cutInRisk || {};
  const opActiveS = Math.max(0, nullableNumber(openpilot.activeDurationS) ?? 0);
  const stopEvents = Array.isArray(stopQuality.events) ? stopQuality.events : [];
  const peakJerkMps3 = stopEvents.reduce(
    (peak, event) => Math.max(peak, nullableNumber(event?.peak_jerk_mps3) ?? 0),
    0,
  );

  return {
    schemaVersion: "wayon-drive-report-v1-legacy",
    generatedAt: nowIso(),
    dataQuality: {
      confidence: durationS >= 60 ? "medium" : "low",
      durationS,
      source: report.schemaVersion,
    },
    scores: {
      comfort: nullableNumber(stopQuality.score),
      attention: null,
      systemStability: null,
    },
    automation: {
      opActiveS,
      manualS: Math.max(0, durationS - opActiveS),
      opUsagePercent: nullableNumber(openpilot.activePercent),
      disengagementCount: null,
      steeringInterventionCount: null,
    },
    comfort: {
      stopCount: nullableNumber(stopQuality.count),
      harshStopCount: nullableNumber(stopQuality.harshCount),
      hardAccelerationCount: null,
      hardBrakingCount: null,
      lowSpeedOscillationCount: null,
      peakJerkMps3: peakJerkMps3 || null,
    },
    longitudinal: {
      leadAcquisitionCount: null,
      fcwCount: null,
      cutInEventCount: nullableNumber(cutInRisk.eventCount),
      maximumCutInRiskLevel: nullableNumber(cutInRisk.maxLevel),
    },
    attention: {},
    system: {},
    moments: [],
    timeline: [],
    legacyReport: report,
  };
}

function tripWithAnalysis(trip, report = trip?.report) {
  const analysis = normalizeTripAnalysis({
    analysis: trip?.analysis,
    report,
    durationS: trip?.duration_s ?? trip?.durationS,
  });
  return {
    ...trip,
    report: objectWithValues(report) ? report : analysis,
    analysis,
    health: objectWithValues(trip?.health) ? trip.health : {},
  };
}

function validCoordinate(value) {
  const coordinate = nullableNumber(value);
  return coordinate != null && Math.abs(coordinate) > 0.001;
}

function hasLocation(gps) {
  return validCoordinate(gps?.latitude) && validCoordinate(gps?.longitude);
}

function storedGps(rawJson, state) {
  let previousGps = {};
  try {
    previousGps = JSON.parse(rawJson || "{}").gps || {};
  } catch {
    previousGps = {};
  }

  return {
    ...previousGps,
    latitude: nullableNumber(state.latitude),
    longitude: nullableNumber(state.longitude),
    bearingDeg: nullableNumber(state.bearing_deg) ?? previousGps.bearingDeg,
    accuracyM: nullableNumber(state.gps_accuracy_m) ?? previousGps.accuracyM,
    fresh: false,
    source: "lastKnown",
  };
}

async function resolveTelemetryGps(env, deviceId, gps) {
  const gpsHasLocation = hasLocation(gps);
  if (gpsHasLocation && gps.fresh === true) return gps;

  const latestTrip = await env.DB.prepare(`
    SELECT end_lat, end_lon, ended_at
    FROM trips
    WHERE device_id = ? AND end_lat IS NOT NULL AND end_lon IS NOT NULL
    ORDER BY ended_at DESC LIMIT 1
  `).bind(deviceId).first();
  if (latestTrip && validCoordinate(latestTrip.end_lat) && validCoordinate(latestTrip.end_lon)) {
    const tripTimestampMillis = Date.parse(latestTrip.ended_at || "");
    return {
      latitude: nullableNumber(latestTrip.end_lat),
      longitude: nullableNumber(latestTrip.end_lon),
      timestampMillis: Number.isFinite(tripTimestampMillis) ? tripTimestampMillis : null,
      fresh: false,
      source: "latestTrip",
    };
  }

  if (gpsHasLocation) return gps;

  const currentState = await env.DB.prepare(`
    SELECT latitude, longitude, bearing_deg, gps_accuracy_m, raw_json
    FROM latest_state WHERE device_id = ?
  `).bind(deviceId).first();
  if (currentState && validCoordinate(currentState.latitude) && validCoordinate(currentState.longitude)) {
    return storedGps(currentState.raw_json, currentState);
  }

  return gps;
}

function boundedLimit(value, fallback = 100, max = 1000) {
  const parsed = Number.parseInt(value || "", 10);
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback;
  return Math.min(parsed, max);
}

function nowIso() {
  return new Date().toISOString();
}

async function fetchVehicleStatus(env, deviceId) {
  if (!env.WAYON_LEGACY_FIREBASE_DEVICE_ID
      || !constantTimeEqual(deviceId, env.WAYON_LEGACY_FIREBASE_DEVICE_ID)) {
    return { ok: false, error: "not_configured_for_device" };
  }
  try {
    const response = await fetch(FIREBASE_CAR_STATUS_URL, {
      headers: { accept: "application/json" },
      cf: { cacheTtl: 0, cacheEverything: false },
    });
    if (!response.ok) {
      return { ok: false, error: `${response.status} ${response.statusText}` };
    }
    const data = await response.json();
    return { ok: true, source: "firebase", updatedAt: nowIso(), data: data || {} };
  } catch (err) {
    return { ok: false, error: String(err?.message || err) };
  }
}

const GMONE_SENSITIVE_KEY_PARTS = [
  "access_token", "api_key", "auth_token", "door_password", "email", "iccid",
  "imei", "password", "phone_number", "secret", "session_token", "ticket_uuid",
  "token_key", "user_uuid", "uuid", "vin",
];
const GMONE_VIN_PATTERN = /^[A-HJ-NPR-Z0-9]{17}$/i;
const GMONE_UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function gmoneSensitiveKey(key) {
  const normalized = String(key || "").toLowerCase();
  return GMONE_SENSITIVE_KEY_PARTS.some((part) => normalized.includes(part));
}

export function sanitizeGmonePayload(value) {
  if (Array.isArray(value)) return value.map(sanitizeGmonePayload);
  if (value && typeof value === "object") {
    const result = {};
    for (const [key, item] of Object.entries(value)) {
      if (gmoneSensitiveKey(key)) continue;
      const safeKey = GMONE_VIN_PATTERN.test(key) || GMONE_UUID_PATTERN.test(key) ? "redacted" : key;
      result[safeKey] = sanitizeGmonePayload(item);
    }
    return result;
  }
  if (typeof value === "string" && (GMONE_VIN_PATTERN.test(value) || GMONE_UUID_PATTERN.test(value))) {
    return "<redacted>";
  }
  return value;
}

function validIsoOrNow(value) {
  const timestamp = Date.parse(String(value || ""));
  return Number.isFinite(timestamp) ? new Date(timestamp).toISOString() : nowIso();
}

export function vehicleEventNotificationEligible(
  occurredAt,
  nowMs = Date.now(),
  maxAgeSeconds = 600,
) {
  const occurredAtMs = Date.parse(String(occurredAt || ""));
  if (!Number.isFinite(occurredAtMs)) return false;
  const ageSeconds = (nowMs - occurredAtMs) / 1000;
  return ageSeconds >= -120 && ageSeconds <= maxAgeSeconds;
}

async function latestGmoneStatus(env, deviceId) {
  const row = await env.DB.prepare(`
    SELECT source, collected_at, vehicle_updated_at, payload_json, updated_at
    FROM gmone_latest WHERE id = ?
  `).bind(deviceId).first();
  if (!row) return null;

  let payload;
  try {
    payload = JSON.parse(row.payload_json || "{}");
  } catch {
    return null;
  }
  const ageSeconds = isoAgeSeconds(row.collected_at);
  return {
    ok: true,
    source: row.source || "gmone-direct",
    updatedAt: row.vehicle_updated_at || row.collected_at,
    collectedAt: row.collected_at,
    receivedAt: row.updated_at,
    ageSeconds,
    stale: ageSeconds == null || ageSeconds > GMONE_STALE_AFTER_SECONDS,
    data: payload.status && typeof payload.status === "object" ? payload.status : {},
    health: payload.health && typeof payload.health === "object" ? payload.health : {},
    module: payload.module && typeof payload.module === "object" ? payload.module : {},
    diagnostic: payload.diagnostic && typeof payload.diagnostic === "object" ? payload.diagnostic : {},
  };
}

export function mergeVehicleStatus(firebaseStatus, gmoneStatus) {
  const firebaseOk = Boolean(firebaseStatus?.ok && firebaseStatus?.data);
  const gmoneOk = Boolean(gmoneStatus?.ok && gmoneStatus?.data);
  const useFreshGmone = gmoneOk && (!gmoneStatus.stale || !firebaseOk);
  const data = {
    ...(firebaseOk ? firebaseStatus.data : {}),
    ...(useFreshGmone ? gmoneStatus.data : {}),
  };
  const preferred = useFreshGmone ? gmoneStatus : firebaseStatus;
  const sourceNames = [firebaseOk ? "firebase" : null, useFreshGmone ? gmoneStatus.source : null]
    .filter(Boolean);
  return {
    ok: firebaseOk || gmoneOk,
    source: sourceNames.join("+") || gmoneStatus?.source || "unavailable",
    updatedAt: preferred?.updatedAt || preferred?.collectedAt || nowIso(),
    stale: useFreshGmone ? Boolean(gmoneStatus.stale) : false,
    data,
    sources: { firebase: firebaseStatus, gmone: gmoneStatus },
  };
}

async function fetchMergedVehicleStatus(env, deviceId) {
  const [firebaseStatus, gmoneStatus] = await Promise.all([
    fetchVehicleStatus(env, deviceId),
    latestGmoneStatus(env, deviceId),
  ]);
  return mergeVehicleStatus(firebaseStatus, gmoneStatus);
}

function gmoneDeviceId(request, env, payload = {}) {
  return authenticatedDeviceId(request)
    || (constantTimeEqual(getBearerToken(request), env.WAYON_GMONE_TOKEN || "")
      ? String(payload.deviceId || env.WAYON_LEGACY_FIREBASE_DEVICE_ID || "")
      : "");
}

async function handleGmoneStatus(request, env) {
  if (!authorizeGmoneUpload(request, env)) return json({ error: "unauthorized" }, 401);
  const contentLength = Number(request.headers.get("content-length") || 0);
  if (contentLength > GMONE_MAX_PAYLOAD_BYTES) return json({ error: "payload_too_large" }, 413);

  const rawPayload = await request.json();
  const deviceId = gmoneDeviceId(request, env, rawPayload);
  const payload = sanitizeGmonePayload(rawPayload);
  if (!validDeviceId(deviceId) || payload?.schemaVersion !== "wayon-gmone-v1"
      || !payload.status || typeof payload.status !== "object") {
    return json({ error: "invalid_gmone_payload" }, 400);
  }
  const encoded = JSON.stringify(payload);
  if (new TextEncoder().encode(encoded).byteLength > GMONE_MAX_PAYLOAD_BYTES) {
    return json({ error: "payload_too_large" }, 413);
  }

  const source = String(payload.source || payload.status.source || "gmone-direct").slice(0, 64);
  const collectedAt = validIsoOrNow(payload.collectedAt);
  const vehicleUpdatedAt = payload.vehicleUpdatedAt ? validIsoOrNow(payload.vehicleUpdatedAt) : null;
  const receivedAt = nowIso();
  await env.DB.prepare(`
    INSERT INTO gmone_latest (
      id, source, collected_at, vehicle_updated_at, payload_json, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      source = excluded.source,
      collected_at = excluded.collected_at,
      vehicle_updated_at = excluded.vehicle_updated_at,
      payload_json = excluded.payload_json,
      updated_at = excluded.updated_at
  `).bind(deviceId, source, collectedAt, vehicleUpdatedAt, encoded, receivedAt).run();
  await env.DB.prepare(`
    UPDATE gmone_refresh_requests SET completed_at = ?
    WHERE id = ? AND requested_at <= ?
  `).bind(receivedAt, deviceId, collectedAt).run();
  return json({ ok: true, deviceId, collectedAt, receivedAt });
}

async function handleGmoneRefreshRequest(request, env) {
  if (!authorize(request, env, false)) return json({ error: "unauthorized" }, 401);
  const deviceId = authenticatedDeviceId(request);
  const existing = await env.DB.prepare(`
    SELECT requested_at, completed_at FROM gmone_refresh_requests WHERE id = ?
  `).bind(deviceId).first();
  const ageSeconds = existing?.requested_at ? isoAgeSeconds(existing.requested_at) : null;
  if (ageSeconds != null && ageSeconds < 15) {
    return json({ ok: true, deviceId, requestedAt: existing.requested_at, deduplicated: true });
  }

  const requestedAt = nowIso();
  await env.DB.prepare(`
    INSERT INTO gmone_refresh_requests (id, requested_at, completed_at)
    VALUES (?, ?, NULL)
    ON CONFLICT(id) DO UPDATE SET requested_at = excluded.requested_at, completed_at = NULL
  `).bind(deviceId, requestedAt).run();
  return json({ ok: true, deviceId, requestedAt, deduplicated: false });
}

async function handleGmoneRefreshPoll(request, env) {
  if (!authorizeGmoneRefreshPoll(request, env)) return json({ error: "unauthorized" }, 401);
  const deviceId = gmoneDeviceId(request, env, {});
  if (!validDeviceId(deviceId)) return json({ error: "missing_device_id" }, 400);
  const row = await env.DB.prepare(`
    SELECT requested_at, completed_at FROM gmone_refresh_requests WHERE id = ?
  `).bind(deviceId).first();
  const pending = Boolean(row?.requested_at && (!row.completed_at || row.completed_at < row.requested_at));
  return json({ deviceId, pending, requestedAt: row?.requested_at || null, completedAt: row?.completed_at || null });
}

function base64ToBytes(value) {
  const clean = String(value || "").replace(/^data:image\/jpeg;base64,/, "");
  const binary = atob(clean);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function handleTelemetry(request, env) {
  if (!authorize(request, env, true)) {
    return json({ error: "unauthorized" }, 401);
  }

  const payload = await request.json();
  const deviceId = authenticatedDeviceId(request);
  const updatedAt = payload.updatedAt || nowIso();
  const [gps, previousState] = await Promise.all([
    resolveTelemetryGps(env, deviceId, payload.gps || {}),
    env.DB.prepare(`
      SELECT updated_at, raw_json
      FROM latest_state WHERE device_id = ?
    `).bind(deviceId).first(),
  ]);
  payload.gps = gps;
  attachPandaCounterHealth(
    payload,
    parseJsonObject(previousState?.raw_json),
    previousState?.updated_at,
    updatedAt,
  );
  const speedMps = payload.vehicleSpeedMps ?? payload.speedMps ?? gps.speedMps;

  await env.DB.prepare(`
    INSERT INTO latest_state (
      device_id, updated_at, onroad, ignition, enabled, voltage_v, current_ma,
      power_w, device_power_w, thermal_status, fan_percent,
      screen_brightness_percent, latitude, longitude, speed_mps, bearing_deg,
      gps_accuracy_m, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(device_id) DO UPDATE SET
      updated_at = excluded.updated_at,
      onroad = excluded.onroad,
      ignition = excluded.ignition,
      enabled = excluded.enabled,
      voltage_v = excluded.voltage_v,
      current_ma = excluded.current_ma,
      power_w = excluded.power_w,
      device_power_w = excluded.device_power_w,
      thermal_status = excluded.thermal_status,
      fan_percent = excluded.fan_percent,
      screen_brightness_percent = excluded.screen_brightness_percent,
      latitude = excluded.latitude,
      longitude = excluded.longitude,
      speed_mps = excluded.speed_mps,
      bearing_deg = excluded.bearing_deg,
      gps_accuracy_m = excluded.gps_accuracy_m,
      raw_json = excluded.raw_json
  `).bind(
    deviceId,
    updatedAt,
    toInt(payload.onroad),
    toInt(payload.ignition),
    toInt(payload.enabled),
    nullableNumber(payload.voltageV),
    nullableNumber(payload.currentMa),
    nullableNumber(payload.powerW),
    nullableNumber(payload.devicePowerW),
    payload.thermalStatus || null,
    payload.fanPercent ?? null,
    payload.screenBrightnessPercent ?? null,
    nullableNumber(gps.latitude),
    nullableNumber(gps.longitude),
    nullableNumber(speedMps),
    nullableNumber(gps.bearingDeg),
    nullableNumber(gps.accuracyM),
    JSON.stringify(payload),
  ).run();

  return json({ ok: true });
}

async function handleHealthEvent(request, env) {
  if (!authorize(request, env, true)) return json({ error: "unauthorized" }, 401);
  const payload = await request.json();
  const deviceId = authenticatedDeviceId(request);
  const id = String(payload.id || crypto.randomUUID()).slice(0, 160);
  const occurredAt = validIsoOrNow(payload.occurredAt);
  const category = String(payload.category || "system").slice(0, 48);
  const severity = ["normal", "warning", "critical"].includes(payload.severity)
    ? payload.severity : "warning";
  const title = String(payload.title || "Vehicle health update").slice(0, 120);
  const detail = String(payload.detail || "").slice(0, 500);
  const snapshot = payload.snapshot && typeof payload.snapshot === "object" ? payload.snapshot : {};
  await env.DB.prepare(`
    INSERT OR REPLACE INTO health_events (
      id, device_id, occurred_at, category, severity, title, detail, snapshot_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(id, deviceId, occurredAt, category, severity, title, detail, JSON.stringify(snapshot), nowIso()).run();
  return json({ ok: true, id });
}

async function latestHealthTimeline(env, deviceId, limit = 40) {
  const result = await env.DB.prepare(`
    SELECT id, occurred_at, category, severity, title, detail, snapshot_json
    FROM health_events WHERE device_id = ? ORDER BY occurred_at DESC LIMIT ?
  `).bind(deviceId, limit).all();
  return (result.results || []).map((row) => ({
    id: row.id,
    occurred_at: row.occurred_at,
    category: row.category,
    severity: row.severity,
    title: row.title,
    detail: row.detail,
    snapshot: parseJsonObject(row.snapshot_json),
  }));
}

function impactData(event) {
  return Object.fromEntries(Object.entries({
    type: "wayon_impact",
    impactId: event.id,
    deviceId: event.deviceId,
    detectedAt: event.detectedAt,
    severity: event.severity,
    peakDynamicG: event.peakDynamicG,
    peakTotalG: event.peakTotalG,
    peakJerkGPerSec: event.peakJerkGPerSec,
    peakGyroRadPerSec: event.peakGyroRadPerSec,
    latitude: event.latitude,
    longitude: event.longitude,
    test: event.test ? "true" : "false",
  }).filter(([, value]) => value != null).map(([key, value]) => [key, String(value)]));
}

function doorLockData(event) {
  return Object.fromEntries(Object.entries({
    type: "wayon_door_lock",
    vehicleEventId: event.id,
    deviceId: event.deviceId,
    occurredAt: event.occurredAt,
    locked: event.locked ? "true" : "false",
    test: event.test ? "true" : "false",
  }).filter(([, value]) => value != null).map(([key, value]) => [key, String(value)]));
}

export function visibleFcmNotification(data) {
  if (data?.type !== "wayon_door_lock") return null;
  const locked = data.locked === "true";
  return {
    title: data.test === "true"
      ? "차량 잠금 알림 테스트"
      : (locked ? "차량 잠금 활성화" : "차량 잠금 해제"),
    body: locked ? "차량 잠금이 활성화되었습니다." : "차량 잠금이 해제되었습니다.",
    channelId: "wayon_door_lock_alerts",
  };
}

function parkingUnlockedData(event) {
  return Object.fromEntries(Object.entries({
    type: "wayon_parking_unlocked",
    vehicleEventId: event.id,
    deviceId: event.deviceId,
    occurredAt: event.occurredAt,
    delaySeconds: event.delaySeconds,
    latitude: event.latitude,
    longitude: event.longitude,
    locationUpdatedAt: event.locationUpdatedAt,
    test: event.test ? "true" : "false",
  }).filter(([, value]) => value != null).map(([key, value]) => [key, String(value)]));
}

async function sendFcmMessage(env, token, data) {
  if (!env.FCM_PROJECT_ID) throw new Error("FCM project binding is missing");
  const accessToken = await getFcmAccessToken(env);
  const visibleNotification = visibleFcmNotification(data);
  const message = {
    token,
    data,
    android: {
      priority: "HIGH",
      ttl: "300s",
      ...(visibleNotification ? {
        notification: { channel_id: visibleNotification.channelId },
      } : {}),
    },
    ...(visibleNotification ? {
      notification: {
        title: visibleNotification.title,
        body: visibleNotification.body,
      },
    } : {}),
  };
  const response = await fetch(
    `https://fcm.googleapis.com/v1/projects/${encodeURIComponent(env.FCM_PROJECT_ID)}/messages:send`,
    {
      method: "POST",
      headers: {
        authorization: `Bearer ${accessToken}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({ message }),
    },
  );
  const result = await response.json().catch(() => ({}));
  return { ok: response.ok, status: response.status, result };
}

function invalidFcmToken(response) {
  const details = response?.result?.error?.details || [];
  const errorCodes = details.map((detail) => detail.errorCode).filter(Boolean);
  return response.status === 404 || errorCodes.includes("UNREGISTERED")
    || errorCodes.includes("INVALID_ARGUMENT");
}

async function sendDataNotifications(env, deviceId, data) {
  const query = deviceId === "*"
    ? env.DB.prepare("SELECT token FROM push_subscriptions")
    : env.DB.prepare("SELECT token FROM push_subscriptions WHERE device_id = ? OR device_id = '*'")
      .bind(deviceId);
  const subscriptions = await query.all();
  const tokens = [...new Set((subscriptions.results || []).map((row) => row.token).filter(Boolean))];
  let sent = 0;
  let failed = 0;
  let invalid = 0;

  for (const token of tokens) {
    const response = await sendFcmMessage(env, token, data);
    if (response.ok) {
      sent += 1;
    } else if (invalidFcmToken(response)) {
      await env.DB.prepare("DELETE FROM push_subscriptions WHERE token = ?").bind(token).run();
      invalid += 1;
    } else {
      failed += 1;
      console.error("Wayon FCM send failed", response.status, response.result?.error?.status || "unknown");
    }
  }
  return { sent, failed, invalid, subscriptions: tokens.length };
}

async function sendImpactNotifications(env, event) {
  return sendDataNotifications(env, event.deviceId, impactData(event));
}

async function handleImpact(request, env) {
  if (!authorize(request, env, true)) return json({ error: "unauthorized" }, 401);

  const payload = await request.json();
  const id = String(payload.id || crypto.randomUUID()).slice(0, 128);
  const deviceId = authenticatedDeviceId(request);
  const detectedAt = String(payload.detectedAt || nowIso()).slice(0, 64);
  const suppression = await env.DB.prepare(`
    SELECT request_id, suppress_from, suppress_until, reason
    FROM impact_suppressions WHERE device_id = ?
  `).bind(deviceId).first();
  if (!payload.test && impactSuppressedByRemoteStart(detectedAt, suppression)) {
    return json({
      ok: true,
      id,
      suppressed: true,
      reason: suppression.reason || "remote_start_request",
      requestId: suppression.request_id,
    });
  }
  const severity = ["light", "moderate", "severe"].includes(payload.severity)
    ? payload.severity : "light";
  const state = await env.DB.prepare(
    "SELECT latitude, longitude FROM latest_state WHERE device_id = ?",
  ).bind(deviceId).first();
  const latitude = nullableNumber(payload.latitude) ?? nullableNumber(state?.latitude);
  const longitude = nullableNumber(payload.longitude) ?? nullableNumber(state?.longitude);
  const receivedAt = nowIso();
  const captureStatus = payload.captureRequested ? "pending" : "not_requested";

  const inserted = await env.DB.prepare(`
    INSERT OR IGNORE INTO impact_events (
      id, device_id, detected_at, received_at, severity, peak_dynamic_g,
      peak_total_g, peak_jerk_g_per_s, peak_gyro_rad_per_s, duration_ms,
      sample_count, sensor_clipped, latitude, longitude, capture_status,
      notified_count, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
  `).bind(
    id,
    deviceId,
    detectedAt,
    receivedAt,
    severity,
    nullableNumber(payload.peakDynamicG),
    nullableNumber(payload.peakTotalG),
    nullableNumber(payload.peakJerkGPerSec),
    nullableNumber(payload.peakGyroRadPerSec),
    nullableNumber(payload.durationMs),
    nullableNumber(payload.sampleCount),
    toInt(payload.sensorClipped),
    latitude,
    longitude,
    captureStatus,
    JSON.stringify(payload),
  ).run();

  if (!inserted.meta?.changes) {
    const existing = await env.DB.prepare("SELECT notified_count FROM impact_events WHERE id = ?")
      .bind(id).first();
    if (Number(existing?.notified_count || 0) > 0) {
      return json({ ok: true, id, duplicate: true, notified: existing.notified_count });
    }
  }

  const event = {
    id,
    deviceId,
    detectedAt,
    severity,
    peakDynamicG: nullableNumber(payload.peakDynamicG),
    peakTotalG: nullableNumber(payload.peakTotalG),
    peakJerkGPerSec: nullableNumber(payload.peakJerkGPerSec),
    peakGyroRadPerSec: nullableNumber(payload.peakGyroRadPerSec),
    latitude,
    longitude,
    test: Boolean(payload.test),
  };
  const notification = await sendImpactNotifications(env, event);
  if (notification.failed > 0 && notification.sent === 0) {
    throw new Error("FCM delivery failed; impact remains pending");
  }
  await env.DB.prepare("UPDATE impact_events SET notified_count = ? WHERE id = ?")
    .bind(notification.sent, id).run();
  return json({ ok: true, id, duplicate: !inserted.meta?.changes, notified: notification.sent });
}

async function handleImpactMedia(request, env) {
  if (!authorize(request, env, true)) return json({ error: "unauthorized" }, 401);

  const payload = await request.json();
  const id = String(payload.id || "").slice(0, 128);
  const deviceId = authenticatedDeviceId(request);
  const capturedAt = String(payload.capturedAt || nowIso()).slice(0, 64);
  const captureStatus = ["complete", "partial", "failed"].includes(payload.captureStatus)
    ? payload.captureStatus : "failed";
  const captureAttempts = Math.max(0, Math.min(20, Number.parseInt(payload.captureAttempts || "0", 10) || 0));
  if (!id || !deviceId) return json({ error: "invalid_impact_media" }, 400);

  const impact = await env.DB.prepare(`
    SELECT device_id, capture_status, wide_snapshot_id, driver_snapshot_id
    FROM impact_events WHERE id = ?
  `).bind(id).first();
  if (!impact || impact.device_id !== deviceId) return json({ error: "impact_not_found" }, 404);
  if (impact.capture_status === "complete" && impact.wide_snapshot_id && impact.driver_snapshot_id) {
    return json({
      ok: true,
      id,
      duplicate: true,
      captureStatus: "complete",
      wideSnapshotId: impact.wide_snapshot_id,
      driverSnapshotId: impact.driver_snapshot_id,
    });
  }

  let wideSnapshotId = impact.wide_snapshot_id || null;
  let driverSnapshotId = impact.driver_snapshot_id || null;
  if (!wideSnapshotId && payload.wideJpegBase64) {
    wideSnapshotId = (await saveSnapshotImage(
      env, deviceId, "wide", capturedAt, payload.wideJpegBase64,
    ))?.id || null;
  }
  if (!driverSnapshotId && payload.driverJpegBase64) {
    driverSnapshotId = (await saveSnapshotImage(
      env, deviceId, "driver", capturedAt, payload.driverJpegBase64,
    ))?.id || null;
  }

  const resolvedStatus = wideSnapshotId && driverSnapshotId
    ? "complete"
    : (wideSnapshotId || driverSnapshotId ? "partial" : captureStatus);
  await env.DB.prepare(`
    UPDATE impact_events SET
      capture_status = ?, captured_at = ?, capture_attempts = ?,
      wide_snapshot_id = ?, driver_snapshot_id = ?
    WHERE id = ? AND device_id = ?
  `).bind(
    resolvedStatus,
    capturedAt,
    captureAttempts,
    wideSnapshotId,
    driverSnapshotId,
    id,
    deviceId,
  ).run();

  return json({
    ok: true,
    id,
    captureStatus: resolvedStatus,
    wideSnapshotId,
    driverSnapshotId,
  });
}

async function handleVehicleEvent(request, env) {
  if (!authorize(request, env, true)) return json({ error: "unauthorized" }, 401);

  const payload = await request.json();
  const eventType = String(payload.eventType || "").slice(0, 64);
  const doorLockEvent = eventType === "door_lock";
  const parkingUnlockedEvent = eventType === "parking_unlocked";
  if ((!doorLockEvent && !parkingUnlockedEvent)
      || (doorLockEvent && typeof payload.locked !== "boolean")) {
    return json({ error: "invalid_vehicle_event" }, 400);
  }

  const id = String(payload.id || crypto.randomUUID()).slice(0, 128);
  const deviceId = authenticatedDeviceId(request);
  const occurredAt = validIsoOrNow(payload.occurredAt);
  const receivedAt = nowIso();
  const notificationEligible = vehicleEventNotificationEligible(occurredAt);
  const locked = doorLockEvent ? Boolean(payload.locked) : null;
  const delaySeconds = parkingUnlockedEvent
    ? Math.max(0, Math.min(3600, Number.parseInt(payload.delaySeconds || "180", 10) || 180))
    : null;
  const state = parkingUnlockedEvent ? await env.DB.prepare(
    "SELECT latitude, longitude, updated_at FROM latest_state WHERE device_id = ?",
  ).bind(deviceId).first() : null;
  const latitude = parkingUnlockedEvent
    ? (nullableNumber(payload.latitude) ?? nullableNumber(state?.latitude)) : null;
  const longitude = parkingUnlockedEvent
    ? (nullableNumber(payload.longitude) ?? nullableNumber(state?.longitude)) : null;
  const inserted = await env.DB.prepare(`
    INSERT OR IGNORE INTO vehicle_events (
      id, device_id, event_type, occurred_at, received_at, locked, notified_count, raw_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id,
    deviceId,
    eventType,
    occurredAt,
    receivedAt,
    locked == null ? null : toInt(locked),
    notificationEligible ? 0 : -3,
    JSON.stringify(payload),
  ).run();

  if (!notificationEligible) {
    if (!inserted.meta?.changes) {
      await env.DB.prepare(`
        UPDATE vehicle_events SET notified_count = -3
        WHERE id = ? AND notified_count = 0
      `).bind(id).run();
    }
    return json({ ok: true, id, stale: true, notified: 0 });
  }

  if (!inserted.meta?.changes) {
    const existing = await env.DB.prepare("SELECT notified_count FROM vehicle_events WHERE id = ?")
      .bind(id).first();
    if (Number(existing?.notified_count || 0) !== 0) {
      return json({ ok: true, id, duplicate: true, notified: existing.notified_count });
    }
  }

  // Claim delivery before calling FCM. A timed-out FCM request may still reach
  // the phone, so retrying the same event would produce an alert storm.
  const claimed = await env.DB.prepare(`
    UPDATE vehicle_events SET notified_count = -1
    WHERE id = ? AND notified_count = 0
  `).bind(id).run();
  if (!claimed.meta?.changes) {
    const existing = await env.DB.prepare("SELECT notified_count FROM vehicle_events WHERE id = ?")
      .bind(id).first();
    return json({ ok: true, id, duplicate: true, notified: existing?.notified_count || 0 });
  }

  const event = {
    id,
    deviceId,
    eventType,
    occurredAt,
    locked,
    delaySeconds,
    latitude,
    longitude,
    locationUpdatedAt: state?.updated_at || null,
    test: Boolean(payload.test),
  };
  const notificationData = parkingUnlockedEvent ? parkingUnlockedData(event) : doorLockData(event);
  const notification = await sendDataNotifications(env, deviceId, notificationData);
  if (notification.failed > 0 && notification.sent === 0) {
    await env.DB.prepare("UPDATE vehicle_events SET notified_count = -2 WHERE id = ?")
      .bind(id).run();
    return json({ ok: true, id, notificationAccepted: false, notified: 0 });
  }
  await env.DB.prepare("UPDATE vehicle_events SET notified_count = ? WHERE id = ?")
    .bind(notification.sent, id).run();
  return json({ ok: true, id, duplicate: !inserted.meta?.changes, notified: notification.sent });
}

async function handlePushRegistration(request, env) {
  if (!authorizePushRegistration(request, env)) return json({ error: "unauthorized" }, 401);

  const payload = await request.json();
  const token = String(payload.fcmToken || "").trim();
  const deviceId = authenticatedDeviceId(request);
  if (token.length < 32 || token.length > 4096) return json({ error: "invalid_fcm_token" }, 400);

  if (payload.action === "unregister") {
    await env.DB.prepare("DELETE FROM push_subscriptions WHERE token = ?").bind(token).run();
    return json({ ok: true, registered: false });
  }

  const now = nowIso();
  await env.DB.prepare(`
    INSERT INTO push_subscriptions (token, device_id, platform, app_version, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(token) DO UPDATE SET
      device_id = excluded.device_id,
      platform = excluded.platform,
      app_version = excluded.app_version,
      updated_at = excluded.updated_at
  `).bind(token, deviceId, String(payload.platform || "android").slice(0, 32),
    String(payload.appVersion || "").slice(0, 32), now, now).run();
  return json({ ok: true, registered: true, deviceId });
}

async function handlePushTest(request, env) {
  if (!authorize(request, env, true)) return json({ error: "unauthorized" }, 401);
  const payload = await request.json().catch(() => ({}));
  const event = {
    id: `test-${crypto.randomUUID()}`,
    deviceId: authenticatedDeviceId(request),
    detectedAt: nowIso(),
    severity: "light",
    peakDynamicG: 0.62,
    peakTotalG: 1.18,
    peakJerkGPerSec: 6.4,
    peakGyroRadPerSec: 0.21,
    test: true,
  };
  const notification = await sendImpactNotifications(env, event);
  return json({ ok: true, notified: notification.sent, subscriptions: notification.subscriptions });
}

async function handleImpacts(request, env) {
  if (!authorize(request, env, false)) return json({ error: "unauthorized" }, 401);
  const url = new URL(request.url);
  const deviceId = authenticatedDeviceId(request);
  const limit = Math.max(1, Math.min(100, Number.parseInt(url.searchParams.get("limit") || "25", 10)));
  try {
    return historyJson({ impacts: await fetchServerImpactList(env, limit, deviceId) }, "server");
  } catch (error) {
    console.warn("Wayon server impact list unavailable; using D1", error?.message || error);
  }

  const impacts = await env.DB.prepare(`
    SELECT id, device_id, detected_at, received_at, severity, peak_dynamic_g,
           peak_total_g, peak_jerk_g_per_s, peak_gyro_rad_per_s, duration_ms,
           sample_count, sensor_clipped, latitude, longitude, capture_status,
           captured_at, capture_attempts, wide_snapshot_id, driver_snapshot_id,
           notified_count,
           (
             SELECT locked FROM vehicle_events
             WHERE device_id = impact_events.device_id
               AND event_type = 'door_lock'
               AND locked IS NOT NULL
               AND occurred_at <= impact_events.detected_at
             ORDER BY occurred_at DESC LIMIT 1
           ) AS vehicle_locked
    FROM impact_events WHERE device_id = ? ORDER BY detected_at DESC LIMIT ?
  `).bind(deviceId, limit).all();
  return historyJson({ impacts: impacts.results || [] }, "d1");
}

async function handleMobileImpacts(request, env) {
  if (!authorizePushRegistration(request, env)) return json({ error: "unauthorized" }, 401);
  const url = new URL(request.url);
  const deviceId = String(url.searchParams.get("deviceId") || "").slice(0, 128);
  const limit = Math.max(1, Math.min(50, Number.parseInt(url.searchParams.get("limit") || "25", 10)));
  if (!deviceId) return json({ error: "missing_device_id" }, 400);

  const impacts = await env.DB.prepare(`
    SELECT id, detected_at, received_at, severity, peak_dynamic_g,
           peak_total_g, peak_jerk_g_per_s, peak_gyro_rad_per_s, duration_ms,
           sample_count, sensor_clipped, latitude, longitude, capture_status,
           captured_at, wide_snapshot_id, driver_snapshot_id
    FROM impact_events
    WHERE device_id = ?
    ORDER BY detected_at DESC LIMIT ?
  `).bind(deviceId, limit).all();
  return json({ deviceId, impacts: impacts.results || [] });
}

async function handleMobileImpactImage(request, env) {
  if (!authorizePushRegistration(request, env)) return json({ error: "unauthorized" }, 401);
  const url = new URL(request.url);
  const deviceId = String(url.searchParams.get("deviceId") || "").slice(0, 128);
  const snapshotId = String(url.searchParams.get("snapshotId") || "").slice(0, 128);
  if (!deviceId || !snapshotId) return json({ error: "missing_image_identity" }, 400);

  const snapshot = await env.DB.prepare(`
    SELECT kv_key FROM snapshots WHERE id = ? AND device_id = ?
  `).bind(snapshotId, deviceId).first();
  if (!snapshot) return json({ error: "not_found" }, 404);
  const image = await env.SNAPSHOTS.get(snapshot.kv_key, "arrayBuffer");
  if (!image) return json({ error: "not_found" }, 404);

  return new Response(image, {
    headers: {
      ...CORS_HEADERS,
      "content-type": "image/jpeg",
      "cache-control": "private, max-age=300",
    },
  });
}

async function saveSnapshotImage(env, deviceId, camera, capturedAt, jpegBase64) {
  if (!jpegBase64) return null;

  const id = crypto.randomUUID();
  const bytes = base64ToBytes(jpegBase64);
  const safeCapturedAt = capturedAt.replace(/[:.]/g, "-");
  const key = `snapshots/${deviceId}/${camera}/${safeCapturedAt}-${id}.jpg`;
  const createdAt = nowIso();

  await env.SNAPSHOTS.put(key, bytes, {
    metadata: { deviceId, camera, capturedAt },
  });

  await env.DB.prepare(`
    INSERT INTO snapshots (id, device_id, camera, captured_at, kv_key, size_bytes, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).bind(id, deviceId, camera, capturedAt, key, bytes.length, createdAt).run();

  const column = camera === "driver" ? "last_snapshot_driver_id" : "last_snapshot_wide_id";
  await env.DB.prepare(`UPDATE latest_state SET ${column} = ? WHERE device_id = ?`)
    .bind(id, deviceId)
    .run();

  return { id, camera, key, sizeBytes: bytes.length };
}

async function handleSnapshot(request, env) {
  if (!authorize(request, env, true)) {
    return json({ error: "unauthorized" }, 401);
  }

  const payload = await request.json();
  const deviceId = authenticatedDeviceId(request);
  const capturedAt = payload.capturedAt || nowIso();

  const saved = [];
  const driver = await saveSnapshotImage(env, deviceId, "driver", capturedAt, payload.driverJpegBase64);
  const wide = await saveSnapshotImage(env, deviceId, "wide", capturedAt, payload.wideJpegBase64);
  if (driver) saved.push(driver);
  if (wide) saved.push(wide);

  return json({ ok: true, snapshots: saved });
}

const MAX_LIVE_CAPTURE_BYTES = 48 * 1024 * 1024;
const LIVE_CAPTURE_PART_BYTES = 20 * 1024 * 1024;
const LIVE_CAPTURE_UPLOAD_PART_BYTES = 2 * 1024 * 1024;
const MAX_LIVE_CAPTURE_UPLOAD_PARTS = 32;

async function putLiveCaptureBytes(env, key, bytes, metadata) {
  if (bytes.byteLength <= LIVE_CAPTURE_PART_BYTES) {
    metadata.multipart = false;
    await env.SNAPSHOTS.put(key, bytes, { metadata });
    return;
  }

  const partKeys = [];
  for (let offset = 0, index = 0; offset < bytes.byteLength; offset += LIVE_CAPTURE_PART_BYTES, index += 1) {
    const partKey = `${key}.part${String(index).padStart(3, "0")}`;
    await env.SNAPSHOTS.put(partKey, bytes.slice(offset, offset + LIVE_CAPTURE_PART_BYTES));
    partKeys.push(partKey);
  }
  metadata.multipart = true;
  metadata.partCount = partKeys.length;
  await env.SNAPSHOTS.put(key, JSON.stringify({
    schema: "wayon-live-capture-parts-v1",
    sizeBytes: bytes.byteLength,
    partKeys,
  }), { metadata: { ...metadata, multipart: true, partCount: partKeys.length } });
}

async function getLiveCaptureBytes(env, capture) {
  let metadata = {};
  try {
    metadata = JSON.parse(capture.metadata_json || "{}");
  } catch (_) {}
  if (!metadata.multipart) {
    return env.SNAPSHOTS.get(capture.kv_key, "arrayBuffer");
  }

  const manifest = await env.SNAPSHOTS.get(capture.kv_key, "json");
  if (manifest?.schema !== "wayon-live-capture-parts-v1" || !Array.isArray(manifest.partKeys)) return null;
  const chunks = await Promise.all(manifest.partKeys.map((key) => env.SNAPSHOTS.get(key, "arrayBuffer")));
  if (chunks.some((chunk) => !chunk)) return null;
  const joined = new Uint8Array(Number(capture.size_bytes));
  let offset = 0;
  for (const chunk of chunks) {
    joined.set(new Uint8Array(chunk), offset);
    offset += chunk.byteLength;
  }
  return offset === joined.byteLength ? joined.buffer : null;
}

function safeCaptureHeader(request, name, fallback, maxLength = 128) {
  return String(request.headers.get(name) || fallback || "").trim().slice(0, maxLength);
}

function safeCapturePathPart(value) {
  return String(value || "unknown").replace(/[^0-9A-Za-z_-]/g, "-").slice(0, 128);
}

function liveCaptureUploadPartKey(deviceId, uploadId, index) {
  return `live-capture-parts/${safeCapturePathPart(deviceId)}/${uploadId}/part${String(index).padStart(3, "0")}`;
}

async function handleLiveCapturePartUpload(request, env) {
  if (!authorize(request, env, true)) return json({ error: "unauthorized" }, 401);

  const declaredSize = Number(request.headers.get("content-length") || 0);
  if (declaredSize > LIVE_CAPTURE_UPLOAD_PART_BYTES) return json({ error: "part_too_large" }, 413);
  const deviceId = safeCaptureHeader(request, "x-wayon-device-id", "unknown");
  const uploadId = safeCaptureHeader(request, "x-wayon-upload-id", "", 64);
  const partIndex = Number.parseInt(request.headers.get("x-wayon-part-index") || "-1", 10);
  const partCount = Number.parseInt(request.headers.get("x-wayon-part-count") || "0", 10);
  const totalSize = Number.parseInt(request.headers.get("x-wayon-total-size") || "0", 10);
  if (!/^[0-9a-f]{32}$/.test(uploadId) || partIndex < 0 || partIndex >= partCount ||
      partCount < 1 || partCount > MAX_LIVE_CAPTURE_UPLOAD_PARTS ||
      totalSize < 1 || totalSize > MAX_LIVE_CAPTURE_BYTES) {
    return json({ error: "invalid_capture_part" }, 400);
  }

  const bytes = await request.arrayBuffer();
  if (!bytes.byteLength || bytes.byteLength > LIVE_CAPTURE_UPLOAD_PART_BYTES) {
    return json({ error: "invalid_part_size" }, bytes.byteLength ? 413 : 400);
  }
  const key = liveCaptureUploadPartKey(deviceId, uploadId, partIndex);
  await env.SNAPSHOTS.put(key, bytes, {
    metadata: { schema: "wayon-live-upload-part-v1", uploadId, partIndex, partCount, totalSize },
  });
  return json({ ok: true, uploadId, partIndex, sizeBytes: bytes.byteLength });
}

async function handleLiveCaptureCommit(request, env) {
  if (!authorize(request, env, true)) return json({ error: "unauthorized" }, 401);
  const payload = await request.json();
  const deviceId = authenticatedDeviceId(request);
  const uploadId = String(payload.uploadId || "").slice(0, 64);
  const partCount = Number.parseInt(payload.partCount, 10);
  const totalSize = Number.parseInt(payload.sizeBytes, 10);
  const capturedAt = String(payload.capturedAt || nowIso()).slice(0, 64);
  const durationS = Number(payload.durationS);
  if (!/^[0-9a-f]{32}$/.test(uploadId) || partCount < 1 ||
      partCount > MAX_LIVE_CAPTURE_UPLOAD_PARTS || totalSize < 1 ||
      totalSize > MAX_LIVE_CAPTURE_BYTES || !Number.isFinite(durationS) || durationS <= 0) {
    return json({ error: "invalid_capture_commit" }, 400);
  }

  const existing = await env.DB.prepare(`
    SELECT id, kind, captured_at, duration_s, size_bytes FROM live_captures WHERE id = ?
  `).bind(uploadId).first();
  if (existing) {
    return json({
      ok: true,
      id: existing.id,
      kind: existing.kind,
      capturedAt: existing.captured_at,
      durationS: existing.duration_s,
      sizeBytes: existing.size_bytes,
    });
  }

  const partKeys = [];
  let verifiedSize = 0;
  for (let index = 0; index < partCount; index += 1) {
    const partKey = liveCaptureUploadPartKey(deviceId, uploadId, index);
    const part = await env.SNAPSHOTS.get(partKey, "arrayBuffer");
    if (!part) return json({ error: "missing_capture_part", partIndex: index }, 409);
    verifiedSize += part.byteLength;
    partKeys.push(partKey);
  }
  if (verifiedSize !== totalSize) return json({ error: "capture_size_mismatch", verifiedSize }, 409);

  const contentType = "application/zip";
  const cameraLayout = String(payload.cameraLayout || "dual_h264_360").slice(0, 64);
  const safeCapturedAt = capturedAt.replace(/[^0-9A-Za-z_-]/g, "-");
  const key = `live-captures/${safeCapturePathPart(deviceId)}/${safeCapturedAt}-${uploadId}.zip`;
  const createdAt = nowIso();
  const metadata = {
    schema: "wayon-live-capture-v1",
    uploadSchema: "wayon-live-chunk-upload-v1",
    deviceId,
    kind: "clip",
    capturedAt,
    durationS,
    cameraLayout,
    contentType,
    multipart: true,
    partCount,
  };
  await env.SNAPSHOTS.put(key, JSON.stringify({
    schema: "wayon-live-capture-parts-v1",
    sizeBytes: totalSize,
    partKeys,
  }), { metadata });
  await env.DB.prepare(`
    INSERT INTO live_captures (
      id, device_id, kind, captured_at, duration_s, content_type,
      camera_layout, kv_key, size_bytes, metadata_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    uploadId,
    deviceId,
    "clip",
    capturedAt,
    durationS,
    contentType,
    cameraLayout,
    key,
    totalSize,
    JSON.stringify(metadata),
    createdAt,
  ).run();
  return json({ ok: true, id: uploadId, kind: "clip", capturedAt, durationS, sizeBytes: totalSize });
}

async function handleLiveCaptureUpload(request, env) {
  if (!authorize(request, env, true)) return json({ error: "unauthorized" }, 401);

  const declaredSize = Number(request.headers.get("content-length") || 0);
  if (declaredSize > MAX_LIVE_CAPTURE_BYTES) return json({ error: "capture_too_large" }, 413);

  const deviceId = safeCaptureHeader(request, "x-wayon-device-id", "unknown");
  const kind = safeCaptureHeader(request, "x-wayon-capture-kind", "photo", 16);
  const capturedAt = safeCaptureHeader(request, "x-wayon-captured-at", nowIso(), 64);
  const cameraLayout = safeCaptureHeader(request, "x-wayon-camera-layout", "stitched_360", 64);
  const requestedDuration = Number(request.headers.get("x-wayon-duration-s") || 0);
  const durationS = Number.isFinite(requestedDuration) && requestedDuration > 0 ? requestedDuration : null;
  const contentType = String(request.headers.get("content-type") || "application/octet-stream")
    .split(";", 1)[0].trim().toLowerCase();
  const allowedType = kind === "photo" ? contentType === "image/jpeg" : contentType === "application/zip";
  if (!deviceId || !["photo", "clip"].includes(kind) || !allowedType) {
    return json({ error: "invalid_live_capture" }, 400);
  }

  const bytes = await request.arrayBuffer();
  if (!bytes.byteLength || bytes.byteLength > MAX_LIVE_CAPTURE_BYTES) {
    return json({ error: "invalid_capture_size" }, bytes.byteLength ? 413 : 400);
  }

  const id = crypto.randomUUID();
  const extension = kind === "photo" ? "jpg" : "zip";
  const safeCapturedAt = capturedAt.replace(/[^0-9A-Za-z_-]/g, "-");
  const key = `live-captures/${deviceId}/${safeCapturedAt}-${id}.${extension}`;
  const createdAt = nowIso();
  const metadata = {
    schema: "wayon-live-capture-v1",
    deviceId,
    kind,
    capturedAt,
    durationS,
    cameraLayout,
    contentType,
  };

  await putLiveCaptureBytes(env, key, bytes, metadata);
  await env.DB.prepare(`
    INSERT INTO live_captures (
      id, device_id, kind, captured_at, duration_s, content_type,
      camera_layout, kv_key, size_bytes, metadata_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id,
    deviceId,
    kind,
    capturedAt,
    durationS,
    contentType,
    cameraLayout,
    key,
    bytes.byteLength,
    JSON.stringify(metadata),
    createdAt,
  ).run();

  return json({ ok: true, id, kind, capturedAt, durationS, sizeBytes: bytes.byteLength });
}

async function handleLiveCaptures(request, env) {
  if (!authorize(request, env, false)) return json({ error: "unauthorized" }, 401);
  const url = new URL(request.url);
  const deviceId = authenticatedDeviceId(request);
  const limit = Math.max(1, Math.min(100, Number.parseInt(url.searchParams.get("limit") || "25", 10)));
  const captures = await env.DB.prepare(`
    SELECT id, device_id, kind, captured_at, duration_s, content_type,
           camera_layout, size_bytes, created_at
    FROM live_captures WHERE device_id = ? ORDER BY captured_at DESC LIMIT ?
  `).bind(deviceId, limit).all();
  return json({ captures: captures.results || [] });
}

async function handleLiveCapture(request, env) {
  if (!authorize(request, env, false)) return json({ error: "unauthorized" }, 401);
  const id = String(new URL(request.url).searchParams.get("id") || "").slice(0, 128);
  const deviceId = authenticatedDeviceId(request);
  if (!id) return json({ error: "missing_capture_id" }, 400);

  const capture = await env.DB.prepare(`
    SELECT kind, captured_at, content_type, kv_key, size_bytes, metadata_json
    FROM live_captures WHERE id = ? AND device_id = ?
  `).bind(id, deviceId).first();
  if (!capture) return json({ error: "not_found" }, 404);
  const bytes = await getLiveCaptureBytes(env, capture);
  if (!bytes) return json({ error: "not_found" }, 404);

  const extension = capture.kind === "photo" ? "jpg" : "zip";
  return new Response(bytes, {
    headers: {
      ...CORS_HEADERS,
      "content-type": capture.content_type,
      "content-disposition": `attachment; filename="wayon-${capture.kind}-${capture.captured_at.replace(/[^0-9A-Za-z_-]/g, "-")}.${extension}"`,
      "cache-control": "private, max-age=300",
    },
  });
}

async function handleTrip(request, env) {
  if (!authorize(request, env, true)) {
    return json({ error: "unauthorized" }, 401);
  }

  const payload = await request.json();
  const route = Array.isArray(payload.route) ? payload.route : [];
  const start = route[0] || {};
  const end = route[route.length - 1] || {};
  const id = String(payload.id || crypto.randomUUID());
  const deviceId = authenticatedDeviceId(request);
  const analysis = normalizeTripAnalysis(payload);

  await env.DB.prepare(`
    INSERT OR REPLACE INTO trips (
      id, device_id, started_at, ended_at, duration_s, distance_m, start_lat,
      start_lon, end_lat, end_lon, route_point_count, route_json, report_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id,
    deviceId,
    payload.startedAt || nowIso(),
    payload.endedAt || nowIso(),
    payload.durationS ?? null,
    nullableNumber(payload.distanceM),
    nullableNumber(payload.startLat ?? start.latitude),
    nullableNumber(payload.startLon ?? start.longitude),
    nullableNumber(payload.endLat ?? end.latitude),
    nullableNumber(payload.endLon ?? end.longitude),
    route.length,
    JSON.stringify(route),
    JSON.stringify(analysis),
    nowIso(),
  ).run();

  return json({ ok: true, id });
}

async function handleState(request, env) {
  if (!authorize(request, env, false)) {
    return json({ error: "unauthorized" }, 401);
  }

  const deviceId = authenticatedDeviceId(request);
  const [state, snapshots, vehicleStatus, vehicleLock, healthTimeline] = await Promise.all([
    env.DB.prepare(`
      SELECT * FROM latest_state WHERE device_id = ? LIMIT 1
    `).bind(deviceId).first(),
    env.DB.prepare(`
      SELECT s.id, s.device_id, s.camera, s.captured_at, s.kv_key, s.size_bytes,
             COALESCE(iw.id, idr.id) AS impact_id,
             COALESCE(iw.severity, idr.severity) AS impact_severity,
             COALESCE(iw.peak_dynamic_g, idr.peak_dynamic_g) AS impact_peak_dynamic_g,
             COALESCE(iw.peak_total_g, idr.peak_total_g) AS impact_peak_total_g,
             COALESCE(iw.detected_at, idr.detected_at) AS impact_detected_at
      FROM snapshots s
      LEFT JOIN impact_events iw ON s.id = iw.wide_snapshot_id
      LEFT JOIN impact_events idr ON s.id = idr.driver_snapshot_id
      WHERE s.device_id = ? ORDER BY s.captured_at DESC LIMIT 12
    `).bind(deviceId).all(),
    fetchMergedVehicleStatus(env, deviceId),
    latestVehicleLock(env, deviceId),
    latestHealthTimeline(env, deviceId),
  ]);

  return json({ state, snapshots: snapshots.results || [], vehicleStatus, vehicleLock, healthTimeline });
}

function ambientByte(value, maximum, field) {
  const number = Number(value);
  if (!Number.isInteger(number) || number < 0 || number > maximum) {
    throw new Error(`invalid_${field}`);
  }
  return number;
}

function normalizeAmbientZone(zone, name) {
  if (!zone || typeof zone !== "object" || !Array.isArray(zone.rgb) || zone.rgb.length !== 3) {
    throw new Error(`invalid_${name}`);
  }
  return {
    enabled: zone.enabled !== false,
    rgb: zone.rgb.map((value, index) => ambientByte(value, 255, `${name}_rgb_${index}`)),
    brightness: ambientByte(zone.brightness, 100, `${name}_brightness`),
  };
}

function ambientNumber(value, minimum, maximum, field) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < minimum || number > maximum) {
    throw new Error(`invalid_${field}`);
  }
  return Math.round(number);
}

function normalizeAmbientProfileZone(zone, name, options = {}) {
  const normalized = normalizeAmbientZone(zone, name);
  if (options.allowAutomaticBrightness) {
    normalized.automaticBrightness = zone.automaticBrightness !== false;
  }
  return normalized;
}

function normalizeAmbientProfile(profile) {
  if (!profile || typeof profile !== "object") throw new Error("invalid_profile");
  const driving = profile.driving || {};
  const onroadDoor = profile.onroadDoor || {};
  const offroadDoor = profile.offroadDoor || {};
  const exitCourtesy = profile.exitCourtesy || {};
  const overspeed = profile.overspeed || {};
  const timing = profile.timing || {};
  const dataWatchdog = profile.dataWatchdog || {};
  return {
    enabled: profile.enabled !== false,
    driving: {
      zone1: normalizeAmbientProfileZone(driving.zone1, "driving_zone1", { allowAutomaticBrightness: true }),
      zone2: normalizeAmbientProfileZone(driving.zone2, "driving_zone2"),
    },
    onroadDoor: {
      enabled: onroadDoor.enabled !== false,
      zone1: normalizeAmbientProfileZone(onroadDoor.zone1 || driving.zone1, "onroad_door_zone1"),
      zone2: normalizeAmbientProfileZone(onroadDoor.zone2, "onroad_door_zone2"),
    },
    offroadDoor: {
      enabled: offroadDoor.enabled !== false,
      zone1: normalizeAmbientProfileZone(offroadDoor.zone1, "offroad_door_zone1"),
      zone2: normalizeAmbientProfileZone(offroadDoor.zone2, "offroad_door_zone2"),
    },
    exitCourtesy: {
      enabled: exitCourtesy.enabled !== false,
      zone2: normalizeAmbientProfileZone(exitCourtesy.zone2, "exit_courtesy_zone2"),
      durationSeconds: ambientNumber(exitCourtesy.durationSeconds ?? 120, 0, 600, "exit_courtesy_duration_seconds"),
    },
    overspeed: {
      enabled: overspeed.enabled !== false,
      zone1: normalizeAmbientProfileZone(overspeed.zone1, "overspeed_zone1"),
      brightnessCap: ambientNumber(overspeed.brightnessCap ?? 50, 1, 100, "overspeed_brightness_cap"),
    },
    reverseOff: { enabled: profile.reverseOff?.enabled !== false },
    dataWatchdog: {
      enabled: dataWatchdog.enabled !== false,
      timeoutSeconds: ambientNumber(dataWatchdog.timeoutSeconds ?? 20, 5, 120, "data_watchdog_timeout_seconds"),
    },
    timing: {
      fadeMilliseconds: ambientNumber(timing.fadeMilliseconds ?? 1000, 200, 5000, "fade_milliseconds"),
      doorCloseDelaySeconds: ambientNumber(timing.doorCloseDelaySeconds ?? 20, 0, 120, "door_close_delay_seconds"),
      doorMaxOnMinutes: ambientNumber(timing.doorMaxOnMinutes ?? 20, 1, 60, "door_max_on_minutes"),
      transitionUpdatesPerSecond: ambientNumber(timing.transitionUpdatesPerSecond ?? 30, 5, 40, "transition_updates_per_second"),
    },
  };
}

export function normalizeAmbientCommand(payload, now = new Date()) {
  const mode = String(payload?.mode || "manual").toLowerCase();
  if (mode === "auto") {
    return {
      schema: "wayon.ambient.command.v1",
      mode: "auto",
      durationSeconds: 0,
      requestedAt: now.toISOString(),
    };
  }
  if (mode === "profile") {
    return {
      schema: "wayon.ambient.command.v1",
      mode: "profile",
      profile: normalizeAmbientProfile(payload.profile),
      durationSeconds: 0,
      requestedAt: now.toISOString(),
    };
  }
  if (mode !== "manual") throw new Error("invalid_mode");
  const durationSeconds = ambientByte(payload.durationSeconds ?? 900, 1200, "duration_seconds");
  if (durationSeconds < 30) throw new Error("invalid_duration_seconds");
  return {
    schema: "wayon.ambient.command.v1",
    mode: "manual",
    zone1: normalizeAmbientZone(payload.zone1, "zone1"),
    zone2: normalizeAmbientZone(payload.zone2, "zone2"),
    durationSeconds,
    requestedAt: now.toISOString(),
  };
}

async function handleAmbientCommandCreate(request, env) {
  if (!authorize(request, env, false)) return json({ error: "unauthorized" }, 401);
  const deviceId = authenticatedDeviceId(request);
  if (!deviceId) return json({ error: "device_not_found" }, 404);
  const input = await request.json().catch(() => ({}));
  let command;
  try {
    command = normalizeAmbientCommand(input);
  } catch (error) {
    return json({ error: String(error?.message || "invalid_ambient_command") }, 400);
  }
  const id = crypto.randomUUID();
  const createdAt = command.requestedAt;
  const ttlSeconds = command.mode === "manual" ? command.durationSeconds : 60;
  const expiresAt = new Date(Date.parse(createdAt) + ttlSeconds * 1000).toISOString();
  await env.DB.batch([
    env.DB.prepare(`
      UPDATE ambient_commands SET status = 'superseded'
      WHERE device_id = ? AND status IN ('pending', 'delivered')
    `).bind(deviceId),
    env.DB.prepare(`
      INSERT INTO ambient_commands (
        id, device_id, created_at, expires_at, status, payload_json
      ) VALUES (?, ?, ?, ?, 'pending', ?)
    `).bind(id, deviceId, createdAt, expiresAt, JSON.stringify(command)),
  ]);
  return json({ ok: true, id, deviceId, status: "pending", expiresAt, command });
}

async function handleAmbientCommandPoll(request, env) {
  if (!authorize(request, env, true)) return json({ error: "unauthorized" }, 401);
  const deviceId = authenticatedDeviceId(request);
  if (!deviceId) return json({ command: null });
  const now = nowIso();
  await env.DB.prepare(`
    UPDATE ambient_commands SET status = 'expired'
    WHERE device_id = ? AND status IN ('pending', 'delivered') AND expires_at <= ?
  `).bind(deviceId, now).run();
  const row = await env.DB.prepare(`
    SELECT id, device_id, created_at, expires_at, status, payload_json
    FROM ambient_commands
    WHERE device_id = ? AND status IN ('pending', 'delivered') AND expires_at > ?
    ORDER BY created_at DESC LIMIT 1
  `).bind(deviceId, now).first();
  if (!row) return json({ command: null });
  return json({ command: {
    id: row.id,
    deviceId: row.device_id,
    createdAt: row.created_at,
    expiresAt: row.expires_at,
    status: row.status,
    payload: JSON.parse(row.payload_json),
  } });
}

async function handleAmbientCommandAck(request, env) {
  if (!authorize(request, env, true)) return json({ error: "unauthorized" }, 401);
  const deviceId = authenticatedDeviceId(request);
  const payload = await request.json().catch(() => ({}));
  const id = String(payload.id || "").trim().slice(0, 128);
  if (!id || !deviceId) return json({ error: "invalid_ack" }, 400);
  const acknowledgedAt = nowIso();
  const status = payload.applied === false ? "failed" : "acknowledged";
  const result = await env.DB.prepare(`
    UPDATE ambient_commands SET status = ?, acknowledged_at = ?, ack_json = ?
    WHERE id = ? AND device_id = ?
  `).bind(status, acknowledgedAt, JSON.stringify(payload), id, deviceId).run();
  return json({ ok: true, id, status, acknowledgedAt, changes: result.meta?.changes || 0 });
}

async function handleAmbientCommandStatus(request, env) {
  if (!authorize(request, env, false)) return json({ error: "unauthorized" }, 401);
  const deviceId = authenticatedDeviceId(request);
  if (!deviceId) return json({ command: null });
  const row = await env.DB.prepare(`
    SELECT id, device_id, created_at, expires_at, status, payload_json,
           acknowledged_at, ack_json
    FROM ambient_commands WHERE device_id = ? ORDER BY created_at DESC LIMIT 1
  `).bind(deviceId).first();
  if (!row) return json({ command: null });
  return json({ command: {
    id: row.id,
    deviceId: row.device_id,
    createdAt: row.created_at,
    expiresAt: row.expires_at,
    status: row.status,
    acknowledgedAt: row.acknowledged_at,
    payload: JSON.parse(row.payload_json),
    ack: row.ack_json ? JSON.parse(row.ack_json) : null,
  } });
}

async function latestVehicleLock(env, deviceId) {
  const event = await env.DB.prepare(`
    SELECT locked, occurred_at, received_at
    FROM vehicle_events
    WHERE device_id = ? AND event_type = 'door_lock' AND locked IS NOT NULL
    ORDER BY occurred_at DESC LIMIT 1
  `).bind(deviceId).first();

  return event ? {
    known: true,
    locked: Boolean(event.locked),
    occurredAt: event.occurred_at,
    receivedAt: event.received_at,
  } : {
    known: false,
    locked: null,
    occurredAt: null,
    receivedAt: null,
  };
}

function parseTripRoute(trip) {
  const { route_json: routeJson, report_json: reportJson, health_json: healthJson, ...rest } = trip;
  const parsed = tripWithAnalysis({
    ...rest,
    route: JSON.parse(routeJson || "[]"),
  }, parseJsonObject(reportJson));
  parsed.health = parseJsonObject(healthJson);
  return parsed;
}

function maxRoutePointSpeedMps(route) {
  let maxSpeed = null;
  for (const point of route) {
    const speed = Number(point?.speedMps ?? point?.speed_mps ?? point?.speed);
    if (Number.isFinite(speed)) {
      maxSpeed = Math.max(maxSpeed ?? speed, speed);
    }
  }
  return maxSpeed;
}

function maxRouteSpeedMps(routeJson) {
  try {
    const route = JSON.parse(routeJson || "[]");
    return maxRoutePointSpeedMps(Array.isArray(route) ? route : []);
  } catch {
    return null;
  }
}

function parseTripSummary(trip) {
  const { route_json: routeJson, report_json: reportJson, health_json: healthJson, ...rest } = trip;
  const parsed = tripWithAnalysis({
    ...rest,
    max_speed_mps: maxRouteSpeedMps(routeJson),
  }, parseJsonObject(reportJson));
  parsed.health = parseJsonObject(healthJson);
  return parsed;
}

function parseServerTripSummary(trip) {
  const { route, ...summary } = trip || {};
  const suppliedMaxSpeed = summary.max_speed_mps == null
    ? null
    : Number(summary.max_speed_mps);
  return tripWithAnalysis({
    ...summary,
    max_speed_mps: Number.isFinite(suppliedMaxSpeed)
      ? suppliedMaxSpeed
      : maxRoutePointSpeedMps(Array.isArray(route) ? route : []),
  });
}

async function fetchD1TripSummaries(env, deviceId, limit) {
  const trips = await env.DB.prepare(`
    SELECT id, device_id, started_at, ended_at, duration_s, distance_m,
           start_lat, start_lon, end_lat, end_lon, route_point_count,
           CASE
             WHEN duration_s > 0 AND distance_m IS NOT NULL THEN distance_m / duration_s
             ELSE NULL
           END AS avg_speed_mps,
           route_json, report_json, health_json, health_updated_at
    FROM trips WHERE device_id = ? ORDER BY ended_at DESC LIMIT ?
  `).bind(deviceId, Math.min(limit, 1000)).all();
  return (trips.results || []).map(parseTripSummary);
}

function mergeServerTripsWithD1(serverTrips, d1Trips) {
  const d1ById = new Map(d1Trips.map((trip) => [String(trip.id || ""), trip]));
  return serverTrips.map((serverTrip) => {
    const d1Trip = d1ById.get(String(serverTrip.id || ""));
    if (!d1Trip) return serverTrip;
    return {
      ...d1Trip,
      ...serverTrip,
      report: objectWithValues(d1Trip.report) ? d1Trip.report : serverTrip.report,
      analysis: objectWithValues(d1Trip.analysis) ? d1Trip.analysis : serverTrip.analysis,
      health: objectWithValues(serverTrip.health) ? serverTrip.health : d1Trip.health,
    };
  });
}

function finiteNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function mean(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function percentile(values, ratio) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const position = Math.max(0, Math.min(sorted.length - 1, (sorted.length - 1) * ratio));
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

function rounded(value, digits = 1) {
  return value == null || !Number.isFinite(value) ? null : Number(value.toFixed(digits));
}

function clampNumber(value, lower, upper) {
  return Math.max(lower, Math.min(upper, value));
}

function parseHealthValues(record) {
  const values = record?.values;
  return values && typeof values === "object" && !Array.isArray(values) ? values : {};
}

function heartSamples(records, since, until) {
  const byTime = new Map();
  for (const record of records.filter((item) => item.type === "heart_rate" || item.type === "watch_heart_rate_1m")) {
    const values = parseHealthValues(record);
    const series = Array.isArray(values.series) ? values.series : [];
    const candidates = series.length ? series : [{
      value: values.heart_rate ?? values.mean_heart_rate_bpm,
      start_time: record.start_time,
    }];
    for (const sample of candidates) {
      const bpm = finiteNumber(sample?.value ?? sample?.heart_rate);
      const time = finiteNumber(sample?.start_time ?? sample?.time ?? record.start_time);
      if (bpm == null || time == null || bpm < 30 || bpm > 240 || time < since || time > until) continue;
      byTime.set(time, { time, bpm });
    }
  }
  return [...byTime.values()].sort((a, b) => a.time - b.time);
}

function closestTimelineState(timeline, timestamp) {
  let closest = null;
  let distance = Infinity;
  for (const point of timeline) {
    const time = Date.parse(point?.time || "");
    const delta = Math.abs(time - timestamp);
    if (Number.isFinite(time) && delta < distance) {
      closest = point;
      distance = delta;
    }
  }
  return distance <= 12_000 ? closest : null;
}

function averageHeartRateByAutomation(samples, timeline) {
  const op = [];
  const manual = [];
  for (const sample of samples) {
    const state = closestTimelineState(timeline, sample.time);
    if (!state) continue;
    (state.opActive ? op : manual).push(sample.bpm);
  }
  const opAverage = op.length >= 3 ? mean(op) : null;
  const manualAverage = manual.length >= 3 ? mean(manual) : null;
  return {
    opSampleCount: op.length,
    manualSampleCount: manual.length,
    opAverageBpm: rounded(opAverage),
    manualAverageBpm: rounded(manualAverage),
    opMinusManualBpm: opAverage != null && manualAverage != null ? rounded(opAverage - manualAverage) : null,
    comparable: opAverage != null && manualAverage != null,
  };
}

function correlateMomentsWithHealth(moments, heartRateSamples, sensorRecords) {
  const severityWeight = { critical: 30, high: 20, medium: 10, low: 0 };
  return moments.map((moment) => {
    const eventTime = Date.parse(moment?.time || "");
    if (!Number.isFinite(eventTime)) return null;
    const before = heartRateSamples.filter((sample) => sample.time >= eventTime - 60_000 && sample.time <= eventTime - 8_000);
    const after = heartRateSamples.filter((sample) => sample.time >= eventTime && sample.time <= eventTime + 90_000);
    if (!before.length || !after.length) return null;
    const baseline = mean(before.map((sample) => sample.bpm));
    const peak = Math.max(...after.map((sample) => sample.bpm));
    const delta = peak - baseline;
    const peakSample = after.find((sample) => sample.bpm === peak);
    const recovered = after.find((sample) => sample.time > (peakSample?.time ?? eventTime) && sample.bpm <= baseline + 3);
    const nearbySensors = sensorRecords.filter((record) => (
      Number(record.start_time) <= eventTime + 90_000 && Number(record.end_time) >= eventTime - 30_000
    ));
    const edaValues = nearbySensors.map((record) => finiteNumber(parseHealthValues(record).eda_mean_us)).filter((value) => value != null);
    return {
      ...moment,
      baselineBpm: rounded(baseline),
      peakBpm: rounded(peak),
      heartRateDeltaBpm: rounded(delta),
      edaAboveBaselineMicrosiemens: edaValues.length ? rounded(Math.max(...edaValues) - Math.min(...edaValues), 2) : null,
      recoverySeconds: recovered && peakSample ? Math.round((recovered.time - peakSample.time) / 1000) : null,
      correlationConfidence: before.length >= 2 && after.length >= 3 ? "high" : "medium",
      loadRank: Math.max(0, delta) * 3 + (severityWeight[moment.severity] || 0),
    };
  }).filter(Boolean).sort((a, b) => b.loadRank - a.loadRank);
}

function recentContext(records, tripStart) {
  const beforeTrip = records.filter((record) => Number(record.start_time) <= tripStart);
  const latest = (type) => beforeTrip.filter((record) => record.type === type)
    .sort((a, b) => Number(b.start_time) - Number(a.start_time))[0];
  const sleepValues = parseHealthValues(latest("sleep"));
  const sleepDailyValues = parseHealthValues(latest("sleep_duration_daily"));
  const energyValues = parseHealthValues(latest("energy_score"));
  const sleepDurationSeconds = finiteNumber(sleepValues.duration_seconds) ?? finiteNumber(sleepDailyValues.seconds);
  return {
    sleepScore: finiteNumber(sleepValues.sleep_score),
    sleepDurationMinutes: sleepDurationSeconds == null ? null : rounded(sleepDurationSeconds / 60, 0),
    energyScore: rounded(finiteNumber(energyValues.score), 0),
  };
}

function buildAuxiliarySensorSummary(records, startedAt, endedAt) {
  const sensorRecords = records.filter((record) => (
    record.type === "watch_driver_sensors_1m" &&
    Number(record.start_time) <= endedAt && Number(record.end_time) >= startedAt
  ));
  const values = sensorRecords.map(parseHealthValues);
  const edaMeans = values.map((item) => finiteNumber(item.eda_mean_us)).filter((value) => value != null);
  const edaP90 = values.map((item) => finiteNumber(item.eda_p90_us)).filter((value) => value != null);
  const edaSamples = values.reduce((sum, item) => sum + (finiteNumber(item.eda_sample_count) ?? 0), 0);
  const edaRises = values.reduce((sum, item) => sum + (finiteNumber(item.eda_phasic_rise_count) ?? 0), 0);
  const skinMeans = values.map((item) => finiteNumber(item.skin_temperature_mean_c)).filter((value) => value != null);
  const ambientMeans = values.map((item) => finiteNumber(item.ambient_temperature_mean_c)).filter((value) => value != null);
  const skinSamples = values.reduce((sum, item) => sum + (finiteNumber(item.skin_temperature_sample_count) ?? 0), 0);
  const motionRms = values.map((item) => finiteNumber(item.motion_rms_mps2)).filter((value) => value != null);
  const motionP95 = values.map((item) => finiteNumber(item.motion_p95_mps2)).filter((value) => value != null);
  const moving = values.map((item) => finiteNumber(item.moving_percent)).filter((value) => value != null);
  const motionSamples = values.reduce((sum, item) => sum + (finiteNumber(item.accelerometer_sample_count) ?? 0), 0);
  const edaAvailable = edaSamples > 0 && edaMeans.length > 0;
  const temperatureAvailable = skinSamples > 0 && skinMeans.length > 0;
  const motionAvailable = motionSamples > 0 && motionRms.length > 0;
  const movingPercent = mean(moving);
  const signalContaminationLikely = motionAvailable && movingPercent != null && movingPercent >= 75;
  const edaRange = edaP90.length && edaMeans.length ? Math.max(...edaP90) - Math.min(...edaMeans) : 0;
  const edaConfidence = !edaAvailable ? "low" : signalContaminationLikely ? "medium" : edaSamples >= 60 ? "high" : "medium";
  return {
    available: edaAvailable || temperatureAvailable || motionAvailable,
    windowCount: sensorRecords.length,
    eda: {
      available: edaAvailable,
      confidence: edaConfidence,
      averageMicrosiemens: rounded(mean(edaMeans), 2),
      p90Microsiemens: rounded(percentile(edaP90, 0.9), 2),
      phasicRiseCount: edaRises,
      sampleCount: edaSamples,
      arousalProxy0To100: edaAvailable ? Math.round(clampNumber(edaRange * 18 + edaRises * 1.5, 0, 100)) : null,
    },
    temperature: {
      available: temperatureAvailable,
      confidence: temperatureAvailable && skinSamples >= 10 ? "high" : temperatureAvailable ? "medium" : "low",
      averageSkinC: rounded(mean(skinMeans), 1),
      averageAmbientC: rounded(mean(ambientMeans), 1),
      sampleCount: skinSamples,
    },
    motion: {
      available: motionAvailable,
      confidence: motionAvailable && motionSamples >= 300 ? "high" : motionAvailable ? "medium" : "low",
      rmsMps2: rounded(mean(motionRms), 2),
      p95Mps2: rounded(percentile(motionP95, 0.95), 2),
      movingPercent: rounded(movingPercent, 0),
      sampleCount: motionSamples,
      signalContaminationLikely,
    },
  };
}

export function buildTripHealthSummary(records, trip, analysis = {}) {
  const startedAt = Date.parse(trip?.started_at || trip?.startedAt || "");
  const endedAt = Date.parse(trip?.ended_at || trip?.endedAt || "");
  if (!Number.isFinite(startedAt) || !Number.isFinite(endedAt) || endedAt <= startedAt) {
    return { available: false, status: "invalid_trip_time" };
  }

  const samples = heartSamples(records, startedAt, endedAt);
  const context = recentContext(records, startedAt);
  const sensors = buildAuxiliarySensorSummary(records, startedAt, endedAt);
  if (!samples.length) {
    const edaLoad = finiteNumber(sensors?.eda?.arousalProxy0To100);
    if (sensors?.eda?.available && edaLoad != null) {
      const loadScore = Math.round(clampNumber(edaLoad, 0, 100));
      return {
        schemaVersion: "wayon-driver-load-v1",
        available: true,
        status: "ready_eda_only",
        generatedAt: nowIso(),
        confidence: sensors.motion?.signalContaminationLikely ? "low" : "medium",
        notice: "심박은 수집되지 않아 EDA 기반 보조 추정치만 표시합니다. 의료적 스트레스 진단이 아닙니다.",
        load: {
          estimatedLoad0To100: loadScore,
          band: loadScore >= 65 ? "high" : loadScore >= 35 ? "moderate" : "low",
          highLoadPercent: null,
          highLoadMinutesEstimate: null,
          basis: "eda_only",
        },
        heartRate: {
          available: false,
          sampleCount: 0,
          coveragePercent: 0,
          trend: [],
        },
        hrv: { validWindowCount: 0, averageRmssdMs: null },
        sensors,
        context,
        automationComparison: {
          opSampleCount: 0,
          manualSampleCount: 0,
          opAverageBpm: null,
          manualAverageBpm: null,
          opMinusManualBpm: null,
          comparable: false,
        },
        topStressMoments: [],
      };
    }
    return {
      available: false,
      status: "no_heart_rate_during_trip",
      context,
      sensors,
      notice: "심박 데이터가 없어 주행 부담도를 계산하지 않았습니다.",
    };
  }

  const bpms = samples.map((sample) => sample.bpm);
  const preDriveSamples = heartSamples(records, startedAt - 10 * 60_000, startedAt - 1);
  const baseline = preDriveSamples.length >= 3 ? mean(preDriveSamples.map((sample) => sample.bpm)) : percentile(bpms, 0.2);
  const average = mean(bpms);
  const maximum = Math.max(...bpms);
  const minimum = Math.min(...bpms);
  const highLoadCount = samples.filter((sample) => sample.bpm >= baseline + 12).length;
  const highLoadPercent = 100 * highLoadCount / samples.length;
  const averageElevation = Math.max(0, average - baseline);
  const loadScore = Math.round(clampNumber(averageElevation * 5 + highLoadPercent * 0.55, 0, 100));
  const hrvWindows = records.filter((record) => {
    if (record.type !== "watch_hrv_5m") return false;
    const quality = finiteNumber(parseHealthValues(record).signal_quality_percent);
    return Number(record.start_time) <= endedAt && Number(record.end_time) >= startedAt && quality != null && quality >= 80;
  });
  const hrvRmssd = hrvWindows.map((record) => finiteNumber(parseHealthValues(record).rmssd_ms)).filter((value) => value != null);
  const timeline = Array.isArray(analysis.timeline) ? analysis.timeline : [];
  const moments = Array.isArray(analysis.moments) ? analysis.moments : [];
  const sensorRecords = records.filter((record) => record.type === "watch_driver_sensors_1m");
  const correlations = correlateMomentsWithHealth(moments, samples, sensorRecords);
  const tripDurationMinutes = Math.max(1, (endedAt - startedAt) / 60_000);
  const expectedSamples = Math.max(1, tripDurationMinutes / 1.5);
  const coveragePercent = Math.min(100, 100 * samples.length / expectedSamples);
  const confidence = samples.length >= 20 && coveragePercent >= 65 ? "high" : samples.length >= 5 ? "medium" : "low";
  const stride = Math.max(1, Math.ceil(samples.length / 80));

  return {
    schemaVersion: "wayon-driver-load-v1",
    available: true,
    status: "ready",
    generatedAt: nowIso(),
    confidence,
    notice: "생활·웰니스 참고용 추정치이며 의료적 스트레스 진단이 아닙니다.",
    load: {
      estimatedLoad0To100: loadScore,
      band: loadScore >= 65 ? "high" : loadScore >= 35 ? "moderate" : "low",
      highLoadPercent: rounded(highLoadPercent),
      highLoadMinutesEstimate: rounded(tripDurationMinutes * highLoadPercent / 100),
    },
    heartRate: {
      available: true,
      sampleCount: samples.length,
      coveragePercent: rounded(coveragePercent),
      baselineBpm: rounded(baseline),
      baselineMethod: preDriveSamples.length >= 3 ? "pre_drive_10m" : "trip_low_percentile",
      averageBpm: rounded(average),
      minimumBpm: rounded(minimum),
      maximumBpm: rounded(maximum),
      peakAboveBaselineBpm: rounded(maximum - baseline),
      trend: samples.filter((_, index) => index % stride === 0).map((sample) => ({
        time: new Date(sample.time).toISOString(),
        bpm: rounded(sample.bpm),
        load0To100: Math.round(clampNumber((sample.bpm - baseline) * 5, 0, 100)),
        opActive: closestTimelineState(timeline, sample.time)?.opActive ?? null,
      })),
    },
    hrv: {
      validWindowCount: hrvRmssd.length,
      averageRmssdMs: rounded(mean(hrvRmssd)),
    },
    sensors,
    context,
    automationComparison: averageHeartRateByAutomation(samples, timeline),
    topStressMoments: correlations.slice(0, 5),
  };
}

async function fetchHealthBridgeRecords(env, since, until, types) {
  const token = String(env.HEALTH_BRIDGE_READ_TOKEN || "");
  if (!token) return null;
  const endpoint = String(env.HEALTH_BRIDGE_URL || DEFAULT_HEALTH_BRIDGE_URL).replace(/\/$/, "");
  const url = new URL(`${endpoint}/v1/records`);
  url.searchParams.set("since", String(Math.max(0, Math.floor(since))));
  url.searchParams.set("until", String(Math.max(0, Math.floor(until))));
  url.searchParams.set("limit", "500");
  for (const type of types) url.searchParams.append("type", type);
  const init = {
    headers: { authorization: `Bearer ${token}`, accept: "application/json" },
    cf: { cacheTtl: 0, cacheEverything: false },
  };
  const response = env.HEALTH_BRIDGE_API
    ? await env.HEALTH_BRIDGE_API.fetch(new Request(`https://health-bridge-api${url.pathname}${url.search}`, init))
    : await fetch(url, init);
  if (!response.ok) throw new Error(`health_bridge_${response.status}`);
  const payload = await response.json();
  return Array.isArray(payload.records) ? payload.records : [];
}

async function tripWithHealth(env, trip) {
  const parsed = parseTripRoute(trip);
  const cachedAt = Date.parse(trip.health_updated_at || "");
  if (parsed.health?.status === "ready" && Number.isFinite(cachedAt) && Date.now() - cachedAt < TRIP_HEALTH_CACHE_SECONDS * 1000) {
    return parsed;
  }
  if (!env.HEALTH_BRIDGE_READ_TOKEN) {
    parsed.health = { available: false, status: "not_configured" };
    return parsed;
  }
  const startedAt = Date.parse(trip.started_at || "");
  const endedAt = Date.parse(trip.ended_at || "");
  if (!Number.isFinite(startedAt) || !Number.isFinite(endedAt)) return parsed;
  try {
    const [driveRecords, contextRecords] = await Promise.all([
      // Samsung Health stores heart rate in hour-sized records. Fetch far enough
      // back to include a record that started before the trip but overlaps it.
      fetchHealthBridgeRecords(env, startedAt - 2 * 60 * 60_000, endedAt + 2 * 60_000, [
        "heart_rate", "watch_heart_rate_1m", "watch_hrv_5m", "watch_driver_sensors_1m",
      ]),
      fetchHealthBridgeRecords(env, startedAt - 36 * 60 * 60_000, startedAt, [
        "sleep", "sleep_duration_daily", "energy_score",
      ]),
    ]);
    parsed.health = buildTripHealthSummary([...(driveRecords || []), ...(contextRecords || [])], trip, parsed.analysis);
    await env.DB.prepare("UPDATE trips SET health_json = ?, health_updated_at = ? WHERE id = ? AND device_id = ?")
      .bind(JSON.stringify(parsed.health), nowIso(), trip.id, trip.device_id).run();
  } catch (error) {
    parsed.health = { available: false, status: "temporarily_unavailable", detail: String(error?.message || error) };
  }
  return parsed;
}

async function fetchServerApi(env, path, deviceId) {
  if (!env.WAYON_SERVER_API || !env.WAYON_SERVER_SYNC_TOKEN) return null;

  return env.WAYON_SERVER_API.fetch(`http://wayon-server${path}`, {
    headers: {
      accept: "application/json",
      authorization: `Bearer ${env.WAYON_SERVER_SYNC_TOKEN}`,
      "x-wayon-device-id": deviceId,
    },
    signal: AbortSignal.timeout(SERVER_API_TIMEOUT_MS),
  });
}

async function fetchServerTripList(env, limit, deviceId) {
  const response = await fetchServerApi(
    env,
    `/v1/wayon/trips?limit=${encodeURIComponent(limit)}&offset=0&include_route=false`,
    deviceId,
  );
  if (!response || !response.ok) {
    throw new Error(`server_trip_list_${response?.status || "unavailable"}`);
  }

  const payload = await response.json();
  if (payload?.schemaVersion !== "wayon-trip-read-v1" || !Array.isArray(payload.trips)) {
    throw new Error("server_trip_list_schema");
  }
  return payload.trips
    .filter((trip) => String(trip.device_id || trip.deviceId || "") === deviceId)
    .map(parseServerTripSummary);
}

async function fetchServerTrip(env, tripId, deviceId) {
  const response = await fetchServerApi(
    env,
    `/v1/wayon/trips/${encodeURIComponent(tripId)}`,
    deviceId,
  );
  if (!response || !response.ok) {
    throw new Error(`server_trip_${response?.status || "unavailable"}`);
  }

  const payload = await response.json();
  if (payload?.schemaVersion !== "wayon-trip-read-v1" || !payload.trip) {
    throw new Error("server_trip_schema");
  }
  const tripDeviceId = String(payload.trip.device_id || payload.trip.deviceId || "");
  if (tripDeviceId !== deviceId) throw new Error("server_trip_device_mismatch");
  return tripWithAnalysis(payload.trip);
}

async function fetchServerImpactList(env, limit, deviceId) {
  const response = await fetchServerApi(
    env,
    `/v1/wayon/impacts?limit=${encodeURIComponent(limit)}&offset=0`,
    deviceId,
  );
  if (!response || !response.ok) {
    throw new Error(`server_impact_list_${response?.status || "unavailable"}`);
  }

  const payload = await response.json();
  if (payload?.schemaVersion !== "wayon-impact-read-v1" || !Array.isArray(payload.impacts)) {
    throw new Error("server_impact_list_schema");
  }
  return payload.impacts.filter(
    (impact) => String(impact.device_id || impact.deviceId || "") === deviceId,
  );
}

async function fetchServerSnapshotList(env, limit, date, deviceId) {
  const dateQuery = date ? `&date=${encodeURIComponent(date)}` : "";
  const response = await fetchServerApi(
    env,
    `/v1/wayon/snapshots?limit=${encodeURIComponent(limit)}&offset=0${dateQuery}`,
    deviceId,
  );
  if (!response || !response.ok) {
    throw new Error(`server_snapshot_list_${response?.status || "unavailable"}`);
  }

  const payload = await response.json();
  if (payload?.schemaVersion !== "wayon-snapshot-read-v1" || !Array.isArray(payload.snapshots)) {
    throw new Error("server_snapshot_list_schema");
  }
  return {
    generatedAt: payload.generatedAt || nowIso(),
    snapshots: payload.snapshots.filter(
      (snapshot) => String(snapshot.device_id || snapshot.deviceId || "") === deviceId,
    ),
    days: Array.isArray(payload.days) ? payload.days : [],
    total: Number.isFinite(Number(payload.total)) ? Number(payload.total) : 0,
    limit,
  };
}

function parseSyncCursor(value) {
  if (!value) return { valid: true, cursor: null };
  if (value.length > 512) return { valid: false, cursor: null };

  try {
    const parsed = JSON.parse(base64UrlToText(value));
    const createdAt = String(parsed?.createdAt || "");
    const id = String(parsed?.id || "");
    if (!createdAt || !id || createdAt.length > 64 || id.length > 256) {
      return { valid: false, cursor: null };
    }
    return { valid: true, cursor: { createdAt, id } };
  } catch {
    return { valid: false, cursor: null };
  }
}

function syncCursor(row, timestampField = "created_at") {
  return textToBase64Url(JSON.stringify({
    createdAt: row[timestampField],
    id: row.id,
  }));
}

async function handleServerSyncTrips(request, env) {
  if (!authorizeServerSync(request, env)) {
    return json({ error: "unauthorized" }, 401);
  }

  const url = new URL(request.url);
  const cursorValue = url.searchParams.get("cursor") || "";
  const parsedCursor = parseSyncCursor(cursorValue);
  if (!parsedCursor.valid) return json({ error: "invalid_cursor" }, 400);

  const limit = boundedLimit(url.searchParams.get("limit"), 50, 100);
  const queryLimit = limit + 1;
  const select = `
    SELECT id, device_id, started_at, ended_at, duration_s, distance_m,
           start_lat, start_lon, end_lat, end_lon, route_point_count,
           route_json, created_at
    FROM trips
  `;
  const result = parsedCursor.cursor
    ? await env.DB.prepare(`
        ${select}
        WHERE created_at > ? OR (created_at = ? AND id > ?)
        ORDER BY created_at ASC, id ASC LIMIT ?
      `).bind(
        parsedCursor.cursor.createdAt,
        parsedCursor.cursor.createdAt,
        parsedCursor.cursor.id,
        queryLimit,
      ).all()
    : await env.DB.prepare(`
        ${select}
        ORDER BY created_at ASC, id ASC LIMIT ?
      `).bind(queryLimit).all();

  const rows = result.results || [];
  const hasMore = rows.length > limit;
  const page = rows.slice(0, limit);
  return json({
    schemaVersion: "wayon-trip-sync-v1",
    generatedAt: nowIso(),
    trips: page.map(parseTripRoute),
    nextCursor: page.length ? syncCursor(page[page.length - 1]) : (cursorValue || null),
    hasMore,
  });
}

async function handleServerSyncImpacts(request, env) {
  if (!authorizeServerSync(request, env)) return json({ error: "unauthorized" }, 401);

  const url = new URL(request.url);
  const cursorValue = url.searchParams.get("cursor") || "";
  const parsedCursor = parseSyncCursor(cursorValue);
  if (!parsedCursor.valid) return json({ error: "invalid_cursor" }, 400);

  const limit = boundedLimit(url.searchParams.get("limit"), 50, 100);
  const queryLimit = limit + 1;
  const select = `
    SELECT id, device_id, detected_at, received_at, severity, peak_dynamic_g,
           peak_total_g, peak_jerk_g_per_s, peak_gyro_rad_per_s, duration_ms,
           sample_count, sensor_clipped, latitude, longitude, capture_status,
           captured_at, capture_attempts, wide_snapshot_id, driver_snapshot_id,
           notified_count, raw_json
    FROM impact_events
  `;
  const result = parsedCursor.cursor
    ? await env.DB.prepare(`
        ${select}
        WHERE received_at > ? OR (received_at = ? AND id > ?)
        ORDER BY received_at ASC, id ASC LIMIT ?
      `).bind(
        parsedCursor.cursor.createdAt,
        parsedCursor.cursor.createdAt,
        parsedCursor.cursor.id,
        queryLimit,
      ).all()
    : await env.DB.prepare(`
        ${select}
        ORDER BY received_at ASC, id ASC LIMIT ?
      `).bind(queryLimit).all();

  const rows = result.results || [];
  const hasMore = rows.length > limit;
  const page = rows.slice(0, limit);
  return json({
    schemaVersion: "wayon-impact-sync-v1",
    generatedAt: nowIso(),
    impacts: page,
    nextCursor: page.length ? syncCursor(page[page.length - 1], "received_at") : (cursorValue || null),
    hasMore,
  });
}

async function handleServerSyncSnapshots(request, env) {
  if (!authorizeServerSync(request, env)) return json({ error: "unauthorized" }, 401);

  const url = new URL(request.url);
  const cursorValue = url.searchParams.get("cursor") || "";
  const parsedCursor = parseSyncCursor(cursorValue);
  if (!parsedCursor.valid) return json({ error: "invalid_cursor" }, 400);

  const limit = boundedLimit(url.searchParams.get("limit"), 50, 100);
  const queryLimit = limit + 1;
  const select = `
    SELECT id, device_id, camera, captured_at, kv_key, size_bytes, created_at
    FROM snapshots
  `;
  const result = parsedCursor.cursor
    ? await env.DB.prepare(`
        ${select}
        WHERE created_at > ? OR (created_at = ? AND id > ?)
        ORDER BY created_at ASC, id ASC LIMIT ?
      `).bind(
        parsedCursor.cursor.createdAt,
        parsedCursor.cursor.createdAt,
        parsedCursor.cursor.id,
        queryLimit,
      ).all()
    : await env.DB.prepare(`
        ${select}
        ORDER BY created_at ASC, id ASC LIMIT ?
      `).bind(queryLimit).all();

  const rows = result.results || [];
  const hasMore = rows.length > limit;
  const page = rows.slice(0, limit);
  return json({
    schemaVersion: "wayon-snapshot-sync-v1",
    generatedAt: nowIso(),
    snapshots: page,
    nextCursor: page.length ? syncCursor(page[page.length - 1]) : (cursorValue || null),
    hasMore,
  });
}

async function handleExport(request, env) {
  if (!authorize(request, env, false)) {
    return json({ error: "unauthorized" }, 401);
  }

  const deviceId = authenticatedDeviceId(request);
  const [state, snapshots, trips, vehicleStatus, vehicleLock, healthTimeline] = await Promise.all([
    env.DB.prepare(`
      SELECT * FROM latest_state WHERE device_id = ? LIMIT 1
    `).bind(deviceId).first(),
    env.DB.prepare(`
      SELECT id, device_id, camera, captured_at, kv_key, size_bytes, created_at
      FROM snapshots WHERE device_id = ? ORDER BY captured_at DESC LIMIT 24
    `).bind(deviceId).all(),
    env.DB.prepare(`
      SELECT * FROM trips WHERE device_id = ? ORDER BY ended_at DESC LIMIT 25
    `).bind(deviceId).all(),
    fetchMergedVehicleStatus(env, deviceId),
    latestVehicleLock(env, deviceId),
    latestHealthTimeline(env, deviceId),
  ]);

  return json({
    generatedAt: nowIso(),
    state,
    vehicleStatus,
    vehicleLock,
    healthTimeline,
    snapshots: snapshots.results || [],
    trips: (trips.results || []).map(parseTripRoute),
  });
}

async function handleSnapshotsList(request, env) {
  if (!authorize(request, env, false)) {
    return json({ error: "unauthorized" }, 401);
  }

  const url = new URL(request.url);
  const deviceId = authenticatedDeviceId(request);
  const limit = boundedLimit(url.searchParams.get("limit"), 500, 1000);
  const date = url.searchParams.get("date");
  try {
    return historyJson(await fetchServerSnapshotList(env, limit, date, deviceId), "server");
  } catch (error) {
    console.warn("Wayon server snapshot list unavailable; using D1", error?.message || error);
  }

  const dateWhere = date
    ? "WHERE s.device_id = ? AND date(s.captured_at, '+9 hours') = ?"
    : "WHERE s.device_id = ?";
  const snapshotQuery = `
    SELECT s.id, s.device_id, s.camera, s.captured_at, s.kv_key, s.size_bytes, s.created_at,
           COALESCE(iw.id, idr.id) AS impact_id,
           COALESCE(iw.severity, idr.severity) AS impact_severity,
           COALESCE(iw.peak_dynamic_g, idr.peak_dynamic_g) AS impact_peak_dynamic_g,
           COALESCE(iw.peak_total_g, idr.peak_total_g) AS impact_peak_total_g,
           COALESCE(iw.detected_at, idr.detected_at) AS impact_detected_at
    FROM snapshots s
    LEFT JOIN impact_events iw ON s.id = iw.wide_snapshot_id
    LEFT JOIN impact_events idr ON s.id = idr.driver_snapshot_id
    ${dateWhere}
    ORDER BY s.captured_at DESC LIMIT ?
  `;
  const snapshots = date
    ? await env.DB.prepare(snapshotQuery).bind(deviceId, date, limit).all()
    : await env.DB.prepare(snapshotQuery).bind(deviceId, limit).all();
  const days = await env.DB.prepare(`
    SELECT date(captured_at, '+9 hours') AS date, COUNT(*) AS count
    FROM snapshots WHERE device_id = ? GROUP BY date ORDER BY date DESC
  `).bind(deviceId).all();
  const total = await env.DB.prepare(`SELECT COUNT(*) AS count FROM snapshots WHERE device_id = ?`)
    .bind(deviceId).first();

  return historyJson({
    generatedAt: nowIso(),
    snapshots: snapshots.results || [],
    days: days.results || [],
    total: total?.count || 0,
    limit,
  }, "d1");
}

async function handleTrips(request, env, pathname) {
  if (!authorize(request, env, false)) {
    return json({ error: "unauthorized" }, 401);
  }

  const deviceId = authenticatedDeviceId(request);
  const parts = pathname.split("/").filter(Boolean);
  if (parts.length === 3) {
    const d1Trip = await env.DB.prepare(`SELECT * FROM trips WHERE id = ? AND device_id = ?`)
      .bind(parts[2], deviceId)
      .first();
    try {
      const serverTrip = await fetchServerTrip(env, parts[2], deviceId);
      const d1TripWithHealth = d1Trip ? await tripWithHealth(env, d1Trip) : null;
      const merged = mergeServerTripsWithD1(
        [serverTrip],
        d1TripWithHealth ? [d1TripWithHealth] : [],
      )[0];
      return historyJson(merged, "server+d1");
    } catch (error) {
      console.warn("Wayon server trip detail unavailable; using D1", error?.message || error);
    }

    if (!d1Trip) return json({ error: "not_found" }, 404);

    return historyJson(await tripWithHealth(env, d1Trip), "d1");
  }

  const url = new URL(request.url);
  const requestedLimit = boundedLimit(url.searchParams.get("limit"), 100, 5000);
  try {
    const [serverTrips, d1Trips] = await Promise.all([
      fetchServerTripList(env, requestedLimit, deviceId),
      fetchD1TripSummaries(env, deviceId, requestedLimit),
    ]);
    return historyJson({ trips: mergeServerTripsWithD1(serverTrips, d1Trips) }, "server+d1");
  } catch (error) {
    console.warn("Wayon server trip list unavailable; using D1", error?.message || error);
  }

  return historyJson({ trips: await fetchD1TripSummaries(env, deviceId, requestedLimit) }, "d1");
}

async function handleSnapshotImage(request, env) {
  if (!authorize(request, env, false)) {
    return json({ error: "unauthorized" }, 401);
  }

  const url = new URL(request.url);
  const key = url.searchParams.get("key");
  if (!key) return json({ error: "missing_key" }, 400);

  const deviceId = authenticatedDeviceId(request);
  const snapshot = await env.DB.prepare(`SELECT kv_key FROM snapshots WHERE kv_key = ? AND device_id = ?`)
    .bind(key, deviceId).first();
  if (!snapshot) return json({ error: "not_found" }, 404);

  const image = await env.SNAPSHOTS.get(snapshot.kv_key, "arrayBuffer");
  if (!image) return json({ error: "not_found" }, 404);

  return new Response(image, {
    headers: {
      ...CORS_HEADERS,
      "content-type": "image/jpeg",
      "cache-control": "private, max-age=60",
    },
  });
}

function parseJsonObject(value) {
  try {
    const parsed = JSON.parse(value || "{}");
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function isoAgeSeconds(timestamp) {
  const millis = Date.parse(timestamp || "");
  if (!Number.isFinite(millis)) return null;
  return Math.max(0, Math.round((Date.now() - millis) / 1000));
}

function aiImageUrl(request, snapshotId) {
  if (!snapshotId) return null;
  return new URL(`/api/ai/images/${encodeURIComponent(snapshotId)}`, request.url).toString();
}

function aiSnapshot(request, snapshot) {
  return {
    id: snapshot.id,
    deviceId: snapshot.device_id,
    camera: snapshot.camera,
    capturedAt: snapshot.captured_at,
    createdAt: snapshot.created_at,
    sizeBytes: snapshot.size_bytes,
    impact: snapshot.impact_id ? {
      id: snapshot.impact_id,
      severity: snapshot.impact_severity,
      peakDynamicG: nullableNumber(snapshot.impact_peak_dynamic_g),
      peakTotalG: nullableNumber(snapshot.impact_peak_total_g),
      detectedAt: snapshot.impact_detected_at,
    } : null,
    imageUrl: aiImageUrl(request, snapshot.id),
    contentType: "image/jpeg",
  };
}

function aiImpact(request, impact) {
  return {
    id: impact.id,
    deviceId: impact.device_id,
    detectedAt: impact.detected_at,
    receivedAt: impact.received_at,
    severity: impact.severity,
    peakDynamicG: nullableNumber(impact.peak_dynamic_g),
    peakTotalG: nullableNumber(impact.peak_total_g),
    peakJerkGPerSec: nullableNumber(impact.peak_jerk_g_per_s),
    peakGyroRadPerSec: nullableNumber(impact.peak_gyro_rad_per_s),
    durationMs: impact.duration_ms,
    sampleCount: impact.sample_count,
    sensorClipped: Boolean(impact.sensor_clipped),
    location: validCoordinate(impact.latitude) && validCoordinate(impact.longitude) ? {
      latitude: nullableNumber(impact.latitude),
      longitude: nullableNumber(impact.longitude),
    } : null,
    capture: {
      status: impact.capture_status,
      capturedAt: impact.captured_at,
      attempts: impact.capture_attempts,
      wideSnapshotId: impact.wide_snapshot_id,
      driverSnapshotId: impact.driver_snapshot_id,
      wideImageUrl: aiImageUrl(request, impact.wide_snapshot_id),
      driverImageUrl: aiImageUrl(request, impact.driver_snapshot_id),
    },
    notifiedCount: impact.notified_count,
  };
}

function aiVehicleEvent(event) {
  const raw = parseJsonObject(event.raw_json);
  return {
    id: event.id,
    deviceId: event.device_id,
    eventType: event.event_type,
    occurredAt: event.occurred_at,
    receivedAt: event.received_at,
    locked: event.locked == null ? null : Boolean(event.locked),
    notifiedCount: event.notified_count,
    details: raw,
  };
}

const AI_IMPACT_SELECT = `
  SELECT id, device_id, detected_at, received_at, severity, peak_dynamic_g,
         peak_total_g, peak_jerk_g_per_s, peak_gyro_rad_per_s, duration_ms,
         sample_count, sensor_clipped, latitude, longitude, capture_status,
         captured_at, capture_attempts, wide_snapshot_id, driver_snapshot_id,
         notified_count
  FROM impact_events
`;

const AI_SNAPSHOT_SELECT = `
  SELECT s.id, s.device_id, s.camera, s.captured_at, s.size_bytes, s.created_at,
         COALESCE(iw.id, idr.id) AS impact_id,
         COALESCE(iw.severity, idr.severity) AS impact_severity,
         COALESCE(iw.peak_dynamic_g, idr.peak_dynamic_g) AS impact_peak_dynamic_g,
         COALESCE(iw.peak_total_g, idr.peak_total_g) AS impact_peak_total_g,
         COALESCE(iw.detected_at, idr.detected_at) AS impact_detected_at
  FROM snapshots s
  LEFT JOIN impact_events iw ON s.id = iw.wide_snapshot_id
  LEFT JOIN impact_events idr ON s.id = idr.driver_snapshot_id
`;

async function handleAiContext(request, env) {
  if (!authorizeAi(request, env)) return json({ error: "unauthorized" }, 401);

  const url = new URL(request.url);
  const impactLimit = boundedLimit(url.searchParams.get("impacts"), 8, 50);
  const eventLimit = boundedLimit(url.searchParams.get("events"), 20, 100);
  const snapshotLimit = boundedLimit(url.searchParams.get("snapshots"), 12, 50);
  const [state, impactResult, eventResult, latestTrip, snapshotResult, firebaseVehicleStatus] = await Promise.all([
    env.DB.prepare("SELECT * FROM latest_state ORDER BY updated_at DESC LIMIT 1").first(),
    env.DB.prepare(`${AI_IMPACT_SELECT} ORDER BY detected_at DESC LIMIT ?`).bind(impactLimit).all(),
    env.DB.prepare(`
      SELECT id, device_id, event_type, occurred_at, received_at, locked, notified_count, raw_json
      FROM vehicle_events ORDER BY occurred_at DESC LIMIT ?
    `).bind(eventLimit).all(),
    env.DB.prepare("SELECT * FROM trips ORDER BY ended_at DESC LIMIT 1").first(),
    env.DB.prepare(`${AI_SNAPSHOT_SELECT} ORDER BY s.captured_at DESC LIMIT ?`).bind(snapshotLimit).all(),
    fetchMergedVehicleStatus(env, env.WAYON_LEGACY_FIREBASE_DEVICE_ID || ""),
  ]);

  if (!state) return json({ error: "no_telemetry" }, 404);
  const raw = parseJsonObject(state.raw_json);
  const telemetryAgeSeconds = isoAgeSeconds(state.updated_at);
  const staleAfterSeconds = state.onroad ? 45 : 600;
  const location = validCoordinate(state.latitude) && validCoordinate(state.longitude) ? {
    latitude: nullableNumber(state.latitude),
    longitude: nullableNumber(state.longitude),
    bearingDeg: nullableNumber(state.bearing_deg),
    accuracyM: nullableNumber(state.gps_accuracy_m),
    source: raw.gps?.source || null,
    freshAtUpload: raw.gps?.fresh === true,
  } : null;
  const rawDevice = raw.device || {};
  const rawPanda = raw.panda || {};
  const aiPanda = buildAiPandaInterface(rawPanda);
  const rawVehicle = raw.vehicle || {};
  const rawOpenpilot = raw.openpilot || {};

  return json({
    schemaVersion: "wayon-ai-context-v1",
    generatedAt: nowIso(),
    access: {
      mode: "read-only",
      controlsAvailable: false,
      privacy: "Location and driver-camera images are sensitive. Use only for the user's explicit request.",
    },
    freshness: {
      telemetryUpdatedAt: state.updated_at,
      telemetryAgeSeconds,
      staleAfterSeconds,
      stale: telemetryAgeSeconds == null || telemetryAgeSeconds > staleAfterSeconds,
      expectedUploadIntervalSeconds: state.onroad ? 15 : 300,
    },
    live: {
      deviceId: state.device_id,
      dongleId: raw.dongleId || null,
      onroad: Boolean(state.onroad),
      ignition: Boolean(state.ignition),
      vehicle: {
        ...rawVehicle,
        speedMps: nullableNumber(state.speed_mps) ?? rawVehicle.speedMps ?? null,
        speedKph: state.speed_mps == null ? (rawVehicle.speedKph ?? null) : Number(state.speed_mps) * 3.6,
        location,
      },
      openpilot: {
        ...rawOpenpilot,
        enabled: Boolean(state.enabled),
      },
      electrical: {
        vehicleBusVoltageV: nullableNumber(state.voltage_v),
        vehicleCurrentMa: nullableNumber(state.current_ma),
        estimatedVehicleInputPowerW: nullableNumber(state.power_w),
        commaDevicePowerDrawW: nullableNumber(state.device_power_w),
        commaSomPowerDrawW: nullableNumber(rawDevice.power?.somDrawW),
        offroadEnergyUsedWh: nullableNumber(rawDevice.power?.offroadUsageWh),
        estimatedCarBatteryCapacityWh: nullableNumber(rawDevice.power?.carBatteryCapacityWh),
      },
      thermal: {
        status: state.thermal_status,
        fanPercent: state.fan_percent,
        temperaturesC: rawDevice.thermal?.temperaturesC || null,
      },
      system: {
        deviceType: rawDevice.type || null,
        usage: rawDevice.usage || null,
        network: rawDevice.network || null,
        screenBrightnessPercent: state.screen_brightness_percent,
      },
      commaInterface: aiPanda,
    },
    firebaseVehicleStatus,
    latestTrip: latestTrip ? parseTripRoute(latestTrip) : null,
    recentImpacts: (impactResult.results || []).map((impact) => aiImpact(request, impact)),
    recentVehicleEvents: (eventResult.results || []).map(aiVehicleEvent),
    recentSnapshots: (snapshotResult.results || []).map((snapshot) => aiSnapshot(request, snapshot)),
    rawTelemetry: {
      ...raw,
      panda: aiPanda,
    },
  });
}

async function handleAiTrips(request, env, pathname) {
  if (!authorizeAi(request, env)) return json({ error: "unauthorized" }, 401);

  const prefix = "/api/ai/trips/";
  if (pathname.startsWith(prefix) && pathname.length > prefix.length) {
    const tripId = decodeURIComponent(pathname.slice(prefix.length));
    const trip = await env.DB.prepare("SELECT * FROM trips WHERE id = ?").bind(tripId).first();
    if (!trip) return json({ error: "not_found" }, 404);
    return json({ schemaVersion: "wayon-ai-trip-v1", trip: parseTripRoute(trip) });
  }

  const url = new URL(request.url);
  const limit = boundedLimit(url.searchParams.get("limit"), 25, 250);
  const trips = await env.DB.prepare(`
    SELECT id, device_id, started_at, ended_at, duration_s, distance_m,
           start_lat, start_lon, end_lat, end_lon, route_point_count,
           CASE WHEN duration_s > 0 AND distance_m IS NOT NULL
                THEN distance_m / duration_s ELSE NULL END AS avg_speed_mps,
           route_json
    FROM trips ORDER BY ended_at DESC LIMIT ?
  `).bind(limit).all();
  return json({
    schemaVersion: "wayon-ai-trip-list-v1",
    generatedAt: nowIso(),
    trips: (trips.results || []).map(parseTripSummary),
  });
}

async function handleAiImpacts(request, env) {
  if (!authorizeAi(request, env)) return json({ error: "unauthorized" }, 401);
  const url = new URL(request.url);
  const limit = boundedLimit(url.searchParams.get("limit"), 25, 100);
  const result = await env.DB.prepare(`${AI_IMPACT_SELECT} ORDER BY detected_at DESC LIMIT ?`).bind(limit).all();
  return json({
    schemaVersion: "wayon-ai-impact-list-v1",
    generatedAt: nowIso(),
    impacts: (result.results || []).map((impact) => aiImpact(request, impact)),
  });
}

async function handleAiVehicleEvents(request, env) {
  if (!authorizeAi(request, env)) return json({ error: "unauthorized" }, 401);
  const url = new URL(request.url);
  const limit = boundedLimit(url.searchParams.get("limit"), 50, 250);
  const result = await env.DB.prepare(`
    SELECT id, device_id, event_type, occurred_at, received_at, locked, notified_count, raw_json
    FROM vehicle_events ORDER BY occurred_at DESC LIMIT ?
  `).bind(limit).all();
  return json({
    schemaVersion: "wayon-ai-vehicle-event-list-v1",
    generatedAt: nowIso(),
    events: (result.results || []).map(aiVehicleEvent),
  });
}

async function handleAiSnapshots(request, env) {
  if (!authorizeAi(request, env)) return json({ error: "unauthorized" }, 401);
  const url = new URL(request.url);
  const limit = boundedLimit(url.searchParams.get("limit"), 25, 100);
  const result = await env.DB.prepare(`${AI_SNAPSHOT_SELECT} ORDER BY s.captured_at DESC LIMIT ?`).bind(limit).all();
  return json({
    schemaVersion: "wayon-ai-snapshot-list-v1",
    generatedAt: nowIso(),
    snapshots: (result.results || []).map((snapshot) => aiSnapshot(request, snapshot)),
  });
}

async function handleAiImage(request, env, pathname) {
  if (!authorizeAi(request, env)) return json({ error: "unauthorized" }, 401);
  const prefix = "/api/ai/images/";
  const snapshotId = decodeURIComponent(pathname.slice(prefix.length));
  if (!snapshotId) return json({ error: "missing_snapshot_id" }, 400);
  const snapshot = await env.DB.prepare("SELECT kv_key FROM snapshots WHERE id = ?")
    .bind(snapshotId).first();
  if (!snapshot) return json({ error: "not_found" }, 404);
  const image = await env.SNAPSHOTS.get(snapshot.kv_key, "arrayBuffer");
  if (!image) return json({ error: "not_found" }, 404);
  return new Response(image, {
    headers: {
      ...CORS_HEADERS,
      "content-type": "image/jpeg",
      "cache-control": "private, max-age=300",
      "x-content-type-options": "nosniff",
    },
  });
}

export default {
  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    if (!requireBindings(env)) {
      return json({ error: "missing_cloudflare_bindings" }, 503);
    }

    const url = new URL(request.url);
    const { pathname } = url;

    if (request.method === "POST" && pathname === DEVICE_REGISTER_PATH) {
      return handleDeviceRegistration(request, env);
    }
    if (request.method === "GET" && pathname.startsWith(DEVICE_RELAY_PREFIX)) {
      const kind = pathname.slice(DEVICE_RELAY_PREFIX.length);
      return handleDeviceRelay(request, env, kind);
    }

    if (request.method === "POST" && pathname === REMOTE_SESSION_PATH) {
      return handleRemoteSession(request, env);
    }
    if (request.method === "GET" && pathname === REMOTE_SSH_PATH) {
      return handleRemoteSsh(request, env, ctx);
    }
    if (request.method === "POST" && pathname === LIVE_SESSION_PATH) {
      return handleLiveSession(request, env);
    }
    if (request.method === "GET" && pathname === LIVE_STREAM_PATH) {
      return handleLiveStream(request, env, ctx);
    }

    const gmoneCollector = constantTimeEqual(
      getBearerToken(request), env.WAYON_GMONE_TOKEN || "",
    );
    if (gmoneCollector && request.method === "POST" && pathname === "/api/gmone/status") {
      return handleGmoneStatus(request, env);
    }
    if (gmoneCollector && request.method === "GET" && pathname === "/api/gmone/refresh") {
      return handleGmoneRefreshPoll(request, env);
    }

    const separatelyAuthorized = pathname.startsWith("/api/ai/")
      || pathname.startsWith("/api/server-sync/");
    if (pathname.startsWith("/api/") && !separatelyAuthorized) {
      const identity = await authenticateDeviceKey(request, env);
      if (!identity) return json({ error: "unauthorized" }, 401);
      request = scopedDeviceRequest(request, identity.deviceId);
    }

    if (request.method === "POST" && pathname === "/api/telemetry") {
      return handleTelemetry(request, env);
    }
    if (request.method === "POST" && pathname === "/api/health-event") {
      return handleHealthEvent(request, env);
    }
    if (request.method === "POST" && pathname === "/api/ambient/command") {
      return handleAmbientCommandCreate(request, env);
    }
    if (request.method === "GET" && pathname === "/api/ambient/command") {
      return handleAmbientCommandPoll(request, env);
    }
    if (request.method === "POST" && pathname === "/api/ambient/ack") {
      return handleAmbientCommandAck(request, env);
    }
    if (request.method === "GET" && pathname === "/api/ambient/status") {
      return handleAmbientCommandStatus(request, env);
    }
    if (request.method === "POST" && pathname === "/api/gmone/status") {
      return handleGmoneStatus(request, env);
    }
    if (request.method === "POST" && pathname === "/api/gmone/refresh") {
      return handleGmoneRefreshRequest(request, env);
    }
    if (request.method === "GET" && pathname === "/api/gmone/refresh") {
      return handleGmoneRefreshPoll(request, env);
    }
    if (request.method === "POST" && pathname === "/api/snapshot") {
      return handleSnapshot(request, env);
    }
    if (request.method === "POST" && pathname === "/api/live-capture") {
      return handleLiveCaptureUpload(request, env);
    }
    if (request.method === "POST" && pathname === "/api/live-capture-part") {
      return handleLiveCapturePartUpload(request, env);
    }
    if (request.method === "POST" && pathname === "/api/live-capture-commit") {
      return handleLiveCaptureCommit(request, env);
    }
    if (request.method === "POST" && pathname === "/api/trips") {
      return handleTrip(request, env);
    }
    if (request.method === "POST" && pathname === "/api/impact") {
      return handleImpact(request, env);
    }
    if (request.method === "POST" && pathname === "/api/mobile/impact-suppression") {
      return handleImpactSuppression(request, env);
    }
    if (request.method === "POST" && pathname === "/api/impact-media") {
      return handleImpactMedia(request, env);
    }
    if (request.method === "POST" && pathname === "/api/vehicle-event") {
      return handleVehicleEvent(request, env);
    }
    if (request.method === "POST" && pathname === "/api/push/register") {
      return handlePushRegistration(request, env);
    }
    if (request.method === "POST" && pathname === "/api/push/test") {
      return handlePushTest(request, env);
    }
    if (request.method === "GET" && pathname === "/api/state") {
      return handleState(request, env);
    }
    if (request.method === "GET" && pathname === "/api/ai/context") {
      return handleAiContext(request, env);
    }
    if (request.method === "GET" && (pathname === "/api/ai/trips" || pathname.startsWith("/api/ai/trips/"))) {
      return handleAiTrips(request, env, pathname);
    }
    if (request.method === "GET" && pathname === "/api/server-sync/trips") {
      return handleServerSyncTrips(request, env);
    }
    if (request.method === "GET" && pathname === "/api/server-sync/impacts") {
      return handleServerSyncImpacts(request, env);
    }
    if (request.method === "GET" && pathname === "/api/server-sync/snapshots") {
      return handleServerSyncSnapshots(request, env);
    }
    if (request.method === "GET" && pathname === "/api/ai/impacts") {
      return handleAiImpacts(request, env);
    }
    if (request.method === "GET" && pathname === "/api/ai/events") {
      return handleAiVehicleEvents(request, env);
    }
    if (request.method === "GET" && pathname === "/api/ai/snapshots") {
      return handleAiSnapshots(request, env);
    }
    if (request.method === "GET" && pathname.startsWith("/api/ai/images/")) {
      return handleAiImage(request, env, pathname);
    }
    if (request.method === "GET" && (pathname === "/api/export" || pathname === "/api/json")) {
      return handleExport(request, env);
    }
    if (request.method === "GET" && pathname === "/api/snapshots") {
      return handleSnapshotsList(request, env);
    }
    if (request.method === "GET" && pathname === "/api/live-captures") {
      return handleLiveCaptures(request, env);
    }
    if (request.method === "GET" && pathname === "/api/live-capture") {
      return handleLiveCapture(request, env);
    }
    if (request.method === "GET" && pathname.startsWith("/api/trips")) {
      return handleTrips(request, env, pathname);
    }
    if (request.method === "GET" && pathname === "/api/impacts") {
      return handleImpacts(request, env);
    }
    if (request.method === "GET" && pathname === "/api/mobile/impacts") {
      return handleMobileImpacts(request, env);
    }
    if (request.method === "GET" && pathname === "/api/mobile/impact-image") {
      return handleMobileImpactImage(request, env);
    }
    if (request.method === "GET" && pathname === "/api/snapshot") {
      return handleSnapshotImage(request, env);
    }

    return env.ASSETS.fetch(request);
  },
};
