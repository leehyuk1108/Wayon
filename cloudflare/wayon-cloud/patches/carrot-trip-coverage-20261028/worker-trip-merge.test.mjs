import assert from "node:assert/strict";
import { createHash, webcrypto } from "node:crypto";
import { readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import test from "node:test";
import vm from "node:vm";

const baseline = readFileSync(process.env.WAYON_WORKER_BASELINE || new URL("./private/baseline.js", import.meta.url), "utf8");
const candidate = readFileSync(process.env.WAYON_WORKER_CANDIDATE || new URL("./private/candidate.js", import.meta.url), "utf8");
const owner = "authorized-device";
const other = "another-device";
const trip = (id, ended_at, extra = {}) => ({ id, device_id: owner, ended_at, ...extra });
const ids = (rows) => Array.from(rows, (row) => row.id);

function loadWorker(source = candidate) {
  // Only module declarations are removed; all tested function bodies are exact.
  const imports = source.match(/^import .*;$/gm) || [];
  assert.equal(imports.length, 2);
  assert.ok(imports[0].includes('"./key_diagnostics.mjs"'));
  assert.ok(imports[1].includes('"./device_reissue.mjs"'));
  const exportStart = source.lastIndexOf("\nexport {");
  assert.ok(exportStart > 0);
  const context = vm.createContext({
    Request, Response, Headers, URL, AbortSignal, TextEncoder, TextDecoder,
    crypto: webcrypto, atob, btoa,
    console: { warn() {} },
    fetch() { throw new Error("Network forbidden in this test"); },
  });
  vm.runInContext(source.slice(0, exportStart).replace(/^import .*;$/gm, ""), context, { timeout: 1000 });
  return context;
}

function mergeBlock(source) {
  const normalizer = source.indexOf("function normalizeTripId(");
  const start = normalizer >= 0 ? normalizer : source.indexOf("function mergeServerTripsWithD1(");
  const end = source.indexOf('\n__name(mergeServerTripsWithD1, "mergeServerTripsWithD1");', start);
  assert.ok(start >= 0 && end > start);
  return source.slice(start, end);
}

function fixtures({ server = [], d1 = [], unavailable = false, detail = false, healthOwner = owner } = {}) {
  const calls = { db: [], server: [] };
  const env = {
    HEALTH_BRIDGE_DEVICE_ID: healthOwner,
    WAYON_SERVER_SYNC_TOKEN: "unit-test-only-not-a-credential",
    DB: {
      prepare(sql) {
        assert.match(sql, /WHERE (?:id = \? AND )?device_id = \?/);
        return {
          bind(...args) {
            calls.db.push({ sql, args });
            assert.equal(args[detail ? 1 : 0], owner);
            return { all: async () => ({ results: d1 }), first: async () => d1[0] || null };
          },
        };
      },
    },
    WAYON_SERVER_API: {
      async fetch(url, options) {
        calls.server.push({ url, options });
        assert.equal(options.headers["x-wayon-device-id"], owner);
        if (unavailable) throw new Error("Mock Server API unavailable");
        return Response.json(detail
          ? { schemaVersion: "wayon-trip-read-v1", trip: server[0] }
          : { schemaVersion: "wayon-trip-read-v1", trips: server });
      },
    },
  };
  return { env, calls };
}

function request(suffix = "?limit=100") {
  // Conflicting public hints cannot replace the already authenticated identity.
  return new Request(`https://unit.invalid/api/trips${suffix}${suffix.includes("?") ? "&" : "?"}deviceId=${other}`, {
    headers: { "x-wayon-auth-device": owner, "x-wayon-device-id": other },
  });
}

test("baseline is pinned; only trip merge, detail validation and cache invalidation differ", () => {
  assert.equal(createHash("sha256").update(baseline).digest("hex"),
    "10a24bb45918761edf2a5b34c63a1034c74fc9125b1adc236fac29146d437f3e");
  const restored = candidate.replace(mergeBlock(candidate), mergeBlock(baseline))
    .replace("d1TripWithHealth ? [d1TripWithHealth] : [],\n        deviceId, 1", "d1TripWithHealth ? [d1TripWithHealth] : []")
    .replace('      if (normalizeTripId(serverTrip?.id) !== parts[2]) throw new Error("server_trip_id_mismatch");\n', "")
    .replace('if (merged && merged.id === parts[2]) return historyJson(merged, "server+d1");', 'return historyJson(merged, "server+d1");')
    .replace("      health_json = CASE WHEN trips.report_json IS NOT excluded.report_json THEN '{}' ELSE trips.health_json END,\n", "")
    .replace("      health_updated_at = CASE WHEN trips.report_json IS NOT excluded.report_json THEN NULL ELSE trips.health_updated_at END,\n", "")
    .replace('WHERE id = ? AND device_id = ? AND report_json IS ?").bind', 'WHERE id = ? AND device_id = ?").bind')
    .replace("trip.id, trip.device_id, trip.report_json ?? null).run();", "trip.id, trip.device_id).run();")
    .replace("mergeServerTripsWithD1(serverTrips, d1Trips, deviceId, requestedLimit)", "mergeServerTripsWithD1(serverTrips, d1Trips)");
  assert.equal(restored, baseline);
});

test("regression: original successful-server merge drops the D1-only trip", () => {
  const server = [trip("shared", "2026-10-27T00:00:00Z")];
  const d1 = [trip("d1-new", "2026-10-28T00:00:00Z")];
  assert.deepEqual(ids(loadWorker(baseline).mergeServerTripsWithD1(server, d1)), ["shared"]);
  assert.deepEqual(ids(loadWorker().mergeServerTripsWithD1(server, d1, owner, 100)), ["d1-new", "shared"]);
});

test("union deduplicates and preserves server fields, D1 analysis, and server health precedence", () => {
  const d1Analysis = { schemaVersion: "wayon-drive-report-v2", scores: { comfort: 91 } };
  const serverHealth = { available: true, source: "current-server" };
  const server = [
    trip("shared", "2026-10-28T10:00:00Z", { distance_m: 200, analysis: { old: true }, health: serverHealth }),
    trip("shared", "2026-10-27T10:00:00Z", { distance_m: 1 }),
    trip("server-only", "2026-10-28T08:00:00Z"),
  ];
  const d1 = [
    trip("shared", "2026-10-28T09:00:00Z", { distance_m: 100, analysis: d1Analysis, report: { updated: true }, health: { old: true } }),
    trip("d1-only", "2026-10-28T11:00:00Z"),
    trip("d1-only", "2026-10-28T11:00:00Z"),
  ];
  const before = JSON.stringify({ server, d1 });
  const rows = loadWorker().mergeServerTripsWithD1(server, d1, owner, 100);
  assert.deepEqual(ids(rows), ["d1-only", "shared", "server-only"]);
  assert.equal(rows[1].distance_m, 200);
  assert.equal(rows[1].ended_at, server[0].ended_at);
  assert.equal(rows[1].analysis, d1Analysis);
  assert.equal(rows[1].report, d1[0].report);
  assert.equal(rows[1].health, serverHealth);
  assert.equal(JSON.stringify({ server, d1 }), before);
});

test("empty D1 analysis/report and empty server health retain the existing fallbacks", () => {
  const server = trip("same", "2026-10-28T00:00:00Z", { analysis: { rich: true }, report: { rich: true }, health: {} });
  const d1 = trip("same", server.ended_at, { analysis: {}, report: {}, health: { available: true } });
  const [row] = loadWorker().mergeServerTripsWithD1([server], [d1], owner, 1);
  assert.equal(row.analysis, server.analysis);
  assert.equal(row.report, server.report);
  assert.equal(row.health, d1.health);
});

test("only the authorized device is merged, including collisions and conflicting owner aliases", () => {
  const foreign = trip("same", "2099-01-01", { device_id: other, analysis: { secret: true } });
  const conflicting = trip("conflict", "2099-01-01", { deviceId: other });
  const missing = { id: "missing-owner", ended_at: "2099-01-01" };
  const own = trip("same", "2026-10-28");
  const camel = { id: "camel", deviceId: owner, endedAt: "2026-10-27" };
  const worker = loadWorker();
  const rows = worker.mergeServerTripsWithD1([foreign, conflicting, own, missing, camel],
    [foreign, conflicting, missing, { device_id: owner }, trip("d1", "2026-10-26")], owner, 100);
  assert.deepEqual(ids(rows), ["same", "camel", "d1"]);
  assert.equal(rows[0].analysis, undefined);
  assert.deepEqual(ids(worker.mergeServerTripsWithD1([own], [own], "", 100)), []);
});

test("newest first uses parsed end times, deterministic ties, invalid times last, then limit", () => {
  const server = [trip("older", "2026-10-28T10:00:00+09:00"), trip("b", "2026-10-28T02:00:00Z")];
  const d1 = [trip("invalid", "not-a-date"), trip("a", "2026-10-28T02:00:00Z"), trip("newest", "2026-10-28T03:00:00Z")];
  const worker = loadWorker();
  assert.deepEqual(ids(worker.mergeServerTripsWithD1(server, d1, owner, 100)), ["newest", "a", "b", "older", "invalid"]);
  assert.deepEqual(ids(worker.mergeServerTripsWithD1(server, d1, owner, 2)), ["newest", "a"]);
  const many = Array.from({ length: 5002 }, (_, i) => trip(String(i), "2026-10-28"));
  assert.equal(worker.mergeServerTripsWithD1(many, [], owner, 99999).length, 5000);
  for (const limit of [undefined, "invalid", 0, -1]) {
    assert.equal(worker.mergeServerTripsWithD1(many, [], owner, limit).length, 100);
  }
});

test("actual list handler unions successful Server API and scoped D1, limits after merge", async () => {
  const { env, calls } = fixtures({
    server: [trip("server", "2026-10-27"), trip("foreign", "2099-01-01", { device_id: other })],
    d1: [trip("d1-new", "2026-10-28"), trip("foreign-d1", "2099-01-01", { device_id: other })],
  });
  const response = await loadWorker().handleTrips(request("?limit=1"), env, "/api/trips");
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("x-wayon-history-source"), "server+d1");
  assert.deepEqual(ids((await response.json()).trips), ["d1-new"]);
  assert.equal(calls.db.length, 1);
  assert.equal(calls.db[0].args[1], 1);
  assert.equal(new URL(calls.server[0].url).searchParams.get("limit"), "1");
});

