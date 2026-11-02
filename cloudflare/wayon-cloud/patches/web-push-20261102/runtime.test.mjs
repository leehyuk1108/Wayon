import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';
import {test} from 'node:test';
import {patch} from './patch.mjs';

const require = createRequire(import.meta.url);
const {Miniflare, convertV4MiniflareOptions} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/.npm/_npx/32026684e21afda6/node_modules/miniflare');
const root = '/Users/hyuklee/Documents/parking-vision-review-20261102/sign-deployment';
const baseline = readFileSync(process.env.WAYON_WEB_PUSH_BASELINE || join(root, 'candidate.js'), 'utf8');
const moduleRoot = process.env.WAYON_WEB_PUSH_MODULE_DIR || join(root, 'baseline');
const DEVICE = 'isolated-owner', SECRET = 'isolated-web-secret-' + 'x'.repeat(32);
const DESTINATION = 'https://my-traverse-web.hyuklee.workers.dev/api/internal/notify';
const iso = offset => new Date(Date.now() + offset).toISOString();

async function fixture(bindings = {}) {
  const calls = [];
  let webStatus = 202;
  const script = patch(baseline) + `
getFcmAccessToken = async () => "isolated-oauth";
const originalWebPushTestFetch = worker_default.fetch;
worker_default.fetch = async (request, env, ctx) => {
  if (new URL(request.url).pathname === "/__test/send") {
    return Response.json(await sendDataNotifications(env, "${DEVICE}", await request.json()));
  }
  return originalWebPushTestFetch(request, env, ctx);
};`;
  const modules = [{type: 'ESModule', path: '/isolated/worker.js', contents: script}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type: 'ESModule', path: '/isolated/' + name, contents: readFileSync(join(moduleRoot, name), 'utf8')});
  }
  const options = {modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14', cf: false,
    d1Databases: {DB: 'web-push-isolated'}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {FCM_PROJECT_ID: 'isolated-project', WAYON_AI_DEVICE_ID: DEVICE,
      WAYON_PARKING_NOTIFY_TOKEN: 'isolated-parking-notify',
      MY_TRAVERSE_WEB_PUSH_TOKEN: SECRET, ...bindings},
    outboundService: async request => {
      const payload = await request.json();
      if (request.url === DESTINATION) {
        assert.equal(request.headers.get('authorization'), 'Bearer ' + SECRET);
        calls.push({kind: 'web', payload});
        return new Response(null, {status: webStatus});
      }
      assert.equal(request.url, 'https://fcm.googleapis.com/v1/projects/isolated-project/messages:send', 'Unexpected outbound request blocked');
      assert.equal(request.headers.get('authorization'), 'Bearer isolated-oauth');
      calls.push({kind: 'fcm', payload: payload.message});
      return Response.json({name: 'isolated-receipt'});
    },
  };
  const mf = new Miniflare(convertV4MiniflareOptions ? convertV4MiniflareOptions(options) : options);
  try {
    const db = await mf.getD1Database('DB');
    await db.exec('CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT); ' +
      'CREATE TABLE push_subscriptions(token TEXT PRIMARY KEY,device_id TEXT);');
    await db.prepare('INSERT INTO wayon_devices VALUES(?,?,NULL)').bind(DEVICE, 'isolated-hash').run();
    for (const token of ['android-a', 'android-b']) {
      await db.prepare('INSERT INTO push_subscriptions VALUES(?,?)').bind(token, DEVICE).run();
    }
    await db.prepare('INSERT INTO push_subscriptions VALUES(?,?)').bind('other-android', 'other-device').run();
    const schema = readFileSync(new URL('../parking-sign-20261102/schema.sql', import.meta.url), 'utf8');
    await db.exec(schema.replace(/^--.*$/gm, '').replace(/\n/g, ' '));
    return {db, calls, dispose: () => mf.dispose(), setWebStatus: status => {webStatus = status;},
      async call(path, body, token = 'isolated-parking-notify') {
        const r = await mf.dispatchFetch('https://isolated.test' + path, {method: 'POST',
          headers: {'content-type': 'application/json', authorization: 'Bearer ' + token}, body: JSON.stringify(body)});
        return {status: r.status, body: await r.json()};
      },
      async finished(id) {
        for (let i = 0; i < 300; i++) {
          const row = await db.prepare('SELECT notified_count FROM parking_sign_notifications WHERE event_id=?').bind(id).first();
          if (row && row.notified_count !== -1) return row;
          await new Promise(resolve => setTimeout(resolve, 10));
        }
        assert.fail('Parking FCM receipt did not finish');
      },
    };
  } catch (error) {await mf.dispose(); throw error;}
}

