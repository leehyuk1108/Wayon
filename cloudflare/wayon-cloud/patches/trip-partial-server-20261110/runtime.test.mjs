import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';
import {test} from 'node:test';
import {patch as placePatch} from '../parking-place-20261110/patch.mjs';
import {patch as historyPatch} from '../trip-history-20261110/patch.mjs';
import {patch, unpatch, BASELINE_SHA256, OUTPUT_SHA256} from './patch.mjs';
import {sha256} from '../fast-vehicle-state-20261028/patch.mjs';

// Private copies of the production modules (downloaded read-only); not committed.
const root = process.env.WAYON_ACTIVE_MODULE_DIR || '/Users/hyuklee/Documents/my-traverse-web-20261110';
const require = createRequire(import.meta.url);
const {Miniflare} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/Documents/sunnypilot/apps/my-traverse-web/node_modules/miniflare');
const baseline = historyPatch(placePatch(readFileSync(join(root, 'stage-candidate.worker.js'), 'utf8')));
const KEY = 'wayon_' + 'a'.repeat(48), DEVICE = 'owner';
const hash = value => createHash('sha256').update(value).digest('hex');
const point = minute => ({time: new Date(Date.UTC(2026, 10, 8, 7, 24 + minute)).toISOString().replace('.000', ''),
  latitude: 35 + minute / 1000, longitude: 128, speedMps: minute % 40});
const full = Array.from({length: 149}, (_, i) => point(i));
const head = full.slice(0, 34);
const D1 = {started_at: '2026-11-08T07:24:28Z', ended_at: '2026-11-08T09:52:33Z', distance_m: 200677, duration_s: 8884};
const PARTIAL = {started_at: '2026-11-08T07:24:28Z', ended_at: '2026-11-08T07:57:19Z', distance_m: 19528, duration_s: 1970,
  route: head, route_point_count: head.length, route_name: 'server-name', segment_count: 33};
const COMPLETE = {...D1, ended_at: '2026-11-08T09:52:00Z', distance_m: 200700, duration_s: 8852, route: full,
  route_point_count: full.length, route_name: 'server-name', segment_count: 148};

test('patch is byte-exact and reversible on top of the deployed bundle', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  const candidate = patch(baseline);
  assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
});

