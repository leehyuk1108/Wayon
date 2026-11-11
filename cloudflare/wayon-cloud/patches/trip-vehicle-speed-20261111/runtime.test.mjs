import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';
import {test} from 'node:test';
import {patch as compatPatch} from '../trip-speed-compat-20261111/patch.mjs';
import {patch, unpatch, BASELINE_SHA256, OUTPUT_SHA256} from './patch.mjs';
import {sha256} from '../fast-vehicle-state-20261028/patch.mjs';

// Private copies of the active production modules (downloaded read-only); not committed.
const root = process.env.WAYON_ACTIVE_MODULE_DIR || '/Users/hyuklee/Documents/my-traverse-web-20261110/trip-sqlmax';
const require = createRequire(import.meta.url);
const {Miniflare} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/Documents/sunnypilot/apps/my-traverse-web/node_modules/miniflare');
const deployed = readFileSync(join(root, 'stage-baseline-worker.js'), 'utf8');
const baseline = compatPatch(deployed);
const KEY = 'wayon_' + 'a'.repeat(48), DEVICE = 'owner';
const hash = value => createHash('sha256').update(value).digest('hex');

test('patch is byte-exact and reversible on top of the compatibility bundle', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  const candidate = patch(baseline);
  assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
});

// 2026-11-10 23:11: GPS points stop in two tunnels (route max 112 km/h); carState peaked near 149 km/h.
const route = Array.from({length: 40}, (_, i) => ({time: new Date(Date.UTC(2026, 10, 10, 14, 11, 21 + i * 22)).toISOString(),
  latitude: 37.5 + i / 1000, longitude: 126.6, speedMps: i === 20 ? 31.2 : 10, speedSource: 'vEgoCluster'}));
// The carState timeline every 5 s over the whole 915 s trip (cluster speed), with the 148.6 km/h peak.
const timeline = (end = 915, peakAt = 537.5) => Array.from({length: Math.floor((end - 1.5) / 5) + 1}, (_, i) => {
  const offsetS = 1.5 + i * 5;
  return {offsetS, speedKph: offsetS === peakAt - 1 ? 148.6 : 21.2};
});
const report = (fuel = {source: 'traverseCan', odometerDistanceKm: 5.12, partial: false}, samples = 9140, extra = {}) => ({
  schemaVersion: 'wayon-drive-report-v1', dataQuality: {confidence: 'high', carStateSamples: samples, timelineTruncated: false},
  fuel, timeline: timeline(), ...extra});
const trip = (id, extra = {}) => ({id, deviceId: DEVICE, startedAt: '2026-11-10T14:11:21Z', endedAt: '2026-11-10T14:26:36Z',
  durationS: 915, distanceM: 5110, maxSpeedMps: 41.28, avgSpeedMps: 5110 / 915, route, analysis: report(), ...extra});

