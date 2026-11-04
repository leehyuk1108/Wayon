import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {baseline, OWNER, MAX, payload} from './fixture.mjs';

const fragment = readFileSync(new URL('./latest.js', import.meta.url), 'utf8');
const helpers = ['parkingBatchTimestamp', 'getBearerToken', 'constantTimeEqual', 'validDeviceId', 'parkingSignString'].map(name => {
  const start = baseline.indexOf('function ' + name + '(');
  return baseline.slice(start, baseline.indexOf('\n}', start) + 2);
}).join('\n');
const json = (body, status = 200) => Response.json(body, {status, headers: {'cache-control': 'no-store'}});

function fixture({stored = null, timeout = 100} = {}) {
  const calls = {db: [], get: [], put: []};
  let current = stored === null ? null : JSON.stringify(stored);
  const env = {WAYON_PARKING_NOTIFY_TOKEN: 'fixture-notify', WAYON_AI_READ_TOKEN: 'fixture-read', WAYON_AI_DEVICE_ID: OWNER,
    DB: {prepare(sql) { return {bind(id) { calls.db.push([sql, id]); return this; }, async first() { return {device_id: OWNER}; }}; }},
    SNAPSHOTS: {async get(key) { calls.get.push(key); return current; }, async put(key, value, options) {
      calls.put.push([key, value, JSON.parse(JSON.stringify(options))]); current = value;
    }}};
  const api = vm.runInNewContext(helpers + '\n' + fragment + '\n({handleParkingLatest,handleParkingDisplay,parkingDisplayPayload})', {
    Response, TextDecoder, TextEncoder, Uint8Array, setTimeout: (fn, ms) => setTimeout(fn, Math.min(ms, timeout)), clearTimeout,
    authenticatedDeviceId: () => OWNER, json,
  });
  async function read(pending) { const response = await pending; return {status: response.status, body: await response.json(), headers: response.headers}; }
  return {env, calls, api, raw: () => current, setRaw(value) { current = value; },
    get: () => read(api.handleParkingLatest(new Request('https://fixture.invalid/api/parking/latest'), env)),
    async post({value = payload(), raw, token = 'fixture-notify', method = 'POST', headers = {}} = {}) {
      const body = raw === undefined ? JSON.stringify(value) : raw;
      const request = new Request('https://fixture.invalid/api/parking/display?deviceId=spoofed', {
        method, headers: {'content-type': 'application/json', ...(token === null ? {} : {authorization: 'Bearer ' + token}), ...headers},
        ...(['GET', 'HEAD'].includes(method) ? {} : {body, duplex: 'half'}),
      });
      return read(await api.handleParkingDisplay(request, env));
    }};
}

test('POST stores allowlisted whole object, GET preserves old capture times, seven-day TTL and no extra queries', async () => {
  const f = fixture(), value = payload();
  value.extra = 'PRIVATE'; value.observation.extra = 'PRIVATE'; value.observation.result.extra = 'PRIVATE';
  value.observation.result.frames[0].imageBase64 = 'PRIVATE'; value.observation.result.frames[0].url = 'PRIVATE';
  value.observation.result.analysis.readings[0].private = 'PRIVATE';
  value.observation.result.inspection.surroundings[0].evidence[0].private = 'PRIVATE';
  assert.deepEqual((await f.post({value})).body, {ok: true, stored: true});
  assert.equal(f.calls.db.length, 1); assert.equal(f.calls.get.length, 1); assert.equal(f.calls.put.length, 1);
  assert.equal(f.calls.put[0][0], 'parking-display-v1:' + OWNER);
  assert.deepEqual(f.calls.put[0][2], {expirationTtl: 604800});
  const r = await f.get(); assert.equal(r.status, 200); assert.deepEqual(r.body, {ok: true, ...payload()});
  assert.equal(r.headers.get('cache-control'), 'no-store'); assert.ok(!f.raw().includes('PRIVATE'));
  assert.deepEqual(f.calls.get, ['parking-display-v1:' + OWNER, 'parking-display-v1:' + OWNER]);
  assert.equal(f.calls.db.length, 1);
});

