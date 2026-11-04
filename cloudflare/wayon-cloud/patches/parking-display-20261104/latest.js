// WAYON_PARKING_DISPLAY_V1_BEGIN
const PARKING_DISPLAY_MAX_BYTES = 196608;
const PARKING_DISPLAY_TTL = 7 * 24 * 60 * 60;
const PARKING_DISPLAY_TIMEOUT_MS = 5000;

function parkingDisplayCheck(condition) {
  if (!condition) throw new Error("parking_display_invalid");
}

function parkingDisplayObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function parkingDisplayProduction(payload) {
  const pending = [payload];
  const flags = new Set(["test", "istest", "testmode", "testonly", "simulation", "issimulation", "simulated", "issimulated", "synthetic", "issynthetic", "dryrun"]);
  const provenance = new Set(["source", "mode", "origin", "recordtype", "jobtype", "environment", "namespace", "jobid", "eventid"]);
  while (pending.length) {
    const item = pending.pop();
    if (!item || typeof item !== "object") continue;
    for (const [name, value] of Object.entries(item)) {
      const key = name.toLowerCase().replace(/[_-]/g, "");
      if (flags.has(key)) parkingDisplayCheck(value === false || value === null || value === 0 || value === "");
      if (provenance.has(key) && typeof value === "string") {
        parkingDisplayCheck(!/(?:^|[^a-z0-9])(?:test|simulation|simulated|synthetic|snapshot|replay|dryrun)(?:$|[^a-z0-9])/i.test(value));
      }
      if (value && typeof value === "object") pending.push(value);
    }
  }
}

function parkingDisplayText(value, max) {
  parkingDisplayCheck(typeof value === "string" && value.trim().length > 0 &&
    Array.from(value).length <= max && !/[\p{Cc}\p{Cf}\p{Cs}\p{Zl}\p{Zp}]/u.test(value));
  return value;
}

function parkingDisplayList(value, max) {
  parkingDisplayCheck(Array.isArray(value) && value.length <= max);
  return value;
}

function parkingDisplayTime(value) {
  const time = parkingBatchTimestamp(value);
  parkingDisplayCheck(Number.isFinite(time));
  return time;
}

function parkingDisplayEvidence(value, frameCount) {
  const indices = new Set();
  const evidence = parkingDisplayList(value, 12).map(item => {
    parkingDisplayCheck(parkingDisplayObject(item) && Number.isInteger(item.frameIndex) &&
      item.frameIndex >= 0 && item.frameIndex < frameCount && !indices.has(item.frameIndex));
    const box = parkingDisplayList(item.box, 4);
    parkingDisplayCheck(box.length === 4 && box.every(n => typeof n === "number" && Number.isFinite(n) && n >= 0 && n <= 1) &&
      box[0] < box[2] && box[1] < box[3]);
    indices.add(item.frameIndex);
    return {frameIndex: item.frameIndex, box: [...box]};
  });
  parkingDisplayCheck(evidence.length > 0);
  return evidence;
}

function parkingDisplayReading(item, frameCount, inspected) {
  parkingDisplayCheck(parkingDisplayObject(item) && ["floor", "zone", "pillar", "bay", "unknown"].includes(item.kind) &&
    ["readable", "ambiguous"].includes(item.status));
  const alternatives = parkingDisplayList(item.alternatives, 4).map(text => parkingDisplayText(text, 32));
  const evidence = parkingDisplayEvidence(item.evidence, frameCount);
  const text = item.status === "readable" ? parkingDisplayText(item.text, 32) : null;
  parkingDisplayCheck(item.status === "readable" ? alternatives.length === 0 && evidence.length >= 2 : item.text === null);
  const result = {kind: item.kind, text, status: item.status, alternatives, evidence};
  if (inspected) {
    parkingDisplayCheck((item.status === "readable" ? ["baseline", "corroborated", "additional"] : ["conflict", "uncertain"]).includes(item.confidence));
    result.confidence = item.confidence;
  }
  return result;
}

