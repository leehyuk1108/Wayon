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
const REMOTE_BOOTSTRAP_PATH = "/api/remote/bootstrap";
const REMOTE_SESSION_PATH = "/api/remote/session";
const REMOTE_SSH_PATH = "/api/remote/ssh";
const REMOTE_SSH_PROTOCOL_PREFIX = "wayon-ssh-v1";
const REMOTE_SSH_MAX_AGE_SECONDS = 60;
const REMOTE_SSH_TARGET = "172.31.255.254:22";
const FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging";
const FCM_TOKEN_URL = "https://oauth2.googleapis.com/token";
let cachedFcmAccessToken = null;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: JSON_HEADERS,
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

export async function issueRemoteSshProtocol(
  sessionSecret,
  nowSeconds = Math.floor(Date.now() / 1000),
) {
  const nonceBytes = new Uint8Array(16);
  crypto.getRandomValues(nonceBytes);
  const nonce = bytesToHex(nonceBytes);
  const key = await importHmacKey(sessionSecret, "sign");
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(`${nowSeconds}:${nonce}`),
  );
  return `${REMOTE_SSH_PROTOCOL_PREFIX}.${nowSeconds}.${nonce}.${bytesToHex(new Uint8Array(signature))}`;
}

export async function verifyRemoteSshProtocol(
  header,
  sessionSecret,
  nowSeconds = Math.floor(Date.now() / 1000),
) {
  if (!header || !sessionSecret) return "";

  const protocol = header.split(",").map((value) => value.trim())
    .find((value) => value.startsWith(`${REMOTE_SSH_PROTOCOL_PREFIX}.`));
  if (!protocol) return "";

  const parts = protocol.split(".");
  if (parts.length !== 4 || parts[0] !== REMOTE_SSH_PROTOCOL_PREFIX) return "";
  const timestamp = Number.parseInt(parts[1], 10);
  const nonce = parts[2];
  const signature = hexToBytes(parts[3]);
  if (!Number.isFinite(timestamp) || Math.abs(nowSeconds - timestamp) > REMOTE_SSH_MAX_AGE_SECONDS) return "";
  if (!/^[0-9a-f]{32}$/i.test(nonce) || !signature || signature.length !== 32) return "";

  const encoder = new TextEncoder();
  const key = await importHmacKey(sessionSecret, "verify");
  const valid = await crypto.subtle.verify(
    "HMAC",
    key,
    signature,
    encoder.encode(`${timestamp}:${nonce}`),
  );
  return valid ? protocol : "";
}

function basicCredentials(request) {
  const header = request.headers.get("authorization") || "";
  if (!header.toLowerCase().startsWith("basic ")) return null;

  try {
    const decoded = atob(header.slice(6).trim());
    const separator = decoded.indexOf(":");
    if (separator < 1) return null;
    return {
      username: decoded.slice(0, separator),
      password: decoded.slice(separator + 1),
    };
  } catch {
    return null;
  }
}

async function handleRemoteSession(request, env) {
  if (!env.WAYON_SSH_USERNAME || !env.WAYON_SSH_PASSWORD || !env.WAYON_SSH_SESSION_SECRET) {
    return json({ error: "remote_access_unavailable" }, 503);
  }

  const credentials = basicCredentials(request);
  if (!credentials
      || !constantTimeEqual(credentials.username, env.WAYON_SSH_USERNAME)
      || !constantTimeEqual(credentials.password, env.WAYON_SSH_PASSWORD)) {
    return new Response(JSON.stringify({ error: "unauthorized" }), {
      status: 401,
      headers: {
        ...JSON_HEADERS,
        "www-authenticate": "Basic realm=\"Wayon Remote SSH\", charset=\"UTF-8\"",
      },
    });
  }

  const issuedAt = Math.floor(Date.now() / 1000);
  return json({
    protocol: await issueRemoteSshProtocol(env.WAYON_SSH_SESSION_SECRET, issuedAt),
    expiresAt: issuedAt + REMOTE_SSH_MAX_AGE_SECONDS,
  });
}

