import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {after, before, beforeEach, test} from 'node:test';
import {BASELINE_SHA256, OUTPUT_SHA256, patch, unpatch, replaceOnce, sha256} from './patch.mjs';
import {createRuntime, baseline, candidate, migration, DEVICE, OTHER_DEVICE, TOKEN, READ_TOKEN,
  KEY, OTHER_KEY, iso, payload} from './runtime.mjs';

let f;
before(async () => {f = await createRuntime();});
beforeEach(async () => {
  f.setBehavior('ok'); f.messages.length = 0;
  await f.db.exec('DELETE FROM parking_sign_notifications; UPDATE wayon_devices SET revoked_at=NULL;');
  for (const device of [DEVICE, OTHER_DEVICE]) {
    await f.db.prepare('INSERT OR IGNORE INTO push_subscriptions VALUES(?,?)').bind(device + '-fcm', device).run();
  }
});
after(async () => {if (f) await f.dispose();});
const count = async () => (await f.db.prepare('SELECT COUNT(*) AS n FROM parking_sign_notifications').first()).n;
const bad = async (p, status = 400, options = {}) => {
  assert.equal((await f.call(p, options)).status, status);
  assert.equal(await count(), 0); assert.equal(f.messages.length, 0);
};
const changeReading = change => {const p = payload(); change(p.readings[0]); return p;};
const changeEvidence = change => changeReading(r => change(r.evidence));
const withTimes = (parked, completed) => payload({parkedAt: iso(parked), completedAt: iso(completed),
  readings: [{kind: 'pillar', text: 'B12', status: 'readable', evidence: [0, 1].map(i => ({frameIndex: i,
    box: [0, 0, 1, 1], capturedAt: iso(parked - 1000 + 1000 * i), sha256: String(i).repeat(64), phase: 'parked'}))}]});

test('hash-pinned patch reverses byte-for-byte; unknown, repeat and partial input refuse', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256); assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
  for (const source of [baseline + ' ', candidate, candidate.slice(0, -1)]) assert.throws(() => patch(source));
  assert.throws(() => unpatch(candidate + ' '));
  assert.throws(() => replaceOnce('a a', 'a', 'b'));
  assert.throws(() => replaceOnce('a', 'missing', 'b'));
  const auth = source => source.slice(source.indexOf('async function authenticateAiRequest'), source.indexOf('import { createKeyDiagnostic'));
  assert.equal(auth(candidate), auth(baseline));
  const aiRoute = source => source.slice(source.indexOf('    if (pathname.startsWith("/api/ai/"))'), source.indexOf('    if (request.method === "POST" && pathname === "/api/telemetry")'));
  assert.equal(aiRoute(candidate), aiRoute(baseline));
  assert.ok(candidate.indexOf('return handleParkingRecognition(request, env, ctx);') < candidate.indexOf('const separatelyAuthorized'));
});

test('migration is additive, repeatable and does not alter existing tables or rows', async () => {
  const existing = await f.db.prepare("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'parking_sign%' ORDER BY name").all();
  const rows = await f.db.prepare('SELECT * FROM sentinel').all();
  assert.ok(!/\b(?:DROP|ALTER|DELETE|UPDATE)\b/i.test(migration.replace(/^--.*$/gm, '')));
  await f.applyMigration(); await f.applyMigration();
  assert.deepEqual((await f.db.prepare("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'parking_sign%' ORDER BY name").all()).results, existing.results);
  assert.deepEqual((await f.db.prepare('SELECT * FROM sentinel').all()).results, rows.results);
});

test('auth rejects empty, mismatch, AI read/device keys and forged caller scope', async () => {
  for (const token of [null, '', 'invalid', READ_TOKEN, KEY, OTHER_KEY]) {
    await bad(payload(), 401, {token, headers: {'x-wayon-auth-device': DEVICE, 'x-wayon-device-id': DEVICE}});
  }
  await bad(payload({deviceId: OTHER_DEVICE}), 400, {headers: {'x-wayon-auth-device': OTHER_DEVICE}});
  const p = payload();
  assert.equal((await f.call(p, {path: '/api/parking/recognition?deviceId=' + OTHER_DEVICE,
    headers: {'x-wayon-auth-device': OTHER_DEVICE, 'x-wayon-device-id': OTHER_DEVICE}})).status, 202);
  await f.done(); assert.equal(f.messages[0].token, DEVICE + '-fcm');
});

