import assert from 'node:assert/strict';
import {after, before, beforeEach, test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {dirname, join} from 'node:path';
import {runInNewContext} from 'node:vm';
import {BASELINE_SHA256, patch, unpatch, replaceOnce, sha256} from './parking_batch.mjs';

const baselinePath = process.env.WAYON_PARKING_BASELINE;
assert.ok(baselinePath, 'Set WAYON_PARKING_BASELINE to the private downloaded production bundle');
const baseline = readFileSync(baselinePath, 'utf8');
const candidate = patch(baseline);
const fragment = readFileSync(new URL('./parking_batch.js', import.meta.url), 'utf8');
const migration = readFileSync(new URL('./parking_batch.sql', import.meta.url), 'utf8');
const schema = readFileSync(new URL('../schema.sql', import.meta.url), 'utf8');
const require = createRequire(import.meta.url);
const {Miniflare, convertV4MiniflareOptions} = require(process.env.MINIFLARE_MODULE || 'miniflare');
const keyA = 'wayon_' + 'a'.repeat(40), keyB = 'wayon_' + 'b'.repeat(40), aiKey = 'isolated-owner-read';
const devA = 'parking-device-a', devB = 'parking-device-b';
const jpeg = Buffer.from([255,216,255,224,0,2,255,217]).toString('base64');
let mf, db, kv, remoteRequests = 0;
let now;
const iso = ms => new Date(ms).toISOString();
function frame(index = 0, count = 3, eventId = 'test-event', parkedAt = iso(now - 10000)) {
  const parked = Date.parse(parkedAt);
  return {capturedAt: iso(parked - (count - 1 - index) * 2000), wideJpegBase64: jpeg,
    parking: {version: 1, eventId, parkedAt, index, count, phase: index === count - 1 ? 'parked' : 'approach'}};
}
const post = async (payload, key = keyA, extraHeaders = {}) => {
  const response = await mf.dispatchFetch('https://isolated.test/api/snapshot', {
    method: 'POST', headers: {authorization: 'Bearer ' + key, 'content-type':'application/json', ...extraHeaders}, body: JSON.stringify(payload),
  });
  return {status: response.status, body: await response.json()};
};
const list = async (key = keyA, query = '') => {
  const response = await mf.dispatchFetch('https://isolated.test/api/ai/snapshots?limit=100' + query, {headers: {authorization: 'Bearer ' + key}});
  return {status: response.status, body: await response.json()};
};
const count = async table => (await db.prepare(`SELECT COUNT(*) AS n FROM ${table}`).first()).n;

before(async () => {
  const moduleRoot = process.env.WAYON_PARKING_MODULE_DIR || join(dirname(baselinePath), 'cloud-baseline');
  const modules = [{type:'ESModule',path:'/isolated/worker.js',contents:candidate}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type:'ESModule', path:'/isolated/' + name, contents:readFileSync(join(moduleRoot, name), 'utf8')});
  }
  const options = {modules, modulesRoot:'/isolated', compatibilityDate:'2026-05-14', cf:false,
    d1Databases:{DB:'parking-isolated'}, kvNamespaces:['SNAPSHOTS'],
    bindings:{WAYON_AI_READ_TOKEN:aiKey, WAYON_AI_DEVICE_ID:devA},
    outboundService: () => {remoteRequests++; throw new Error('Network access forbidden in parking tests');}};
  mf = new Miniflare(convertV4MiniflareOptions ? convertV4MiniflareOptions(options) : options);
  db = await mf.getD1Database('DB'); kv = await mf.getKVNamespace('SNAPSHOTS');
  await db.exec(schema.replace(/\n/g, ' '));
  await db.exec(migration.replace(/^--.*$/gm, '').replace(/\n/g, ' '));
  await db.exec('CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT)');
  for (const [device, key] of [[devA,keyA],[devB,keyB]]) {
    await db.prepare('INSERT INTO wayon_devices VALUES(?,?,NULL)').bind(device,sha256(key)).run();
  }
});
beforeEach(async () => {
  now = Date.now();
  for (const table of ['snapshots', 'parking_snapshot_frames_v1', 'latest_state', 'impact_events']) await db.exec(`DELETE FROM ${table}`);
  await db.exec('UPDATE wayon_devices SET revoked_at = NULL');
  for (const device of [devA,devB]) await db.prepare(`INSERT INTO latest_state
    (device_id,updated_at,onroad,ignition,enabled) VALUES(?,?,0,0,0)`).bind(device,iso(now)).run();
  for (const item of (await kv.list()).keys) await kv.delete(item.name);
});
after(async () => { if (mf) await mf.dispose(); assert.equal(remoteRequests, 0); });