function handleRemoteBootstrap(request, env) {
  if (!authorize(request, env, true)) {
    return json({ error: "unauthorized" }, 401);
  }
  if (!env.WAYON_TUNNEL_TOKEN) {
    return json({ error: "remote_access_unavailable" }, 503);
  }

  return json({ tunnelToken: env.WAYON_TUNNEL_TOKEN });
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

async function handleRemoteSsh(request, env, ctx) {
  if ((request.headers.get("upgrade") || "").toLowerCase() !== "websocket") {
    return json({ error: "websocket_required" }, 426);
  }
  if (!env.COMMA_NETWORK || !env.WAYON_SSH_SESSION_SECRET) {
    return json({ error: "remote_access_unavailable" }, 503);
  }

  const protocol = await verifyRemoteSshProtocol(
    request.headers.get("sec-websocket-protocol") || "",
    env.WAYON_SSH_SESSION_SECRET,
  );
  if (!protocol) return json({ error: "unauthorized" }, 401);

  let socket;
  try {
    socket = env.COMMA_NETWORK.connect(REMOTE_SSH_TARGET);
    await socket.opened;
  } catch (error) {
    console.error("Wayon remote SSH origin connection failed", error);
    try { socket?.close(); } catch {}
    return json({ error: "comma_offline" }, 503);
  }

  const pair = new WebSocketPair();
  const [client, server] = Object.values(pair);
  server.accept();

  const writer = socket.writable.getWriter();
  let clientWriteQueue = Promise.resolve();
  let closed = false;
  const close = () => {
    if (closed) return;
    closed = true;
    try { socket.close(); } catch {}
    try { server.close(1000, "closed"); } catch {}
  };

  server.addEventListener("message", (event) => {
    if (closed) return;
    clientWriteQueue = clientWriteQueue.then(async () => {
      const bytes = await websocketBytes(event.data);
      if (!bytes) throw new TypeError("unsupported WebSocket message");
      await writer.write(bytes);
    }).catch((error) => {
      console.error("Wayon remote SSH client write failed", error);
      close();
    });
  });
  server.addEventListener("close", close);
  server.addEventListener("error", close);

  ctx.waitUntil((async () => {
    const reader = socket.readable.getReader();
    try {
      while (!closed) {
        const { value, done } = await reader.read();
        if (done) break;
        if (server.readyState === 1) server.send(value);
      }
    } catch {
      // The SSH client will report the closed transport.
    } finally {
      try { reader.releaseLock(); } catch {}
      close();
    }
  })());

  return new Response(null, {
    status: 101,
    webSocket: client,
    headers: { "Sec-WebSocket-Protocol": protocol },
  });
}

function authorize(request, env, write = false) {
  const token = getBearerToken(request);
  const uploadToken = env.WAYON_UPLOAD_TOKEN || "";
  const viewToken = env.WAYON_VIEW_TOKEN || uploadToken;

  if (write) {
    return constantTimeEqual(token, uploadToken);
  }
  return constantTimeEqual(token, viewToken) || constantTimeEqual(token, uploadToken);
}

function authorizePushRegistration(request, env) {
  return constantTimeEqual(getBearerToken(request), env.WAYON_PUSH_REGISTRATION_TOKEN || "");
}

function authorizeAi(request, env) {
  return constantTimeEqual(getBearerToken(request), env.WAYON_AI_READ_TOKEN || "");
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

async function fetchVehicleStatus() {
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
  const deviceId = String(payload.deviceId || "unknown");
  const updatedAt = payload.updatedAt || nowIso();
  const gps = await resolveTelemetryGps(env, deviceId, payload.gps || {});
  payload.gps = gps;
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
  const response = await fetch(
    `https://fcm.googleapis.com/v1/projects/${encodeURIComponent(env.FCM_PROJECT_ID)}/messages:send`,
    {
      method: "POST",
      headers: {
        authorization: `Bearer ${accessToken}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        message: {
          token,
          data,
          android: {
            priority: "HIGH",
            ttl: "300s",
          },
        },
      }),
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
  const deviceId = String(payload.deviceId || "unknown").slice(0, 128);
  const detectedAt = String(payload.detectedAt || nowIso()).slice(0, 64);
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
  const deviceId = String(payload.deviceId || "").slice(0, 128);
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
  const deviceId = String(payload.deviceId || "unknown").slice(0, 128);
  const occurredAt = String(payload.occurredAt || nowIso()).slice(0, 64);
  const receivedAt = nowIso();
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
    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?)
  `).bind(
    id,
    deviceId,
    eventType,
    occurredAt,
    receivedAt,
    locked == null ? null : toInt(locked),
    JSON.stringify(payload),
  ).run();

  if (!inserted.meta?.changes) {
    const existing = await env.DB.prepare("SELECT notified_count FROM vehicle_events WHERE id = ?")
      .bind(id).first();
    if (Number(existing?.notified_count || 0) > 0) {
      return json({ ok: true, id, duplicate: true, notified: existing.notified_count });
    }
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
    throw new Error("FCM delivery failed; vehicle event remains pending");
  }
  await env.DB.prepare("UPDATE vehicle_events SET notified_count = ? WHERE id = ?")
    .bind(notification.sent, id).run();
  return json({ ok: true, id, duplicate: !inserted.meta?.changes, notified: notification.sent });
}

async function handlePushRegistration(request, env) {
  if (!authorizePushRegistration(request, env)) return json({ error: "unauthorized" }, 401);

  const payload = await request.json();
  const token = String(payload.fcmToken || "").trim();
  const deviceId = String(payload.deviceId || "*").trim().slice(0, 128) || "*";
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
    deviceId: String(payload.deviceId || "*"),
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
  const limit = Math.max(1, Math.min(100, Number.parseInt(url.searchParams.get("limit") || "25", 10)));
  const impacts = await env.DB.prepare(`
    SELECT id, device_id, detected_at, received_at, severity, peak_dynamic_g,
           peak_total_g, peak_jerk_g_per_s, peak_gyro_rad_per_s, duration_ms,
           sample_count, sensor_clipped, latitude, longitude, capture_status,
           captured_at, capture_attempts, wide_snapshot_id, driver_snapshot_id,
           notified_count
    FROM impact_events ORDER BY detected_at DESC LIMIT ?
  `).bind(limit).all();
  return json({ impacts: impacts.results || [] });
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
  const deviceId = String(payload.deviceId || "unknown");
  const capturedAt = payload.capturedAt || nowIso();

  const saved = [];
  const driver = await saveSnapshotImage(env, deviceId, "driver", capturedAt, payload.driverJpegBase64);
  const wide = await saveSnapshotImage(env, deviceId, "wide", capturedAt, payload.wideJpegBase64);
  if (driver) saved.push(driver);
  if (wide) saved.push(wide);

  return json({ ok: true, snapshots: saved });
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
  const deviceId = String(payload.deviceId || "unknown");

  await env.DB.prepare(`
    INSERT OR REPLACE INTO trips (
      id, device_id, started_at, ended_at, duration_s, distance_m, start_lat,
      start_lon, end_lat, end_lon, route_point_count, route_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    nowIso(),
  ).run();

  return json({ ok: true, id });
}

async function handleState(request, env) {
  if (!authorize(request, env, false)) {
    return json({ error: "unauthorized" }, 401);
  }

  const [state, snapshots, vehicleStatus] = await Promise.all([
    env.DB.prepare(`
      SELECT * FROM latest_state ORDER BY updated_at DESC LIMIT 1
    `).first(),
    env.DB.prepare(`
      SELECT s.id, s.device_id, s.camera, s.captured_at, s.kv_key, s.size_bytes,
             i.id AS impact_id, i.severity AS impact_severity,
             i.peak_dynamic_g AS impact_peak_dynamic_g,
             i.peak_total_g AS impact_peak_total_g,
             i.detected_at AS impact_detected_at
      FROM snapshots s
      LEFT JOIN impact_events i
        ON s.id = i.wide_snapshot_id OR s.id = i.driver_snapshot_id
      ORDER BY s.captured_at DESC LIMIT 12
    `).all(),
    fetchVehicleStatus(),
  ]);

  return json({ state, snapshots: snapshots.results || [], vehicleStatus });
}

function parseTripRoute(trip) {
  const { route_json: routeJson, ...rest } = trip;
  return {
    ...rest,
    route: JSON.parse(routeJson || "[]"),
  };
}

function maxRouteSpeedMps(routeJson) {
  let maxSpeed = null;
  try {
    const route = JSON.parse(routeJson || "[]");
    for (const point of route) {
      const speed = Number(point?.speedMps ?? point?.speed_mps ?? point?.speed);
      if (Number.isFinite(speed)) {
        maxSpeed = Math.max(maxSpeed ?? speed, speed);
      }
    }
  } catch {
    return null;
  }
  return maxSpeed;
}

function parseTripSummary(trip) {
  const { route_json: routeJson, ...rest } = trip;
  return {
    ...rest,
    max_speed_mps: maxRouteSpeedMps(routeJson),
  };
}

async function handleExport(request, env) {
  if (!authorize(request, env, false)) {
    return json({ error: "unauthorized" }, 401);
  }

  const [state, snapshots, trips, vehicleStatus] = await Promise.all([
    env.DB.prepare(`
      SELECT * FROM latest_state ORDER BY updated_at DESC LIMIT 1
    `).first(),
    env.DB.prepare(`
      SELECT id, device_id, camera, captured_at, kv_key, size_bytes, created_at
      FROM snapshots ORDER BY captured_at DESC LIMIT 24
    `).all(),
    env.DB.prepare(`
      SELECT * FROM trips ORDER BY ended_at DESC LIMIT 25
    `).all(),
    fetchVehicleStatus(),
  ]);

  return json({
    generatedAt: nowIso(),
    state,
    vehicleStatus,
    snapshots: snapshots.results || [],
    trips: (trips.results || []).map(parseTripRoute),
  });
}

async function handleSnapshotsList(request, env) {
  if (!authorize(request, env, false)) {
    return json({ error: "unauthorized" }, 401);
  }

  const url = new URL(request.url);
  const limit = boundedLimit(url.searchParams.get("limit"), 500, 1000);
  const date = url.searchParams.get("date");
  const dateWhere = date ? "WHERE date(s.captured_at, '+9 hours') = ?" : "";
  const snapshotQuery = `
    SELECT s.id, s.device_id, s.camera, s.captured_at, s.kv_key, s.size_bytes, s.created_at,
           i.id AS impact_id, i.severity AS impact_severity,
           i.peak_dynamic_g AS impact_peak_dynamic_g,
           i.peak_total_g AS impact_peak_total_g,
           i.detected_at AS impact_detected_at
    FROM snapshots s
    LEFT JOIN impact_events i
      ON s.id = i.wide_snapshot_id OR s.id = i.driver_snapshot_id
    ${dateWhere}
    ORDER BY s.captured_at DESC LIMIT ?
  `;
  const snapshots = date
    ? await env.DB.prepare(snapshotQuery).bind(date, limit).all()
    : await env.DB.prepare(snapshotQuery).bind(limit).all();
  const days = await env.DB.prepare(`
    SELECT date(captured_at, '+9 hours') AS date, COUNT(*) AS count
    FROM snapshots GROUP BY date ORDER BY date DESC
  `).all();
  const total = await env.DB.prepare(`SELECT COUNT(*) AS count FROM snapshots`).first();

  return json({
    generatedAt: nowIso(),
    snapshots: snapshots.results || [],
    days: days.results || [],
    total: total?.count || 0,
    limit,
  });
}

async function handleTrips(request, env, pathname) {
  if (!authorize(request, env, false)) {
    return json({ error: "unauthorized" }, 401);
  }

  const parts = pathname.split("/").filter(Boolean);
  if (parts.length === 3) {
    const trip = await env.DB.prepare(`SELECT * FROM trips WHERE id = ?`)
      .bind(parts[2])
      .first();
    if (!trip) return json({ error: "not_found" }, 404);

    return json({
      ...trip,
      route: JSON.parse(trip.route_json || "[]"),
    });
  }

  const url = new URL(request.url);
  const limit = boundedLimit(url.searchParams.get("limit"), 100, 1000);
  const trips = await env.DB.prepare(`
    SELECT id, device_id, started_at, ended_at, duration_s, distance_m,
           start_lat, start_lon, end_lat, end_lon, route_point_count,
           CASE
             WHEN duration_s > 0 AND distance_m IS NOT NULL THEN distance_m / duration_s
             ELSE NULL
           END AS avg_speed_mps,
           route_json
    FROM trips ORDER BY ended_at DESC LIMIT ?
  `).bind(limit).all();

  return json({ trips: (trips.results || []).map(parseTripSummary) });
}

async function handleSnapshotImage(request, env) {
  if (!authorize(request, env, false)) {
    return json({ error: "unauthorized" }, 401);
  }

  const url = new URL(request.url);
  const key = url.searchParams.get("key");
  if (!key) return json({ error: "missing_key" }, 400);

  const image = await env.SNAPSHOTS.get(key, "arrayBuffer");
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
         i.id AS impact_id, i.severity AS impact_severity,
         i.peak_dynamic_g AS impact_peak_dynamic_g,
         i.peak_total_g AS impact_peak_total_g,
         i.detected_at AS impact_detected_at
  FROM snapshots s
  LEFT JOIN impact_events i
    ON s.id = i.wide_snapshot_id OR s.id = i.driver_snapshot_id
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
    fetchVehicleStatus(),
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
      commaInterface: rawPanda,
    },
    firebaseVehicleStatus,
    latestTrip: latestTrip ? parseTripRoute(latestTrip) : null,
    recentImpacts: (impactResult.results || []).map((impact) => aiImpact(request, impact)),
    recentVehicleEvents: (eventResult.results || []).map(aiVehicleEvent),
    recentSnapshots: (snapshotResult.results || []).map((snapshot) => aiSnapshot(request, snapshot)),
    rawTelemetry: raw,
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

    if (request.method === "GET" && pathname === REMOTE_BOOTSTRAP_PATH) {
      return handleRemoteBootstrap(request, env);
    }
    if (request.method === "POST" && pathname === REMOTE_SESSION_PATH) {
      return handleRemoteSession(request, env);
    }
    if (request.method === "GET" && pathname === REMOTE_SSH_PATH) {
      return handleRemoteSsh(request, env, ctx);
    }

    if (request.method === "POST" && pathname === "/api/telemetry") {
      return handleTelemetry(request, env);
    }
    if (request.method === "POST" && pathname === "/api/snapshot") {
      return handleSnapshot(request, env);
    }
    if (request.method === "POST" && pathname === "/api/trips") {
      return handleTrip(request, env);
    }
    if (request.method === "POST" && pathname === "/api/impact") {
      return handleImpact(request, env);
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
