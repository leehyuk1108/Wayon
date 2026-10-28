import assert from 'node:assert/strict';
import test from 'node:test';
import {readFileSync} from 'node:fs';
import {BASELINE_SHA256, namedFunction, patch, sha256} from './patch.mjs';
import {baseline, candidate, COLLECTOR, DEVICE, KEY, OTHER_KEY, iso, load, mockEnv, payload, request, sqliteEnv} from './test-support.mjs';

const post = async (h, data = payload(), headers, query, worker = load().worker) => worker.fetch(request('POST', data, headers, query), h.env, {});
const collectorPost = (h, data = payload({source: 'gmone-direct'})) => post(h, data, {authorization: `Bearer ${COLLECTOR}`});
const ackCalls = h => h.calls.filter(call => call.sql.includes('UPDATE gmone_refresh_requests'));

test('baseline reproduces lost update, missing GET, and array acceptance', async () => {
  const h = sqliteEnv();
  try {
    const worker = load(baseline).worker;
    h.env.ASSETS = {fetch: async () => new Response('not found', {status: 404})};
    assert.equal((await post(h, payload(), {}, '', worker)).status, 200);
    assert.equal((await post(h, payload({vehicleUpdatedAt: iso(-50000), status: {fuel: 'old'}}), {}, '', worker)).status, 200);
    assert.equal(JSON.parse(h.stored().payload_json).status.fuel, 'old');
    assert.notEqual((await worker.fetch(request('GET'), h.env, {})).status, 200);
    assert.equal((await post(h, payload({status: []}), {}, '', worker)).status, 200);
  } finally { h.sqlite.close(); }
});

test('rejected atomic write never ACKs and performs no status pre-read', async () => {
  const h = mockEnv({writeResult: {success: true, meta: {changes: 0}}});
  const response = await collectorPost(h);
  assert.equal(response.status, 409);
  assert.deepEqual(await response.json(), {ok: false, stored: false, error: 'snapshot_not_newer'});
  assert.equal(ackCalls(h).length, 0);
  assert.equal(h.calls.filter(call => call.method === 'first' && !call.sql.includes('wayon_devices')).length, 0);
});

for (const [name, options] of [
  ['DB exception', {writeError: true}], ['missing changes', {writeResult: {success: true}}],
  ['explicit DB failure', {writeResult: {success: false, meta: {changes: 1}}}],
  ['negative changes', {writeResult: {success: true, meta: {changes: -1}}}],
  ['unexpected changes', {writeResult: {success: true, meta: {changes: 2}}}],
  ['string changes', {writeResult: {success: true, meta: {changes: '1'}}}],
]) test(`${name} cannot ACK`, async () => {
  const h = mockEnv(options);
  const response = await collectorPost(h);
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), {error: 'gmone_status_unavailable'});
  assert.equal(ackCalls(h).length, 0);
});

test('ACK exception reports unavailable even if snapshot was saved', async () => {
  const h = mockEnv({ackError: true});
  assert.equal((await collectorPost(h)).status, 503);
  assert.equal(ackCalls(h).length, 1);
});

test('ACK explicit failure is not a successful response', async () => {
  const h = mockEnv({ackResult: {success: false}});
  assert.equal((await collectorPost(h)).status, 503);
});

test('bounded body rejects chunked bytes before JSON.parse, even if secrets would strip smaller', async () => {
  let parses = 0, cancelled = false;
  const worker = load(candidate, {...JSON, stringify: JSON.stringify, parse: (...args) => { parses++; return JSON.parse(...args); }}).worker;
  const stream = new ReadableStream({
    pull(controller) { controller.enqueue(new Uint8Array(65536).fill(32)); },
    cancel() { cancelled = true; },
  });
  const h = mockEnv();
  const response = await post(h, stream, {'content-length': '1'}, '', worker);
  assert.equal(response.status, 413);
  assert.equal(parses, 0);
  assert.equal(cancelled, true);
  assert.equal(h.calls.filter(c => c.method === 'run').length, 0);
});

test('oversized declared body is not read', async () => {
  let reads = 0;
  const h = mockEnv();
  const req = {headers: new Headers({'content-length': '262145', 'x-wayon-auth-device': DEVICE}),
    get body() { reads++; throw new Error('must not read'); }};
  assert.equal((await load().handleGmoneStatus(req, h.env)).status, 413);
  assert.equal(reads, 0);
});

