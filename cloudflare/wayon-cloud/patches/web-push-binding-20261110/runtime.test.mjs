import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';
import {test} from 'node:test';
import {patch, unpatch, BASELINE_SHA256, OUTPUT_SHA256} from './patch.mjs';
import {sha256} from '../fast-vehicle-state-20261028/patch.mjs';

// Private copy of the active production modules (downloaded read-only); not committed.
const root = process.env.WAYON_ACTIVE_MODULE_DIR || '/Users/hyuklee/Documents/my-traverse-web-20261110/baseline';
const require = createRequire(import.meta.url);
const {Miniflare} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/Documents/sunnypilot/apps/my-traverse-web/node_modules/miniflare');
const baseline = readFileSync(join(root, 'worker.js'), 'utf8');
const DEVICE = 'isolated-owner', SECRET = 'isolated-web-secret-' + 'x'.repeat(32);
const DESTINATION = 'https://my-traverse-web.hyuklee.workers.dev/api/internal/notify';
const iso = offset => new Date(Date.now() + offset).toISOString();

test('patch is byte-exact and reversible against the active bundle', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  const candidate = patch(baseline);
  assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
});

async function fixture(withBinding) {
  const calls = [];
  const script = patch(baseline) + `
getFcmAccessToken = async () => "isolated-oauth";
const originalBindingTestFetch = worker_default.fetch;
worker_default.fetch = async (request, env, ctx) => {
  if (new URL(request.url).pathname === "/__test/send") {
    return Response.json(await sendDataNotifications(env, "${DEVICE}", await request.json()));
  }
  return originalBindingTestFetch(request, env, ctx);
};`;
  const modules = [{type: 'ESModule', path: '/isolated/worker.js', contents: script}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type: 'ESModule', path: '/isolated/' + name, contents: readFileSync(join(root, name), 'utf8')});
  }
  const mf = new Miniflare({modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14',
    d1Databases: {DB: 'web-push-binding-isolated'}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {FCM_PROJECT_ID: 'isolated-project', WAYON_LEGACY_FIREBASE_DEVICE_ID: DEVICE, MY_TRAVERSE_WEB_PUSH_TOKEN: SECRET},
    ...(withBinding ? {serviceBindings: {MY_TRAVERSE_WEB: async request => {
      assert.equal(request.url, DESTINATION);
      assert.equal(request.method, 'POST');
      assert.equal(request.headers.get('authorization'), 'Bearer ' + SECRET);
      calls.push({kind: 'binding', payload: await request.json()});
      return new Response(JSON.stringify({ok: true, accepted: true}), {status: 202});
    }}} : {}),
    outboundService: async request => {
      if (request.url === DESTINATION) {
        // Production behaviour for a same-account workers.dev subrequest: it never reaches the other Worker.
        calls.push({kind: 'public-web'});
        return new Response('error code: 1042', {status: 404});
      }
      assert.equal(request.url, 'https://fcm.googleapis.com/v1/projects/isolated-project/messages:send', 'Unexpected outbound request');
      calls.push({kind: 'fcm', payload: (await request.json()).message});
      return Response.json({name: 'isolated-receipt'});
    },
  });
  const db = await mf.getD1Database('DB');
  await db.exec('CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT); ' +
    'CREATE TABLE push_subscriptions(token TEXT PRIMARY KEY,device_id TEXT);');
  await db.prepare('INSERT INTO wayon_devices VALUES(?,?,NULL)').bind(DEVICE, 'isolated-hash').run();
  await db.prepare('INSERT INTO push_subscriptions VALUES(?,?)').bind('android-a', DEVICE).run();
  return {calls, dispose: () => mf.dispose(), async send(data) {
    const r = await mf.dispatchFetch('https://isolated.test/__test/send', {method: 'POST',
      headers: {'content-type': 'application/json'}, body: JSON.stringify(data)});
    return r.json();
  }};
}

const doorLock = id => ({type: 'wayon_door_lock', deviceId: DEVICE, vehicleEventId: id, locked: 'true',
  occurredAt: iso(-1000), test: 'false'});
const impact = id => ({type: 'wayon_impact', deviceId: DEVICE, impactId: id, detectedAt: iso(-1000), test: 'true'});

test('with the service binding every web-eligible notification reaches the web app beside FCM', async () => {
  const f = await fixture(true);
  try {
    for (const data of [doorLock('door-1'), impact('impact-1')]) {
      f.calls.length = 0;
      const receipt = await f.send(data);
      assert.equal(receipt.sent, 1);
      assert.deepEqual(f.calls.map(c => c.kind).sort(), ['binding', 'fcm']);
      const web = f.calls.find(c => c.kind === 'binding').payload;
      assert.equal(web.type, data.type);
      assert.equal(web.deviceId, DEVICE);
      assert.ok(web.title && web.body);
    }
    assert.ok(!f.calls.some(c => c.kind === 'public-web'), 'no public same-account fetch when the binding exists');
  } finally {await f.dispose();}
});

test('without the binding the original public fetch is attempted unchanged and FCM is unaffected', async () => {
  const f = await fixture(false);
  try {
    const receipt = await f.send(doorLock('door-2'));
    assert.equal(receipt.sent, 1);
    assert.deepEqual(f.calls.map(c => c.kind).sort(), ['fcm', 'public-web']);
  } finally {await f.dispose();}
});
