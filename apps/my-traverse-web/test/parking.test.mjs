import {test, after} from 'node:test';
import assert from 'node:assert/strict';
import worker from '../server/worker.mjs';

const originalFetch = globalThis.fetch;
let networkAttempts = 0;
globalThis.fetch = () => { networkAttempts++; throw new Error('NETWORK_FORBIDDEN'); };
after(() => { globalThis.fetch = originalFetch; assert.equal(networkAttempts, 0); });
const origin = 'https://parking-pwa.test';
const COOKIE = '__Host-traverse=' + 's'.repeat(43);
const payload = {ok: true, schemaVersion: 'wayon-parking-read-v1', deviceId: 'fixture-owner', generatedAt: '2026-11-04T01:00:00Z',
  observation: {jobId: 'a'.repeat(32), eventId: 'event-fixture', parkedAt: '2026-10-01T01:00:00Z', status: 'completed',
    result: {analysis: {readings: [], exactParkingSpotKnown: false}, frames: [], inspection: {version: 1, status: 'failed'}}}};
function fixture() {
  const calls = [];
  const env = {PUBLIC_ORIGIN: origin, WAYON_DEVICE_KEY: 'fixture-server-only-key',
    DB: {prepare() { return {bind() { return this; }, async first() { return {id: 'fixture-session', csrf: 'fixture-csrf'}; }}; }},
    WAYON: {async fetch(request) { calls.push(request); return Response.json(payload); }}};
  return {env, calls, async run(path = '/api/wayon/parking/latest', {method = 'GET', cookie = COOKIE, headers = {}} = {}) {
    const request = new Request(origin + path, {method, headers: {origin, 'x-csrf-token': 'fixture-csrf', ...(cookie ? {cookie} : {}), ...headers}});
    const response = await worker.fetch(request, env, {});
    return {status: response.status, headers: response.headers, body: await response.json()};
  }};
}

test('parking GET is allowlisted, cookie-authenticated and forwards the full inspection with original times', async () => {
  const f = fixture();
  const r = await f.run('/api/wayon/parking/latest?deviceId=other&url=https://evil.invalid', {headers: {
    authorization: 'Bearer browser-forgery', 'x-wayon-auth-device': 'other', 'x-wayon-device-id': 'other',
  }});
  assert.equal(r.status, 200); assert.deepEqual(r.body, payload); assert.equal(r.headers.get('cache-control'), 'no-store');
  assert.equal(f.calls.length, 1);
  const request = f.calls[0];
  assert.equal(new URL(request.url).pathname, '/api/parking/latest'); assert.equal(new URL(request.url).search, '');
  assert.equal(request.method, 'GET'); assert.equal(request.headers.get('authorization'), 'Bearer fixture-server-only-key');
  for (const name of ['cookie', 'x-wayon-device-id', 'x-wayon-auth-device']) assert.equal(request.headers.get(name), null);
  assert.ok(!JSON.stringify(r.body).includes('fixture-server-only-key'));
});

test('no session and expired sessions cannot read, browser Bearer never substitutes for session auth', async () => {
  const f = fixture();
  assert.equal((await f.run(undefined, {cookie: '', headers: {authorization: 'Bearer fixture-server-only-key'}})).status, 401);
  f.env.DB.prepare = () => ({bind() { return this; }, async first() { return null; }});
  assert.equal((await f.run()).status, 401); assert.equal(f.calls.length, 0);
});

test('only exact parking/latest GET is allowed; recognition, jobs, extra path and all mutation verbs remain denied', async () => {
  const f = fixture();
  for (const path of ['/api/wayon/parking/display', '/api/wayon/parking/recognition', '/api/wayon/parking/jobs/a', '/api/wayon/parking/latest/extra', '/api/wayon/parking/latest/']) {
    assert.equal((await f.run(path)).status, 403);
  }
  for (const method of ['POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']) {
    assert.equal((await f.run(undefined, {method})).status, 403);
  }
  assert.equal(f.calls.length, 0);
});

test('empty observation passes; Cloud 503 keeps existing sanitized PWA error policy without retry', async () => {
  const f = fixture();
  f.env.WAYON.fetch = async request => { f.calls.push(request); return Response.json({...payload, observation: null}); };
  assert.equal((await f.run()).body.observation, null);
  f.env.WAYON.fetch = async request => { f.calls.push(request); return new Response('PRIVATE_UPSTREAM_BODY', {status: 503}); };
  const r = await f.run(); assert.equal(r.status, 502); assert.equal(r.body.upstreamStatus, 503);
  assert.equal(r.body.code, 'upstream_http'); assert.ok(!JSON.stringify(r.body).includes('PRIVATE_UPSTREAM_BODY'));
  assert.equal(f.calls.length, 2);
});