test('patch is exact, reversible and idempotent; unknown, partial, duplicate and drifted bundles fail', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  assert.equal(unpatch(candidate), baseline);
  assert.equal(patch(candidate), candidate);
  assert.throws(() => patch(baseline + '\n'));
  assert.throws(() => patch(candidate.replace('7200000', '7200001')));
  assert.throws(() => patch(candidate.replace('return authorize(request, env, true);', 'return true;')));
  assert.throws(() => patch(baseline + '\n// WAYON_PARKING_BATCH_V1_BEGIN'));
  assert.throws(() => replaceOnce('one one', 'one', 'two'));
  assert.throws(() => replaceOnce('one', 'missing', 'two'));
  assert.ok(candidate.includes('headers.delete(AUTH_DEVICE_HEADER);'));
});

test('timestamp and freshness boundaries are strict without changing real capture time', () => {
  const validate = runInNewContext(fragment + '; parkingBatchInput', {Date, Uint8Array,
    base64ToBytes: value => new Uint8Array(Buffer.from(value, 'base64'))});
  for (const age of [-5000, 0, 7200000]) {
    const body = frame(1,2,'boundary',iso(now - age));
    assert.equal(validate(body, now).error, undefined);
  }
  for (const age of [-5001, 7200001]) assert.equal(validate(frame(1,2,'boundary',iso(now - age)), now).error, 'parking_time_out_of_bounds');
  const body = frame(); body.capturedAt = iso(Date.parse(body.parking.parkedAt) - 120000);
  assert.equal(validate(body, now).capturedAt, body.capturedAt);
  body.capturedAt = iso(Date.parse(body.parking.parkedAt) - 120001);
  assert.equal(validate(body, now).error, 'parking_time_out_of_bounds');
  for (const value of ['2026-02-30T00:00:00Z','2026-01-01T24:00:00Z','2026-01-01T00:00:00',
    '2026-01-01', '2026-01-01T00:00:00+99:00',null,1700000000000]) {
    assert.equal(validate({...frame(),capturedAt:value}, now).error, 'invalid_parking_timestamp');
  }
  const offset = frame(); offset.capturedAt = offset.capturedAt.replace('Z','+00:00');
  assert.equal(validate(offset, now).capturedAt, offset.capturedAt);
});

test('auth remains owner scoped; forged header/body/query, read token writes, revoked keys denied', async () => {
  assert.equal((await post(frame(), 'invalid', {'x-wayon-auth-device':devA})).status, 401);
  assert.equal((await post(frame(), aiKey)).status, 401);
  assert.equal((await list('invalid')).status, 401);
  const spoof = {...frame(),deviceId:devB};
  const saved = await post(spoof, keyA, {'x-wayon-auth-device':devB});
  assert.equal(saved.status,200);
  assert.equal((await db.prepare('SELECT device_id FROM parking_snapshot_frames_v1').first()).device_id,devA);
  await db.prepare('UPDATE wayon_devices SET revoked_at = ? WHERE device_id = ?').bind(iso(now),devA).run();
  assert.equal((await post(frame())).status,401);
  assert.equal((await list(aiKey, '&deviceId=' + devB)).status,401);
  assert.equal(await count('snapshots'),0);
});

test('malformed metadata/images reject before storing driver or wide images', async () => {
  const base = frame();
  const cases = [null,{},[],{...base.parking,version:2},{...base.parking,version:true},
    {...base.parking,index:-1},{...base.parking,index:12},{...base.parking,index:3},{...base.parking,index:0.1},
    {...base.parking,count:1},{...base.parking,count:13},{...base.parking,count:'3'},
    {...base.parking,eventId:'a'.repeat(97)},{...base.parking,eventId:''},{...base.parking,eventId:'test\n'},
    {...base.parking,eventId:'\uac00'},{...base.parking,phase:'stopped'},{...base.parking,extra:true}];
  for (const parking of cases) assert.equal((await post({...base,parking})).status,400);
  for (const wideJpegBase64 of ['', '??', '/9j/', Buffer.alloc(2097153).toString('base64'), jpeg + '\n']) {
    assert.equal((await post({...base,wideJpegBase64})).status,400);
  }
  assert.equal((await post({...base,driverJpegBase64:jpeg})).status,400);
  assert.equal((await post({...base,capturedAt:undefined})).status,400);
  assert.equal(await count('parking_snapshot_frames_v1'),0);
  assert.equal(await count('snapshots'),0);
  assert.equal((await kv.list()).keys.length,0);
});