for (const [name, data, headers = {}] of [
  ['invalid JSON', '{'], ['null envelope', 'null'], ['array envelope', '[]'],
  ['array status', payload({status: []})], ['null status', payload({status: null})],
  ['empty status', payload({status: {}})], ['secret-only status', payload({status: {password: 'synthetic'}})],
  ['wrong schema', payload({schemaVersion: 'v2'})], ['object source', payload({source: {}})],
  ['missing collection', payload({collectedAt: undefined})], ['epoch zero', payload({collectedAt: '1970-01-01T00:00:00Z'})],
  ['invalid day rollover', payload({vehicleUpdatedAt: '2026-02-30T00:00:00Z'})],
  ['date only', payload({vehicleUpdatedAt: '2026-10-28'})], ['numeric epoch', payload({vehicleUpdatedAt: 1793190000})],
  ['bad offset', payload({vehicleUpdatedAt: '2026-10-28T11:00:00+24:00'})],
  ['future collection', payload({collectedAt: iso(120001)})],
  ['old collection', payload({collectedAt: iso(-86400001)})],
  ['future vehicle', payload({vehicleUpdatedAt: iso(120001)})],
  ['vehicle after collection', payload({collectedAt: iso(-300000), vehicleUpdatedAt: iso(-1000)})],
  ['Android missing actual time', payload({vehicleUpdatedAt: null})],
  ['bad scope', payload({clientScope: 'wrong'})], ['null scope', payload({clientScope: null})],
  ['number scope', payload({clientScope: 123})], ['scope suffix', payload({clientScope: 'a'.repeat(65)})],
  ['prototype key', '{"__proto__":{},"schemaVersion":"wayon-gmone-v1","status":{}}'],
  ['depth limit', payload({status: JSON.parse('{"x":'.repeat(34) + '1' + '}'.repeat(34))})],
  ['node limit', payload({status: Object.fromEntries(Array.from({length: 4100}, (_, i) => ['k' + i, i]))})],
  ['negative length', payload(), {'content-length': '-1'}],
  ['invalid UTF8', new Uint8Array([0xff, 0xfe])],
]) test(`malformed upload: ${name}`, async () => {
  const h = mockEnv();
  const response = await post(h, data, headers);
  assert.equal(response.status, 400);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(h.calls.filter(c => c.method === 'run').length, 0);
});

test('GET is D1-only, no SNAPSHOTS binding, empty result is null', async () => {
  const h = mockEnv(); delete h.env.SNAPSHOTS;
  const response = await load().worker.fetch(request('GET'), h.env, {});
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), {vehicleStatus: null});
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(h.calls.length, 2);
  assert.ok(h.calls.every(c => c.method === 'first'));
});

test('GET DB failure has no error details or remote fallback', async () => {
  const h = mockEnv({readError: true});
  const response = await load().worker.fetch(request('GET'), h.env, {});
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), {error: 'gmone_status_unavailable'});
});

test('GET authentication DB failure is no-store 503, not remote fallback or access', async () => {
  const h = mockEnv({authError: true});
  const response = await load().worker.fetch(request('GET'), h.env, {});
  assert.equal(response.status, 503);
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.deepEqual(await response.json(), {error: 'gmone_status_unavailable'});
  assert.equal(h.calls.length, 1);
});

for (const token of ['', 'wrong', COLLECTOR, 'synthetic-legacy-view']) test(`GET rejects non-device credential: ${token || 'absent'}`, async () => {
  const h = mockEnv();
  const response = await load().worker.fetch(request('GET', null, {authorization: `Bearer ${token}`, 'x-wayon-auth-device': DEVICE}), h.env, {});
  assert.equal(response.status, 401);
  assert.equal(h.calls.filter(c => c.sql.includes('gmone_latest')).length, 0);
});

test('POST rejects forged internal identity before body consumption', async () => {
  const h = mockEnv();
  const response = await post(h, '{', {authorization: 'Bearer wrong', 'x-wayon-auth-device': DEVICE});
  assert.equal(response.status, 401);
  assert.equal(h.calls.length, 0);
});

test('hash pin and exact function patch leave identity, collector and remote logic untouched', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  assert.throws(() => patch(baseline + '\n'), /unknown production bundle/);
  assert.throws(() => patch(candidate), /unknown production bundle/);
  for (const name of ['gmoneDeviceId', 'sanitizeGmonePayload', 'authorizeGmoneUpload', 'authenticateDeviceKey', 'scopedDeviceRequest', 'fetchVehicleStatus', 'fetchMergedVehicleStatus', 'handleGmoneRefreshRequest', 'handleGmoneRefreshPoll']) {
    assert.equal(namedFunction(baseline, name), namedFunction(candidate, name), name);
  }
  if (process.env.WAYON_FAST_STATE_CANDIDATE) {
    assert.equal(readFileSync(process.env.WAYON_FAST_STATE_CANDIDATE, 'utf8'), candidate);
  }
});