test('scope chooses explicit AI device or identical legacy fallback, never arbitrary caller', async () => {
  for (const bindings of [
    {WAYON_PARKING_NOTIFY_TOKEN: ''}, {WAYON_PARKING_NOTIFY_TOKEN: READ_TOKEN},
    {WAYON_AI_DEVICE_ID: '', WAYON_LEGACY_FIREBASE_DEVICE_ID: ''},
    {WAYON_AI_DEVICE_ID: 'bad\n'}, {WAYON_AI_DEVICE_ID: 'unregistered-device'},
    {WAYON_AI_DEVICE_ID: 12345},
  ]) {
    const isolated = await createRuntime({bindings});
    try {assert.equal((await isolated.call(payload())).status, 401); assert.equal(isolated.messages.length, 0);}
    finally {await isolated.dispose();}
  }
  const isolated = await createRuntime({bindings: {WAYON_AI_DEVICE_ID: '', WAYON_LEGACY_FIREBASE_DEVICE_ID: DEVICE}});
  try {assert.equal((await isolated.call(payload())).status, 202); await isolated.done(); assert.equal(isolated.messages[0].token, DEVICE + '-fcm');}
  finally {await isolated.dispose();}
});

test('revoked owner fails closed and method gate preserves GET-only AI authorization', async () => {
  await f.db.prepare('UPDATE wayon_devices SET revoked_at=? WHERE device_id=?').bind(iso(Date.now()), DEVICE).run();
  await bad(payload(), 401);
  await f.db.exec('UPDATE wayon_devices SET revoked_at=NULL');
  assert.equal((await f.call(undefined, {method: 'GET'})).status, 405);
  for (const method of ['POST', 'PUT', 'DELETE']) {
    assert.equal((await f.call({}, {path: '/api/ai/images/', method, token: READ_TOKEN})).status, 405);
  }
  assert.equal((await f.call(undefined, {path: '/api/ai/images/', method: 'GET', token: READ_TOKEN})).status, 400);
  assert.equal((await f.call(undefined, {path: '/api/ai/images/', method: 'GET', token: TOKEN})).status, 401);
  assert.equal((await f.call({}, {path: '/api/telemetry', token: TOKEN})).status, 401);
  assert.equal(await count(), 0);
});

test('strict top-level schema, identifiers and booleans cannot coerce or inject titles', async () => {
  for (const p of [null, [], {}, true, 1, 'payload', payload({eventId: 1}), payload({eventId: ''}),
    payload({eventId: 'a'.repeat(129)}), payload({eventId: 'event.id'}), payload({eventId: 'event\n'}),
    payload({jobId: 'a'.repeat(31)}), payload({jobId: 2}), payload({deviceId: 1234}),
    payload({test: 'false'}), payload({test: 0}), payload({test: null}), payload({test: undefined}),
    payload({phaseHint: 'unknown'}), payload({notificationTitle: 'forged'}), payload({title: 'forged'}),
    payload({readings: []}), payload({readings: Array.from({length: 17}, () => payload().readings[0])}),
    payload({readings: null})]) await bad(p);
});

test('readings reject unknown/ambiguous, empty text, controls, bidi, surrogate and extra fields', async () => {
  for (const change of [r => r.kind = 'unknown', r => r.status = 'ambiguous', r => r.text = null,
    r => r.text = '', r => r.text = ' ', r => r.text = ' B12', r => r.text = 12,
    r => r.text = 'x'.repeat(33), r => r.alternatives = [], r => r.title = 'forged',
    ...['\u0000', '\n', '\t', '\u0085', '\u202e', '\u2066', '\u200b', '\u2028', '\u2029', '\ud800'].map(c => r => r.text = 'B' + c + '12')]) {
    await bad(changeReading(change));
  }
});