test('dedicated notify token only, exact active server owner, fallback scope, and method guards', async () => {
  for (const token of [null, '', 'fixture-read', 'fixture-sync', 'wayon_' + 'a'.repeat(48), 'wrong']) {
    const f = fixture(); assert.equal((await f.post({token})).status, 401); assert.equal(f.calls.db.length, 0); assert.equal(f.calls.put.length, 0);
  }
  for (const secret of [undefined, '', ' fixture-notify', 'fixture-notify ', 'fixture-read']) {
    const f = fixture(); f.env.WAYON_PARKING_NOTIFY_TOKEN = secret;
    assert.equal((await f.post({token: secret || 'wrong'})).status, 401); assert.equal(f.calls.db.length, 0);
  }
  for (const scope of [undefined, 'bad', ' bad-owner ', ['fixture-owner']]) {
    const f = fixture(); f.env.WAYON_AI_DEVICE_ID = scope;
    assert.equal((await f.post()).status, 401); assert.equal(f.calls.db.length, 0);
  }
  const fallback = fixture(); delete fallback.env.WAYON_AI_DEVICE_ID; fallback.env.WAYON_LEGACY_FIREBASE_DEVICE_ID = OWNER;
  assert.equal((await fallback.post()).status, 200);
  const scoped = fixture(); scoped.env.WAYON_LEGACY_FIREBASE_DEVICE_ID = 'other-owner';
  assert.equal((await scoped.post()).status, 200);
  for (const method of ['GET', 'HEAD', 'PUT', 'DELETE', 'PATCH']) {
    const f = fixture(); assert.equal((await f.post({method})).status, 405); assert.equal(f.calls.db.length, 0);
  }
  for (const row of [null, {device_id: 'other-owner'}]) {
    const f = fixture(); f.env.DB.prepare = () => ({bind() { return this; }, async first() { return row; }});
    assert.equal((await f.post()).status, 401); assert.equal(f.calls.get.length, 0); assert.equal(f.calls.put.length, 0);
  }
});

test('schema, owner, timestamps, enums, text and normalized evidence reject without any KV write', async () => {
  const changes = [p => p.schemaVersion = 'bad', p => p.deviceId = 'other', p => delete p.observation,
    p => delete p.generatedAt, p => p.generatedAt = '2026-02-31T01:00:00Z', p => p.observation.deviceId = 'other',
    p => p.observation.jobId = 'snapshot-fixture', p => p.observation.eventId = 'replay-fixture',
    p => p.observation.jobId = '../x', p => p.observation.eventId = '', p => p.observation.status = 'bad',
    p => p.observation.parkedAt = '2027-01-01T01:00:00Z', p => delete p.observation.result,
    p => p.observation.result.analysis.exactParkingSpotKnown = true,
    p => p.observation.result.analysis.readings = Array(17).fill(p.observation.result.analysis.readings[0]),
    p => p.observation.result.frames = Array(13).fill(p.observation.result.frames[0]),
    p => p.observation.result.frames[0].phase = 'inferred', p => p.observation.result.frames[0].camera = 'driver',
    p => p.observation.result.frames[0].capturedAt = 'yesterday', p => p.observation.result.frames[0].width = 4097,
    p => p.observation.result.inspection.version = 2, p => p.observation.result.inspection.humanVerified = true,
    p => p.observation.result.inspection.status = 'failed', p => p.observation.result.inspection.coverage.completeSceneGuaranteed = true,
    p => p.observation.result.inspection.coverage.overviewViews = 97, p => p.observation.result.inspection.coverage.targetsInspected = 5,
    p => p.observation.result.inspection.readings[0].confidence = 'certain',
    p => p.observation.result.inspection.readings[0].confidence = 'conflict',
    p => p.observation.result.inspection.surroundings[0].type = 'coordinate',
    p => p.observation.result.inspection.surroundings[0].color = 'beige',
    p => p.observation.result.inspection.surroundings[0].label = 'x'.repeat(97),
  ];
  const readingChanges = [r => r.kind = 'coordinate', r => r.status = 'confident', r => r.text = ' ', r => r.text = 'x'.repeat(33),
    r => r.text = 'x\u202ey', r => r.text = 'x\ny', r => r.text = '\ud800', r => r.alternatives = ['other'],
    r => r.evidence = [], r => r.evidence[0].frameIndex = 12, r => r.evidence[0].frameIndex = 0.5,
    r => r.evidence[1].frameIndex = 0, r => r.evidence[0].box = [0, 0, 0, 1],
    r => r.evidence[0].box = [0, 0, 2, 1], r => r.evidence[0].box = [0, 0, '1', 1],
    r => r.status = 'ambiguous', r => r.text = null];
  changes.push(...readingChanges.map(change => p => change(p.observation.result.analysis.readings[0])));
  for (const [index, change] of changes.entries()) {
    const f = fixture(), value = payload(); change(value);
    const r = await f.post({value}); assert.equal(r.status, 503, 'mutation ' + index);
    assert.deepEqual(r.body, {error: 'parking_display_unavailable'}); assert.equal(f.calls.put.length, 0);
  }
});

