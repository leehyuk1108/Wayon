import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {patch, sha256} from './patch.mjs';

const require = createRequire(import.meta.url);
const {Miniflare, convertV4MiniflareOptions} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/.npm/_npx/32026684e21afda6/node_modules/miniflare');
export const baselinePath = process.env.WAYON_PARKING_SIGN_BASELINE ||
  '/Users/hyuklee/Documents/parking-vision-review-20261102/cloud-candidate/worker.js';
export const baseline = readFileSync(baselinePath, 'utf8');
export const candidate = patch(baseline);
export const migration = readFileSync(new URL('./schema.sql', import.meta.url), 'utf8');
export const DEVICE = 'isolated-parking-device', OTHER_DEVICE = 'isolated-other-device';
export const TOKEN = 'isolated-parking-notify', READ_TOKEN = 'isolated-ai-read';
export const KEY = 'wayon_' + 'a'.repeat(40), OTHER_KEY = 'wayon_' + 'b'.repeat(40);
export const iso = ms => new Date(ms).toISOString();
export const payload = (extra = {}, now = Date.now()) => ({
  eventId: 'parking-event-1', jobId: 'a'.repeat(32), deviceId: DEVICE,
  parkedAt: iso(now - 60000), completedAt: iso(now - 1000),
  readings: [{kind: 'pillar', text: 'B12', status: 'readable',
    evidence: [0, 1].map(frameIndex => ({frameIndex, box: [0.1, 0.2, 0.4, 0.8],
      capturedAt: iso(now - 60000 + frameIndex * 1000), sha256: String(frameIndex).repeat(64), phase: 'parked'}))}],
  phaseHint: 'parked', test: false, ...extra,
});