test('evidence validates two unique indices, finite normalized ordered boxes and source metadata', async () => {
  const changes = [e => e.pop(), e => e[1].frameIndex = 0, e => e[1].frameIndex = 12,
    e => e[1].frameIndex = -1, e => e[1].frameIndex = 1.5, e => e[1].frameIndex = '1',
    e => e[1].frameIndex = true, e => e[0].box = [0, 0, 1], e => e[0].box = [0, 0, 1, 1, 1],
    e => e[0].box = [-0.1, 0, 1, 1], e => e[0].box = [0, 0, 1.1, 1],
    e => e[0].box = [0.5, 0, 0.5, 1], e => e[0].box = [0, 1, 1, 0],
    e => e[0].box = ['0', 0, 1, 1], e => e[0].box = [false, 0, 1, 1], e => e[0].box = [NaN, 0, 1, 1],
    e => e[0].sha256 = 'not-a-hash', e => e[0].phase = 'unknown', e => e[0].capturedAt = 'bad',
    e => delete e[0].sha256, e => e[0].extra = 1, e => e[1].sha256 = e[0].sha256];
  for (const change of changes) await bad(changeEvidence(change));
  const p = payload(); p.readings.push(structuredClone(p.readings[0]));
  p.readings[1].evidence[0].sha256 = 'f'.repeat(64); await bad(p);
});

test('source window, phaseHint and microsecond corroboration boundaries fail closed', async () => {
  const now = Math.floor(Date.now() / 1000) * 1000, parked = now - 60000;
  for (const [delta, accepted] of [[499, false], [500, true], [1000, true]]) {
    const p = withTimes(parked, now - 1000);
    p.readings[0].evidence[0].capturedAt = iso(parked);
    p.readings[0].evidence[1].capturedAt = iso(parked + delta);
    assert.equal(Boolean((await f.validate(p, now)).input), accepted);
  }
  const p = withTimes(parked, now - 1000);
  p.readings[0].evidence[0].capturedAt = iso(parked).replace('.000Z', '.000001Z');
  p.readings[0].evidence[1].capturedAt = iso(parked + 500);
  assert.equal((await f.validate(p, now)).error, 'uncorroborated_parking_reading');
  for (const change of [p => p.phaseHint = 'mixed', p => p.phaseHint = 'approach',
    p => p.readings[0].evidence[0].capturedAt = iso(parked - 120001),
    p => p.readings[0].evidence[1].capturedAt = iso(parked + 60001),
    p => p.readings[0].evidence[1].capturedAt = iso(now),
    p => {p.readings[0].evidence[1].phase = 'approach'; p.readings[0].evidence[1].capturedAt = iso(parked + 1); p.phaseHint = 'mixed';}]) {
    const input = withTimes(parked, now - 1000); change(input);
    assert.ok((await f.validate(input, now)).error);
  }
});

test('strict calendar/timezone timestamps, freshness inclusive limits and completion ordering', async () => {
  const now = Math.floor(Date.now() / 1000) * 1000;
  for (const value of [null, 123, '2026-02-30T00:00:00Z', '2026-01-01T24:00:00Z', '2026-01-01',
    '2026-01-01T00:00:00', '2026-01-01T00:00:00+99:00', iso(now) + '\n', 'bad']) {
    assert.ok((await f.validate(payload({parkedAt: value}), now)).error);
    assert.ok((await f.validate(payload({completedAt: value}), now)).error);
  }
  for (const [parked, completed, accepted] of [
    [now - 1800000, now - 600000, true], [now - 1800001, now - 600000, false],
    [now - 1800000, now - 600001, false], [now + 120000, now + 120000, true],
    [now + 120001, now + 120001, false], [now - 60000, now + 120001, false],
    [now, now - 1, false],
  ]) assert.equal(Boolean((await f.validate(withTimes(parked, completed), now)).input), accepted);
  const p = withTimes(now - 1000, now);
  p.completedAt = iso(now).replace('.000Z', '.123456+00:00');
  const valid = await f.validate(p, now);
  assert.equal(valid.data.occurredAt, iso(now).replace('.000Z', '.123Z'));
  assert.ok(valid.input.completedAt.endsWith('.123456Z'));
});

test('bounded streaming JSON reads enforce 32KiB by bytes even without Content-Length', async () => {
  await bad(payload(), 415, {headers: {'content-type': 'text/plain'}});
  await bad(payload(), 400, {raw: '{'});
  await bad(payload(), 400, {raw: new Uint8Array([0x7b, 0xff, 0x7d])});
  const p = payload(), raw = JSON.stringify(p), bytes = Buffer.byteLength(raw);
  await bad(p, 413, {raw: raw + ' '.repeat(32769 - bytes)});
  await bad(p, 413, {raw: raw + '\uAC00'.repeat(12000)});
  assert.equal((await f.call(p, {raw: raw + ' '.repeat(32768 - bytes)})).status, 202);
  await f.done(); assert.equal(f.messages.length, 1);
});

