import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import {BASELINE_SHA256, OUTPUT_SHA256, patch, unpatch, sha256} from './patch.mjs';
import {namedFunction} from '../fast-vehicle-state-20261028/patch.mjs';

const baseline = readFileSync(process.env.WAYON_WEB_PUSH_BASELINE ||
  '/Users/hyuklee/Documents/parking-vision-review-20261102/sign-deployment/candidate.js', 'utf8');
const candidate = patch(baseline);
const fragment = readFileSync(new URL('./fanout.js', import.meta.url), 'utf8');
const DESTINATION = 'https://my-traverse-web.hyuklee.workers.dev/api/internal/notify';
const DEVICE = 'isolated-owner';
const SECRET = 'isolated-web-secret-' + 'x'.repeat(32);
const clean = value => JSON.parse(JSON.stringify(value));
const event = (type = 'wayon_parking_sign', extra = {}) => ({
  type, deviceId: DEVICE, parkingEventId: 'parking-1', vehicleEventId: 'event-1', impactId: 'impact-1',
  occurredAt: new Date().toISOString(), detectedAt: new Date().toISOString(), test: 'false', locked: 'true',
  notificationTitle: 'Parking sign', notificationBody: 'B12 - AI clue, not an exact parking location', ...extra,
});

function fixture({source = candidate, tokens = ['android-a', 'android-b', 'android-a'],
  bindings = {}, web = 'ok', fcm = 'ok'} = {}) {
  const calls = [], deleted = [];
  let webCompleted = false;
  const context = vm.createContext({TextEncoder, AbortController, setTimeout, clearTimeout,
    console: {error() {}}, __name() {}, getFcmAccessToken: async () => 'isolated-oauth',
    fetch: async (url, options) => {
      const kind = url === DESTINATION ? 'web' : 'fcm';
      calls.push({kind, url, options, payload: JSON.parse(options.body)});
      if (kind === 'web') {
        if (web === 'throw') throw new Error('isolated web failure');
        if (web === 'hold') return new Promise(() => {});
        if (web === 'late') await new Promise(resolve => setTimeout(resolve, 50));
        webCompleted = true;
        return new Response(null, {status: web === 'redirect' ? 307 : web === 'failed' ? 503 : 202});
      }
      assert.equal(url, 'https://fcm.googleapis.com/v1/projects/isolated-project/messages:send');
      if (fcm === 'throw') throw new Error('isolated FCM failure');
      const status = fcm === 'invalid' ? 404 : fcm === 'failed' ? 503 : 200;
      return Response.json(status === 200 ? {name: 'receipt'} : {error: {status: 'UNAVAILABLE'}}, {status});
    },
  });
  const functions = ['validDeviceId', 'visibleFcmNotification', 'sendFcmMessage', 'invalidFcmToken', 'sendDataNotifications'];
  vm.runInContext((source === candidate ? fragment : '') + '\n' +
    functions.map(name => namedFunction(source, name)).join('\n'), context);
  const env = {FCM_PROJECT_ID: 'isolated-project', MY_TRAVERSE_WEB_PUSH_TOKEN: SECRET,
    WAYON_AI_DEVICE_ID: DEVICE, ...bindings,
    DB: {prepare(sql) {return {bind(...values) {return {
      async all() {assert.match(sql, /^SELECT token/); assert.deepEqual(values, [DEVICE]);
        return {results: tokens.map(token => ({token}))};},
      async run() {assert.match(sql, /^DELETE FROM push_subscriptions/); deleted.push(values);},
    };}};}},
  };
  return {calls, deleted, context, webCompleted: () => webCompleted,
    send: (data = event(), device = DEVICE) => context.sendDataNotifications(env, device, data),
    payload: (data, now = Date.now()) => context.wayonWebPushPayload(DEVICE, data, now),
  };
}

test('exact pinned patch reverses; drift, repeat and partial inputs refuse', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
  for (const source of [baseline + ' ', candidate, candidate.slice(0, -1)]) assert.throws(() => patch(source));
  assert.throws(() => unpatch(candidate + ' '));
  assert.equal(candidate.split('const webPush = sendWayonWebPush(env, deviceId, data).catch(() => false);').length, 2);
  for (const name of ['visibleFcmNotification', 'sendFcmMessage', 'invalidFcmToken', 'handlePushRegistration']) {
    assert.equal(namedFunction(candidate, name), namedFunction(baseline, name));
  }
});