test('out-of-order complete group publishes atomically; partial group is never an ordinary burst', async () => {
  for (const index of [2,0]) {
    const result = await post(frame(index));
    assert.equal(result.status,200); assert.equal(result.body.parking.complete,false);
    assert.deepEqual((await list()).body.snapshots,[]);
  }
  const last = await post(frame(1));
  assert.equal(last.status,200); assert.equal(last.body.parking.complete,true);
  const entries = (await list(aiKey, '&deviceId=' + devB)).body.snapshots;
  assert.equal(entries.length,3);
  for (const entry of entries) {
    assert.equal(entry.deviceId,devA);
    const original = frame(entry.parking.index);
    assert.deepEqual(entry.parking,original.parking);
    assert.equal(entry.capturedAt,original.capturedAt);
    const image = await mf.dispatchFetch(entry.imageUrl,{headers:{authorization:'Bearer '+keyA}});
    assert.equal(image.status,200); assert.equal(Buffer.from(await image.arrayBuffer()).toString('base64'),jpeg);
    const denied = await mf.dispatchFetch(entry.imageUrl,{headers:{authorization:'Bearer '+keyB}});
    assert.equal(denied.status,404);
  }
  const latest = await db.prepare('SELECT last_snapshot_wide_id FROM latest_state WHERE device_id=?').bind(devA).first();
  assert.equal(latest.last_snapshot_wide_id,entries.find(e=>e.parking.index===2).id);
});

test('Comma 6 approach plus 3 parked: first parked driver stays ordinary, immutable and outside the 9-frame group', async () => {
  const parkedAt=iso(Math.floor((now-10000)/1000)*1000).replace('.000Z','Z');
  const bodies=Array.from({length:9},(_,i)=>{
    const body=frame(i,9,'comma-nine',parkedAt);
    body.capturedAt=body.capturedAt.replace('.000Z','Z');
    body.parking.phase=i<6?'approach':'parked';
    if(i===6) body.driverJpegBase64=jpeg;
    return body;
  });
  // Include concurrent first-parked retries and deliberately out-of-order delivery.
  for(const i of [6,8,0,1,2,3,4,5]) assert.equal((await post(bodies[i])).status,200);
  assert.equal(await count('snapshots'),0);
  const retries=await Promise.all([post(bodies[6]),post(bodies[6]),post(bodies[7])]);
  assert.ok(retries.every(r=>r.status===200));
  const entries=(await list()).body.snapshots;
  const wide=entries.filter(e=>e.camera==='wide'),driver=entries.find(e=>e.camera==='driver');
  assert.equal(wide.length,9);assert.equal(entries.length,10);
  assert.ok(wide.every(e=>e.parking.count===9));assert.ok(!('parking' in driver));
  assert.equal(driver.capturedAt,bodies[6].capturedAt);
  const stored=await db.prepare('SELECT * FROM snapshots WHERE id=?').bind(driver.id).first();
  assert.deepEqual((await kv.getWithMetadata(stored.kv_key,'arrayBuffer')).metadata,
    {deviceId:devA,camera:'driver',capturedAt:bodies[6].capturedAt});
  assert.equal((await kv.list()).keys.length,10);
  assert.equal((await db.prepare('SELECT last_snapshot_driver_id FROM latest_state WHERE device_id=?').bind(devA).first()).last_snapshot_driver_id,driver.id);
  const retry=await post(bodies[6]);assert.equal(retry.body.snapshots[0].id,driver.id);
  assert.equal((await kv.list()).keys.length,10);
});

test('driver is allowed only on first parked index; rejects misplaced driver before group publication', async () => {
  const first=frame(1,4);first.parking.phase='parked';first.driverJpegBase64=jpeg;
  assert.equal((await post(first)).status,200);
  const earlier=frame(0,4);earlier.parking.phase='parked';
  assert.equal((await post(earlier)).status,409);
  const later=frame(2,4);later.parking.phase='parked';later.driverJpegBase64=jpeg;
  assert.equal((await post(later)).status,409);
  assert.equal(await count('parking_snapshot_frames_v1'),1);assert.equal(await count('snapshots'),0);
  assert.equal((await kv.list()).keys.length,2);
});