const parking = id => ({eventId: id, jobId: 'a'.repeat(32), deviceId: DEVICE,
  parkedAt: iso(-60000), completedAt: iso(-1000), test: true, phaseHint: 'parked',
  readings: [{kind: 'pillar', text: 'TEST-B12', status: 'readable', evidence: [0, 1].map(frameIndex => ({
    frameIndex, box: [0.1, 0.2, 0.4, 0.8], capturedAt: iso(-61000 + frameIndex * 1000),
    sha256: String(frameIndex).repeat(64), phase: 'parked',
  }))}],
});

test('real workerd/D1 parking route preserves auth, claim, duplicate and FCM receipt contracts', async t => {
  const f = await fixture();
  try {
    await t.test('unauthorized requests cause no outbound send or claim', async () => {
      assert.equal((await f.call('/api/parking/recognition', parking('unauthorized'), 'wrong')).status, 401);
      assert.equal(f.calls.length, 0);
    });
    for (const status of [202, 503]) await t.test('ingress HTTP ' + status + ' keeps two FCM acceptances and one webhook', async () => {
      f.calls.length = 0; f.setWebStatus(status);
      const body = parking('parking-' + status);
      const accepted = await f.call('/api/parking/recognition', body);
      assert.equal(accepted.status, 202); assert.equal(accepted.body.duplicate, false);
      assert.equal((await f.finished(body.eventId)).notified_count, 2);
      assert.equal(f.calls.filter(c => c.kind === 'web').length, 1);
      const android = f.calls.filter(c => c.kind === 'fcm');
      assert.deepEqual(android.map(c => c.payload.token).sort(), ['android-a', 'android-b']);
      const web = f.calls.find(c => c.kind === 'web').payload;
      assert.deepEqual(Object.keys(web).sort(), ['deviceId', 'type', 'id', 'title', 'body', 'occurredAt', 'test'].sort());
      assert.equal(web.id, body.eventId); assert.equal(web.test, true);
      assert.equal(web.title, android[0].payload.notification.title);
      assert.equal(web.body, android[0].payload.notification.body);
      assert.equal(android[0].payload.android.notification.channel_id, 'wayon_parking_sign_alerts');
      assert.equal(android[0].payload.android.notification.tag, body.eventId);
      const duplicate = await f.call('/api/parking/recognition', body);
      assert.equal(duplicate.status, 202); assert.equal(duplicate.body.duplicate, true);
      assert.equal(f.calls.length, 3);
      assert.equal((await f.db.prepare('SELECT COUNT(*) AS n FROM push_subscriptions').first()).n, 3);
    });
    await t.test('no Android recipients still fan out without altering zero FCM count', async () => {
      await f.db.prepare('DELETE FROM push_subscriptions WHERE device_id=?').bind(DEVICE).run();
      f.calls.length = 0; f.setWebStatus(202);
      const body = parking('parking-no-android');
      assert.equal((await f.call('/api/parking/recognition', body)).status, 202);
      assert.equal((await f.finished(body.eventId)).notified_count, 0);
      assert.deepEqual(f.calls.map(c => c.kind), ['web']);
    });
  } finally {await f.dispose();}
});

test('real workerd optional-unconfigured hook requires no new bindings or schema', async () => {
  const f = await fixture({MY_TRAVERSE_WEB_PUSH_TOKEN: ''});
  try {
    const body = parking('parking-unconfigured');
    assert.equal((await f.call('/api/parking/recognition', body)).status, 202);
    assert.equal((await f.finished(body.eventId)).notified_count, 2);
    assert.deepEqual(f.calls.map(c => c.kind), ['fcm', 'fcm']);
  } finally {await f.dispose();}
});
