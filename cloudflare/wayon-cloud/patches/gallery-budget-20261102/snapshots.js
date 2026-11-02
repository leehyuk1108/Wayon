const SNAPSHOT_STATS_HOUR_MS = 3600000;
const snapshotStatsMemory = new Map();

function snapshotStatsValid(value, deviceId, now) {
  if (!value || value.version !== 1 || value.deviceId !== deviceId ||
      !Number.isSafeInteger(value.computedAtMs) || value.computedAtMs > now ||
      Math.floor(value.computedAtMs / SNAPSHOT_STATS_HOUR_MS) !== Math.floor(now / SNAPSHOT_STATS_HOUR_MS) ||
      !Array.isArray(value.days) || value.days.length > 20000) return false;
  const dates = new Set();
  let total = 0;
  for (const day of value.days) {
    if (!day || !(day.date === null || (typeof day.date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(day.date))) ||
        dates.has(day.date) || !Number.isSafeInteger(day.count) || day.count <= 0) return false;
    dates.add(day.date);
    total += day.count;
  }
  return Number.isSafeInteger(total) && value.total === total;
}

async function snapshotListStats(env, deviceId) {
  const now = Date.now(), bucket = Math.floor(now / SNAPSHOT_STATS_HOUR_MS);
  const ownerHash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(deviceId)))]
    .map(byte => byte.toString(16).padStart(2, '0')).join('');
  const key = `meta/snapshot-stats/v1/${ownerHash}/${bucket}`;
  let entry = snapshotStatsMemory.get(key);
  if (entry?.value && snapshotStatsValid(entry.value, deviceId, now)) return entry.value;
  if (entry?.pending) return entry.pending;
  entry = {};
  snapshotStatsMemory.set(key, entry);
  // Metadata is display-only. Never put session, vehicle freshness or command state here.
  if (snapshotStatsMemory.size > 32) snapshotStatsMemory.delete(snapshotStatsMemory.keys().next().value);
  entry.pending = (async () => {
    // A failed cache read must not turn into repeated full-table scans.
    const cached = await env.SNAPSHOTS.get(key, 'json');
    if (snapshotStatsValid(cached, deviceId, now)) return cached;
    const {results: days} = await env.DB.prepare(`
      SELECT date(captured_at, '+9 hours') AS date, COUNT(*) AS count
      FROM snapshots WHERE device_id = ? GROUP BY date ORDER BY date DESC
    `).bind(deviceId).all();
    const value = {version: 1, deviceId, computedAtMs: now, days,
      total: Array.isArray(days) ? days.reduce((sum, day) => sum + day.count, 0) : null};
    if (!snapshotStatsValid(value, deviceId, now)) throw new Error('snapshot_stats_invalid');
    // Keep a successful aggregate in this isolate even if KV is temporarily unwritable.
    entry.value = value;
    await env.SNAPSHOTS.put(key, JSON.stringify(value), {expirationTtl: 7200}).catch(() => {});
    return value;
  })();
  try { entry.value = await entry.pending; return entry.value; }
  finally { delete entry.pending; }
}

async function readSnapshotList(env, deviceId, limit, date = null) {
  const dateWhere = date
    ? "WHERE s.device_id = ? AND date(s.captured_at, '+9 hours') = ?"
    : "WHERE s.device_id = ?";
  const query = `
    SELECT s.id, s.device_id, s.camera, s.captured_at, s.kv_key, s.size_bytes, s.created_at,
           COALESCE(iw.id, idr.id) AS impact_id,
           COALESCE(iw.severity, idr.severity) AS impact_severity,
           COALESCE(iw.peak_dynamic_g, idr.peak_dynamic_g) AS impact_peak_dynamic_g,
           COALESCE(iw.peak_total_g, idr.peak_total_g) AS impact_peak_total_g,
           COALESCE(iw.detected_at, idr.detected_at) AS impact_detected_at
    FROM snapshots s
    LEFT JOIN impact_events iw ON s.id = iw.wide_snapshot_id AND s.device_id = iw.device_id
    LEFT JOIN impact_events idr ON s.id = idr.driver_snapshot_id AND s.device_id = idr.device_id
    ${dateWhere}
    ORDER BY s.captured_at DESC LIMIT ?
  `;
  const result = date ? await env.DB.prepare(query).bind(deviceId, date, limit).all()
    : await env.DB.prepare(query).bind(deviceId, limit).all();
  if (!Array.isArray(result.results)) throw new Error('snapshot_list_invalid');
  return result.results;
}

async function handleWebSnapshots(request, env) {
  if (!authorize(request, env, false)) return json({error: 'unauthorized'}, 401);
  if (request.method !== 'GET') return json({error: 'method_not_allowed'}, 405);
  const deviceId = authenticatedDeviceId(request);
  const limit = boundedLimit(new URL(request.url).searchParams.get('limit'), 24, 1000);
  try { return json({snapshots: await readSnapshotList(env, deviceId, limit)}); }
  catch { return json({error: 'web_snapshots_unavailable'}, 503); }
}

async function handleSnapshotsList(request, env) {
  if (!authorize(request, env, false)) return json({error: 'unauthorized'}, 401);
  const url = new URL(request.url), deviceId = authenticatedDeviceId(request);
  const limit = boundedLimit(url.searchParams.get('limit'), 500, 1000);
  const date = url.searchParams.get('date');
  try {
    return historyJson(await fetchServerSnapshotList(env, limit, date, deviceId), 'server');
  } catch {
    console.warn('Wayon server snapshot list unavailable; using D1');
  }
  const snapshots = await readSnapshotList(env, deviceId, limit, date);
  const stats = await snapshotListStats(env, deviceId);
  return historyJson({generatedAt: nowIso(), snapshots, days: stats.days, total: stats.total, limit,
    statsComputedAt: new Date(stats.computedAtMs).toISOString(),
    statsExpiresAt: new Date((Math.floor(stats.computedAtMs / SNAPSHOT_STATS_HOUR_MS) + 1) * SNAPSHOT_STATS_HOUR_MS).toISOString(),
  }, 'd1');
}
