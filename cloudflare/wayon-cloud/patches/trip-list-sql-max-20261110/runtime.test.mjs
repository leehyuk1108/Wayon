import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';
import {test} from 'node:test';
import {patch as placePatch} from '../parking-place-20261110/patch.mjs';
import {patch as historyPatch} from '../trip-history-20261110/patch.mjs';
import {patch as partialPatch} from '../trip-partial-server-20261110/patch.mjs';
import {patch, unpatch, BASELINE_SHA256, OUTPUT_SHA256} from './patch.mjs';
import {sha256} from '../fast-vehicle-state-20261028/patch.mjs';

// Private copies of the production modules (downloaded read-only); not committed.
const root = process.env.WAYON_ACTIVE_MODULE_DIR || '/Users/hyuklee/Documents/my-traverse-web-20261110';
const require = createRequire(import.meta.url);
const {Miniflare} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/Documents/sunnypilot/apps/my-traverse-web/node_modules/miniflare');
const baseline = partialPatch(historyPatch(placePatch(readFileSync(join(root, 'stage-candidate.worker.js'), 'utf8'))));
const KEY = 'wayon_' + 'a'.repeat(48), DEVICE = 'owner';
const hash = value => createHash('sha256').update(value).digest('hex');

test('patch is byte-exact and reversible on top of the deployed bundle', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  const candidate = patch(baseline);
  assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
});

// Route shapes: plain ones (SQLite path) and every odd shape the Worker must still parse itself.
const plainRoutes = {
  numbers: JSON.stringify([{speedMps: 3}, {speedMps: 27.5}, {speedMps: -4}, {time: 'x'}, {speedMps: null}]),
  integers: JSON.stringify([{speedMps: 0}, {speedMps: 12}]),
  empty: '[]',
  noSpeeds: JSON.stringify([{time: 'a'}, {latitude: 1}]),
  mixedElements: JSON.stringify(['bad', 5, null, [1], {speedMps: 9}]),
  exponent: '[{"speedMps": 1e2}, {"speedMps": 2.5e-1}]',
  smallestInteger: '[{"speedMps": -9223372036854775808}, {"speedMps": 3}]',
};
const oddRoutes = {
  codex: JSON.stringify([{speed: null}, {speed: '0x10'}, {speed: []}, {speed: [12.25]}, {speed: '1e309'}, {speed: 22}, 'bad',
    {speed: ''}, {speed: '08'}, {speed: 'unknown'}, {speedMps: true}]),
  stringSpeed: JSON.stringify([{speedMps: '5'}, {speedMps: 3}]),
  legacyKeys: JSON.stringify([{speed_mps: 7.5}, {speed: '12.25'}]),
  nullChain: JSON.stringify([{speedMps: null, speed: null}, {speedMps: -1}]),
  infinity: '[{"speedMps": 1e309}, {"speedMps": 22}]',
  negativeInfinity: '[{"speedMps": -1e309}, {"speedMps": 4}]',
  objectTop: '{"speedMps": 30}',
  stringTop: '"abc"',
  numberTop: '5',
  broken: '[{"time":',
  arraySpeed: JSON.stringify([{speedMps: [8]}, {speedMps: 2}]),
};