test('chunked reads cannot bypass byte cap with missing or forged short length', async () => {
  for (const headers of [{'content-type': 'application/json'}, {'content-type': 'application/json', 'content-length': '1'}]) {
    const result = await f.call({headers, chunks: [' '.repeat(20000), ' '.repeat(12769)]}, {path: '/__test/body'});
    assert.equal(result.body.status, 413); assert.equal(result.body.error, 'parking_body_too_large');
  }
  const result = await f.call({headers: {'content-type': 'application/json', 'content-length': '32769'}, chunks: ['{}']}, {path: '/__test/body'});
  assert.equal(result.body.status, 413);
  assert.equal(await count(), 0); assert.equal(f.messages.length, 0);
});

test('20 concurrent identical requests atomically claim once before held FCM completes', async () => {
  f.setBehavior('hold'); const p = payload();
  try {
    const replies = await Promise.all(Array.from({length: 20}, () => f.call(p)));
    assert.ok(replies.every(r => r.status === 202 && r.body.claimed === true && r.body.eventId === p.eventId));
    assert.equal(replies.filter(r => r.body.status === 'accepted').length, 1);
    assert.equal(replies.filter(r => r.body.status === 'duplicate').length, 19);
    await f.waitFor(() => f.messages.length === 1);
    assert.equal((await f.row()).notified_count, -1);
    assert.equal((await f.row()).finished_at, null);
    assert.equal(await count(), 1);
  } finally {f.release();}
  assert.equal((await f.done()).notified_count, 1);
});

test('payload fingerprint is canonical and conflicts never overwrite or resend', async () => {
  const p = payload(); assert.equal((await f.call(p)).status, 202); await f.done();
  const original = await f.row();
  assert.equal(original.payload_sha256, sha256(original.payload_json));
  const reordered = Object.fromEntries(Object.entries(p).reverse());
  reordered.readings[0].evidence.reverse();
  assert.equal((await f.call(reordered)).body.status, 'duplicate');
  for (const change of [p => p.jobId = 'b'.repeat(32), p => p.readings[0].text = 'C13',
    p => p.readings[0].evidence[0].box = [0, 0, 1, 1], p => p.completedAt = iso(Date.parse(p.completedAt) + 1)]) {
    const changed = structuredClone(p); change(changed);
    assert.equal((await f.call(changed)).status, 409);
  }
  assert.deepEqual(await f.row(), original); assert.equal(f.messages.length, 1);
});

test('concurrent conflicting payloads have one accepted claim and one 409', async () => {
  const p = payload(), q = structuredClone(p); q.readings[0].text = 'C13';
  const results = await Promise.all([f.call(p), f.call(q)]);
  assert.deepEqual(results.map(r => r.status).sort(), [202, 409]);
  await f.done(); assert.equal(f.messages.length, 1);
});

test('visible and data payloads use fixed Korean content, completion timestamp, channel and event tag', async () => {
  const now = Date.now(), p = withTimes(now - 20 * 60000, now - 1000);
  assert.equal((await f.call(p)).status, 202); await f.done();
  const msg = f.messages[0];
  assert.equal(msg.data.type, 'wayon_parking_sign'); assert.equal(msg.data.parkingEventId, p.eventId);
  assert.equal(msg.data.jobId, p.jobId); assert.equal(msg.data.occurredAt, iso(Date.parse(p.completedAt)));
  assert.equal(msg.data.notificationTitle, '\uC8FC\uCC28 \uC8FC\uBCC0 \uD45C\uC9C0 \uC778\uC2DD');
  assert.equal(msg.data.notificationBody, '\uAE30\uB465 B12 \u00B7 AI \uD310\uB3C5, \uC815\uD655\uD55C \uC8FC\uCC28 \uC704\uCE58\uB294 \uC544\uB2D8');
  assert.deepEqual(msg.notification, {title: msg.data.notificationTitle, body: msg.data.notificationBody});
  assert.deepEqual(msg.android.notification, {channel_id: 'wayon_parking_sign_alerts', tag: p.eventId});
  assert.equal(msg.android.ttl, '300s'); assert.equal(msg.data.test, 'false');
  assert.ok(Object.values(msg.data).every(v => typeof v === 'string'));
});