async function fixture(script, server, d1Route = full, d1Override = {}) {
  const modules = [{type: 'ESModule', path: '/isolated/worker.js', contents: script}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type: 'ESModule', path: '/isolated/' + name, contents: readFileSync(join(root, 'stage-baseline-' + name), 'utf8')});
  }
  const serverTrip = id => ({id, device_id: DEVICE, ...server});
  const mf = new Miniflare({modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14',
    d1Databases: {DB: 'trip-partial-isolated'}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {WAYON_SERVER_SYNC_TOKEN: 'fixture-sync', WAYON_VIEW_TOKEN: 'fixture-view', WAYON_AI_READ_TOKEN: 'fixture-ai',
      WAYON_AI_DEVICE_ID: DEVICE, WAYON_GMONE_TOKEN: 'fixture-gmone', WAYON_PARKING_NOTIFY_TOKEN: 'fixture-notify'},
    serviceBindings: {ASSETS: () => new Response(null, {status: 404}),
      WAYON_SERVER_API: request => {
        const url = new URL(request.url);
        if (url.pathname === '/v1/wayon/trips') return Response.json({schemaVersion: 'wayon-trip-read-v1',
          trips: [{...serverTrip('long'), route: undefined}]});
        return Response.json({schemaVersion: 'wayon-trip-read-v1', trip: serverTrip(decodeURIComponent(url.pathname.split('/').pop()))});
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
  await db.prepare('INSERT INTO trips(id,device_id,started_at,ended_at,duration_s,distance_m,route_point_count,route_json,report_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)')
    .bind('long', DEVICE, D1.started_at, D1.ended_at, D1.duration_s, 'distance_m' in d1Override ? d1Override.distance_m : D1.distance_m, d1Route.length, JSON.stringify(d1Route), '{}', D1.ended_at).run();
  await db.prepare('INSERT INTO trips(id,device_id,started_at,ended_at,duration_s,distance_m,route_point_count,route_json,report_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)')
    .bind('short', DEVICE, '2026-11-07T01:00:00Z', '2026-11-07T01:10:00Z', 600, 5000, 2, '[{"speedMps":3},{"speedMps":5}]', '{}', '2026-11-07T01:10:00Z').run();
  const get = async path => (await mf.dispatchFetch('https://isolated.test' + path, {headers: {authorization: 'Bearer ' + KEY}})).json();
  return {get, dispose: () => mf.dispose()};
}

const core = trip => ({ended_at: trip.ended_at, distance_m: trip.distance_m, duration_s: trip.duration_s});

test('a partial server copy no longer shortens the trip in the detail or the list', async () => {
  for (const [label, script] of [['deployed', baseline], ['patched', patch(baseline)]]) {
    const f = await fixture(script, PARTIAL);
    try {
      const detail = await f.get('/api/trips/long');
      const list = await f.get('/api/trips?limit=1000');
      const item = list.trips.find(t => t.id === 'long');
      assert.equal(detail.route.length, full.length, `${label}: the route already came from D1`);
      if (label === 'deployed') {
        assert.deepEqual(core(detail), {ended_at: PARTIAL.ended_at, distance_m: PARTIAL.distance_m, duration_s: PARTIAL.duration_s}, 'the bug');
        assert.equal(item.distance_m, PARTIAL.distance_m, 'the bug in the list');
      } else {
        assert.deepEqual(core(detail), core(D1));
        assert.deepEqual(core(item), core(D1));
        assert.equal(detail.route_point_count, full.length);
        assert.equal(detail.route_name, 'server-name', 'server-only fields stay');
        assert.equal(item.max_speed_mps, 39, 'the D1 maximum over the whole drive');
        // The D1 row stores no avg/max columns: the detail derives them instead of copying null.
        assert.equal(detail.avg_speed_mps, D1.distance_m / D1.duration_s);
        assert.equal(detail.max_speed_mps, 39);
      }
      assert.equal(list.trips.find(t => t.id === 'short').distance_m, 5000);
    } finally { await f.dispose(); }
  }
});

test('a complete server copy still wins as before, so the patch changes nothing there', async () => {
  const results = {};
  for (const [label, script] of [['deployed', baseline], ['patched', patch(baseline)]]) {
    const f = await fixture(script, COMPLETE);
    try { results[label] = {detail: await f.get('/api/trips/long'), list: await f.get('/api/trips?limit=1000')}; }
    finally { await f.dispose(); }
  }
  assert.deepEqual(results.patched, results.deployed);
  assert.deepEqual(core(results.patched.detail), core(COMPLETE));
});

test('a longer server route is kept even when its summary times are short', async () => {
  // Codex review case: server summary 33 min but route to 09:52; D1 summary 148 min but route to 07:57.
  const f = await fixture(patch(baseline), {...PARTIAL, route: full, route_point_count: full.length}, head);
  try {
    const detail = await f.get('/api/trips/long');
    assert.equal(detail.route.length, full.length);
    assert.equal(detail.route_point_count, full.length);
    assert.deepEqual(core(detail), core(D1), 'timing and distance still from D1');
    assert.equal(detail.max_speed_mps, 39, 'the maximum of the route that is shown, not of the short D1 route');
  } finally { await f.dispose(); }
});

test('a missing D1 distance never turns into a zero average over the server value', async () => {
  // A D1 row whose distance is unknown.
  const f = await fixture(patch(baseline), {...PARTIAL, avg_speed_mps: 9.9}, full, {distance_m: null});
  try {
    const detail = await f.get('/api/trips/long');
    assert.equal(detail.avg_speed_mps, 9.9);
    assert.equal(detail.distance_m, PARTIAL.distance_m, 'an unknown D1 distance does not erase the server value');
  } finally { await f.dispose(); }
});