test("successful empty server list still returns D1 trips with owner health restrictions", async () => {
  const { env } = fixtures({ healthOwner: other, d1: [trip("d1", "2026-10-28", {
    health_json: JSON.stringify({ available: true, sensitive: "must-be-removed" }),
  })] });
  const response = await loadWorker().handleTrips(request(), env, "/api/trips");
  const [row] = (await response.json()).trips;
  assert.equal(row.id, "d1");
  assert.deepEqual(row.health, { available: false, status: "not_configured" });
  assert.equal(row.health_json, undefined);
});

test("list handler preserves the existing 5000 server and 1000 D1 fetch caps", async () => {
  const { env, calls } = fixtures();
  await loadWorker().handleTrips(request("?limit=99999"), env, "/api/trips");
  assert.equal(new URL(calls.server[0].url).searchParams.get("limit"), "5000");
  assert.equal(calls.db[0].args[1], 1000);
});

test("unavailable Server API still uses the unchanged D1 fallback", async () => {
  const { env } = fixtures({ unavailable: true, d1: [trip("d1", "2026-10-28")] });
  const response = await loadWorker().handleTrips(request(), env, "/api/trips");
  assert.equal(response.headers.get("x-wayon-history-source"), "d1");
  assert.deepEqual(ids((await response.json()).trips), ["d1"]);
});