test('SQLite: older actual epoch cannot replace newer despite later receipt; no rejected ACK', async () => {
  const h = sqliteEnv();
  try {
    h.sqlite.prepare('INSERT INTO gmone_refresh_requests VALUES (?, ?, NULL)').run('collector-device', iso(-500));
    assert.equal((await collectorPost(h)).status, 200);
    const before = h.stored('collector-device');
    assert.equal(h.refresh('collector-device').completed_at, null);
    assert.equal((await collectorPost(h, payload({source: 'gmone-direct', collectedAt: iso(0), vehicleUpdatedAt: iso(-20000), status: {fuel: 'old'}}))).status, 409);
    assert.deepEqual(h.stored('collector-device'), before);
    assert.equal(h.refresh('collector-device').completed_at, null);
    assert.equal(ackCalls(h).length, 1);
    assert.equal((await collectorPost(h, payload({source: 'gmone-direct', collectedAt: iso(0), vehicleUpdatedAt: iso(-5000), status: {fuel: 'new'}}))).status, 200);
    assert.equal(JSON.parse(h.stored('collector-device').payload_json).status.fuel, 'new');
    assert.equal(h.refresh('collector-device').completed_at, iso(0));
  } finally { h.sqlite.close(); }
});

test('SQLite: successful phone writes never complete collector requests, even with spoofed source', async () => {
  const h = sqliteEnv();
  try {
    h.sqlite.prepare('INSERT INTO gmone_refresh_requests VALUES (?, ?, NULL)').run(DEVICE, iso(-2000));
    h.sqlite.prepare('INSERT INTO gmone_refresh_requests VALUES (?, ?, NULL)').run('collector-device', iso(-2000));
    assert.equal((await post(h)).status, 200);
    assert.equal((await post(h, payload({source: 'gmone-direct'}))).status, 200);
    assert.equal((await collectorPost(h, payload())).status, 200);
    assert.equal(h.refresh().completed_at, null);
    assert.equal(h.refresh('collector-device').completed_at, null);
    assert.equal(ackCalls(h).length, 0);
  } finally { h.sqlite.close(); }
});

test('SQLite: same-epoch full enriches basic, including an earlier full receipt; later basic cannot erase it', async () => {
  const h = sqliteEnv();
  try {
    assert.equal((await post(h)).status, 200);
    const full = payload({collectedAt: iso(-2000), status: {...payload().status, gmone_details: {module: {info: {version: 1}, settings: {enabled: false}}}}});
    assert.equal((await post(h, full)).status, 200);
    const before = h.stored();
    assert.equal((await post(h, payload({collectedAt: iso(0)}))).status, 409);
    assert.deepEqual(h.stored(), before);
    assert.equal((await post(h, {...full, collectedAt: iso(0)})).status, 200);
    assert.equal((await post(h, {...full, collectedAt: iso(-3000)})).status, 409);
    const cleared = structuredClone(full); cleared.collectedAt = iso(0); cleared.status.gmone_details.module.info = null;
    assert.equal((await post(h, cleared)).status, 409);
  } finally { h.sqlite.close(); }
});

test('SQLite: incomparable equal-size partial snapshots and null/empty loss are rejected', async () => {
  const h = sqliteEnv();
  try {
    assert.equal((await post(h, payload({status: {fuel: 0, locked: false, details: {known: 'yes'}}}))).status, 200);
    for (const status of [
      {fuel: 0, locked: false, details: {other: 'yes'}},
      {fuel: 0, locked: false, details: {known: ''}},
      {fuel: null, locked: false, details: {known: 'yes'}},
    ]) assert.equal((await post(h, payload({collectedAt: iso(0), status}))).status, 409);
  } finally { h.sqlite.close(); }
});

test('SQLite: known actual epoch beats unknown legacy, unknown never replaces known', async () => {
  const h = sqliteEnv();
  try {
    const legacy = payload({source: 'gmone-direct', vehicleUpdatedAt: null});
    assert.equal((await post(h, legacy)).status, 200);
    assert.equal((await post(h, payload())).status, 200);
    assert.equal((await post(h, {...legacy, collectedAt: iso(0)})).status, 409);
  } finally { h.sqlite.close(); }
});

