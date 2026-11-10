import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';
import {test} from 'node:test';
import {patch as placePatch} from '../parking-place-20261110/patch.mjs';
import {patch, unpatch, BASELINE_SHA256, OUTPUT_SHA256} from './patch.mjs';
import {sha256} from '../fast-vehicle-state-20261028/patch.mjs';

// Private copies of the active production modules (downloaded read-only); not committed.
const root = process.env.WAYON_ACTIVE_MODULE_DIR || '/Users/hyuklee/Documents/my-traverse-web-20261110';
const require = createRequire(import.meta.url);
const {Miniflare} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/Documents/sunnypilot/apps/my-traverse-web/node_modules/miniflare');
const baseline = placePatch(readFileSync(join(root, 'stage-candidate.worker.js'), 'utf8'));
const KEY = 'wayon_' + 'a'.repeat(48), DEVICE = 'owner';
const hash = value => createHash('sha256').update(value).digest('hex');
const point = (minute, extra = {}) => ({time: new Date(Date.UTC(2026, 10, 8, 7, 24 + minute)).toISOString().replace('.000', ''),
  latitude: 35 + minute / 1000, longitude: 128, speedMps: minute % 40, ...extra});
const full = Array.from({length: 148}, (_, i) => point(i));          // 07:24-09:51, like D1
const head = Array.from({length: 34}, (_, i) => point(i, {speedMps: 1}));  // 07:24-07:57, like the server copy

test('patch is byte-exact and reversible on top of the parking-place candidate', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  const candidate = patch(baseline);
  assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
});