test('identical event IDs on two devices never collide and owner list never crosses scope', async () => {
  for (const key of [keyA,keyB]) for (let i=0;i<2;i++) assert.equal((await post(frame(i,2),key)).status,200);
  const a = (await list()).body.snapshots, b = (await list(keyB)).body.snapshots;
  assert.equal(a.length,2); assert.equal(b.length,2);
  assert.ok(a.every(e=>e.deviceId===devA)); assert.ok(b.every(e=>e.deviceId===devB));
  assert.ok(a.every(e=>!b.some(other=>other.id===e.id)));
});

test('count/reference/phase/order conflicts fail without publishing a partial group', async () => {
  assert.equal((await post(frame(0))).status,200);
  const changes = [b=>b.parking.count=4, b=>b.parking.parkedAt=iso(now-9000),
    b=>b.capturedAt=frame(0).capturedAt, b=>b.capturedAt=iso(now-15000)];
  for (const change of changes) {const body=frame(1);change(body);assert.equal((await post(body)).status,409);}
  assert.equal(await count('parking_snapshot_frames_v1'),1);
  assert.equal(await count('snapshots'),0);
  const parked = frame(1); parked.parking.phase='parked'; assert.equal((await post(parked)).status,200);
  const tooLate = frame(2);tooLate.parking.phase='approach';assert.equal((await post(tooLate)).status,400);
  assert.equal(await count('snapshots'),0);
});

test('phase reversal is rejected even when later frames arrive first', async () => {
  assert.equal((await post(frame(1,4))).status,200);
  const earlier=frame(0,4);earlier.parking.phase='parked';
  assert.equal((await post(earlier)).status,409);
  assert.equal(await count('parking_snapshot_frames_v1'),1);
});

test('concurrent exact retries preserve one immutable frame per index and all stored bytes', async () => {
  const bodies = Array.from({length:18},(_,i)=>frame(i%3));
  const responses=await Promise.all(bodies.map(body=>post(body)));
  assert.ok(responses.every(r=>r.status===200));
  assert.equal(await count('parking_snapshot_frames_v1'),3);assert.equal(await count('snapshots'),3);
  assert.equal((await kv.list()).keys.length,3);
  const before=(await db.prepare('SELECT * FROM snapshots ORDER BY id').all()).results;
  const ids=responses.filter((_,i)=>i%3===0).map(r=>r.body.snapshots[0].id);
  assert.equal(new Set(ids).size,1);
  assert.equal((await post(frame(0))).body.parking.complete,true);
  const changed=frame(0);changed.wideJpegBase64=Buffer.from([255,216,1,255,217]).toString('base64');
  assert.equal((await post(changed)).status,409);
  assert.deepEqual((await db.prepare('SELECT * FROM snapshots ORDER BY id').all()).results,before);
});

test('concurrent conflicting group declarations accept only one count/reference', async () => {
  const responses=await Promise.all([post(frame(0,3)),post(frame(0,4))]);
  assert.deepEqual(responses.map(r=>r.status).sort(),[200,409]);
  assert.equal(await count('parking_snapshot_frames_v1'),1);assert.equal((await kv.list()).keys.length,1);
});

test('twelve-frame maximum accepted; request bytes and total group bytes bounded', async () => {
  for(let i=0;i<12;i++) assert.equal((await post(frame(i,12,'a'.repeat(96)))).status,200);
  assert.equal((await list()).body.snapshots.length,12);
  // Exercise total-byte guard without allocating a network payload for every frame.
  await db.exec('DELETE FROM snapshots; DELETE FROM parking_snapshot_frames_v1');
  for(let i=0;i<8;i++) {
    const body=frame(i,10,'large'); assert.equal((await post(body)).status,200);
    await db.prepare('UPDATE parking_snapshot_frames_v1 SET size_bytes=2097152 WHERE frame_index=?').bind(i).run();
  }
  assert.equal((await post(frame(8,10,'large'))).status,409);
  assert.equal(await count('snapshots'),0);
});

test('largest allowed JPEG envelope validates without regex stack overflow', async () => {
  const bytes=Buffer.alloc(2097152);bytes[0]=255;bytes[1]=216;bytes[bytes.length-2]=255;bytes[bytes.length-1]=217;
  const body=frame(0,2);body.wideJpegBase64=bytes.toString('base64');
  assert.equal((await post(body)).status,200);
  assert.equal((await db.prepare('SELECT size_bytes FROM parking_snapshot_frames_v1').first()).size_bytes,2097152);
});