test('one fixed-destination hook outside token loop; original FCM messages and counts match', async () => {
  for (const type of ['wayon_parking_sign', 'wayon_automatic_shutdown', 'wayon_door_lock', 'wayon_parking_unlocked', 'wayon_impact']) {
    const data = event(type), original = fixture({source: baseline}), patched = fixture();
    assert.deepEqual(clean(await patched.send(data)), clean(await original.send(data)));
    assert.deepEqual(clean(patched.calls.filter(c => c.kind === 'fcm')), clean(original.calls));
    assert.deepEqual(patched.calls.map(c => c.kind), ['web', 'fcm', 'fcm']);
    assert.equal(patched.calls[0].options.redirect, 'manual');
    assert.equal(patched.calls[0].options.headers.authorization, 'Bearer ' + SECRET);
    assert.equal(patched.calls[0].options.signal.aborted, true);
    assert.deepEqual(data, event(type, {occurredAt: data.occurredAt, detectedAt: data.detectedAt}));
  }
});

test('missing or malformed secret and missing/mismatched explicit scope are no-ops', async () => {
  for (const bindings of [{MY_TRAVERSE_WEB_PUSH_TOKEN: undefined}, {MY_TRAVERSE_WEB_PUSH_TOKEN: ''},
    {MY_TRAVERSE_WEB_PUSH_TOKEN: 'short'}, {MY_TRAVERSE_WEB_PUSH_TOKEN: SECRET + '\n'},
    {MY_TRAVERSE_WEB_PUSH_TOKEN: 'x'.repeat(257)}, {MY_TRAVERSE_WEB_PUSH_TOKEN: 123},
    {WAYON_AI_DEVICE_ID: undefined}, {WAYON_AI_DEVICE_ID: 'another-device'},
    {WAYON_AI_DEVICE_ID: DEVICE + '\n'}, {WAYON_AI_DEVICE_ID: 123}]) {
    const f = fixture({bindings});
    assert.deepEqual(clean(await f.send()), {sent: 2, failed: 0, invalid: 0, subscriptions: 2});
    assert.ok(f.calls.every(c => c.kind === 'fcm'));
  }
});

test('payload is minimized and caller URL, device and credential fields cannot expand authority', async () => {
  const f = fixture({bindings: {WAYON_WEB_PUSH_URL: 'https://untrusted.invalid'}});
  await f.send(event('wayon_parking_sign', {url: 'https://untrusted.invalid', token: 'private',
    latitude: 1, longitude: 2, health: {secret: 1}, readings: ['private'], image: 'x'.repeat(100000)}));
  const call = f.calls[0];
  assert.equal(call.url, DESTINATION);
  assert.deepEqual(Object.keys(call.payload).sort(), ['deviceId', 'type', 'id', 'title', 'body', 'occurredAt', 'test'].sort());
  assert.equal(call.payload.id, 'parking-1');
  assert.equal(call.payload.test, false);
  assert.ok(!call.options.body.includes('private'));
  const wrong = fixture(); await wrong.send(event('wayon_parking_sign', {deviceId: 'another-device'}));
  assert.ok(wrong.calls.every(c => c.kind === 'fcm'));
  const invalid = fixture(); await assert.rejects(invalid.send(event(), '!'), /invalid_notification_scope/);
  assert.equal(invalid.calls.length, 0);
});

test('failed, thrown and redirecting ingress cannot change FCM results or token cleanup', async () => {
  for (const web of ['failed', 'throw', 'redirect']) for (const fcm of ['ok', 'failed', 'invalid']) {
    const original = fixture({source: baseline, fcm}), patched = fixture({web, fcm});
    const data = event();
    assert.deepEqual(clean(await patched.send(data)), clean(await original.send(data)));
    assert.deepEqual(patched.deleted, original.deleted);
    assert.equal(patched.calls.filter(c => c.kind === 'web').length, 1);
  }
});

test('deadline bounds an ingress that ignores abort; Android still sends', async () => {
  const f = fixture({web: 'hold'}), started = performance.now();
  const pending = f.send();
  await new Promise(resolve => setTimeout(resolve, 20));
  assert.equal(f.calls.filter(c => c.kind === 'fcm').length, 2);
  assert.equal((await pending).sent, 2);
  assert.ok(performance.now() - started < 3000);
  assert.equal(f.calls[0].options.signal.aborted, true);
  assert.equal(f.calls.filter(c => c.kind === 'web').length, 1);
});