test('approach and mixed evidence always warn; explicit test is separately deduplicated', async () => {
  const now = Date.now();
  for (const [index, phaseHint] of ['parked', 'approach', 'mixed'].entries()) {
    const p = withTimes(now - 60000, now - 1000); p.eventId += index; p.phaseHint = phaseHint;
    p.readings[0].evidence.forEach((e, i) => {e.phase = phaseHint === 'mixed' ? (i ? 'parked' : 'approach') : phaseHint;});
    assert.equal((await f.call(p)).status, 202); await f.done(p.eventId);
    const msg = f.messages.at(-1);
    assert.equal(msg.notification.body.includes('\uC811\uADFC \uC911'), phaseHint !== 'parked');
  }
  const p = payload(); assert.equal((await f.call(p)).status, 202); await f.done();
  p.test = true; assert.equal((await f.call(p)).status, 202); await f.done(p.eventId, true);
  assert.equal((await f.call(p)).body.status, 'duplicate');
  assert.ok(f.messages.at(-1).notification.title.includes('\uD14C\uC2A4\uD2B8'));
  assert.equal(f.messages.at(-1).data.test, 'true');
});

for (const mode of ['failed', 'ambiguous', 'invalid']) test(`${mode} FCM result never permits a resend`, async () => {
  f.setBehavior(mode); const p = payload();
  assert.equal((await f.call(p)).status, 202); assert.equal((await f.done()).notified_count, -2);
  f.setBehavior('ok'); assert.equal((await f.call(p)).body.status, 'duplicate');
  assert.equal(f.messages.length, 1);
});

test('missing migration or context never claims or sends', async () => {
  await bad(payload(), 503, {headers: {'x-test-no-context': '1'}});
  const isolated = await createRuntime({migrate: false});
  try {assert.equal((await isolated.call(payload())).status, 503); assert.equal(isolated.messages.length, 0);}
  finally {await isolated.dispose();}
});

test('D1 claim failure never schedules FCM', async () => {
  await f.db.exec("CREATE TRIGGER block_claim BEFORE INSERT ON parking_sign_notifications BEGIN SELECT RAISE(FAIL, 'isolated claim failure'); END;");
  try {await bad(payload(), 503);} finally {await f.db.exec('DROP TRIGGER block_claim');}
});

test('zero subscriptions still leaves a permanent non-resend claim', async () => {
  await f.db.prepare('DELETE FROM push_subscriptions WHERE device_id=?').bind(DEVICE).run();
  const p = payload(); assert.equal((await f.call(p)).status, 202);
  assert.equal((await f.done()).notified_count, 0);
  await f.db.prepare('INSERT INTO push_subscriptions VALUES(?,?)').bind(DEVICE + '-fcm', DEVICE).run();
  assert.equal((await f.call(p)).body.status, 'duplicate'); assert.equal(f.messages.length, 0);
});

test('ambiguous D1 receipt failure preserves the claim and does not retry FCM', async () => {
  await f.db.exec("CREATE TRIGGER block_receipt BEFORE UPDATE ON parking_sign_notifications BEGIN SELECT RAISE(FAIL, 'isolated receipt failure'); END;");
  try {
    const p = payload(); assert.equal((await f.call(p)).status, 202);
    await f.waitFor(() => f.messages.length === 1); await new Promise(resolve => setTimeout(resolve, 100));
    assert.equal((await f.call(p)).body.status, 'duplicate'); assert.equal(f.messages.length, 1);
    assert.equal((await f.row()).notified_count, -1);
  } finally {await f.db.exec('DROP TRIGGER block_receipt');}
});

test('max readings and Unicode text fit FCM; no image evidence or secrets go to FCM', async () => {
  const p = payload({eventId: 'a'.repeat(128)});
  p.readings = Array.from({length: 16}, (_, i) => ({...structuredClone(p.readings[0]),
    kind: ['floor', 'zone', 'pillar', 'bay'][i % 4], text: '\uAC00'.repeat(32)}));
  assert.equal((await f.call(p)).status, 202); await f.done(p.eventId);
  assert.ok(Buffer.byteLength(JSON.stringify(f.messages[0])) < 4096);
  assert.equal(f.messages[0].data.evidence, undefined);
  assert.ok(!JSON.stringify(f.messages[0]).includes(TOKEN));
  assert.ok(f.messages[0].notification.body.includes('13\uAC74'));
});

