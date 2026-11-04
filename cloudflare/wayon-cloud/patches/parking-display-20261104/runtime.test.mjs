import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {test} from 'node:test';
import {patchModules} from './patch.mjs';
import {baseline, retained, payload} from './fixture.mjs';
const require = createRequire(import.meta.url);
const {Miniflare, convertV4MiniflareOptions} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/.npm/_npx/32026684e21afda6/node_modules/miniflare');
const KEY = 'wayon_' + 'a'.repeat(48), OTHER = 'wayon_' + 'b'.repeat(48), REVOKED = 'wayon_' + 'c'.repeat(48);
const hash = value => createHash('sha256').update(value).digest('hex');

async function fixture(bindings = {}) {
  let outbound = 0;
  const modules = [
    {type: 'ESModule', path: '/isolated/entry.mjs', contents: `
      import worker from './worker.js';
      export default {async fetch(request, env, ctx) {
        const queries = [];
        const DB = {prepare(sql) {
          queries.push(sql);
          if (queries.length > 1 || !/^\\s*SELECT device_id FROM wayon_devices\\s+WHERE (?:key_hash|device_id) = \\? AND revoked_at IS NULL\\s*$/.test(sql)) {
            throw new Error('unexpected_database_access');
          }
          return env.DB.prepare(sql);
        }};
        const response = await worker.fetch(request, {...env, DB}, ctx);
        const headers = new Headers(response.headers);
        headers.set('x-test-auth-reads', String(queries.length));
        return new Response(response.body, {status: response.status, headers});
      }};`},
    ...Object.entries(patchModules(baseline, retained)).map(([name, contents]) => ({type: 'ESModule', path: '/isolated/' + name, contents})),
  ];
  const options = {modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14', cf: false,
    d1Databases: {DB: 'parking-isolated'}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {WAYON_SERVER_SYNC_TOKEN: 'fixture-sync', WAYON_VIEW_TOKEN: 'fixture-view',
      WAYON_AI_READ_TOKEN: 'fixture-ai', WAYON_AI_DEVICE_ID: 'owner', WAYON_GMONE_TOKEN: 'fixture-gmone',
      WAYON_PARKING_NOTIFY_TOKEN: 'fixture-notify', ...bindings},
    serviceBindings: {ASSETS: () => new Response(null, {status: 404})},
    outboundService: () => { outbound++; return new Response(null, {status: 599}); },
  };
  const mf = new Miniflare(convertV4MiniflareOptions ? convertV4MiniflareOptions(options) : options);
  try {
    const db = await mf.getD1Database('DB'), kv = await mf.getKVNamespace('SNAPSHOTS');
    await db.exec('CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT,last_seen_at TEXT);');
    for (const [id, key, revoked] of [['owner', KEY, null], ['other', OTHER, null], ['revoked', REVOKED, '2026-11-01']]) {
      await db.prepare('INSERT INTO wayon_devices VALUES(?,?,?,?)').bind(id, hash(key), revoked, 'unchanged').run();
    }
    for (const action of ['INSERT', 'UPDATE', 'DELETE']) await db.exec(
      `CREATE TRIGGER no_${action} BEFORE ${action} ON wayon_devices BEGIN SELECT RAISE(ABORT,'read_only_violation'); END;`);
    return {db, kv, outbound: () => outbound, dispose: () => mf.dispose(),
      async call({key = KEY, method = 'GET', query = '', path = '/api/parking/latest', headers = {}, value} = {}) {
        const h = new Headers(headers); if (key !== null) h.set('authorization', 'Bearer ' + key);
        if (value !== undefined) h.set('content-type', 'application/json');
        const r = await mf.dispatchFetch('https://isolated.test' + path + query, {method, headers: h,
          ...(value === undefined ? {} : {body: JSON.stringify(value)})});
        const raw = await r.text();
        return {status: r.status, body: raw ? JSON.parse(raw) : null, headers: r.headers};
      }};
  } catch (error) { await mf.dispose(); throw error; }
}

