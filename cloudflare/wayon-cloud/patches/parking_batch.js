// WAYON_PARKING_BATCH_V1_BEGIN
const PARKING_BATCH_MAX_AGE_MS = 7200000;
const PARKING_BATCH_MAX_IMAGE_BYTES = 2097152;

function parkingBatchTimestamp(value) {
  if (typeof value !== "string" || value.length > 40) return NaN;
  const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?(Z|[+-]\d{2}:\d{2})$/.exec(value);
  if (!match) return NaN;
  const local = `${match[1]}T${match[2]}.${(match[3] || "").padEnd(3, "0").slice(0, 3)}Z`;
  const localMs = Date.parse(local);
  if (!Number.isFinite(localMs) || new Date(localMs).toISOString() !== local) return NaN;
  if (match[4] !== "Z" && (Number(match[4].slice(1, 3)) > 23 || Number(match[4].slice(4)) > 59)) return NaN;
  return Date.parse(value);
}

function parkingBatchImage(encoded) {
  if (typeof encoded !== "string" || !encoded.length || encoded.length % 4 ||
      encoded.length > Math.ceil(PARKING_BATCH_MAX_IMAGE_BYTES / 3) * 4 || !/^[A-Za-z0-9+/]*={0,2}$/.test(encoded)) return null;
  let bytes;
  try { bytes = base64ToBytes(encoded); } catch { return null; }
  if (bytes.length < 4 || bytes.length > PARKING_BATCH_MAX_IMAGE_BYTES ||
      bytes[0] !== 255 || bytes[1] !== 216 || bytes.at(-2) !== 255 || bytes.at(-1) !== 217) return null;
  return bytes;
}

function parkingBatchInput(payload, now = Date.now()) {
  const p = payload.parking;
  if (!p || Array.isArray(p) || typeof p !== "object" ||
      Object.keys(p).sort().join(",") !== "count,eventId,index,parkedAt,phase,version" ||
      p.version !== 1 || typeof p.eventId !== "string" || !/^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$/.test(p.eventId) ||
      !Number.isInteger(p.count) || p.count < 2 || p.count > 12 ||
      !Number.isInteger(p.index) || p.index < 0 || p.index >= p.count ||
      !["approach", "parked"].includes(p.phase)) return { error: "invalid_parking_metadata" };
  const parkedMs = parkingBatchTimestamp(p.parkedAt);
  const capturedMs = parkingBatchTimestamp(payload.capturedAt);
  if (!Number.isFinite(parkedMs) || !Number.isFinite(capturedMs)) return { error: "invalid_parking_timestamp" };
  if (now - parkedMs > PARKING_BATCH_MAX_AGE_MS || parkedMs > now + 5000 || capturedMs > now + 5000 ||
      capturedMs > parkedMs || capturedMs < parkedMs - 120000 ||
      (p.phase === "approach" && capturedMs >= parkedMs) ||
      (p.index === p.count - 1 && (p.phase !== "parked" || capturedMs !== parkedMs))) {
    return { error: "parking_time_out_of_bounds" };
  }
  const bytes = parkingBatchImage(payload.wideJpegBase64);
  if (!bytes) return { error: "invalid_parking_image" };
  let driverBytes = null;
  if (payload.driverJpegBase64 != null && payload.driverJpegBase64 !== "") {
    driverBytes = parkingBatchImage(payload.driverJpegBase64);
    if (p.phase !== "parked" || !driverBytes) return { error: "invalid_parking_driver_image" };
  }
  return { parking: { ...p }, capturedAt: payload.capturedAt, parkedMs, capturedMs, bytes, driverBytes };
}

function parkingBatchSame(row, input, digest, driverDigest) {
  const p = input.parking;
  return row && row.frame_count === p.count && row.parked_at === p.parkedAt && row.phase === p.phase &&
    row.captured_at === input.capturedAt && row.image_sha256 === digest && row.driver_sha256 === driverDigest;
}

