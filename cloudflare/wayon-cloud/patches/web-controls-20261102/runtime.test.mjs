import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {test} from 'node:test';
import {patchModules} from './patch.mjs';
import {baseline, columns, retained} from './fixture.mjs';

const require = createRequire(import.meta.url);
const {Miniflare, convertV4MiniflareOptions} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/.npm/_npx/32026684e21afda6/node_modules/miniflare');
const hash = value => createHash('sha256').update(value).digest('hex');
const OWNER = 'isolated-owner', OTHER = 'isolated-other', EMPTY = 'isolated-empty';
const KEY = 'wayon_' + 'a'.repeat(48), OTHER_KEY = 'wayon_' + 'b'.repeat(48);
const EMPTY_KEY = 'wayon_' + 'c'.repeat(48), REVOKED_KEY = 'wayon_' + 'd'.repeat(48);
const PATH = '/api/mobile/web-trips';
const scalarSchema = 'id TEXT PRIMARY KEY,device_id TEXT NOT NULL,started_at TEXT,ended_at TEXT,' +
  'duration_s INTEGER,distance_m REAL,start_lat REAL,start_lon REAL,end_lat REAL,end_lon REAL,' +
  'route_point_count INTEGER,source TEXT,route_name TEXT,segment_count INTEGER,avg_speed_mps REAL,max_speed_mps REAL';
const iso = n => new Date(Date.UTC(2026, 10, 1) + n * 60000).toISOString();
const row = (device, n, overrides = {}) => ({id: device + '-' + n, device_id: device,
  started_at: iso(n), ended_at: iso(n + 1), duration_s: 60, distance_m: 120,
  start_lat: 37.5, start_lon: 127.1, end_lat: 37.6, end_lon: 127.2,
  route_point_count: 12, source: 'isolated', route_name: 'test-route', segment_count: 1,
  avg_speed_mps: 2, max_speed_mps: 4, ...overrides});

async function fixture() {
  const modules = Object.entries(patchModules(baseline, retained))
    .map(([name, contents]) => ({type: 'ESModule', path: '/isolated/' + name, contents}));
  let outbound = 0;
  const options = {modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14', cf: false,
    d1Databases: {DB: 'web-controls-isolated'}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {WAYON_VIEW_TOKEN: 'isolated-view', WAYON_GMONE_TOKEN: 'isolated-collector',
      WAYON_AI_TOKEN: 'isolated-ai', WAYON_AI_DEVICE_ID: OWNER, WAYON_SERVER_SYNC_TOKEN: 'isolated-sync'},
    serviceBindings: {ASSETS: () => new Response('isolated-asset', {status: 404})},
    outboundService: () => {outbound++; return new Response(null, {status: 599});},
  };
  const mf = new Miniflare(convertV4MiniflareOptions ? convertV4MiniflareOptions(options) : options);
  try {
    const db = await mf.getD1Database('DB');
    await db.exec('CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT,last_seen_at TEXT); ' +
      'CREATE TABLE trips(' + scalarSchema + ',route_json TEXT,report_json TEXT,analysis_json TEXT,health_json TEXT); ' +
      'CREATE INDEX trips_device_ended_idx ON trips(device_id,ended_at DESC);');
    for (const [device, key, revoked] of [[OWNER, KEY, null], [OTHER, OTHER_KEY, null], [EMPTY, EMPTY_KEY, null],
      ['isolated-revoked', REVOKED_KEY, iso(0)]]) {
      await db.prepare('INSERT INTO wayon_devices VALUES(?,?,?,?)').bind(device, hash(key), revoked, 'unchanged').run();
    }
    // Any write by the new route or its authentication path fails the test.
    for (const table of ['wayon_devices', 'trips']) for (const action of ['UPDATE', 'DELETE']) {
      await db.exec(`CREATE TRIGGER no_${table}_${action} BEFORE ${action} ON ${table} BEGIN SELECT RAISE(ABORT,'read_only_violation'); END;`);
    }
    return {db, dispose: () => mf.dispose(), outbound: () => outbound,
      async insert(rows) {
        const sql = 'INSERT INTO trips(' + columns.join(',') + ',route_json,report_json,analysis_json,health_json) VALUES(' +
          Array(columns.length + 4).fill('?').join(',') + ')';
        for (let i = 0; i < rows.length; i += 100) {
          await db.batch(rows.slice(i, i + 100).map(r => db.prepare(sql).bind(...columns.map(c => r[c]),
            'not-json', 'not-json', 'not-json', 'not-json')));
        }
      },
      async call(query = '', {key = KEY, headers = {}, method = 'GET', path = PATH} = {}) {
        const requestHeaders = new Headers(headers);
        if (key !== null) requestHeaders.set('authorization', 'Bearer ' + key);
        const response = await mf.dispatchFetch('https://isolated.test' + path + query, {method, headers: requestHeaders});
        const text = await response.text();
        return {status: response.status, headers: response.headers, text, body: text ? JSON.parse(text) : null};
      },
    };
  } catch (error) {await mf.dispose(); throw error;}
}