test('marked test/simulation/snapshot/replay records are rejected even inside stripped metadata', async () => {
  for (const marker of [{test: true}, {is_test: true}, {testMode: 'yes'}, {simulation: true}, {simulated: 1},
    {isSynthetic: true}, {dry_run: true}, {mode: 'simulation'}, {source: 'snapshot-fixture'}, {origin: 'replay-candidate'},
    {jobType: 'test'}, {environment: 'test'}, {eventId: 'replay-fixture'}]) {
    const f = fixture(), value = payload(); value.privateMetadata = {nested: [marker]};
    assert.equal((await f.post({value})).status, 503); assert.equal(f.calls.put.length, 0);
  }
  const f = fixture(), value = payload(); value.test = false;
  value.observation.result.analysis.readings[0].text = '<b>TEST</b>';
  assert.equal((await f.post({value})).status, 200);
  assert.equal((await f.get()).body.observation.result.analysis.readings[0].text, '<b>TEST</b>');
});

test('empty, missing inspection and failed/skipped/pending inspection preserve baseline without fabricating extra readings', async () => {
  assert.deepEqual((await fixture().get()).body, {ok: true, observation: null});
  for (const status of [undefined, null, 'failed', 'skipped', 'pending']) {
    const f = fixture(), value = payload(), result = value.observation.result;
    if (status === undefined) delete result.inspection;
    else if (status === null) result.inspection = null;
    else { result.inspection.status = status; result.inspection.readings = []; result.inspection.surroundings = []; delete result.inspection.coverage; }
    assert.equal((await f.post({value})).status, 200);
    assert.deepEqual((await f.get()).body.observation.result.analysis, result.analysis);
  }
});

test('stale exports/jobs cannot overwrite; latest failed/no-result and null replace old success entirely', async () => {
  const previous = payload();
  const stale = [p => p.generatedAt = '2026-11-03T01:00:00Z',
    p => { p.generatedAt = '2026-11-05T01:00:00Z'; p.observation.parkedAt = '2026-09-30T01:00:00Z'; },
    p => { p.generatedAt = '2026-11-05T01:00:00Z'; p.observation.jobId = 'b'.repeat(32); },
    p => { p.generatedAt = '2026-11-05T01:00:00Z'; p.observation.parkedAt = '2026-10-02T01:00:00Z'; },
    p => p.observation.result = null];
  for (const change of stale) {
    const f = fixture({stored: previous}), value = payload(); change(value);
    assert.equal((await f.post({value})).status, 503); assert.equal(f.calls.put.length, 0);
    assert.deepEqual((await f.get()).body, {ok: true, ...previous});
  }
  for (const empty of ['same-job-failed', 'new-job-failed', 'null']) {
    const f = fixture({stored: previous}), value = payload(); value.generatedAt = '2026-11-05T01:00:00Z';
    if (empty === 'null') value.observation = null;
    else { value.observation.status = 'failed'; value.observation.result = null; }
    if (empty === 'new-job-failed') Object.assign(value.observation, {jobId: 'b'.repeat(32), eventId: 'new-event', parkedAt: '2026-10-02T01:00:00Z'});
    assert.equal((await f.post({value})).status, 200); assert.deepEqual((await f.get()).body, {ok: true, ...value});
  }
});

