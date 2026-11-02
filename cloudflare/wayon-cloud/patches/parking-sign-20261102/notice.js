// WAYON_PARKING_SIGN_V1_BEGIN
const PARKING_SIGN_MAX_BODY = 32768;

function parkingSignObject(value, keys) {
  return value !== null && typeof value === "object" && !Array.isArray(value) &&
    Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
}

function parkingSignString(value, max) {
  return typeof value === "string" && value.length > 0 && [...value].length <= max &&
    value.trim() === value && !/[\p{Cc}\p{Cf}\p{Cs}\p{Zl}\p{Zp}]/u.test(value);
}

function parkingSignTimestamp(value) {
  if (!parkingSignString(value, 40)) return NaN;
  // Reuse the pinned batch parser's calendar, timezone and microsecond checks.
  return parkingBatchTimestamp(value);
}

function parkingSignMicros(value) {
  const fraction = /\.(\d{1,6})/.exec(value)?.[1] || "";
  return parkingSignTimestamp(value) * 1000 + Number(fraction.padEnd(6, "0").slice(3));
}

function parkingSignCanonicalTime(value) {
  const fraction = /\.(\d{1,6})/.exec(value)?.[1] || "";
  return new Date(parkingSignTimestamp(value)).toISOString().replace("Z", fraction.padEnd(6, "0").slice(3) + "Z");
}

function parkingSignInput(payload, deviceId, now = Date.now()) {
  if (!parkingSignObject(payload, ["eventId", "jobId", "deviceId", "parkedAt", "completedAt", "readings", "phaseHint", "test"]) ||
      !parkingSignString(payload.eventId, 128) || !/^[A-Za-z0-9_-]{1,128}$/.test(payload.eventId) ||
      !parkingSignString(payload.jobId, 32) || !/^[A-Fa-f0-9]{32}$/.test(payload.jobId) ||
      !parkingSignString(payload.deviceId, 128) || !validDeviceId(payload.deviceId) || payload.deviceId !== deviceId ||
      typeof payload.test !== "boolean" || !["approach", "parked", "mixed"].includes(payload.phaseHint) ||
      !Array.isArray(payload.readings) || payload.readings.length < 1 || payload.readings.length > 16) {
    return {error: "invalid_parking_recognition"};
  }
  const parkedMs = parkingSignTimestamp(payload.parkedAt);
  const completedMs = parkingSignTimestamp(payload.completedAt);
  if (!Number.isFinite(parkedMs) || !Number.isFinite(completedMs)) return {error: "invalid_parking_timestamp"};
  const parkedUs = parkingSignMicros(payload.parkedAt), completedUs = parkingSignMicros(payload.completedAt);
  if (now * 1000 - parkedUs > 1800000000 || now * 1000 - completedUs > 600000000 ||
      parkedUs > now * 1000 + 120000000 || completedUs > now * 1000 + 120000000 || completedUs < parkedUs) {
    return {error: "parking_time_out_of_bounds"};
  }
  const readings = [];
  const frameSources = new Map(), phases = new Set();
  for (const reading of payload.readings) {
    if (!parkingSignObject(reading, ["kind", "text", "status", "evidence"]) ||
        !["floor", "zone", "pillar", "bay"].includes(reading.kind) || reading.status !== "readable" ||
        !parkingSignString(reading.text, 32) || !Array.isArray(reading.evidence) ||
        reading.evidence.length < 2 || reading.evidence.length > 12) return {error: "invalid_parking_reading"};
    const indices = new Set();
    const evidence = [];
    for (const item of reading.evidence) {
      if (!parkingSignObject(item, ["frameIndex", "box", "capturedAt", "sha256", "phase"]) ||
          !Number.isInteger(item.frameIndex) || item.frameIndex < 0 || item.frameIndex > 11 ||
          indices.has(item.frameIndex) || !Array.isArray(item.box) || item.box.length !== 4 ||
          !item.box.every(n => typeof n === "number" && Number.isFinite(n) && n >= 0 && n <= 1) ||
          item.box[0] >= item.box[2] || item.box[1] >= item.box[3] ||
          !parkingSignString(item.sha256, 64) || !/^[a-f0-9]{64}$/.test(item.sha256) ||
          !["approach", "parked"].includes(item.phase)) return {error: "invalid_parking_evidence"};
      const captured = parkingSignMicros(item.capturedAt);
      const parked = parkingSignMicros(payload.parkedAt), completed = parkingSignMicros(payload.completedAt);
      if (!Number.isSafeInteger(captured) || captured < parked - 120000000 ||
          captured > Math.min(parked + 60000000, completed) ||
          (item.phase === "approach" && captured > parked)) return {error: "invalid_parking_evidence"};
      const capturedAt = parkingSignCanonicalTime(item.capturedAt);
      const source = JSON.stringify([capturedAt, item.sha256, item.phase]);
      if (frameSources.has(item.frameIndex) && frameSources.get(item.frameIndex) !== source) return {error: "invalid_parking_evidence"};
      frameSources.set(item.frameIndex, source);
      phases.add(item.phase);
      indices.add(item.frameIndex);
      evidence.push({frameIndex: item.frameIndex, box: [...item.box], capturedAt, sha256: item.sha256, phase: item.phase});
    }
    if (!evidence.some(a => evidence.some(b => a.sha256 !== b.sha256 &&
        Math.abs(parkingSignMicros(a.capturedAt) - parkingSignMicros(b.capturedAt)) >= 500000))) {
      return {error: "uncorroborated_parking_reading"};
    }
    evidence.sort((a, b) => a.frameIndex - b.frameIndex);
    readings.push({kind: reading.kind, text: reading.text, status: "readable", evidence});
  }
  const phaseHint = phases.size === 1 ? [...phases][0] : "mixed";
  if (payload.phaseHint !== phaseHint) return {error: "parking_phase_conflict"};
  // Explicit field order makes retries independent of JSON object key order.
  return {value: {
    eventId: payload.eventId, jobId: payload.jobId.toLowerCase(), deviceId,
    parkedAt: parkingSignCanonicalTime(payload.parkedAt), completedAt: parkingSignCanonicalTime(payload.completedAt),
    readings, phaseHint: payload.phaseHint, test: payload.test,
  }};
}

