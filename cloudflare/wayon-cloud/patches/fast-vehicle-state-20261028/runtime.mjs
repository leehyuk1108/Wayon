import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {candidate, COLLECTOR, DEVICE, executable, hash, KEY, OTHER_KEY, schema} from './test-support.mjs';

const require = createRequire(import.meta.url);
const {Miniflare, convertV4MiniflareOptions} = require(process.env.MINIFLARE_MODULE || 'miniflare');
const opts = {
  modules: true,
  script: 'const fetch = () => { throw new Error("Remote fetch forbidden"); };\n' + executable(candidate),
  compatibilityDate: '2026-05-14',
  d1Databases: {DB: 'fast-state-isolated-db'},
  kvNamespaces: ['SNAPSHOTS'],
  bindings: {WAYON_GMONE_TOKEN: COLLECTOR, WAYON_LEGACY_FIREBASE_DEVICE_ID: 'collector-device'},
};
const mf = new Miniflare(convertV4MiniflareOptions ? convertV4MiniflareOptions(opts) : opts);
let assertions = 0;
function equal(actual, expected, message) { assertions++; assert.deepEqual(actual, expected, message); }
const now = Date.now();
const iso = delta => new Date(now + delta).toISOString();
const payload = overrides => ({schemaVersion: 'wayon-gmone-v1', source: 'gmone-direct-android',
  collectedAt: iso(-2000), vehicleUpdatedAt: iso(-30000), status: {fuel: '63', locked: false}, ...overrides});