test("detail merge stays scoped and preserves current server fields plus D1 analysis", async () => {
  const analysis = { schemaVersion: "wayon-drive-report-v2", scores: { comfort: 90 }, automation: { opActiveS: 60 }, comfort: { stopCount: 2 } };
  const { env } = fixtures({ detail: true, healthOwner: other,
    server: [trip("same", "2026-10-28", { distance_m: 200, health: { sensitive: true } })],
    d1: [trip("same", "2026-10-27", { distance_m: 100, report_json: JSON.stringify(analysis) })],
  });
  const response = await loadWorker().handleTrips(request("/same"), env, "/api/trips/same");
  assert.equal(response.headers.get("x-wayon-history-source"), "server+d1");
  const row = await response.json();
  assert.equal(row.id, "same");
  assert.equal(row.device_id, owner);
  assert.equal(row.distance_m, 200);
  assert.deepEqual(row.analysis, analysis);
  assert.deepEqual(row.health, { available: false, status: "not_configured" });
});

test("unauthenticated handler still rejects before either backing store is touched", async () => {
  const response = await loadWorker().handleTrips(new Request("https://unit.invalid/api/trips"), {}, "/api/trips");
  assert.equal(response.status, 401);
});

test("numeric server IDs normalize losslessly and deduplicate against string D1 IDs", () => {
  const worker = loadWorker();
  const analysis = { scores: { comfort: 90 } };
  const rows = worker.mergeServerTripsWithD1([
    trip(42, "2026-10-28", { distance_m: 200 }), trip(0, "2026-10-27"),
  ], [trip("42", "2026-10-26", { analysis })], owner, 100);
  assert.deepEqual(ids(rows), ["42", "0"]);
  assert.equal(rows[0].distance_m, 200);
  assert.equal(rows[0].analysis, analysis);
  const invalid = [NaN, Infinity, -Infinity, true, false, null, undefined, {}, [],
    { toString() { throw new Error("ID object must not be coerced"); } }, Number.MAX_SAFE_INTEGER + 1, 1.5, "", " "];
  assert.deepEqual(ids(worker.mergeServerTripsWithD1(invalid.map((id) => trip(id, "2026-10-28")), [], owner, 100)), []);
});