test('pending capacity and expiry bounded; completed metadata and image are never cleaned up', async () => {
  for(let i=0;i<2;i++) await post(frame(i,2,'complete'));
  const kept=(await list()).body.snapshots;
  for(let i=0;i<8;i++) assert.equal((await post(frame(0,2,'pending-'+i))).status,200);
  assert.equal((await post(frame(0,2,'ninth'))).status,409);
  await db.exec('PRAGMA ignore_check_constraints=ON');
  await db.prepare('UPDATE parking_snapshot_frames_v1 SET parked_ms = ?').bind(now-7600000).run();
  await db.exec('PRAGMA ignore_check_constraints=OFF');
  assert.equal((await post(frame(0,2,'ninth'))).status,200);
  assert.equal(await count('parking_snapshot_frames_v1'),3);
  assert.equal((await kv.list()).keys.length,3);
  assert.deepEqual((await list()).body.snapshots,kept);
});

test('ordinary old uploads/rows/images unchanged and do not acquire parking metadata', async () => {
  const oldAt='2026-01-01T00:00:00Z';
  const response=await post({capturedAt:oldAt,driverJpegBase64:jpeg,wideJpegBase64:jpeg});
  assert.equal(response.status,200);assert.equal(response.body.snapshots.length,2);
  assert.ok(!('parking' in response.body));
  const before=(await db.prepare('SELECT * FROM snapshots ORDER BY id').all()).results;
  for(let i=0;i<2;i++) await post(frame(i,2));
  for(const row of before) assert.deepEqual(await db.prepare('SELECT * FROM snapshots WHERE id=?').bind(row.id).first(),row);
  const entries=(await list()).body.snapshots.filter(e=>e.capturedAt===oldAt);
  assert.equal(entries.length,2);assert.ok(entries.every(e=>!('parking' in e)));
  assert.equal(await count('parking_snapshot_frames_v1'),2);
});

test('a delayed older parking group cannot move the app latest image backward', async () => {
  const ordinary=await post({capturedAt:iso(now),wideJpegBase64:jpeg});
  for(let i=0;i<2;i++) await post(frame(i,2));
  assert.equal((await db.prepare('SELECT last_snapshot_wide_id FROM latest_state WHERE device_id=?').bind(devA).first()).last_snapshot_wide_id,
    ordinary.body.snapshots[0].id);
});

test('100-row owner list uses bounded SQL parameters and leaves historical entries unchanged', async () => {
  const inserts=[];
  for(let i=0;i<98;i++) inserts.push(db.prepare('INSERT INTO snapshots VALUES(?,?,?,?,?,?,?)').bind(
    'historical-'+i,devA,'wide',iso(now-100000-i),'old-key-'+i,8,iso(now-100000-i)));
  await db.batch(inserts);
  for(let i=0;i<2;i++) await post(frame(i,2));
  const entries=(await list()).body.snapshots;
  assert.equal(entries.length,100);assert.equal(entries.filter(e=>e.parking).length,2);
  assert.equal(entries.filter(e=>!('parking' in e)).length,98);
});

test('D1 failure rolls back publication; retry recovers staging without overwriting existing frames', async () => {
  await post(frame(0,2));
  await db.exec("CREATE TRIGGER parking_test_fail BEFORE INSERT ON snapshots BEGIN SELECT RAISE(ABORT, 'isolated failure'); END");
  try {
    assert.equal((await post(frame(1,2))).status,503);
    assert.equal(await count('snapshots'),0);assert.equal(await count('parking_snapshot_frames_v1'),1);
  } finally {await db.exec('DROP TRIGGER parking_test_fail');}
  assert.equal((await post(frame(1,2))).body.parking.complete,true);
  assert.equal(await count('snapshots'),2);
});

test('additive migration is repeatable and preserves old rows', async () => {
  await post({capturedAt:'2026-01-01T00:00:00Z',wideJpegBase64:jpeg});
  const before=(await db.prepare('SELECT * FROM snapshots').all()).results;
  await db.exec(migration.replace(/^--.*$/gm, '').replace(/\n/g,' '));
  assert.deepEqual((await db.prepare('SELECT * FROM snapshots').all()).results,before);
});
