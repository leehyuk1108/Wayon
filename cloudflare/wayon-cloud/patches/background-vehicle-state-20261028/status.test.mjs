import assert from 'node:assert/strict';
import test from 'node:test';
import {patch} from './patch.mjs';
import {candidate, COLLECTOR, DEVICE, KEY, iso, load, payload, request, sqliteEnv} from '../fast-vehicle-state-20261028/test-support.mjs';

const worker = load(patch(candidate)).worker;
const post = (env, body, token = COLLECTOR) => worker.fetch(request('POST', body, {authorization:`Bearer ${token}`}), env, {});
const fresh = extra => payload({source:'gmone-direct', refreshStartedAt:iso(-20000), ...extra});

for (const [label, data, token, complete] of [
  ['active', fresh(), COLLECTOR, true],
  ['passive', fresh({source:'gmone-official-cache'}), COLLECTOR, false],
  ['missing start', fresh({refreshStartedAt:undefined}), COLLECTOR, false],
  ['stale fallback', fresh({vehicleUpdatedAt:iso(-50000)}), COLLECTOR, false],
  ['started before request', fresh({refreshStartedAt:iso(-40000)}), COLLECTOR, false],
  ['future start', fresh({refreshStartedAt:iso(1000)}), COLLECTOR, false],
  ['invalid start', fresh({refreshStartedAt:'wrong'}), COLLECTOR, false],
  ['old request', fresh({refreshStartedAt:iso(-180000)}), COLLECTOR, false],
  ['phone cannot ack', fresh(), KEY, false],
]) test(`refresh completion: ${label}`, async () => {
  const h = sqliteEnv();
  h.env.WAYON_LEGACY_FIREBASE_DEVICE_ID = DEVICE;
  h.sqlite.prepare('INSERT INTO gmone_refresh_requests VALUES (?, ?, NULL)').run(DEVICE, iso(-30000));
  try {
    assert.equal((await post(h.env, data, token)).status, 200);
    assert.equal(Boolean(h.refresh().completed_at), complete);
  } finally {h.sqlite.close();}
});

test('superseded retry can complete its request, not a later request', async () => {
  const h=sqliteEnv(); h.env.WAYON_LEGACY_FIREBASE_DEVICE_ID=DEVICE;
  try {
    await post(h.env, fresh({vehicleUpdatedAt:iso(-100), collectedAt:iso(-50), refreshStartedAt:undefined}));
    h.sqlite.prepare('INSERT INTO gmone_refresh_requests VALUES (?, ?, NULL)').run(DEVICE, iso(-30000));
    assert.equal((await post(h.env, fresh())).status,409);
    assert.ok(h.refresh().completed_at);
    h.sqlite.prepare('UPDATE gmone_refresh_requests SET requested_at=?,completed_at=NULL').run(iso(-15000));
    assert.equal((await post(h.env, fresh())).status,409);
    assert.equal(h.refresh().completed_at,null);
  } finally {h.sqlite.close();}
});

test('source timestamp survives receipt; legacy freshness, auth, ordering and scope stay unchanged', async () => {
  const h=sqliteEnv(); h.env.WAYON_LEGACY_FIREBASE_DEVICE_ID=DEVICE;
  try {
    assert.equal((await post(h.env, fresh({source:'gmone-official-cache',vehicleUpdatedAt:iso(-90000000),clientScope:'c'.repeat(64)}))).status,200);
    const response=await worker.fetch(request('GET'),h.env,{});
    const status=(await response.json()).vehicleStatus;
    assert.equal(status.updatedAt,iso(-90000000));
    assert.equal(status.stale,false); assert.equal(status.clientScope,'c'.repeat(64));
    assert.equal((await worker.fetch(request('GET',null,{authorization:'Bearer wrong'}),h.env,{})).status,401);
    assert.equal((await post(h.env, fresh())).status,200);
    assert.equal((await post(h.env, fresh({vehicleUpdatedAt:iso(-50000)}))).status,409);
  } finally {h.sqlite.close();}
});

test('legacy snapshot readers and merge policy are byte-for-byte unchanged', () => {
  const output=patch(candidate);
  const start=candidate.indexOf('async function latestGmoneStatus');
  const end=candidate.indexOf('async function fetchMergedVehicleStatus');
  assert.ok(start>0 && end>start);
  assert.ok(output.includes(candidate.slice(start,end)));
});
