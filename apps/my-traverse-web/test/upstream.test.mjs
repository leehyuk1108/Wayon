import {test, after} from 'node:test';
import assert from 'node:assert/strict';
import worker, {upstream} from '../server/worker.mjs';

const originalFetch = globalThis.fetch;
let networkAttempts = 0;
globalThis.fetch = () => { networkAttempts++; throw new Error('NETWORK_FORBIDDEN'); };
after(() => { globalThis.fetch = originalFetch; assert.equal(networkAttempts, 0); });
const PRIVATE = 'FIXTURE_PRIVATE_SECRET_AND_UPSTREAM_TEXT';
const origin = 'https://upstream.test';

function fixture() {
  const calls = [];
  const env = {PUBLIC_ORIGIN: origin, WAYON_DEVICE_KEY: PRIVATE,
    DB: {prepare() { return {bind() { return this; }, async first() { return {id: 'fixture-session'}; }}; }},
    WAYON: {async fetch(request) {
      calls.push(request); return Response.json({ok: true, sample: 'fixture'});
    }}};
  const request = new Request(origin + '/api/wayon/state', {headers: {
    cookie: '__Host-traverse=' + 's'.repeat(43), 'accept-encoding': 'gzip, deflate, br, zstd',
  }});
  return {env, calls, request, async run() {
    const response = await worker.fetch(request, env, {});
    return {status: response.status, headers: response.headers, body: await response.json()};
  }};
}

test('internal WAYON does not force encoding or mutate browser headers or add a fallback', async () => {
  const f = fixture();
  const result = await f.run();
  assert.equal(result.status, 200); assert.equal(f.calls.length, 1);
  assert.equal(f.calls[0].headers.get('accept-encoding'), null);
  assert.equal(f.calls[0].headers.get('authorization'), 'Bearer ' + PRIVATE);
  assert.equal(f.calls[0].redirect, 'manual'); assert.ok(f.calls[0].signal instanceof AbortSignal);
  assert.equal(f.request.headers.get('accept-encoding'), 'gzip, deflate, br, zstd');
  assert.equal(result.headers.get('accept-encoding'), null);
  await upstream(f.env, '/api/state', {headers: {'accept-encoding': 'gzip'}});
  assert.equal(f.calls[1].headers.get('accept-encoding'), 'gzip');
});

test('configuration, transport, timeout and invalid response failures return safe typed 502', async t => {
  const cases = [
    ['upstream_binding', f => { delete f.env.WAYON; }],
    ['upstream_credentials', f => { delete f.env.WAYON_DEVICE_KEY; }],
    ['upstream_request', f => { f.env.WAYON_DEVICE_KEY = PRIVATE + '\ninvalid'; }],
    ['upstream_transport', f => { f.env.WAYON.fetch = async () => { throw new TypeError('decompression failed: ' + PRIVATE); }; }],
    ['upstream_timeout', f => { f.env.WAYON.fetch = async () => { throw new DOMException(PRIVATE, 'TimeoutError'); }; }],
    ['upstream_response', f => { f.env.WAYON.fetch = async () => ({}); }],
    ['upstream_response', f => { f.env.WAYON.fetch = async () => {
      const response = Response.json({private: PRIVATE}); await response.text(); return response;
    }; }],
  ];
  for (const [code, configure] of cases) await t.test(code, async () => {
    const f = fixture(); configure(f);
    const result = await f.run();
    assert.equal(result.status, 502); assert.equal(result.body.code, code);
    assert.equal(result.body.ok, false); assert.match(result.body.message, /[\uac00-\ud7a3]/);
    assert.ok(!JSON.stringify(result.body).includes(PRIVATE));
    assert.ok(!JSON.stringify(result.body).includes('decompression failed'));
    assert.ok(!JSON.stringify(result.body).includes('https://'));
  });
});

test('upstream HTTP failures discard raw bodies and retain only the numeric status', async t => {
  for (const status of [301, 400, 401, 403, 429, 500, 503]) await t.test(String(status), async () => {
    const f = fixture(); let calls = 0;
    f.env.WAYON.fetch = async () => { calls++; return new Response(PRIVATE, {status, headers: {location: 'https://private.invalid/'}}); };
    const result = await f.run();
    assert.equal(result.status, 502); assert.equal(result.body.upstreamStatus, status);
    assert.equal(result.body.code, [401, 403].includes(status) ? 'upstream_auth' : 'upstream_http');
    assert.equal(result.headers.get('location'), null); assert.equal(calls, 1);
    assert.ok(!JSON.stringify(result.body).includes(PRIVATE));
  });
});

test('healthy proxy still strips upstream cookies and CORS without rewriting the feed', async () => {
  const f = fixture();
  f.env.WAYON.fetch = async () => Response.json({ok: true, sample: 'fixture'}, {headers: {
    'set-cookie': PRIVATE, 'access-control-allow-origin': '*', 'content-encoding': 'identity',
  }});
  const result = await f.run();
  assert.equal(result.status, 200); assert.deepEqual(result.body, {ok: true, sample: 'fixture'});
  assert.equal(result.headers.get('set-cookie'), null); assert.equal(result.headers.get('access-control-allow-origin'), null);
  assert.equal(result.headers.get('cache-control'), 'no-store');
});
