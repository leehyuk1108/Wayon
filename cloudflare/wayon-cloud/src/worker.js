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
const REMOTE_SSH_TARGET = "127.0.0.1:22";

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

function websocketBytes(data) {
  if (data instanceof ArrayBuffer) return new Uint8Array(data);
  if (ArrayBuffer.isView(data)) return new Uint8Array(data.buffer, data.byteOffset, data.byteLength);
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
    socket = await env.COMMA_NETWORK.connect(REMOTE_SSH_TARGET);
  } catch {
    return json({ error: "comma_offline" }, 503);
  }

  const pair = new WebSocketPair();
  const [client, server] = Object.values(pair);
  server.accept();

  const writer = socket.writable.getWriter();
  let writeQueue = Promise.resolve();
  let closed = false;
  const close = () => {
    if (closed) return;
    closed = true;
    try { socket.close(); } catch {}
    try { server.close(1000, "closed"); } catch {}
  };

  server.addEventListener("message", (event) => {
    const bytes = websocketBytes(event.data);
    if (!bytes) {
      close();
      return;
    }
    writeQueue = writeQueue.then(() => writer.write(bytes)).catch(close);
    ctx.waitUntil(writeQueue);
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
      SELECT id, device_id, camera, captured_at, kv_key, size_bytes
      FROM snapshots ORDER BY captured_at DESC LIMIT 12
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
  const dateWhere = date ? "WHERE date(captured_at, '+9 hours') = ?" : "";
  const snapshotQuery = `
    SELECT id, device_id, camera, captured_at, kv_key, size_bytes, created_at
    FROM snapshots ${dateWhere}
    ORDER BY captured_at DESC LIMIT ?
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
    if (request.method === "GET" && pathname === "/api/state") {
      return handleState(request, env);
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
    if (request.method === "GET" && pathname === "/api/snapshot") {
      return handleSnapshotImage(request, env);
    }

    return env.ASSETS.fetch(request);
  },
};