async function fixture(script, server = null, migrated = true) {
  const modules = [{type: 'ESModule', path: '/isolated/worker.js', contents: script}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type: 'ESModule', path: '/isolated/' + name, contents: readFileSync(join(root, 'stage-baseline-' + name), 'utf8')});
  }
  const mf = new Miniflare({modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14',
    d1Databases: {DB: 'trip-vspeed-isolated'}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {WAYON_SERVER_SYNC_TOKEN: 'fixture-sync', WAYON_VIEW_TOKEN: 'fixture-view', WAYON_AI_READ_TOKEN: 'fixture-ai',
      WAYON_AI_DEVICE_ID: DEVICE, WAYON_GMONE_TOKEN: 'fixture-gmone', WAYON_PARKING_NOTIFY_TOKEN: 'fixture-notify'},
    serviceBindings: {ASSETS: () => new Response(null, {status: 404}),
      WAYON_SERVER_API: request => {
        if (!server) return new Response('down', {status: 503});
        const url = new URL(request.url);
        if (url.pathname === '/v1/wayon/trips') return Response.json({schemaVersion: 'wayon-trip-read-v1',
          trips: Object.keys(server).map(id => ({id, device_id: DEVICE, ...server[id], route: undefined}))});
        const id = decodeURIComponent(url.pathname.split('/').pop());
        return server[id] ? Response.json({schemaVersion: 'wayon-trip-read-v1', trip: {id, device_id: DEVICE, ...server[id]}})
          : new Response('missing', {status: 404});
      }},
    outboundService: () => new Response(null, {status: 599})});
  const db = await mf.getD1Database('DB');
  await db.exec('CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT,last_seen_at TEXT);');
  await db.prepare('INSERT INTO wayon_devices VALUES(?,?,NULL,?)').bind(DEVICE, hash(KEY), 'unchanged').run();
  await db.exec('CREATE TABLE trips(id TEXT PRIMARY KEY, device_id TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT NOT NULL, ' +
    'duration_s INTEGER, distance_m REAL, start_lat REAL, start_lon REAL, end_lat REAL, end_lon REAL, ' +
    'route_point_count INTEGER NOT NULL DEFAULT 0, route_json TEXT NOT NULL, source TEXT, route_name TEXT, segment_count INTEGER, ' +
    "avg_speed_mps REAL, max_speed_mps REAL, analysis_json TEXT NOT NULL DEFAULT '{}', report_json TEXT, " +
    "health_json TEXT NOT NULL DEFAULT '{}', health_updated_at TEXT, created_at TEXT NOT NULL);");
  if (migrated) await db.exec(readFileSync(new URL('./migration.sql', import.meta.url), 'utf8').replace(/--.*\n/g, ''));
  // An existing trip from before the change: no stored speeds.
  await db.prepare('INSERT INTO trips(id,device_id,started_at,ended_at,duration_s,distance_m,route_point_count,route_json,report_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)')
    .bind('old', DEVICE, '2026-11-09T01:00:00Z', '2026-11-09T01:10:00Z', 600, 3000, route.length, JSON.stringify(route), JSON.stringify(report()), '2026-11-09T01:10:00Z').run();
  const call = async (path, method = 'GET', value) => {
    const r = await mf.dispatchFetch('https://isolated.test' + path, {method, headers: {authorization: 'Bearer ' + KEY,
      ...(value ? {'content-type': 'application/json'} : {})}, ...(value ? {body: JSON.stringify(value)} : {})});
    return {status: r.status, body: await r.json()};
  };
  const stored = async id => db.prepare('SELECT avg_speed_mps, max_speed_mps FROM trips WHERE id = ?').bind(id).first();
  return {call, stored, dispose: () => mf.dispose()};
}

test('a new upload stores the carState maximum and the odometer average, and lists and details prefer them', async () => {
  const f = await fixture(patch(baseline));
  try {
    assert.equal((await f.call('/api/trips', 'POST', trip('new'))).status, 200);
    assert.deepEqual(await f.stored('new'), {avg_speed_mps: 5120 / 915, max_speed_mps: 41.28});
    const list = (await f.call('/api/trips?limit=100')).body.trips;
    const item = list.find(t => t.id === 'new');
    assert.equal(item.max_speed_mps, 41.28);
    assert.equal(item.avg_speed_mps, 5120 / 915);
    assert.equal(item.vehicle_max_speed_mps, 41.28);
    const detail = (await f.call('/api/trips/new')).body;
    assert.equal(detail.max_speed_mps, 41.28);
    assert.equal(detail.vehicle_avg_speed_mps, 5120 / 915);
  } finally { await f.dispose(); }
});

test('stored vehicle values win over a complete Wayon server copy, while old trips keep the server values', async () => {
  const copy = {started_at: '2026-11-10T14:11:21Z', ended_at: '2026-11-10T14:26:36Z', duration_s: 915, distance_m: 5110,
    max_speed_mps: 31.2, avg_speed_mps: 5.58, route};
  const f = await fixture(patch(baseline), {new: copy, old: {...copy, started_at: '2026-11-09T01:00:00Z', ended_at: '2026-11-09T01:10:00Z',
    duration_s: 600, distance_m: 3000, avg_speed_mps: 5}});
  try {
    await f.call('/api/trips', 'POST', trip('new'));
    const list = (await f.call('/api/trips?limit=100')).body.trips;
    assert.equal(list.find(t => t.id === 'new').max_speed_mps, 41.28);
    assert.equal(list.find(t => t.id === 'old').max_speed_mps, 31.2);
    assert.equal(list.find(t => t.id === 'old').avg_speed_mps, 5);
    assert.equal((await f.call('/api/trips/new')).body.max_speed_mps, 41.28);
    assert.equal((await f.call('/api/trips/old')).body.max_speed_mps, 31.2);
  } finally { await f.dispose(); }
});