function parkingBatchResponse(row, complete) {
  const snapshots = [];
  if (row.driver_snapshot_id) snapshots.push({ id: row.driver_snapshot_id, camera: "driver", key: row.driver_kv_key, sizeBytes: row.driver_size_bytes });
  snapshots.push({ id: row.snapshot_id, camera: "wide", key: row.kv_key, sizeBytes: row.size_bytes });
  return json({ ok: true, snapshots,
    parking: { version: 1, eventId: row.event_id, parkedAt: row.parked_at,
      index: row.frame_index, count: row.frame_count, phase: row.phase, complete } });
}

async function parkingBatchDigest(bytes) {
  return bytes ? Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
    b => b.toString(16).padStart(2, "0")).join("") : null;
}

async function handleParkingBatchSnapshot(payload, request, env) {
  const input = parkingBatchInput(payload);
  if (input.error) return json({ error: input.error }, 400);
  const deviceId = authenticatedDeviceId(request);
  if (!deviceId) return json({ error: "unauthorized" }, 401);
  const p = input.parking;
  const digest = await parkingBatchDigest(input.bytes);
  const driverDigest = await parkingBatchDigest(input.driverBytes);
  const readRow = () => env.DB.prepare(`SELECT f.*, s.id IS NOT NULL AS published
    FROM parking_snapshot_frames_v1 f LEFT JOIN snapshots s ON s.id = f.snapshot_id AND s.device_id = f.device_id
    WHERE f.device_id = ? AND f.event_id = ? AND f.frame_index = ?`).bind(deviceId, p.eventId, p.index).first();
  // Exact retry is read-only, including the stored immutable image.
  const existing = await readRow();
  if (existing) return parkingBatchSame(existing, input, digest, driverDigest)
    ? parkingBatchResponse(existing, Boolean(existing.published)) : json({ error: "parking_group_conflict" }, 409);

  // Expired partial groups never entered snapshots. DELETE RETURNING claims only
  // their own keys before best-effort cleanup; completed image/metadata is retained.
  const expired = await env.DB.prepare(`DELETE FROM parking_snapshot_frames_v1
    WHERE device_id = ? AND parked_ms < ? AND NOT EXISTS (
      SELECT 1 FROM snapshots s WHERE s.id = parking_snapshot_frames_v1.snapshot_id AND s.device_id = ?)
    RETURNING kv_key,driver_kv_key`).bind(deviceId, Date.now() - PARKING_BATCH_MAX_AGE_MS - 300000, deviceId).all();
  for (const row of expired.results || []) {
    for (const expiredKey of [row.kv_key,row.driver_kv_key].filter(Boolean)) {
      try { await env.SNAPSHOTS.delete(expiredKey); } catch { /* No published image is deleted. */ }
    }
  }
  const id = crypto.randomUUID();
  const key = `snapshots/${deviceId}/wide/parking-${id}.jpg`;
  const driverId = input.driverBytes ? crypto.randomUUID() : null;
  const driverKey = driverId ? `snapshots/${deviceId}/driver/${driverId}.jpg` : null;
  const createdAt = nowIso();
  try {
    await env.SNAPSHOTS.put(key, input.bytes, { metadata: { deviceId, camera: "wide", capturedAt: input.capturedAt, parking: p } });
    if (driverKey) await env.SNAPSHOTS.put(driverKey, input.driverBytes,
      { metadata: { deviceId, camera: "driver", capturedAt: input.capturedAt } });
  } catch {
    for (const unusedKey of [key,driverKey].filter(Boolean)) {
      try { await env.SNAPSHOTS.delete(unusedKey); } catch { /* No D1 claim exists yet. */ }
    }
    return json({ error: "parking_storage_unavailable" }, 503);
  }
  let results;
  try {
    results = await env.DB.batch([
      env.DB.prepare(`INSERT INTO parking_snapshot_frames_v1
        (device_id,event_id,frame_index,frame_count,parked_at,parked_ms,phase,captured_at,captured_ms,
         snapshot_id,kv_key,size_bytes,image_sha256,driver_snapshot_id,driver_kv_key,driver_size_bytes,driver_sha256,created_at)
        SELECT ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        WHERE NOT EXISTS (SELECT 1 FROM parking_snapshot_frames_v1 f WHERE f.device_id = ? AND f.event_id = ? AND (
          f.frame_count != ? OR f.parked_at != ? OR
          (f.frame_index < ? AND (f.captured_ms >= ? OR (f.phase = 'parked' AND (? = 'approach' OR ? IS NOT NULL)))) OR
          (f.frame_index > ? AND (f.captured_ms <= ? OR (? = 'parked' AND (f.phase = 'approach' OR f.driver_snapshot_id IS NOT NULL))))))
        AND (EXISTS (SELECT 1 FROM parking_snapshot_frames_v1 WHERE device_id = ? AND event_id = ?) OR
          (SELECT COUNT(DISTINCT event_id) FROM parking_snapshot_frames_v1 f WHERE device_id = ? AND parked_ms >= ? AND NOT EXISTS (
            SELECT 1 FROM snapshots s WHERE s.id = f.snapshot_id AND s.device_id = f.device_id)) < 8)
        AND COALESCE((SELECT SUM(size_bytes) FROM parking_snapshot_frames_v1
          WHERE device_id = ? AND event_id = ? AND frame_index != ?), 0) + ? <= 16777216
        AND ? >= ?
        ON CONFLICT(device_id,event_id,frame_index) DO NOTHING`).bind(
          deviceId,p.eventId,p.index,p.count,p.parkedAt,input.parkedMs,p.phase,input.capturedAt,input.capturedMs,
          id,key,input.bytes.length,digest,driverId,driverKey,input.driverBytes?.length ?? null,driverDigest,createdAt,
          deviceId,p.eventId,p.count,p.parkedAt,
          p.index,input.capturedMs,p.phase,driverId,p.index,input.capturedMs,p.phase,deviceId,p.eventId,deviceId,
          Date.now() - PARKING_BATCH_MAX_AGE_MS - 300000,
          deviceId,p.eventId,p.index,input.bytes.length,
          input.parkedMs,Date.now() - PARKING_BATCH_MAX_AGE_MS),
      env.DB.prepare(`INSERT INTO snapshots (id,device_id,camera,captured_at,kv_key,size_bytes,created_at)
        SELECT snapshot_id,device_id,'wide',captured_at,kv_key,size_bytes,created_at
        FROM parking_snapshot_frames_v1 f WHERE device_id = ? AND event_id = ?
        AND (SELECT COUNT(*) FROM parking_snapshot_frames_v1 g WHERE g.device_id = f.device_id AND g.event_id = f.event_id) = f.frame_count
        AND NOT EXISTS (SELECT 1 FROM snapshots s WHERE s.id = f.snapshot_id)`).bind(deviceId,p.eventId),
      env.DB.prepare(`INSERT INTO snapshots (id,device_id,camera,captured_at,kv_key,size_bytes,created_at)
        SELECT driver_snapshot_id,device_id,'driver',captured_at,driver_kv_key,driver_size_bytes,created_at
        FROM parking_snapshot_frames_v1 f WHERE device_id = ? AND event_id = ? AND driver_snapshot_id IS NOT NULL
        AND (SELECT COUNT(*) FROM parking_snapshot_frames_v1 g WHERE g.device_id = f.device_id AND g.event_id = f.event_id) = f.frame_count
        AND NOT EXISTS (SELECT 1 FROM snapshots s WHERE s.id = f.driver_snapshot_id)`).bind(deviceId,p.eventId),
      env.DB.prepare(`UPDATE latest_state SET last_snapshot_wide_id = (
        SELECT f.snapshot_id FROM parking_snapshot_frames_v1 f JOIN snapshots s ON s.id = f.snapshot_id AND s.device_id = f.device_id
        WHERE f.device_id = ? AND f.event_id = ? AND f.frame_index = f.frame_count - 1)
        WHERE device_id = ? AND EXISTS (SELECT 1 FROM parking_snapshot_frames_v1 f JOIN snapshots s ON s.id = f.snapshot_id AND s.device_id = f.device_id
          WHERE f.device_id = ? AND f.event_id = ? AND f.frame_index = f.frame_count - 1
          AND f.captured_ms >= COALESCE((SELECT CAST((julianday(old.captured_at) - 2440587.5) * 86400000 AS INTEGER)
            FROM snapshots old WHERE old.id = latest_state.last_snapshot_wide_id AND old.device_id = ?), 0))`)
        .bind(deviceId,p.eventId,deviceId,deviceId,p.eventId,deviceId),
      env.DB.prepare(`UPDATE latest_state SET last_snapshot_driver_id = (
        SELECT f.driver_snapshot_id FROM parking_snapshot_frames_v1 f JOIN snapshots s ON s.id = f.driver_snapshot_id AND s.device_id = f.device_id
        WHERE f.device_id = ? AND f.event_id = ?)
        WHERE device_id = ? AND EXISTS (SELECT 1 FROM parking_snapshot_frames_v1 f JOIN snapshots s ON s.id = f.driver_snapshot_id AND s.device_id = f.device_id
          WHERE f.device_id = ? AND f.event_id = ?
          AND f.captured_ms >= COALESCE((SELECT CAST((julianday(old.captured_at) - 2440587.5) * 86400000 AS INTEGER)
            FROM snapshots old WHERE old.id = latest_state.last_snapshot_driver_id AND old.device_id = ?), 0))`)
        .bind(deviceId,p.eventId,deviceId,deviceId,p.eventId,deviceId),
      env.DB.prepare(`SELECT f.*, s.id IS NOT NULL AS published FROM parking_snapshot_frames_v1 f
        LEFT JOIN snapshots s ON s.id = f.snapshot_id AND s.device_id = f.device_id
        WHERE f.device_id = ? AND f.event_id = ? AND f.frame_index = ?`).bind(deviceId,p.eventId,p.index),
    ]);
  } catch {
    // A transport error can have an unknown commit result. Never delete a key
    // that may already be published; retry resolves the immutable frame identity.
    return json({ error: "parking_storage_unavailable" }, 503);
  }
  const row = results[5].results[0];
  if (!row || row.kv_key !== key) {
    for (const unusedKey of [key,driverKey].filter(Boolean)) {
      try { await env.SNAPSHOTS.delete(unusedKey); } catch { /* Only these unclaimed random keys. */ }
    }
  }
  if (!parkingBatchSame(row, input, digest, driverDigest)) return json({ error: "parking_group_conflict_or_capacity" }, 409);
  return parkingBatchResponse(row, Boolean(row.published));
}

async function parkingBatchAiSnapshots(request, env, snapshots) {
  if (!snapshots.length) return [];
  const deviceId = authenticatedDeviceId(request);
  const rows = await env.DB.prepare(`SELECT f.snapshot_id,f.event_id,f.parked_at,f.frame_index,f.frame_count,f.phase
    FROM parking_snapshot_frames_v1 f JOIN snapshots s ON s.id = f.snapshot_id AND s.device_id = f.device_id
    WHERE f.device_id = ? AND f.snapshot_id IN (SELECT value FROM json_each(?))`)
    .bind(deviceId,JSON.stringify(snapshots.map(s => s.id))).all();
  const metadata = new Map((rows.results || []).map(row => [row.snapshot_id, {
    version: 1, eventId: row.event_id, parkedAt: row.parked_at,
    index: row.frame_index, count: row.frame_count, phase: row.phase,
  }]));
  return snapshots.map(snapshot => ({ ...aiSnapshot(request, snapshot),
    ...(metadata.has(snapshot.id) ? { parking: metadata.get(snapshot.id) } : {}) }));
}
// WAYON_PARKING_BATCH_V1_END
