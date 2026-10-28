function gmoneStatusObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
__name(gmoneStatusObject, "gmoneStatusObject");
function gmonePayloadShape(value) {
  const pending = [[value, 0]];
  let nodes = 0;
  while (pending.length) {
    const [item, depth] = pending.pop();
    if (++nodes > 4096 || depth > 32) return false;
    if (item && typeof item === "object") {
      for (const [key, child] of Object.entries(item)) {
        if (["__proto__", "prototype", "constructor"].includes(key)) return false;
        pending.push([child, depth + 1]);
      }
    }
  }
  return true;
}
__name(gmonePayloadShape, "gmonePayloadShape");
function gmoneTimestamp(value) {
  if (typeof value !== "string" || value.length > 40) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(Z|([+-])(\d{2}):(\d{2}))$/.exec(value);
  if (!match) return null;
  const [year, month, day, hour, minute, second] = match.slice(1, 7).map(Number);
  if (month < 1 || month > 12 || day < 1 || hour > 23 || minute > 59 || second > 59) return null;
  if (Number(match[10]) > 14 || Number(match[11]) > 59 || (Number(match[10]) === 14 && Number(match[11]) !== 0)) return null;
  const calendar = new Date(Date.UTC(year, month - 1, day));
  if (calendar.getUTCFullYear() !== year || calendar.getUTCMonth() !== month - 1 || calendar.getUTCDate() !== day) return null;
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) && timestamp >= Date.UTC(2000, 0, 1) ? timestamp : null;
}
__name(gmoneTimestamp, "gmoneTimestamp");
async function readBoundedGmoneBody(request) {
  const declared = request.headers.get("content-length");
  if (declared !== null && (!/^\d+$/.test(declared) || !Number.isSafeInteger(Number(declared)))) {
    return { error: "invalid_content_length", status: 400 };
  }
  if (Number(declared) > GMONE_MAX_PAYLOAD_BYTES) return { error: "payload_too_large", status: 413 };
  if (!request.body) return { error: "invalid_gmone_payload", status: 400 };
  const reader = request.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > GMONE_MAX_PAYLOAD_BYTES) {
        await reader.cancel().catch(() => {});
        return { error: "payload_too_large", status: 413 };
      }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    return { payload: JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)) };
  } catch {
    return { error: "invalid_gmone_payload", status: 400 };
  } finally {
    reader.releaseLock();
  }
}
__name(readBoundedGmoneBody, "readBoundedGmoneBody");
async function handleStoredGmoneStatus(request, env) {
  try {
    const identity = await authenticateDeviceKey(request, env);
    if (!identity) return json({ error: "unauthorized" }, 401);
    return json({ vehicleStatus: await latestGmoneStatus(env, identity.deviceId) });
  } catch {
    return json({ error: "gmone_status_unavailable" }, 503);
  }
}
__name(handleStoredGmoneStatus, "handleStoredGmoneStatus");
async function handleGmoneStatus(request, env) {
  if (!authorizeGmoneUpload(request, env)) return json({ error: "unauthorized" }, 401);
  const body = await readBoundedGmoneBody(request);
  if (body.error) return json({ error: body.error }, body.status);
  const rawPayload = body.payload;
  const deviceId = gmoneDeviceId(request, env);
  if (!validDeviceId(deviceId) || !gmoneStatusObject(rawPayload) || !gmonePayloadShape(rawPayload)) {
    return json({ error: "invalid_gmone_payload" }, 400);
  }
  if (rawPayload.clientScope !== undefined &&
      (typeof rawPayload.clientScope !== "string" || !/^[0-9a-f]{64}$/i.test(rawPayload.clientScope))) {
    return json({ error: "invalid_client_scope" }, 400);
  }
  const payload = sanitizeGmonePayload(rawPayload);
  if (payload.schemaVersion !== "wayon-gmone-v1" || !gmoneStatusObject(payload.status) || !Object.keys(payload.status).length) {
    return json({ error: "invalid_gmone_payload" }, 400);
  }
  const source = payload.source ?? payload.status.source ?? "gmone-direct";
  if (typeof source !== "string" || !source.trim() || source.length > 64) {
    return json({ error: "invalid_gmone_payload" }, 400);
  }
  const now = Date.now();
  const collected = gmoneTimestamp(payload.collectedAt);
  const vehicle = payload.vehicleUpdatedAt == null ? null : gmoneTimestamp(payload.vehicleUpdatedAt);
  // Receipt can be recent even when the vehicle itself has not reported for days.
  if (collected === null || collected < now - 86400000 || collected > now + 120000 ||
      (payload.vehicleUpdatedAt != null && vehicle === null) ||
      (source === "gmone-direct-android" && vehicle === null) ||
      (vehicle !== null && (vehicle > now + 120000 || vehicle > collected + 120000))) {
    return json({ error: "invalid_gmone_timestamp" }, 400);
  }
  const collectedAt = new Date(collected).toISOString();
  const vehicleUpdatedAt = vehicle === null ? null : new Date(vehicle).toISOString();
  const receivedAt = new Date(now).toISOString();
  payload.collectedAt = collectedAt;
  payload.vehicleUpdatedAt = vehicleUpdatedAt;
  if (payload.clientScope !== undefined) payload.clientScope = payload.clientScope.toLowerCase();
  // Ignore all caller-supplied identity hints, including in the stored envelope.
  delete payload.deviceId;
  const encoded = JSON.stringify(payload);
  if (new TextEncoder().encode(encoded).byteLength > GMONE_MAX_PAYLOAD_BYTES) {
    return json({ error: "payload_too_large" }, 413);
  }
  try {
    // The WHERE and replacement execute atomically, with no status pre-read.
    // At one epoch, a subset cannot erase richer data, even with a later receipt.
    const written = await env.DB.prepare(`
      INSERT INTO gmone_latest (
        id, source, collected_at, vehicle_updated_at, payload_json, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET
        source = excluded.source,
        collected_at = excluded.collected_at,
        vehicle_updated_at = excluded.vehicle_updated_at,
        payload_json = excluded.payload_json,
        updated_at = excluded.updated_at
      WHERE
        (julianday(excluded.vehicle_updated_at) IS NOT NULL AND julianday(gmone_latest.vehicle_updated_at) IS NULL)
        OR (
          (julianday(excluded.vehicle_updated_at) IS NOT NULL OR julianday(gmone_latest.vehicle_updated_at) IS NULL)
          AND (
            coalesce(julianday(excluded.vehicle_updated_at), julianday(excluded.collected_at)) >
              coalesce(julianday(gmone_latest.vehicle_updated_at), julianday(gmone_latest.collected_at), 0)
            OR (
              coalesce(julianday(excluded.vehicle_updated_at), julianday(excluded.collected_at)) =
                coalesce(julianday(gmone_latest.vehicle_updated_at), julianday(gmone_latest.collected_at))
              AND NOT EXISTS (
                SELECT fullkey FROM json_tree(gmone_latest.payload_json, '$.status') WHERE atom IS NOT NULL AND atom != ''
                EXCEPT
                SELECT fullkey FROM json_tree(excluded.payload_json, '$.status') WHERE atom IS NOT NULL AND atom != ''
              )
              AND (
                julianday(excluded.collected_at) >= julianday(gmone_latest.collected_at)
                OR EXISTS (
                  SELECT fullkey FROM json_tree(excluded.payload_json, '$.status') WHERE atom IS NOT NULL AND atom != ''
                  EXCEPT
                  SELECT fullkey FROM json_tree(gmone_latest.payload_json, '$.status') WHERE atom IS NOT NULL AND atom != ''
                )
              )
            )
          )
        )
    `).bind(deviceId, source, collectedAt, vehicleUpdatedAt, encoded, receivedAt).run();
    if (written?.success === false || ![0, 1].includes(written?.meta?.changes)) {
      return json({ error: "gmone_status_unavailable" }, 503);
    }
    if (written.meta.changes === 0) {
      return json({ ok: false, stored: false, error: "snapshot_not_newer" }, 409);
    }
    // A phone receipt does not complete the separate collector refresh job.
    if (source !== "gmone-direct-android" &&
        constantTimeEqual(getBearerToken(request), env.WAYON_GMONE_TOKEN || "")) {
      const acknowledged = await env.DB.prepare(`
        UPDATE gmone_refresh_requests SET completed_at = ?
        WHERE id = ? AND requested_at <= ?
      `).bind(receivedAt, deviceId, collectedAt).run();
      if (acknowledged?.success === false) return json({ error: "gmone_status_unavailable" }, 503);
    }
    return json({ ok: true, deviceId, collectedAt, receivedAt });
  } catch {
    return json({ error: "gmone_status_unavailable" }, 503);
  }
}
__name(handleGmoneStatus, "handleGmoneStatus");