async function fixture(script, rows, serverUp) {
  const modules = [{type: 'ESModule', path: '/isolated/entry.mjs', contents: `
    import worker from './worker.js';
    export default {async fetch(request, env, ctx) {
      const statements = [];
      const DB = new Proxy(env.DB, {get(target, name) {
        if (name === 'prepare') return sql => { statements.push(sql); return target.prepare(sql); };
        const value = target[name]; return typeof value === 'function' ? value.bind(target) : value;
      }});
      const response = await worker.fetch(request, {...env, DB}, ctx);
      const headers = new Headers(response.headers);
      headers.set('x-route-reads', String(statements.filter(sql => sql.includes('SELECT id, route_json')).length));
      return new Response(response.body, {status: response.status, headers});
    }};`},
    {type: 'ESModule', path: '/isolated/worker.js', contents: script}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type: 'ESModule', path: '/isolated/' + name, contents: readFileSync(join(root, 'stage-baseline-' + name), 'utf8')});
  }
  const mf = new Miniflare({modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14',
    d1Databases: {DB: 'trip-sqlmax-isolated'}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {WAYON_SERVER_SYNC_TOKEN: 'fixture-sync', WAYON_VIEW_TOKEN: 'fixture-view', WAYON_AI_READ_TOKEN: 'fixture-ai',
      WAYON_AI_DEVICE_ID: DEVICE, WAYON_GMONE_TOKEN: 'fixture-gmone', WAYON_PARKING_NOTIFY_TOKEN: 'fixture-notify'},
    serviceBindings: {ASSETS: () => new Response(null, {status: 404}),
      WAYON_SERVER_API: () => serverUp ? Response.json({schemaVersion: 'wayon-trip-read-v1', trips: []}) : new Response('down', {status: 503})},
    outboundService: () => new Response(null, {status: 599})});
  const db = await mf.getD1Database('DB');
  await db.exec('CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT,last_seen_at TEXT);');
  await db.prepare('INSERT INTO wayon_devices VALUES(?,?,NULL,?)').bind(DEVICE, hash(KEY), 'unchanged').run();
  await db.exec('CREATE TABLE trips(id TEXT PRIMARY KEY, device_id TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT NOT NULL, ' +
    'duration_s INTEGER, distance_m REAL, start_lat REAL, start_lon REAL, end_lat REAL, end_lon REAL, ' +
    'route_point_count INTEGER NOT NULL DEFAULT 0, route_json TEXT NOT NULL, source TEXT, route_name TEXT, segment_count INTEGER, ' +
    "avg_speed_mps REAL, max_speed_mps REAL, analysis_json TEXT NOT NULL DEFAULT '{}', report_json TEXT, " +
    "health_json TEXT NOT NULL DEFAULT '{}', health_updated_at TEXT, created_at TEXT NOT NULL);");
  for (const [index, [id, route]] of rows.entries()) {
    const end = new Date(Date.UTC(2026, 9, 1) + index * 3600e3).toISOString();
    await db.prepare('INSERT INTO trips(id,device_id,started_at,ended_at,duration_s,distance_m,route_point_count,route_json,report_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)')
      .bind(id, DEVICE, end, end, 600, 1000, 2, route, '{}', end).run();
  }
  const get = async path => {
    const r = await mf.dispatchFetch('https://isolated.test' + path, {headers: {authorization: 'Bearer ' + KEY}});
    return {status: r.status, reads: Number(r.headers.get('x-route-reads')), body: await r.json()};
  };
  return {get, dispose: () => mf.dispose()};
}

function fuzz(count) {
  let seed = 7;
  const random = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
  const odd = Object.values(oddRoutes), plain = Object.values(plainRoutes);
  return Array.from({length: count}, (_, i) => {
    if (random() < 0.15) return [`fuzz-${i}`, odd[Math.floor(random() * odd.length)]];
    if (random() < 0.2) return [`fuzz-${i}`, plain[Math.floor(random() * plain.length)]];
    const points = Array.from({length: 1 + Math.floor(random() * 30)}, () => ({speedMps: Math.round(random() * 4000) / 100}));
    return [`fuzz-${i}`, JSON.stringify(points)];
  });
}

test('list maxima are identical to the deployed bundle for every route shape, with or without the server', async () => {
  const rows = [...Object.entries(plainRoutes), ...Object.entries(oddRoutes), ...fuzz(240)];
  for (const serverUp of [true, false]) {
    const results = {};
    for (const [label, script] of [['deployed', baseline], ['patched', patch(baseline)]]) {
      const f = await fixture(script, rows, serverUp);
      try { results[label] = await f.get('/api/trips?limit=1000'); } finally { await f.dispose(); }
    }
    assert.equal(results.patched.status, 200);
    assert.deepEqual(results.patched.body, results.deployed.body, `identical list (server ${serverUp ? 'up' : 'down'})`);
    const byId = Object.fromEntries(results.patched.body.trips.map(t => [t.id, t.max_speed_mps]));
    assert.equal(byId.numbers, 27.5); assert.equal(byId.empty, null); assert.equal(byId.noSpeeds, null);
    assert.equal(byId.mixedElements, 9); assert.equal(byId.exponent, 100); assert.equal(byId.codex, 22);
    assert.equal(byId.stringSpeed, 5); assert.equal(byId.nullChain, 0); assert.equal(byId.infinity, 22);
    assert.equal(byId.objectTop, null); assert.equal(byId.broken, null); assert.equal(byId.arraySpeed, 8);
    assert.equal(byId.smallestInteger, 3); assert.equal(byId.negativeInfinity, 4);
    // Only routes with odd points are still read into the Worker (one batch per D1 summary call; with the
    // server down the existing fallback calls it twice). The deployed bundle read every route.
    const calls = serverUp ? 1 : 2;
    assert.equal(results.deployed.reads, calls * Math.ceil(rows.length / 90));
    assert.equal(results.patched.reads, calls);
  }
});

test('a list of plain routes reads no route into the Worker', async () => {
  const rows = fuzz(120).filter(([, route]) => !Object.values(oddRoutes).includes(route));
  const f = await fixture(patch(baseline), rows, false);
  try {
    const r = await f.get('/api/trips?limit=1000');
    assert.equal(r.status, 200);
    assert.equal(r.body.trips.length, rows.length);
    assert.equal(r.reads, 0);
  } finally { await f.dispose(); }
});