export async function createRuntime({bindings = {}, migrate = true} = {}) {
  const moduleRoot = process.env.WAYON_PARKING_SIGN_MODULE_DIR || dirname(baselinePath);
  // Only OAuth is stubbed. The real route/auth/body/D1/FCM builder run in workerd.
  const script = candidate + `
getFcmAccessToken = async () => "isolated-oauth-no-credentials";
const originalTestFetch = worker_default.fetch;
worker_default.fetch = async (request, env, ctx) => {
  if (new URL(request.url).pathname === "/__test/validate") {
    const {payload, now, deviceId} = await request.json();
    const input = parkingSignInput(payload, deviceId, now);
    return Response.json(input.error ? input : {input: input.value, data: parkingSignData(input.value)});
  }
  if (new URL(request.url).pathname === "/__test/fcm") {
    const data = await request.json();
    await sendFcmMessage(env, "isolated-direct", data);
    return Response.json({ok: true});
  }
  if (new URL(request.url).pathname === "/__test/body") {
    const {chunks, headers} = await request.json();
    const body = new ReadableStream({start(controller) {
      for (const chunk of chunks) controller.enqueue(new TextEncoder().encode(chunk));
      controller.close();
    }});
    return Response.json(await parkingSignBody(new Request("https://isolated.test/body", {method: "POST", headers, body})));
  }
  return originalTestFetch(request, env, request.headers.has("x-test-no-context") ? null : ctx);
};`;
  const modules = [{type: 'ESModule', path: '/isolated/worker.js', contents: script}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type: 'ESModule', path: '/isolated/' + name, contents: readFileSync(join(moduleRoot, name), 'utf8')});
  }
  const messages = [], releases = new Set();
  let behavior = 'ok', unexpectedFetches = 0;
  const options = {modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14', cf: false,
    d1Databases: {DB: 'parking-sign-isolated'}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {FCM_PROJECT_ID: 'isolated-project', WAYON_PARKING_NOTIFY_TOKEN: TOKEN,
      WAYON_AI_READ_TOKEN: READ_TOKEN, WAYON_AI_DEVICE_ID: DEVICE,
      WAYON_LEGACY_FIREBASE_DEVICE_ID: OTHER_DEVICE, ...bindings},
    outboundService: async request => {
      if (request.url !== 'https://fcm.googleapis.com/v1/projects/isolated-project/messages:send') {
        unexpectedFetches++; throw new Error('Unexpected outbound URL blocked');
      }
      assert.equal(request.headers.get('authorization'), 'Bearer isolated-oauth-no-credentials');
      messages.push((await request.json()).message);
      const mode = behavior;
      if (mode === 'hold') await new Promise(resolve => releases.add(resolve));
      if (mode === 'ambiguous') throw new Error('Synthetic lost FCM response after receipt');
      if (mode === 'failed') return Response.json({error: {status: 'UNAVAILABLE'}}, {status: 503});
      if (mode === 'invalid') return Response.json({error: {status: 'NOT_FOUND'}}, {status: 404});
      return Response.json({name: 'isolated-receipt'});
    },
  };
  const mf = new Miniflare(convertV4MiniflareOptions ? convertV4MiniflareOptions(options) : options);
  try {
    const db = await mf.getD1Database('DB');
    await db.exec(`CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT);
      CREATE TABLE push_subscriptions(token TEXT PRIMARY KEY,device_id TEXT);
      CREATE TABLE vehicle_events(id TEXT PRIMARY KEY,device_id TEXT,event_type TEXT,occurred_at TEXT,received_at TEXT,locked INTEGER,notified_count INTEGER,raw_json TEXT);
      CREATE TABLE sentinel(id TEXT PRIMARY KEY,value TEXT);
      INSERT INTO sentinel VALUES('untouched','parent-data');`.replace(/\n/g, ' '));
    for (const [device, key] of [[DEVICE, KEY], [OTHER_DEVICE, OTHER_KEY]]) {
      await db.prepare('INSERT INTO wayon_devices VALUES(?,?,NULL)').bind(device, sha256(key)).run();
      await db.prepare('INSERT INTO push_subscriptions VALUES(?,?)').bind(device + '-fcm', device).run();
    }
    const applyMigration = () => db.exec(migration.replace(/^--.*$/gm, '').replace(/\n/g, ' '));
    if (migrate) await applyMigration();
    const call = async (body = payload(), {token = TOKEN, headers = {}, method = 'POST', path = '/api/parking/recognition', raw} = {}) => {
      const response = await mf.dispatchFetch('https://isolated.test' + path, {
        method, headers: {...(token === null ? {} : {authorization: 'Bearer ' + token}), 'content-type': 'application/json', ...headers},
        ...(['GET', 'HEAD'].includes(method) ? {} : {body: raw === undefined ? JSON.stringify(body) : raw}),
      });
      return {status: response.status, body: await response.json()};
    };
    const waitFor = async (check, label = 'runtime condition') => {
      for (let i = 0; i < 200; i++) {
        const value = await check();
        if (value) return value;
        await new Promise(resolve => setTimeout(resolve, 10));
      }
      assert.fail('Timed out waiting for ' + label);
    };
    const row = async (eventId = 'parking-event-1', test = false, device = DEVICE) =>
      db.prepare('SELECT * FROM parking_sign_notifications WHERE device_id=? AND event_id=? AND test=?')
        .bind(device, eventId, Number(test)).first();
    const release = () => { for (const resolve of releases) resolve(); releases.clear(); };
    return {mf, db, messages, call, row, waitFor, applyMigration, release,
      setBehavior(value) {behavior = value;},
      async done(eventId = 'parking-event-1', test = false, device = DEVICE) {
        return waitFor(async () => {const r = await row(eventId, test, device); return r?.finished_at ? r : null;}, 'FCM receipt');
      },
      async validate(body, now = Date.now()) {
        return (await call({payload: body, now, deviceId: DEVICE}, {path: '/__test/validate'})).body;
      },
      async dispose() { release(); await mf.dispose(); assert.equal(unexpectedFetches, 0); },
    };
  } catch (error) { await mf.dispose(); throw error; }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const f = await createRuntime();
  try {
    const body = payload();
    assert.equal((await f.call(body)).status, 202);
    assert.equal((await f.done()).notified_count, 1);
    assert.equal((await f.call(body)).body.duplicate, true);
    assert.equal(f.messages.length, 1);
    console.log(JSON.stringify({runtime: 'workerd + D1 + intercepted FCM', candidate: sha256(candidate), remoteFetches: 0}));
  } finally { await f.dispose(); }
}