function parkingDisplayInspection(item, frameCount) {
  parkingDisplayCheck(parkingDisplayObject(item) && item.version === 1 &&
    ["completed", "failed", "skipped", "pending"].includes(item.status) &&
    item.exactParkingSpotKnown === false && item.humanVerified === false);
  const readings = parkingDisplayList(item.readings, 32).map(r => parkingDisplayReading(r, frameCount, true));
  const surroundings = parkingDisplayList(item.surroundings, 3).map(feature => {
    parkingDisplayCheck(parkingDisplayObject(feature) &&
      ["door", "shutter", "vent", "fence", "stairs", "pipe", "parking_line"].includes(feature.type) &&
      ["unknown", "white", "gray", "black", "red", "orange", "yellow", "green", "blue"].includes(feature.color));
    const evidence = parkingDisplayEvidence(feature.evidence, frameCount);
    parkingDisplayCheck(evidence.length >= 2);
    return {type: feature.type, color: feature.color, label: parkingDisplayText(feature.label, 96), evidence};
  });
  parkingDisplayCheck(item.status === "completed" || (readings.length === 0 && surroundings.length === 0));
  const result = {version: 1, status: item.status, readings, surroundings};
  if (Object.hasOwn(item, "coverage")) {
    parkingDisplayCheck(parkingDisplayObject(item.coverage) && item.coverage.completeSceneGuaranteed === false);
    const coverage = {completeSceneGuaranteed: false};
    for (const key of ["overviewViews", "overviewExpected", "targetsRequested", "targetsInspected"]) {
      if (Object.hasOwn(item.coverage, key)) {
        const count = item.coverage[key];
        parkingDisplayCheck(Number.isInteger(count) && count >= 0 && count <= 96);
        coverage[key] = count;
      }
    }
    parkingDisplayCheck(!(coverage.overviewViews > coverage.overviewExpected) && !(coverage.targetsInspected > coverage.targetsRequested));
    result.coverage = coverage;
  }
  return {...result, exactParkingSpotKnown: false, humanVerified: false};
}

function parkingDisplayResult(source) {
  parkingDisplayCheck(parkingDisplayObject(source) && parkingDisplayObject(source.analysis) && source.analysis.exactParkingSpotKnown === false);
  const frames = parkingDisplayList(source.frames, 12).map(frame => {
    parkingDisplayCheck(parkingDisplayObject(frame) && ["road", "wide"].includes(frame.camera));
    parkingDisplayTime(frame.capturedAt);
    const result = {capturedAt: frame.capturedAt, camera: frame.camera};
    if (Object.hasOwn(frame, "phase")) {
      parkingDisplayCheck(["approach", "parked"].includes(frame.phase));
      result.phase = frame.phase;
    }
    for (const key of ["width", "height"]) {
      if (Object.hasOwn(frame, key)) {
        parkingDisplayCheck(Number.isInteger(frame[key]) && frame[key] >= 64 && frame[key] <= 4096);
        result[key] = frame[key];
      }
    }
    return result;
  });
  const analysis = {readings: parkingDisplayList(source.analysis.readings, 16).map(r => parkingDisplayReading(r, frames.length, false)),
    exactParkingSpotKnown: false};
  const result = {analysis, frames};
  if (Object.hasOwn(source, "inspection")) result.inspection = source.inspection === null ? null : parkingDisplayInspection(source.inspection, frames.length);
  return result;
}

function parkingDisplayPayload(payload, deviceId) {
  parkingDisplayCheck(parkingDisplayObject(payload) && payload.schemaVersion === "wayon-parking-read-v1" &&
    payload.deviceId === deviceId && Object.hasOwn(payload, "observation"));
  parkingDisplayProduction(payload);
  const generatedAt = parkingDisplayTime(payload.generatedAt);
  let observation = null;
  if (payload.observation !== null) {
    const item = payload.observation;
    parkingDisplayCheck(parkingDisplayObject(item) && (!Object.hasOwn(item, "deviceId") || item.deviceId === deviceId) &&
      typeof item.jobId === "string" && /^[a-f0-9]{32}$/.test(item.jobId) &&
      typeof item.eventId === "string" && /^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$/.test(item.eventId) &&
      ["queued", "running", "failed", "completed"].includes(item.status) && Object.hasOwn(item, "result"));
    parkingDisplayCheck(parkingDisplayTime(item.parkedAt) <= generatedAt);
    observation = {jobId: item.jobId, eventId: item.eventId, parkedAt: item.parkedAt, status: item.status,
      result: item.result === null ? null : parkingDisplayResult(item.result)};
  }
  return {schemaVersion: payload.schemaVersion, deviceId, generatedAt: payload.generatedAt, observation};
}

function parkingDisplayStored(raw, deviceId) {
  if (raw === null) return null;
  parkingDisplayCheck(typeof raw === "string" && new TextEncoder().encode(raw).byteLength <= PARKING_DISPLAY_MAX_BYTES);
  return parkingDisplayPayload(JSON.parse(raw), deviceId);
}

function parkingDisplayNewer(next, previous) {
  if (!previous) return;
  const time = parkingDisplayTime(next.generatedAt), oldTime = parkingDisplayTime(previous.generatedAt);
  parkingDisplayCheck(time >= oldTime);
  if (time === oldTime) parkingDisplayCheck(JSON.stringify(next) === JSON.stringify(previous));
  if (previous.observation && next.observation) {
    const item = next.observation, old = previous.observation;
    const parked = parkingDisplayTime(item.parkedAt), oldParked = parkingDisplayTime(old.parkedAt);
    parkingDisplayCheck(parked >= oldParked);
    if (parked === oldParked || item.jobId === old.jobId || item.eventId === old.eventId) {
      parkingDisplayCheck(parked === oldParked && item.jobId === old.jobId && item.eventId === old.eventId);
    }
  }
}