test('web fanout is independent of zero FCM tokens and an FCM exception', async () => {
  const empty = fixture({tokens: []});
  assert.deepEqual(clean(await empty.send()), {sent: 0, failed: 0, invalid: 0, subscriptions: 0});
  assert.deepEqual(empty.calls.map(c => c.kind), ['web']);
  const broken = fixture({fcm: 'throw', web: 'late'});
  await assert.rejects(broken.send(), /isolated FCM failure/);
  assert.deepEqual(broken.calls.map(c => c.kind), ['web', 'fcm']);
  assert.equal(broken.webCompleted(), true);
});

test('reject unknown types, malformed identities, controls, booleans and oversized Unicode', () => {
  const f = fixture();
  for (const overrides of [{type: 'unknown'}, {type: '__proto__'}, {test: false}, {test: undefined},
    {parkingEventId: ''}, {parkingEventId: 'a'.repeat(129)}, {parkingEventId: 'bad/id'},
    {notificationTitle: 'x'.repeat(129)}, {notificationBody: 'x'.repeat(2049)},
    {notificationBody: '\u{1f600}'.repeat(2048)}, {notificationTitle: '\u202eunsafe'},
    {notificationBody: 'unsafe\nbody'}, {notificationBody: '\ud800'},
    {occurredAt: 'invalid'}, {occurredAt: '2026-11-02'}, {occurredAt: 123}]) {
    assert.equal(f.payload(event('wayon_parking_sign', overrides)), null);
  }
  assert.equal(f.payload(event('wayon_door_lock', {locked: true})), null);
  assert.equal(f.payload(null), null);
  const body = f.payload(event('wayon_parking_sign', {notificationBody: '\u{1f600}'.repeat(700)}));
  assert.ok(new TextEncoder().encode(body).byteLength < 8192);
});

test('explicit owner wins; legacy fallback works only when explicit scope is absent', async () => {
  const legacy = fixture({bindings: {WAYON_AI_DEVICE_ID: '', WAYON_LEGACY_FIREBASE_DEVICE_ID: DEVICE}});
  await legacy.send(); assert.equal(legacy.calls.filter(c => c.kind === 'web').length, 1);
  const denied = fixture({bindings: {WAYON_AI_DEVICE_ID: 'another-device', WAYON_LEGACY_FIREBASE_DEVICE_ID: DEVICE}});
  await denied.send(); assert.ok(denied.calls.every(c => c.kind === 'fcm'));
});

test('exact UTF-8 wire limit accepts 8192 bytes and rejects 8193 without truncation', () => {
  const f = fixture();
  const data = event('wayon_parking_sign', {notificationBody: 'x'});
  const overhead = new TextEncoder().encode(f.payload(data)).byteLength - 1;
  const available = 8192 - overhead;
  data.notificationBody = '\u{1f600}'.repeat(Math.floor(available / 4)) + 'a'.repeat(available % 4);
  assert.equal(new TextEncoder().encode(f.payload(data)).byteLength, 8192);
  assert.equal(f.payload({...data, notificationBody: data.notificationBody + 'a'}), null);
});

test('freshness bounds and test labels are explicit; parking warning is retained', () => {
  const f = fixture(), now = Date.now();
  for (const [offset, accepted] of [[-600001, false], [-600000, true], [120000, true], [120001, false]]) {
    assert.equal(Boolean(f.payload(event('wayon_parking_sign', {occurredAt: new Date(now + offset).toISOString()}), now)), accepted);
  }
  for (const type of ['wayon_parking_sign', 'wayon_automatic_shutdown', 'wayon_door_lock', 'wayon_parking_unlocked', 'wayon_impact']) {
    const payload = JSON.parse(f.payload(event(type, {test: 'true', notificationTitle: 'Parking \uD14C\uC2A4\uD2B8'})));
    assert.equal(payload.test, true);
    assert.ok(payload.title.includes('\uD14C\uC2A4\uD2B8'));
  }
  assert.equal(JSON.parse(f.payload(event())).body, event().notificationBody);
});