test('native workerd device GET and dedicated publisher POST use KV with one read-only D1 auth lookup', async t => {
  const f = await fixture();
  const publish = value => f.call({key: 'fixture-notify', method: 'POST', path: '/api/parking/display', value});
  try {
    await t.test('GET denies missing, invalid, revoked and all non-device tokens despite forged owner headers', async () => {
      for (const key of [null, 'wrong', REVOKED, 'wayon_' + 'd'.repeat(48), 'fixture-view', 'fixture-ai', 'fixture-gmone', 'fixture-sync', 'fixture-notify']) {
        const r = await f.call({key, query: '?deviceId=owner', headers: {'x-wayon-auth-device': 'owner', 'x-wayon-device-id': 'owner'}});
        assert.equal(r.status, 401); assert.deepEqual(r.body, {error: 'unauthorized'});
      }
    });
    await t.test('POST rejects device/read/other service tokens and accepts only notify token before generic auth', async () => {
      for (const key of [null, KEY, OTHER, REVOKED, 'fixture-ai', 'fixture-sync', 'fixture-view', 'fixture-gmone']) {
        const r = await f.call({key, method: 'POST', path: '/api/parking/display', value: payload('owner')});
        assert.equal(r.status, 401); assert.equal(r.headers.get('x-test-auth-reads'), '0');
      }
      const r = await publish(payload('owner'));
      assert.equal(r.status, 200); assert.deepEqual(r.body, {ok: true, stored: true});
      assert.equal(r.headers.get('x-test-auth-reads'), '1'); assert.equal(r.headers.get('cache-control'), 'no-store');
      const listing = await f.kv.list({prefix: 'parking-display-v1:'}); assert.equal(listing.keys.length, 1);
      assert.ok(Math.abs(listing.keys[0].expiration - Date.now() / 1000 - 604800) < 5);
    });
    await t.test('GET ignores caller owner/URL and returns only its authenticated KV object', async () => {
      await f.kv.put('parking-display-v1:other', JSON.stringify({...payload('other'), observation: null}));
      for (const [key, owner, spoof] of [[KEY, 'owner', 'other'], [OTHER, 'other', 'owner']]) {
        const r = await f.call({key, query: '?deviceId=' + spoof + '&url=https://evil.invalid',
          headers: {'x-wayon-auth-device': spoof, 'x-wayon-device-id': spoof}});
        assert.equal(r.status, 200); assert.equal(r.body.deviceId, owner);
        assert.equal(r.headers.get('cache-control'), 'no-store'); assert.equal(r.headers.get('x-test-auth-reads'), '1');
      }
      assert.deepEqual((await f.call()).body, {ok: true, ...payload('owner')});
    });
    await t.test('publisher cannot select another owner, simulation/replay reject, no changes on failure', async () => {
      const saved = await f.kv.get('parking-display-v1:owner');
      for (const change of [p => p.deviceId = 'other', p => p.test = true, p => p.observation.jobId = 'snapshot-fixture',
        p => p.observation.eventId = 'replay-fixture', p => p.observation.result.simulation = true]) {
        const value = payload('owner'); change(value); const r = await publish(value);
        assert.equal(r.status, 503); assert.deepEqual(r.body, {error: 'parking_display_unavailable'});
      }
      assert.equal(await f.kv.get('parking-display-v1:owner'), saved);
    });
    await t.test('methods deny and inherited OPTIONS/recognition route remain unchanged', async () => {
      for (const method of ['POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']) assert.equal((await f.call({method})).status, 405);
      for (const method of ['GET', 'PUT', 'DELETE', 'HEAD']) {
        assert.equal((await f.call({method, key: 'fixture-notify', path: '/api/parking/display'})).status, 405);
      }
      assert.equal((await f.call({method: 'POST', key: null})).status, 401);
      assert.equal((await f.call({method: 'OPTIONS', key: null})).status, 204);
      assert.equal((await f.call({path: '/api/parking/recognition', method: 'POST'})).status, 401);
    });
    await t.test('latest failed/no-result replaces success, older job cannot restore it', async () => {
      const value = payload('owner'); value.generatedAt = '2026-11-05T01:00:00Z';
      Object.assign(value.observation, {jobId: 'b'.repeat(32), eventId: 'new-event', parkedAt: '2026-10-02T01:00:00Z', status: 'failed', result: null});
      assert.equal((await publish(value)).status, 200); assert.deepEqual((await f.call()).body, {ok: true, ...value});
      const stale = payload('owner'); stale.generatedAt = '2026-11-06T01:00:00Z';
      assert.equal((await publish(stale)).status, 503); assert.deepEqual((await f.call()).body, {ok: true, ...value});
    });
    await t.test('corrupt or wrong-owner stored JSON cannot escape; missing key is empty', async () => {
      for (const raw of ['{PRIVATE', JSON.stringify(payload('other'))]) {
        await f.kv.put('parking-display-v1:owner', raw); const r = await f.call();
        assert.equal(r.status, 503); assert.deepEqual(r.body, {error: 'parking_latest_unavailable'});
      }
      await f.kv.delete('parking-display-v1:owner'); assert.deepEqual((await f.call()).body, {ok: true, observation: null});
    });
    assert.equal(f.outbound(), 0);
    assert.ok((await f.db.prepare('SELECT last_seen_at FROM wayon_devices').all()).results.every(r => r.last_seen_at === 'unchanged'));
  } finally { await f.dispose(); }
});

test('native POST scope revocation and read/notify secret collision fail closed', async () => {
  for (const bindings of [{WAYON_AI_DEVICE_ID: 'revoked'}, {WAYON_PARKING_NOTIFY_TOKEN: 'fixture-ai'},
    {WAYON_AI_DEVICE_ID: '', WAYON_LEGACY_FIREBASE_DEVICE_ID: 'owner'}]) {
    const f = await fixture(bindings);
    try {
      const fallback = bindings.WAYON_AI_DEVICE_ID === '';
      const r = await f.call({key: bindings.WAYON_PARKING_NOTIFY_TOKEN || 'fixture-notify', method: 'POST', path: '/api/parking/display', value: payload('owner')});
      assert.equal(r.status, fallback ? 200 : 401); assert.equal(f.outbound(), 0);
    } finally { await f.dispose(); }
  }
});