function parkingDisplayDeadline() {
  let expired = false, timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => { expired = true; reject(new Error("parking_display_timeout")); }, PARKING_DISPLAY_TIMEOUT_MS);
  });
  return {check() { parkingDisplayCheck(!expired); }, run(work) { return Promise.race([work, timeout]); }, clear() { clearTimeout(timer); }};
}

async function parkingDisplayBody(request, control) {
  const type = request.headers.get("content-type") || "";
  parkingDisplayCheck(/^application\/json(?:\s*;\s*charset\s*=\s*(?:utf-8|"utf-8"))?\s*$/i.test(type));
  const encoding = request.headers.get("content-encoding");
  parkingDisplayCheck(!encoding || encoding.trim().toLowerCase() === "identity");
  const length = request.headers.get("content-length");
  parkingDisplayCheck(length === null || (/^\d+$/.test(length) && Number(length) > 0 && Number(length) <= PARKING_DISPLAY_MAX_BYTES));
  parkingDisplayCheck(Boolean(request.body));
  control.reader = request.body.getReader();
  const chunks = [];
  let size = 0;
  for (;;) {
    const {done, value} = await control.reader.read();
    control.check();
    if (done) break;
    size += value.byteLength;
    parkingDisplayCheck(size <= PARKING_DISPLAY_MAX_BYTES);
    chunks.push(value);
  }
  parkingDisplayCheck(length === null || size === Number(length));
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return JSON.parse(new TextDecoder("utf-8", {fatal: true}).decode(bytes));
}

async function handleParkingLatest(request, env) {
  const deviceId = authenticatedDeviceId(request);
  if (!deviceId) return json({error: "unauthorized"}, 401);
  if (request.method !== "GET") return json({error: "method_not_allowed"}, 405);
  const control = parkingDisplayDeadline();
  try {
    const raw = await control.run(env.SNAPSHOTS.get("parking-display-v1:" + deviceId));
    const payload = parkingDisplayStored(raw, deviceId);
    return json(payload ? {ok: true, ...payload} : {ok: true, observation: null});
  } catch (_) {
    return json({error: "parking_latest_unavailable"}, 503);
  } finally { control.clear(); }
}

async function handleParkingDisplay(request, env) {
  const secret = env.WAYON_PARKING_NOTIFY_TOKEN;
  const deviceId = env.WAYON_AI_DEVICE_ID || env.WAYON_LEGACY_FIREBASE_DEVICE_ID;
  if (typeof secret !== "string" || !secret || secret.trim() !== secret || secret === env.WAYON_AI_READ_TOKEN ||
      !constantTimeEqual(getBearerToken(request), secret) || !parkingSignString(deviceId, 128) || !validDeviceId(deviceId)) {
    return json({error: "unauthorized"}, 401);
  }
  if (request.method !== "POST") return json({error: "method_not_allowed"}, 405);
  const control = parkingDisplayDeadline();
  const store = async () => {
    const device = await env.DB.prepare("SELECT device_id FROM wayon_devices WHERE device_id = ? AND revoked_at IS NULL").bind(deviceId).first();
    control.check();
    if (!device || device.device_id !== deviceId) return json({error: "unauthorized"}, 401);
    const payload = parkingDisplayPayload(await parkingDisplayBody(request, control), deviceId);
    const key = "parking-display-v1:" + deviceId;
    const previous = parkingDisplayStored(await env.SNAPSHOTS.get(key), deviceId);
    control.check();
    parkingDisplayNewer(payload, previous);
    const serialized = JSON.stringify(payload);
    parkingDisplayCheck(new TextEncoder().encode(serialized).byteLength <= PARKING_DISPLAY_MAX_BYTES);
    // KV is eventually consistent: this check is not an atomic compare-and-swap.
    await env.SNAPSHOTS.put(key, serialized, {expirationTtl: PARKING_DISPLAY_TTL});
    control.check();
    return json({ok: true, stored: true});
  };
  try { return await control.run(store()); }
  catch (_) { return json({error: "parking_display_unavailable"}, 503); }
  finally {
    control.clear();
    try { void (control.reader ? control.reader.cancel() : request.body?.cancel())?.catch(() => {}); } catch (_) {}
    try { control.reader?.releaseLock(); } catch (_) {}
  }
}
// WAYON_PARKING_DISPLAY_V1_END