test("numeric detail IDs return JSON and never an empty 200", async () => {
  const { env } = fixtures({ detail: true, server: [trip(42, "2026-10-28")] });
  const response = await loadWorker().handleTrips(request("/42"), env, "/api/trips/42");
  assert.equal(response.status, 200);
  assert.equal((await response.json()).id, "42");
});

test("malformed, mismatched and conflicting-owner detail rows fall back to D1 or JSON 404", async () => {
  for (const bad of [undefined, null, {}, true, "different-id"]) {
    for (const haveD1 of [false, true]) {
      const { env } = fixtures({ detail: true, server: [trip(bad, "2099-01-01")],
        d1: haveD1 ? [trip("same", "2026-10-28")] : [] });
      const response = await loadWorker().handleTrips(request("/same"), env, "/api/trips/same");
      assert.equal(response.status, haveD1 ? 200 : 404);
      const result = await response.json();
      assert.equal(haveD1 ? result.id : result.error, haveD1 ? "same" : "not_found");
      if (haveD1) assert.equal(response.headers.get("x-wayon-history-source"), "d1");
    }
  }
  const { env } = fixtures({ detail: true, server: [trip("same", "2099-01-01", { deviceId: other })] });
  const response = await loadWorker().handleTrips(request("/same"), env, "/api/trips/same");
  assert.equal(response.status, 404);
  assert.equal((await response.json()).error, "not_found");
});

function sqliteFixture(t) {
  const db = new DatabaseSync(":memory:");
  t.after(() => db.close());
  db.exec(`CREATE TABLE trips (
    id TEXT PRIMARY KEY, device_id TEXT, started_at TEXT, ended_at TEXT, duration_s REAL,
    distance_m REAL, start_lat REAL, start_lon REAL, end_lat REAL, end_lon REAL,
    route_point_count INTEGER, route_json TEXT, report_json TEXT, created_at TEXT,
    health_json TEXT NOT NULL DEFAULT '{}', health_updated_at TEXT
  )`);
  const env = { HEALTH_BRIDGE_DEVICE_ID: owner, DB: {
    prepare(sql) {
      const statement = db.prepare(sql);
      return { bind: (...args) => ({
        async run() { return { meta: { changes: statement.run(...args).changes } }; },
        async first() { return statement.get(...args) || null; },
        async all() { return { results: statement.all(...args) }; },
      }) };
    },
  } };
  return { db, env };
}

const richAnalysis = {
  schemaVersion: "wayon-drive-report-v2", scores: { comfort: 90 },
  automation: { opActiveS: 60 }, comfort: { hardBrakingCount: 2 },
  timeline: [{ time: "2026-10-28T01:00:30Z", opActive: true }],
};

async function uploadTrip(worker, env, analysis = richAnalysis, extra = {}, deviceId = owner) {
  const payload = {
    id: "same", startedAt: "2026-10-28T01:00:00Z", endedAt: "2026-10-28T01:02:00Z",
    durationS: 120, distanceM: 1000, analysis,
    route: [{ latitude: 37, longitude: 127, speedMps: 10 }], ...extra,
  };
  return worker.handleTrip(new Request("https://unit.invalid/api/trips", {
    method: "POST", headers: { "x-wayon-auth-device": deviceId, "content-type": "application/json" },
    body: JSON.stringify(payload),
  }), env);
}