async function fixture(script, {serverRoute = head, serverUp = true} = {}) {
  const modules = [{type: 'ESModule', path: '/isolated/worker.js', contents: script}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type: 'ESModule', path: '/isolated/' + name, contents: readFileSync(join(root, 'stage-baseline-' + name), 'utf8')});
  }
  const serverTrip = id => ({id, device_id: DEVICE, started_at: '2026-11-08T07:24:28Z', ended_at: '2026-11-08T09:52:33Z',
    distance_m: 200700, duration_s: 8884, route: serverRoute, route_point_count: serverRoute.length});
  const mf = new Miniflare({modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14',
    d1Databases: {DB: 'trip-history-isolated'}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {WAYON_SERVER_SYNC_TOKEN: 'fixture-sync', WAYON_VIEW_TOKEN: 'fixture-view', WAYON_AI_READ_TOKEN: 'fixture-ai',
      WAYON_AI_DEVICE_ID: DEVICE, WAYON_GMONE_TOKEN: 'fixture-gmone', WAYON_PARKING_NOTIFY_TOKEN: 'fixture-notify'},
    serviceBindings: {ASSETS: () => new Response(null, {status: 404}),
      WAYON_SERVER_API: request => {
        if (!serverUp) return new Response('down', {status: 503});
        const url = new URL(request.url);
        if (url.pathname === '/v1/wayon/trips') return Response.json({schemaVersion: 'wayon-trip-read-v1',
          trips: [{...serverTrip('long'), route: undefined}]});
        const id = decodeURIComponent(url.pathname.split('/').pop());
        return Response.json({schemaVersion: 'wayon-trip-read-v1', trip: serverTrip(id)});
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
  const rows = [
    ['long', '2026-11-08T07:24:28Z', '2026-11-08T09:52:33Z', JSON.stringify(full)],
    ['legacy-keys', '2026-11-07T01:00:00Z', '2026-11-07T01:10:00Z', JSON.stringify([{time: '2026-11-07T01:00:00Z', speed_mps: 7.5}, {time: '2026-11-07T01:05:00Z', speed: '12.25'}, {time: '2026-11-07T01:09:00Z', speed: 9}])],
    ['no-speed', '2026-11-06T01:00:00Z', '2026-11-06T01:10:00Z', JSON.stringify([{time: '2026-11-06T01:00:00Z'}, {time: '2026-11-06T01:09:00Z', speedMps: null}])],
    ['broken', '2026-11-05T01:00:00Z', '2026-11-05T01:10:00Z', '[{"time":'],
    ['object', '2026-11-04T01:00:00Z', '2026-11-04T01:10:00Z', '{"speedMps": 30}'],
    // Codex review inputs: JS Number() semantics, a non-finite value next to a real maximum, non-object points.
    ['odd-values', '2026-11-03T01:00:00Z', '2026-11-03T01:10:00Z', JSON.stringify([{speed: null}, {speed: '0x10'}, {speed: []},
      {speed: [12.25]}, {speed: '1e309'}, {speed: 22}, 'bad', {speed: ''}, {speed: '08'}, {speed: 'unknown'}, {speedMps: true}])],
    ['all-odd', '2026-11-02T01:00:00Z', '2026-11-02T01:10:00Z', JSON.stringify([{speed: '1e309'}, 'bad', {speed: 'x'}])],
    // More than one 90-route batch.
    ...Array.from({length: 200}, (_, i) => [`filler-${String(i).padStart(3, '0')}`, `2026-09-01T00:${String(i % 60).padStart(2, '0')}:00Z`,
      `2026-09-01T0${Math.floor(i / 60)}:${String(i % 60).padStart(2, '0')}:30Z`, JSON.stringify([{speedMps: i / 10}, {speedMps: 1}])]),
  ];
  for (const [id, start, end, route] of rows) {
    await db.prepare('INSERT INTO trips(id,device_id,started_at,ended_at,duration_s,distance_m,route_point_count,route_json,report_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)')
      .bind(id, DEVICE, start, end, 600, 1000, 3, route, '{}', end).run();
  }
  const get = async path => {
    const r = await mf.dispatchFetch('https://isolated.test' + path, {headers: {authorization: 'Bearer ' + KEY}});
    return {status: r.status, body: await r.json()};
  };
  return {get, dispose: () => mf.dispose()};
}

test('trip detail keeps the D1 route when the server copy covers only the start of the drive', async () => {
  for (const [label, script] of [['baseline', baseline], ['patched', patch(baseline)]]) {
    const f = await fixture(script);
    try {
      const r = await f.get('/api/trips/long');
      assert.equal(r.status, 200);
      const times = r.body.route.map(p => p.time);
      if (label === 'baseline') {
        assert.equal(r.body.route.length, head.length, 'the bug: the server head overwrote the D1 route');
      } else {
        assert.equal(r.body.route.length, full.length);
        assert.equal(r.body.route_point_count, full.length);
        assert.equal(times.at(-1), full.at(-1).time);
        assert.equal(r.body.distance_m, 200700, 'other server fields still win');
      }
    } finally { await f.dispose(); }
  }
  // A server copy that covers as much time (or more) is still preferred, as before.
  const f = await fixture(patch(baseline), {serverRoute: full.map(p => ({...p, speedMps: 3}))});
  try {
    const r = await f.get('/api/trips/long');
    assert.equal(r.body.route.length, full.length);
    assert.ok(r.body.route.every(p => p.speedMps === 3));
  } finally { await f.dispose(); }
});

test('trip list maxima come from the same function over batched routes, identical to before', async () => {
  for (const serverUp of [true, false]) {
    const lists = {};
    for (const [label, script] of [['baseline', baseline], ['patched', patch(baseline)]]) {
      const f = await fixture(script, {serverUp});
      try {
        const r = await f.get('/api/trips?limit=1000');
        assert.equal(r.status, 200, label);
        lists[label] = r.body.trips;
      } finally { await f.dispose(); }
    }
    assert.deepEqual(lists.patched, lists.baseline, `identical list (server ${serverUp ? 'up' : 'down'})`);
    const byId = Object.fromEntries(lists.patched.map(t => [t.id, t.max_speed_mps]));
    assert.equal(lists.patched.length, 207);
    // With the server up its summary for 'long' (no maximum) wins the merge, exactly as before.
    assert.deepEqual({long: byId.long, legacy: byId['legacy-keys'], none: byId['no-speed'], broken: byId.broken, object: byId.object,
      odd: byId['odd-values'], allOdd: byId['all-odd'], filler: byId['filler-199']},
      {long: serverUp ? null : 39, legacy: 12.25, none: null, broken: null, object: null, odd: 22, allOdd: null, filler: 19.9});
    assert.ok(lists.patched.every(t => !('route_max_speed_mps' in t) && !('route_json' in t)));
  }
});