test('persistent old generation timestamp and unchanged heartbeat renew seven-day TTL', async () => {
  const value = payload(); value.generatedAt = '2026-10-02T01:00:00Z';
  const f = fixture({stored: value});
  for (let i = 0; i < 2; i++) assert.equal((await f.post({value})).status, 200);
  assert.equal(f.calls.put.length, 2); assert.ok(f.calls.put.every(c => c[2].expirationTtl === 604800));
  assert.equal((await f.get()).body.generatedAt, value.generatedAt);
});

test('JSON media, encoding, malformed lengths, invalid UTF-8 and raw failures never escape generic 503', async () => {
  const cases = [
    ...['', 'text/plain', 'application/jsonx', 'application/json; charset=latin1'].map(type => ({headers: {'content-type': type}})),
    {headers: {'content-encoding': 'gzip'}}, {raw: '{PRIVATE'}, {raw: 'null'}, {raw: '[]'},
    {raw: new Uint8Array([255, 254])}, ...['-1', '0', 'bad', '1', String(MAX + 1)].map(length => ({headers: {'content-length': length}})),
  ];
  for (const options of cases) {
    const f = fixture(), r = await f.post(options); assert.equal(r.status, 503); assert.deepEqual(r.body, {error: 'parking_display_unavailable'});
    assert.equal(r.headers.get('cache-control'), 'no-store'); assert.equal(f.calls.put.length, 0);
  }
  for (const raw of ['{PRIVATE', '[]', JSON.stringify(payload('other-owner')), ' '.repeat(MAX + 1)]) {
    const f = fixture(); f.setRaw(raw); const r = await f.get();
    assert.equal(r.status, 503); assert.deepEqual(r.body, {error: 'parking_latest_unavailable'});
  }
});

test('actual 196608 UTF-8 bytes are bounded for absent/forged lengths and chunked overflow', async () => {
  const value = {...payload(), padding: ''}; value.padding = 'x'.repeat(MAX - Buffer.byteLength(JSON.stringify(value)));
  const exact = JSON.stringify(value); assert.equal(Buffer.byteLength(exact), MAX);
  for (const headers of [{}, {'content-length': String(MAX)}]) assert.equal((await fixture().post({raw: exact, headers})).status, 200);
  for (const headers of [{}, {'content-length': '1'}, {'content-length': String(MAX + 1)}]) assert.equal((await fixture().post({raw: exact + ' ', headers})).status, 503);
  const unicode = JSON.stringify({...payload(), padding: '\uac00'.repeat(MAX / 2)});
  assert.ok(unicode.length < MAX); assert.ok(Buffer.byteLength(unicode) > MAX);
  const bytes = new TextEncoder().encode(unicode); let index = 0, cancelled = false;
  const stream = new ReadableStream({pull(c) { if (index >= bytes.length) c.close(); else c.enqueue(bytes.slice(index, index += 1024)); }, cancel() { cancelled = true; }});
  assert.equal((await fixture().post({raw: stream, headers: {'content-length': '1'}})).status, 503); assert.equal(cancelled, true);
});

test('DB/KV failures, slow reads and stalled body fail boundedly; timed-out pre-write work cannot later put', async () => {
  for (const stage of ['db', 'get', 'put']) {
    const f = fixture();
    if (stage === 'db') f.env.DB.prepare = () => { throw new Error('PRIVATE'); };
    else f.env.SNAPSHOTS[stage] = async () => { throw new Error('PRIVATE'); };
    const r = await f.post(); assert.equal(r.status, 503); assert.deepEqual(r.body, {error: 'parking_display_unavailable'});
  }
  let release, cancelled = false;
  const f = fixture({timeout: 10}); f.env.SNAPSHOTS.get = () => new Promise(r => { release = r; });
  assert.equal((await f.post()).status, 503); release(null); await new Promise(r => setImmediate(r)); assert.equal(f.calls.put.length, 0);
  const g = fixture({timeout: 10}); g.env.SNAPSHOTS.get = () => new Promise(() => {});
  assert.equal((await g.get()).status, 503);
  const stream = new ReadableStream({pull() { return new Promise(() => {}); }, cancel() { cancelled = true; return new Promise(() => {}); }});
  const h = fixture({timeout: 10}), start = Date.now();
  assert.equal((await h.post({raw: stream})).status, 503); assert.ok(Date.now() - start < 1000); assert.equal(cancelled, true); assert.equal(h.calls.put.length, 0);
});