function cacheHealth(db, id = "same") {
  const health = { available: true, load: { scoreVersion: "driver-condition-v3" }, marker: "old-analysis" };
  const timestamp = new Date().toISOString();
  db.prepare("UPDATE trips SET health_json = ?, health_updated_at = ? WHERE id = ?")
    .run(JSON.stringify(health), timestamp, id);
  return { health, timestamp };
}

test("changed analysis invalidates cached health atomically; identical upload keeps it", async (t) => {
  const { db, env } = sqliteFixture(t);
  const worker = loadWorker();
  assert.equal((await uploadTrip(worker, env)).status, 200);
  const cached = cacheHealth(db);
  assert.equal((await uploadTrip(worker, env)).status, 200);
  let row = db.prepare("SELECT * FROM trips WHERE id = 'same'").get();
  assert.equal(row.health_json, JSON.stringify(cached.health));
  assert.equal(row.health_updated_at, cached.timestamp);
  const updated = { ...richAnalysis, comfort: { hardBrakingCount: 5 } };
  assert.equal((await uploadTrip(worker, env, updated)).status, 200);
  row = db.prepare("SELECT * FROM trips WHERE id = 'same'").get();
  assert.equal(row.report_json, JSON.stringify(updated));
  assert.equal(row.health_json, "{}");
  assert.equal(row.health_updated_at, null);
});

test("legacy to richer analysis invalidation causes actual health recomputation", async (t) => {
  const { db, env } = sqliteFixture(t);
  const worker = loadWorker();
  await uploadTrip(worker, env, null, { report: { schemaVersion: "wayon-trip-report-v1", stopQuality: { count: 2 } } });
  cacheHealth(db);
  let row = db.prepare("SELECT * FROM trips WHERE id = 'same'").get();
  assert.equal((await worker.tripWithHealth(env, row)).health.marker, "old-analysis");
  await uploadTrip(worker, env);
  let fetches = 0;
  env.HEALTH_BRIDGE_READ_TOKEN = "unit-test-only-not-a-credential";
  env.HEALTH_BRIDGE_API = { async fetch() {
    fetches += 1;
    return Response.json({ records: [{ type: "watch_heart_rate_1m", start_time: Date.parse("2026-10-28T01:00:30Z"),
      values: { mean_heart_rate_bpm: 80 } }] });
  } };
  row = db.prepare("SELECT * FROM trips WHERE id = 'same'").get();
  const fresh = await worker.tripWithHealth(env, row);
  assert.equal(fetches, 2);
  assert.equal(fresh.health.marker, undefined);
  assert.equal(fresh.health.load.components.drivingSmoothness.eventCounts.hardBrakingCount, 2);
  assert.equal(fresh.health.automationComparison.opSampleCount, 1);
  row = db.prepare("SELECT * FROM trips WHERE id = 'same'").get();
  assert.equal(JSON.parse(row.health_json).load.scoreVersion, "driver-condition-v3");
  await worker.tripWithHealth(env, row);
  assert.equal(fetches, 2, "new cache should be reused");
});

test("cross-device conflict cannot replace analysis or invalidate another owner's cache", async (t) => {
  const { db, env } = sqliteFixture(t);
  const worker = loadWorker();
  await uploadTrip(worker, env);
  cacheHealth(db);
  const before = db.prepare("SELECT * FROM trips WHERE id = 'same'").get();
  assert.equal((await uploadTrip(worker, env, { ...richAnalysis, scores: { comfort: 1 } }, {}, other)).status, 409);
  assert.deepEqual(db.prepare("SELECT * FROM trips WHERE id = 'same'").get(), before);
});

test("in-flight health computation cannot repopulate cache for superseded analysis", async (t) => {
  const { db, env } = sqliteFixture(t);
  const worker = loadWorker();
  await uploadTrip(worker, env, { ...richAnalysis, comfort: { hardBrakingCount: 0 } });
  const oldRow = db.prepare("SELECT * FROM trips WHERE id = 'same'").get();
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  env.HEALTH_BRIDGE_READ_TOKEN = "unit-test-only-not-a-credential";
  env.HEALTH_BRIDGE_API = { async fetch() { await gate; return Response.json({ records: [] }); } };
  const pending = worker.tripWithHealth(env, oldRow);
  await uploadTrip(worker, env);
  release();
  await pending;
  const current = db.prepare("SELECT * FROM trips WHERE id = 'same'").get();
  assert.equal(current.report_json, JSON.stringify(richAnalysis));
  assert.equal(current.health_json, "{}");
  assert.equal(current.health_updated_at, null);
});