test('existing trips stay exactly as before, even when re-uploaded', async () => {
  const results = {};
  // Deployed today (no column) vs the compatibility step after the migration vs the final candidate.
  for (const [label, script, migrated] of [['deployed', deployed, false], ['compat', baseline, true], ['patched', patch(baseline), true]]) {
    const f = await fixture(script, null, migrated);
    try {
      // The detail goes through parseTripRoute, shared with the export and AI trip paths.
      const before = {list: (await f.call('/api/trips?limit=100')).body, detail: (await f.call('/api/trips/old')).body};
      assert.equal((await f.call('/api/trips', 'POST', trip('old', {startedAt: '2026-11-09T01:00:00Z', endedAt: '2026-11-09T01:10:00Z',
        durationS: 600, distanceM: 3000}))).status, 200);
      results[label] = {before, stored: await f.stored('old')};
    } finally { await f.dispose(); }
  }
  assert.deepEqual(results.compat.before, results.deployed.before, 'the migration window shows no new field');
  assert.deepEqual(results.patched.before, results.deployed.before, 'old trip list/detail unchanged');
  assert.deepEqual(results.patched.stored, {avg_speed_mps: null, max_speed_mps: null}, 'a re-upload never fills old rows');
});

test('only consistent vehicle evidence is stored', async () => {
  const f = await fixture(patch(baseline));
  const fuel = (km, extra = {}) => ({source: 'traverseCan', odometerDistanceKm: km, partial: false, ...extra});
  try {
    await f.call('/api/trips', 'POST', trip('partial-fuel', {analysis: report(fuel(5.12, {partial: true}))}));
    assert.deepEqual(await f.stored('partial-fuel'), {avg_speed_mps: null, max_speed_mps: 41.28});
    const item = (await f.call('/api/trips?limit=100')).body.trips.find(t => t.id === 'partial-fuel');
    assert.equal(item.avg_speed_mps, 5110 / 915, 'no odometer average: the GPS average as before');
    await f.call('/api/trips', 'POST', trip('no-carstate', {analysis: report(undefined, 0)}));
    assert.deepEqual(await f.stored('no-carstate'), {avg_speed_mps: 5120 / 915, max_speed_mps: null});
    // Codex review cases: the odometer saw only part of the trip, a tiny trip, an unflagged fuel block.
    for (const [id, analysis, extra] of [
      ['odometer-window', report(fuel(1.0)), {}], ['odometer-once', report(fuel(0)), {}],
      ['short', {...report(fuel(0.1)), timeline: timeline(30)}, {durationS: 30, distanceM: 60}],
      ['unflagged', report({source: 'traverseCan', odometerDistanceKm: 5.12}), {}],
      ['too-far', report(fuel(9)), {}]]) {
      await f.call('/api/trips', 'POST', trip(id, {analysis, ...extra}));
      assert.equal((await f.stored(id)).avg_speed_mps, null, id);
    }
    // A timeline longer than the report keeps (truncated): the GPS distance is the reference instead.
    const truncated = q => report(fuel(5.12), 9140, {dataQuality: {carStateSamples: 9140, timelineTruncated: true}});
    await f.call('/api/trips', 'POST', trip('long-ok', {analysis: truncated()}));
    assert.equal((await f.stored('long-ok')).avg_speed_mps, 5120 / 915);
    await f.call('/api/trips', 'POST', trip('long-bad', {analysis: truncated(), distanceM: 3000}));
    assert.equal((await f.stored('long-bad')).avg_speed_mps, null);
    // A route-based maximum (no carState speeds converted) is raised by the carState timeline.
    await f.call('/api/trips', 'POST', trip('route-fallback', {maxSpeedMps: 31.2}));
    assert.equal((await f.stored('route-fallback')).max_speed_mps, 148.6 / 3.6);
    for (const [id, max] of [['bool', true], ['negative', -1], ['blank', '']]) {
      await f.call('/api/trips', 'POST', trip(id, {maxSpeedMps: max, analysis: report(fuel(5.12), 9140, {timeline: []})}));
      assert.equal((await f.stored(id)).max_speed_mps, null, id);
    }
    await f.call('/api/trips', 'POST', trip('huge', {maxSpeedMps: 500}));
    assert.equal((await f.stored('huge')).max_speed_mps, null);
    await f.call('/api/trips', 'POST', trip('no-fuel', {analysis: report(null)}));
    assert.equal((await f.stored('no-fuel')).avg_speed_mps, null);
  } finally { await f.dispose(); }
});