async function call(method, data, token = KEY, extraHeaders = {}, query = '') {
  const response = await mf.dispatchFetch(`https://fast-state.local/api/gmone/status${query}`, {
    method, headers: {authorization: `Bearer ${token}`, 'content-type': 'application/json', ...extraHeaders},
    ...(method === 'POST' ? {body: typeof data === 'string' ? data : JSON.stringify(data)} : {}),
  });
  equal(response.headers.get('cache-control'), 'no-store');
  return {status: response.status, body: await response.json()};
}
try {
  const db = await mf.getD1Database('DB');
  for (const sql of schema.split(';').map(s => s.trim()).filter(Boolean)) await db.prepare(sql).run();
  await db.prepare('INSERT INTO wayon_devices VALUES (?, ?, NULL)').bind(DEVICE, hash(KEY)).run();
  await db.prepare('INSERT INTO wayon_devices VALUES (?, ?, NULL)').bind('other-device', hash(OTHER_KEY)).run();
  equal((await call('GET')).body, {vehicleStatus: null});
  equal((await call('GET', null, COLLECTOR)).status, 401);
  equal((await call('GET', null, 'wrong', {'x-wayon-auth-device': DEVICE})).status, 401);
  equal((await call('POST', payload(), 'wrong')).status, 401);
  equal((await call('POST', payload(), 'wrong', {'x-wayon-auth-device': DEVICE})).status, 401);
  equal((await call('POST', payload({status: []}))).status, 400);
  equal((await call('POST', payload({vehicleUpdatedAt: iso(300000)}))).status, 400);
  equal((await call('POST', payload({clientScope: null}))).status, 400);
  equal((await call('POST', '{')).status, 400);
  equal((await call('POST', JSON.stringify({password: 'x'.repeat(262145)}))).status, 413);
  equal((await call('POST', payload({deviceId: 'other-device', clientScope: 'ab'.repeat(32)}), KEY,
    {'x-wayon-auth-device': 'other-device', 'x-wayon-device-id': 'other-device'}, '?deviceId=other-device')).status, 200);
  equal(await db.prepare('SELECT id FROM gmone_latest WHERE id = ?').bind('other-device').first(), null);
  await db.prepare('INSERT INTO gmone_refresh_requests VALUES (?, ?, NULL)').bind(DEVICE, iso(-1000)).run();
  equal((await call('POST', payload({collectedAt: iso(0), vehicleUpdatedAt: iso(-60000)}))).status, 409);
  equal((await db.prepare('SELECT completed_at FROM gmone_refresh_requests WHERE id = ?').bind(DEVICE).first()).completed_at, null);
  const full = payload({clientScope: 'ab'.repeat(32), collectedAt: iso(-3000),
    status: {fuel: '63', locked: false, gmone_details: {module: {info: {version: 'test'}, settings: {enabled: false}}}}});
  equal((await call('POST', full)).status, 200);
  equal((await call('POST', payload({collectedAt: iso(0)}))).status, 409);
  const read = await call('GET', null, KEY, {'x-wayon-auth-device': 'other-device'}, '?deviceId=other-device');
  equal(read.status, 200);
  equal(read.body.vehicleStatus.data, full.status);
  equal(read.body.vehicleStatus.clientScope, 'ab'.repeat(32));
  equal(read.body.vehicleStatus.updatedAt, full.vehicleUpdatedAt);
  equal((await call('GET', null, OTHER_KEY, {}, '?deviceId=' + DEVICE)).body, {vehicleStatus: null});
  equal((await call('POST', {...full, collectedAt: iso(0)})).status, 200);
  equal((await db.prepare('SELECT completed_at FROM gmone_refresh_requests WHERE id = ?').bind(DEVICE).first()).completed_at, null);
  const replies = await Promise.all(Array.from({length: 40}, (_, i) => call('POST', payload({
    vehicleUpdatedAt: iso(-25000 + (i % 5) * 1000),
    status: i % 2 ? {fuel: i % 5, gmone_details: {module: {enabled: false}}} : {fuel: i % 5},
  }))));
  equal(replies.every(r => [200, 409].includes(r.status)), true);
  const final = (await call('GET')).body.vehicleStatus;
  equal(final.updatedAt, iso(-21000));
  equal(final.data, {fuel: 4, gmone_details: {module: {enabled: false}}});
  await db.prepare('INSERT INTO gmone_refresh_requests VALUES (?, ?, NULL)').bind('collector-device', iso(-3000)).run();
  equal((await call('POST', payload({source: 'gmone-direct', vehicleUpdatedAt: null,
    deviceId: 'other-device', email: 'synthetic@example.test', status: {fuel: '63', password: 'synthetic'},
    module: {ready: true}, health: {records: []}, diagnostic: {ok: true}}), COLLECTOR)).status, 200);
  const collector = JSON.parse((await db.prepare('SELECT payload_json FROM gmone_latest WHERE id = ?').bind('collector-device').first()).payload_json);
  equal(collector.status, {fuel: '63'});
  equal(collector.email, undefined); equal(collector.deviceId, undefined);
  equal(collector.module, {ready: true});
  assert.ok((await db.prepare('SELECT completed_at FROM gmone_refresh_requests WHERE id = ?').bind('collector-device').first()).completed_at);
  assertions++;
  await db.prepare('UPDATE gmone_refresh_requests SET completed_at = NULL WHERE id = ?').bind('collector-device').run();
  equal((await call('POST', payload({source: 'gmone-direct', vehicleUpdatedAt: null, collectedAt: iso(-4000)}), COLLECTOR)).status, 409);
  equal((await db.prepare('SELECT completed_at FROM gmone_refresh_requests WHERE id = ?').bind('collector-device').first()).completed_at, null);
  await db.prepare('UPDATE wayon_devices SET revoked_at = ? WHERE device_id = ?').bind(iso(0), DEVICE).run();
  equal((await call('GET')).status, 401);
  // Recreate with no KV binding: fast GET needs only D1, not even SNAPSHOTS.
  await mf.setOptions(convertV4MiniflareOptions ? convertV4MiniflareOptions({...opts, kvNamespaces: []}) : {...opts, kvNamespaces: []});
  equal((await call('GET', null, OTHER_KEY)).status, 200);
  console.log(JSON.stringify({runtime: 'workerd + local D1', compatibilityDate: opts.compatibilityDate,
    assertions, concurrentUploads: 40, remoteFetches: 0, deployed: false}));
} finally {
  await mf.dispose();
}