function parkingSignData(payload) {
  const labels = {floor: "\uCE35", zone: "\uAD6C\uC5ED", pillar: "\uAE30\uB465", bay: "\uC8FC\uCC28\uBA74"};
  // Limit visible text (not persisted evidence) so both FCM copies fit its budget.
  const summary = payload.readings.slice(0, 3).map(r => `${labels[r.kind]} ${r.text}`).join(" \u00B7 ");
  const more = payload.readings.length > 3 ? ` \uC678 ${payload.readings.length - 3}\uAC74` : "";
  const warning = payload.phaseHint === "approach" ? " \u00B7 \uC8FC\uCC28 \uC804 \uC811\uADFC \uC911 \uBCF8 \uD45C\uC9C0" :
    payload.phaseHint === "mixed" ? " \u00B7 \uC811\uADFC \uC911 \uBCF8 \uD45C\uC9C0 \uD3EC\uD568" : "";
  return {
    type: "wayon_parking_sign", parkingEventId: payload.eventId, jobId: payload.jobId,
    deviceId: payload.deviceId, occurredAt: new Date(parkingSignTimestamp(payload.completedAt)).toISOString(),
    notificationTitle: "\uC8FC\uCC28 \uC8FC\uBCC0 \uD45C\uC9C0 \uC778\uC2DD" + (payload.test ? " \uD14C\uC2A4\uD2B8" : ""),
    notificationBody: summary + more + " \u00B7 AI \uD310\uB3C5, \uC815\uD655\uD55C \uC8FC\uCC28 \uC704\uCE58\uB294 \uC544\uB2D8" + warning,
    test: String(payload.test),
  };
}

async function parkingSignBody(request) {
  const length = request.headers.get("content-length");
  if (length !== null && (!/^\d+$/.test(length) || Number(length) > PARKING_SIGN_MAX_BODY)) {
    return {error: "parking_body_too_large", status: 413};
  }
  if (request.headers.get("content-type")?.split(";")[0].trim().toLowerCase() !== "application/json") {
    return {error: "json_required", status: 415};
  }
  if (!request.body) return {error: "invalid_json", status: 400};
  const reader = request.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    for (;;) {
      const {value, done} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > PARKING_SIGN_MAX_BODY) {
        await reader.cancel();
        return {error: "parking_body_too_large", status: 413};
      }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    return {value: JSON.parse(new TextDecoder("utf-8", {fatal: true}).decode(bytes))};
  } catch (_) {
    return {error: "invalid_json", status: 400};
  } finally { reader.releaseLock(); }
}