test('the 60 s and 300 s retries are valid averages by themselves', async () => {
  const f = await fixture(patch(baseline));
  try {
    for (const [id, seconds, km] of [['sixty', 60, 0.34], ['three-hundred', 300, 1.7]]) {
      await f.call('/api/trips', 'POST', trip(id, {durationS: seconds, distanceM: km * 1000, maxSpeedMps: 5.9,
        analysis: {...report({source: 'traverseCan', odometerDistanceKm: km, partial: false}), timeline: timeline(seconds)}}));
      assert.equal((await f.stored(id)).avg_speed_mps, km * 1000 / seconds, id);
    }
  } finally { await f.dispose(); }
});

test('a new trip takes later, more complete uploads; an old one never does', async () => {
  const f = await fixture(patch(baseline));
  try {
    await f.call('/api/trips', 'POST', trip('grows', {maxSpeedMps: 10, analysis: report({source: 'traverseCan', odometerDistanceKm: 5.12, partial: true},
      9140, {timeline: timeline().map(row => ({...row, speedKph: 21.2}))})}));
    assert.deepEqual(await f.stored('grows'), {avg_speed_mps: null, max_speed_mps: 10});
    await f.call('/api/trips', 'POST', trip('grows'));
    assert.deepEqual(await f.stored('grows'), {avg_speed_mps: 5120 / 915, max_speed_mps: 41.28});
    await f.call('/api/trips', 'POST', trip('grows', {analysis: report(null, 0)}));
    assert.deepEqual(await f.stored('grows'), {avg_speed_mps: 5120 / 915, max_speed_mps: 41.28}, 'a later upload without evidence keeps the values');
    // Codex review: a shorter, partial retry (60 s of standstill) never lowers the maximum or replaces the average.
    await f.call('/api/trips', 'POST', trip('grows', {durationS: 60, distanceM: 0, maxSpeedMps: 0,
      analysis: {...report({source: 'traverseCan', odometerDistanceKm: 0.4, partial: true}), timeline: timeline(60).map(row => ({...row, speedKph: 0}))}}));
    assert.deepEqual(await f.stored('grows'), {avg_speed_mps: 5120 / 915, max_speed_mps: 41.28});
    const shortRetry = report({source: 'traverseCan', odometerDistanceKm: 1.0, partial: false});
    await f.call('/api/trips', 'POST', trip('grows', {durationS: 300, distanceM: 1000, analysis: {...shortRetry, timeline: timeline(300)}}));
    assert.equal((await f.stored('grows')).avg_speed_mps, 5120 / 915, 'a shorter upload never replaces the average');
    // Codex review (3rd): 915 s, then a valid 60 s upload (the row's duration drops to 60), then a valid 300 s
    // upload: the 915 s average stays.
    const valid = (seconds, km) => trip('grows', {durationS: seconds, distanceM: km * 1000, maxSpeedMps: 5.9,
      analysis: {...report({source: 'traverseCan', odometerDistanceKm: km, partial: false}), timeline: timeline(seconds)}});
    await f.call('/api/trips', 'POST', valid(60, 0.34));
    await f.call('/api/trips', 'POST', valid(300, 1.7));
    assert.equal((await f.stored('grows')).avg_speed_mps, 5120 / 915);
    await f.call('/api/trips', 'POST', trip('grows'));
    assert.deepEqual(await f.stored('grows'), {avg_speed_mps: 5120 / 915, max_speed_mps: 41.28}, 'the full upload again');
    await f.call('/api/trips', 'POST', trip('old', {startedAt: '2026-11-09T01:00:00Z', endedAt: '2026-11-09T01:10:00Z'}));
    assert.deepEqual(await f.stored('old'), {avg_speed_mps: null, max_speed_mps: null});
  } finally { await f.dispose(); }
});