test('native workerd/D1 authenticates, isolates owners and returns compact PWA data without mutation', async t => {
  const f = await fixture();
  try {
    const expected = row(OWNER, 2);
    await f.insert([row(OWNER, 1), expected, row(OTHER, 100)]);
    await t.test('no bearer, unknown, revoked and service credentials all deny, including forged auth headers', async () => {
      for (const key of [null, 'wrong', 'wayon_' + 'z'.repeat(48), REVOKED_KEY,
        'isolated-view', 'isolated-collector', 'isolated-ai', 'isolated-sync']) {
        const r = await f.call('?deviceId=' + OWNER, {key,
          headers: {'x-wayon-auth-device': OWNER, 'x-wayon-device-id': OWNER}});
        assert.equal(r.status, 401);
        assert.deepEqual(r.body, {error: 'unauthorized'});
      }
    });
    await t.test('registered owner overrides forged device query/header and parameters cannot change SQL', async () => {
      for (const scope of [OTHER, "' OR 1=1 --"]) {
        const r = await f.call('?deviceId=' + encodeURIComponent(scope) + '&limit=1',
          {headers: {'x-wayon-auth-device': OTHER, 'x-wayon-device-id': OTHER}});
        assert.equal(r.status, 200);
        assert.deepEqual(r.body, {trips: [expected]});
        assert.equal(r.headers.get('cache-control'), 'no-store');
        assert.match(r.headers.get('content-type'), /application\/json/);
        assert.ok(!r.text.includes(KEY) && !r.text.includes(hash(KEY)) && !r.text.includes('not-json'));
      }
      const other = await f.call('?deviceId=' + OWNER, {key: OTHER_KEY});
      assert.deepEqual(other.body, {trips: [row(OTHER, 100)]});
      assert.deepEqual((await f.call('', {key: EMPTY_KEY})).body, {trips: []});
    });
    await t.test('old endpoints still use their old registered-key gate', async () => {
      for (const path of ['/api/state', '/api/trips', '/api/trips/isolated-owner-1', '/api/json']) {
        assert.equal((await f.call('', {path, key: null, headers: {'x-wayon-auth-device': OWNER}})).status, 401);
      }
    });
    await t.test('non-GET rejects after auth; existing OPTIONS stays unchanged', async () => {
      for (const method of ['POST', 'PUT', 'PATCH', 'DELETE']) {
        assert.deepEqual((await f.call('', {method})).body, {error: 'method_not_allowed'});
        assert.equal((await f.call('', {method})).status, 405);
        assert.equal((await f.call('', {method, key: null})).status, 401);
      }
      assert.equal((await f.call('', {method: 'HEAD'})).status, 405);
      assert.equal((await f.call('', {method: 'OPTIONS', key: null})).status, 204);
    });
    await t.test('authentication and list reads leave all persisted values unchanged', async () => {
      assert.equal((await f.db.prepare('SELECT COUNT(*) AS n FROM trips').first()).n, 3);
      const devices = await f.db.prepare('SELECT last_seen_at FROM wayon_devices').all();
      assert.ok(devices.results.every(r => r.last_seen_at === 'unchanged'));
      assert.equal(f.outbound(), 0);
    });
  } finally {await f.dispose();}
});