test('SQLite: legacy collectors preserve optional shape, microseconds, secret stripping and refresh ACK', async () => {
  const h = sqliteEnv();
  try {
    h.sqlite.prepare('INSERT INTO gmone_refresh_requests VALUES (?, ?, NULL)').run('collector-device', iso(-2000));
    const data = payload({source: 'gmone-direct', collectedAt: '2026-10-28T10:59:59.123456+00:00', vehicleUpdatedAt: null,
      deviceId: 'victim-device', email: 'synthetic@example.test', password: 'synthetic',
      health: {records: [{code: 'P0000', ticket_uuid: 'synthetic'}]}, module: {enabled: true}, diagnostic: {ok: true},
      status: {fuel: '63', nested: {access_token: 'synthetic', safe: 1}}, vehicle: {safe: true},
    });
    const response = await post(h, data, {authorization: `Bearer ${COLLECTOR}`, 'x-wayon-auth-device': 'victim-device'}, '?deviceId=victim-device');
    assert.equal(response.status, 200);
    assert.equal((await response.json()).deviceId, 'collector-device');
    const stored = JSON.parse(h.stored('collector-device').payload_json);
    assert.equal(h.stored('victim-device'), undefined);
    assert.equal(stored.deviceId, undefined);
    assert.equal(stored.email, undefined); assert.equal(stored.password, undefined);
    assert.deepEqual(stored.status.nested, {safe: 1});
    assert.deepEqual(stored.health, {records: [{code: 'P0000'}]});
    assert.deepEqual(stored.module, {enabled: true}); assert.deepEqual(stored.vehicle, {safe: true});
    assert.equal(stored.collectedAt, '2026-10-28T10:59:59.123Z');
    assert.equal(h.refresh('collector-device').completed_at, iso(0));
  } finally { h.sqlite.close(); }
});

test('SQLite: actual device identity wins all overrides; scope round-trips and is not authorization', async () => {
  const h = sqliteEnv();
  try {
    const scope = 'AB'.repeat(32);
    assert.equal((await post(h, payload({deviceId: 'other-device', clientScope: scope}), {'x-wayon-auth-device': 'other-device', 'x-wayon-device-id': 'other-device'}, '?deviceId=other-device')).status, 200);
    assert.equal(h.stored('other-device'), undefined);
    const response = await load().worker.fetch(request('GET', null, {'x-wayon-auth-device': 'other-device'}, '?deviceId=other-device'), h.env, {});
    const result = await response.json();
    assert.equal(result.vehicleStatus.clientScope, scope.toLowerCase());
    assert.deepEqual(result.vehicleStatus.data, payload().status);
    assert.equal(result.vehicleStatus.updatedAt, iso(-10000));
    assert.equal(result.vehicleStatus.collectedAt, iso(-1000));
    assert.equal(result.vehicleStatus.receivedAt, iso(0));
    assert.equal(response.headers.get('cache-control'), 'no-store');
    const other = await load().worker.fetch(request('GET', null, {authorization: `Bearer ${OTHER_KEY}`}, '?deviceId=' + DEVICE), h.env, {});
    assert.deepEqual(await other.json(), {vehicleStatus: null});
    h.sqlite.prepare('UPDATE wayon_devices SET revoked_at = ? WHERE device_id = ?').run(iso(0), DEVICE);
    assert.equal((await load().worker.fetch(request('GET'), h.env, {})).status, 401);
  } finally { h.sqlite.close(); }
});

test('SQLite: no scope remains supported; invalid stored scope is omitted; array/corrupt status is null', async () => {
  const h = sqliteEnv();
  try {
    await post(h);
    for (const data of [payload(), payload({clientScope: 'bad'}), payload({status: []}), null]) {
      h.sqlite.prepare('UPDATE gmone_latest SET payload_json = ?').run(JSON.stringify(data));
      const response = await load().worker.fetch(request('GET'), h.env, {});
      assert.equal(response.status, 200);
      const result = await response.json();
      if (data === null || Array.isArray(data.status)) assert.equal(result.vehicleStatus, null);
      else assert.equal(result.vehicleStatus.clientScope, undefined);
    }
    h.sqlite.prepare('UPDATE gmone_latest SET payload_json = ?').run('{');
    assert.deepEqual(await (await load().worker.fetch(request('GET'), h.env, {})).json(), {vehicleStatus: null});
  } finally { h.sqlite.close(); }
});

test('SQLite: reordered concurrent submissions finish with newest/fullest snapshot', async () => {
  const h = sqliteEnv();
  try {
    const responses = await Promise.all(Array.from({length: 30}, (_, i) => {
      const epoch = -100000 + (i % 5) * 1000;
      const status = i % 2 ? {fuel: epoch, gmone_details: {module: {enabled: false}}} : {fuel: epoch};
      return post(h, payload({vehicleUpdatedAt: iso(epoch), status}));
    }));
    assert.ok(responses.every(r => [200, 409].includes(r.status)));
    assert.equal(h.stored().vehicle_updated_at, iso(-96000));
    assert.deepEqual(JSON.parse(h.stored().payload_json).status.gmone_details.module, {enabled: false});
  } finally { h.sqlite.close(); }
});