async function handleParkingRecognition(request, env, ctx) {
  const secret = env.WAYON_PARKING_NOTIFY_TOKEN;
  const deviceId = env.WAYON_AI_DEVICE_ID || env.WAYON_LEGACY_FIREBASE_DEVICE_ID;
  // No device-key fallback, caller scope, or empty-secret authentication.
  if (typeof secret !== "string" || !secret || secret.trim() !== secret ||
      secret === env.WAYON_AI_READ_TOKEN || !constantTimeEqual(getBearerToken(request), secret) ||
      !parkingSignString(deviceId, 128) || !validDeviceId(deviceId)) return json({error: "unauthorized"}, 401);
  if (request.method !== "POST") return json({error: "method_not_allowed"}, 405);
  let device;
  try {
    device = await env.DB.prepare("SELECT device_id FROM wayon_devices WHERE device_id = ? AND revoked_at IS NULL")
      .bind(deviceId).first();
  } catch (_) { return json({error: "notification_unavailable"}, 503); }
  if (!device) return json({error: "unauthorized"}, 401);
  const body = await parkingSignBody(request);
  if (body.error) return json({error: body.error}, body.status);
  const input = parkingSignInput(body.value, deviceId);
  if (input.error) return json({error: input.error}, 400);
  if (!ctx || typeof ctx.waitUntil !== "function") return json({error: "notification_unavailable"}, 503);
  const payload = input.value;
  const raw = JSON.stringify(payload);
  const fingerprint = await sha256Hex(raw);
  const test = payload.test ? 1 : 0;
  let inserted;
  try {
    // The durable claim is never deleted or reopened, even after uncertain send outcomes.
    inserted = await env.DB.prepare(`
      INSERT INTO parking_sign_notifications (
        device_id, event_id, test, job_id, parked_at, completed_at, claimed_at,
        payload_sha256, payload_json, notified_count
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, -1)
      ON CONFLICT(device_id, event_id, test) DO NOTHING
    `).bind(deviceId, payload.eventId, test, payload.jobId, payload.parkedAt, payload.completedAt,
      nowIso(), fingerprint, raw).run();
    if (!inserted.success || ![0, 1].includes(inserted.meta?.changes)) throw new Error("claim_unconfirmed");
    if (!inserted.meta.changes) {
      const existing = await env.DB.prepare(`
        SELECT payload_sha256 FROM parking_sign_notifications WHERE device_id = ? AND event_id = ? AND test = ?
      `).bind(deviceId, payload.eventId, test).first();
      if (!existing || existing.payload_sha256 !== fingerprint) return json({error: "parking_event_conflict"}, 409);
      return json({ok: true, claimed: true, status: "duplicate", eventId: payload.eventId,
        accepted: true, duplicate: true, parkingEventId: payload.eventId, jobId: payload.jobId, test: payload.test}, 202);
    }
  } catch (_) { return json({error: "notification_unavailable"}, 503); }
  ctx.waitUntil((async () => {
    let sent = -2;
    try {
      const result = await sendDataNotifications(env, deviceId, parkingSignData(payload));
      sent = result.failed || result.invalid ? -2 : result.sent;
    } catch (_) { console.warn("Parking sign notification delivery uncertain"); }
    try {
      await env.DB.prepare(`UPDATE parking_sign_notifications SET notified_count = ?, finished_at = ?
        WHERE device_id = ? AND event_id = ? AND test = ? AND payload_sha256 = ?`)
        .bind(sent, nowIso(), deviceId, payload.eventId, test, fingerprint).run();
    } catch (_) { console.warn("Parking sign notification receipt update failed"); }
  })());
  return json({ok: true, claimed: true, status: "accepted", eventId: payload.eventId,
    accepted: true, duplicate: false, parkingEventId: payload.eventId, jobId: payload.jobId, test: payload.test}, 202);
}
// WAYON_PARKING_SIGN_V1_END