test('existing visible FCM types retain their notification/channel/tag behavior', async () => {
  for (const data of [
    {type: 'wayon_automatic_shutdown', vehicleEventId: 'shutdown-id', notificationTitle: 'fixed', notificationBody: 'body'},
    {type: 'wayon_door_lock', vehicleEventId: 'door-id', locked: 'true', test: 'false'},
    {type: 'wayon_impact', impactId: 'impact-id'},
    {type: 'wayon_parking_unlocked', vehicleEventId: 'unlocked-id'},
  ]) assert.equal((await f.call(data, {path: '/__test/fcm'})).status, 200);
  assert.deepEqual(f.messages[0].android.notification, {channel_id: 'wayon_power_alerts', tag: 'shutdown-id'});
  assert.deepEqual(f.messages[0].notification, {title: 'fixed', body: 'body'});
  assert.deepEqual(f.messages[1].android.notification, {channel_id: 'wayon_door_lock_alerts'});
  for (const msg of f.messages.slice(2)) {assert.equal(msg.notification, undefined); assert.equal(msg.android.notification, undefined);}
});

test('actual Python make_payload -> workerd/D1/FCM -> actual Python send ACK parser', async () => {
  const cwd = fileURLToPath(new URL('../../parking/', import.meta.url));
  const python = process.env.WAYON_PARKING_PYTHON || cwd + 'venv/bin/python';
  const env = {...process.env, PYTHONDONTWRITEBYTECODE: '1'};
  const raw = execFileSync(python, ['-B', '-c',
    'import json,sys; from test_parking_notify import wire_fixture; print(json.dumps(wire_fixture(float(sys.argv[1])), ensure_ascii=True, separators=(",",":")))',
    String(Date.now() / 1000)], {cwd, env, encoding: 'utf8'}).trim();
  const p = JSON.parse(raw);
  const isolated = await createRuntime({bindings: {WAYON_AI_DEVICE_ID: p.deviceId}});
  try {
    await isolated.db.prepare('INSERT INTO wayon_devices VALUES(?,?,NULL)').bind(p.deviceId, sha256('isolated-python-fixture')).run();
    await isolated.db.prepare('INSERT INTO push_subscriptions VALUES(?,?)').bind('python-fixture-fcm', p.deviceId).run();
    const accepted = await isolated.call(p, {raw});
    assert.equal(accepted.status, 202); assert.equal(accepted.body.claimed, true);
    assert.equal((await isolated.done(p.eventId, false, p.deviceId)).notified_count, 1);
    const duplicate = await isolated.call(p, {raw});
    assert.equal(duplicate.status, 202); assert.equal(duplicate.body.status, 'duplicate');
    assert.equal(isolated.messages.length, 1);
    const msg = isolated.messages[0];
    assert.equal(msg.data.occurredAt, iso(Date.parse(p.completedAt)));
    assert.equal(msg.android.notification.tag, p.eventId);
    assert.equal(msg.token, 'python-fixture-fcm');
    assert.ok(msg.notification.body.includes('\uC811\uADFC \uC911'));
    const acknowledged = JSON.parse(execFileSync(python, ['-B', '-c', `
import io,json,sys
from types import SimpleNamespace
from parking_notify import ParkingNotifier, MAX_BODY
data=json.load(sys.stdin)
notifier=ParkingNotifier.__new__(ParkingNotifier)
notifier.endpoint="https://isolated.invalid"
notifier.token="isolated-token-no-credentials"
out=[]
for ack in data["acks"]:
    response=io.BytesIO(json.dumps(ack).encode())
    response.status=202
    notifier.opener=SimpleNamespace(open=lambda *args,**kwargs: response)
    out.append(notifier.send(data["payload"]))
print(json.dumps({"bodyLimit":MAX_BODY,"results":out}))
`], {cwd, env, encoding: 'utf8', input: JSON.stringify({payload: raw, acks: [accepted.body, duplicate.body]})}));
    assert.equal(acknowledged.bodyLimit, 32768);
    assert.deepEqual(acknowledged.results, [['acknowledged', 'cloud_accepted'], ['acknowledged', 'cloud_duplicate']]);
    for (const mutate of [p => p.phaseHint = 'parked', p => p.readings[0].evidence[1].sha256 = p.readings[0].evidence[0].sha256]) {
      const changed = structuredClone(p); changed.eventId += '-invalid'; mutate(changed);
      assert.equal((await isolated.call(changed)).status, 400);
    }
    assert.equal(isolated.messages.length, 1);
  } finally {await isolated.dispose();}
});