test('native workerd/D1 preserves nullable numbers and optional history metadata exactly', async () => {
  const f = await fixture();
  try {
    const nullable = row(OWNER, 1, Object.fromEntries(columns.slice(4).map(c => [c, null])));
    const zero = row(OWNER, 2, {duration_s: 0, distance_m: 0, start_lat: 0, start_lon: 0,
      end_lat: 0, end_lon: 0, route_point_count: 0, source: null, route_name: null,
      segment_count: 0, avg_speed_mps: 0, max_speed_mps: 0});
    await f.insert([nullable, zero]);
    const r = await f.call();
    assert.equal(r.status, 200);
    assert.deepEqual(r.body, {trips: [zero, nullable]});
    for (const item of r.body.trips) assert.deepEqual(Object.keys(item).sort(), [...columns].sort());
    assert.equal(f.outbound(), 0);
  } finally {await f.dispose();}
});

test('native workerd/D1 limits default to 25 and never exceed 1000 per authenticated owner', async t => {
  const f = await fixture();
  try {
    await f.insert(Array.from({length: 1005}, (_, i) => row(OWNER, i)));
    await f.insert(Array.from({length: 5}, (_, i) => row(OTHER, 2000 + i)));
    for (const [value, count] of [[null, 25], ['', 25], ['invalid', 25], ['0', 25], ['-1', 25],
      ['1', 1], ['25', 25], ['1000', 1000], ['1001', 1000], ['999999999999', 1000],
      ['Infinity', 25], ['2.5', 2], ['1; DROP TABLE trips', 1]]) {
      await t.test('limit ' + String(value), async () => {
        const r = await f.call(value === null ? '' : '?limit=' + encodeURIComponent(value));
        assert.equal(r.status, 200);
        assert.equal(r.body.trips.length, count);
        assert.ok(r.body.trips.every(v => v.device_id === OWNER));
        assert.equal(r.body.trips[0].id, OWNER + '-1004');
        assert.equal(r.body.trips.at(-1).id, OWNER + '-' + (1005 - count));
      });
    }
    const plan = await f.db.prepare('EXPLAIN QUERY PLAN SELECT ' + columns.join(',') +
      ' FROM trips WHERE device_id=? ORDER BY ended_at DESC LIMIT ?').bind(OWNER, 25).all();
    assert.ok(plan.results.some(r => r.detail.includes('trips_device_ended_idx')));
    assert.ok(plan.results.every(r => !r.detail.includes('TEMP B-TREE')));
    assert.equal(f.outbound(), 0);
  } finally {await f.dispose();}
});

test('native workerd/D1 never evaluates heavy JSON columns, and sanitizes DB failures', async t => {
  const f = await fixture();
  try {
    await f.insert([row(OWNER, 1)]);
    await t.test('large malformed JSON in legacy columns has no effect', async () => {
      await f.db.exec('DROP TRIGGER no_trips_UPDATE;');
      await f.db.prepare('UPDATE trips SET route_json=?,report_json=?,analysis_json=?,health_json=?')
        .bind('['.repeat(1024 * 1024), 'sensitive-report', 'sensitive-analysis', 'sensitive-health').run();
      assert.deepEqual((await f.call()).body, {trips: [row(OWNER, 1)]});
    });
    await t.test('poisoned lazy JSON columns prove SELECT never accesses any legacy blob', async () => {
      await f.db.exec('ALTER TABLE trips RENAME TO trip_rows;');
      await f.db.exec('CREATE VIEW trips AS SELECT ' + columns.join(',') +
        ",json('private-invalid') AS route_json,json('private-invalid') AS report_json," +
        "json('private-invalid') AS analysis_json,json('private-invalid') AS health_json FROM trip_rows;");
      await assert.rejects(f.db.prepare('SELECT route_json FROM trips').all(), /malformed JSON/);
      assert.deepEqual((await f.call()).body, {trips: [row(OWNER, 1)]});
    });
    await t.test('D1 error is generic and does not expose query, bearer or stored values', async () => {
      await f.db.exec('DROP VIEW trips;');
      const r = await f.call();
      assert.equal(r.status, 503);
      assert.deepEqual(r.body, {error: 'web_trips_unavailable'});
      assert.equal(f.outbound(), 0);
    });
  } finally {await f.dispose();}
});
