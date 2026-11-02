import {test, after} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {DatabaseSync} from 'node:sqlite';
import {handle} from '../server/worker.mjs';
import {COOKIE, digest, encrypt, decrypt} from '../server/security.mjs';
import {ACCOUNT_TTL_MS, COMMAND_SPECS} from '../server/commands.mjs';

// Source-level Worker integration: real SQL/crypto, in-memory storage, no sockets,
// production config, credentials, deployment bundle, or actual GMOne requests.
const originalFetch = globalThis.fetch;
let networkAttempts = 0;
globalThis.fetch = () => { networkAttempts++; throw new Error('NETWORK FORBIDDEN'); };
after(() => { globalThis.fetch = originalFetch; assert.equal(networkAttempts, 0); });

const schema = readFileSync(new URL('../server/schema.sql', import.meta.url), 'utf8');
const ORIGIN = 'https://binding.test';
const NOW = 1_800_000_000_000;
const OWNER = {uuid: 'FIXTURE_OWNER_UUID', vehicleId: 'FIXTURE_OWNER_VEHICLE'};
const DEVICE = 'FIXTURE_OWNER_DEVICE';
const EMAIL = 'owner@example.test';
const PASSWORD = 'FIXTURE_PASSWORD_NOT_REAL';
const SESSION_TOKEN = 's'.repeat(43);
const REQUEST_ID = '11111111-1111-4111-8111-111111111111';

function account(patch = {}) {
  return {version: 1, ...OWNER, token: 'FIXTURE_GMONE_TOKEN_NOT_REAL', vehicleCount: 1,
    issuedAtMs: NOW - 1000, expiresAtMs: NOW - 1000 + ACCOUNT_TTL_MS, ...patch};
}

function feed(deviceId = DEVICE, observedAt = NOW - 300_000) {
  const updatedAt = new Date(observedAt).toISOString();
  return {generatedAt: new Date(NOW).toISOString(), state: {
    device_id: deviceId, updated_at: updatedAt, onroad: 0, enabled: 0, speed_mps: 0,
    raw_json: JSON.stringify({schemaVersion: 'wayon-telemetry-v2', deviceId, updatedAt,
      onroad: false, enabled: false, vehicleSpeedMps: 0, vehicleSpeedSource: 'offroad',
      vehicle: {available: false, reason: 'offroad'}, openpilot: {available: false}}),
  }};
}

async function fixture(t, options = {}) {
  let now = NOW;
  t.mock.method(Date, 'now', () => now);
  const sql = new DatabaseSync(':memory:');
  sql.exec(schema);
  t.after(() => sql.close());
  const f = {sql, events: [], cloudCalls: [], markerCalls: [], protocolCalls: [], sessionReads: 0,
    feed: feed(), loginAccount: account(), requestId: REQUEST_ID, advance: ms => { now += ms; }, now: () => now};
  const env = f.env = {PUBLIC_ORIGIN: ORIGIN, COMMANDS_ENABLED: '1', DEVICE_ID: DEVICE,
    ACCOUNT_FINGERPRINT: await digest(EMAIL), GMONE_UUID_HASH: await digest(OWNER.uuid),
    GMONE_VEHICLE_HASH: await digest(OWNER.vehicleId), ACCOUNT_ENCRYPTION_KEY: 'FIXTURE_ENCRYPTION_KEY_NOT_REAL_0123456789',
    WAYON_DEVICE_KEY: 'FIXTURE_WAYON_KEY_NOT_REAL', ...options.env};
  f.sessionId = await digest(SESSION_TOKEN);
  f.initialCipher = await encrypt(account(options.account), env.ACCOUNT_ENCRYPTION_KEY);
  sql.prepare('INSERT INTO sessions(id,csrf,expires,account,email) VALUES(?,?,?,?,?)')
    .run(f.sessionId, 'fixture-csrf', NOW + 3_600_000, f.initialCipher, EMAIL);

  // Thin D1 adapter executes the actual bound SQL rather than simulating WHEREs.
  env.DB = {prepare(query) {
    const statement = sql.prepare(query);
    function bound(values = []) {
      return {bind: (...args) => bound(args), async first() {
        if (/SELECT \* FROM sessions/.test(query)) {
          f.sessionReads++;
          f.events.push('session:' + f.sessionReads);
          await f.onSessionRead?.(f.sessionReads);
        }
        if (/UPDATE command_lock/.test(query)) {
          f.events.push(query.includes('until_ms=? AND until_ms>?') ? 'lease:renew' : 'lease:claim');
        }
        return statement.get(...values) ?? null;
      }, async run() {
        if (/INSERT OR IGNORE INTO command_claims/.test(query)) f.events.push('claim:persist');
        if (/UPDATE command_claims/.test(query)) f.events.push('result:persist');
        if (/UPDATE command_lock/.test(query)) f.events.push('lease:release');
        const result = statement.run(...values);
        return {success: true, meta: {changes: Number(result.changes)}};
      }, async all() { return {results: statement.all(...values)}; }};
    }
    return bound();
  }};

  env.WAYON = {async fetch(request) {
    const url = new URL(request.url);
    assert.equal(url.origin, 'https://wayon-cloud.hyuklee.workers.dev');
    assert.equal(request.headers.get('authorization'), 'Bearer ' + env.WAYON_DEVICE_KEY);
    assert.equal(request.headers.get('accept-encoding'), null);
    assert.equal(request.redirect, 'manual');
    assert.ok(request.signal instanceof AbortSignal);
    f.cloudCalls.push(url.pathname); f.events.push('cloud:' + url.pathname);
    if (url.pathname === '/api/mobile/impact-suppression') {
      const marker = await request.clone().json();
      assert.ok(['arm', 'cancel'].includes(marker.action));
      assert.equal(marker.requestId, f.requestId);
      f.markerCalls.push(marker); f.events.push('marker:' + marker.action);
    }
    const custom = await f.onCloud?.(request, url.pathname);
    if (custom !== undefined) return custom;
    if (url.pathname === '/api/state') {
      assert.equal(request.method, 'GET'); return Response.json(f.feed);
    }
    assert.equal(url.pathname, '/api/mobile/impact-suppression');
    assert.equal(request.method, 'POST');
    return Response.json({ok: true});
  }};

  t.mock.method(globalThis, 'fetch', async (url, init) => {
    const p = JSON.parse(init.body);
    f.protocolCalls.push(p); f.events.push('gmone:' + p.header.id);
    assert.equal(url, 'https://mp.gmone.co.kr:28354/' + (p.header.id === 8 ? 'b1_init' : 'b1_connect_m'));
    assert.equal(init.method, 'POST'); assert.equal(init.redirect, 'manual');
    assert.ok(init.signal instanceof AbortSignal);
    if (p.header.id !== 8) {
      const claim = sql.prepare('SELECT * FROM command_claims WHERE id=?').get(f.requestId);
      assert.ok(claim, 'parent must claim before any GMOne preflight or command');
      assert.equal(claim.result, null);
      assert.deepEqual(p.login, {uuid: OWNER.uuid, token_key: account().token});
    }
    if (p.header.id === 19) {
      assert.ok(sql.prepare('SELECT until_ms FROM command_lock WHERE id=1').get().until_ms > now);
    }
    const custom = await f.onProtocol?.(p);
    if (custom !== undefined) return custom;
    if (p.header.id === 8) {
      assert.equal(p.login.password, PASSWORD);
      return Response.json({login: {success: 0, user_info_uuid: f.loginAccount.uuid,
        token_key: f.loginAccount.token, car_info: {[f.loginAccount.vehicleId]: {}}}, body: {success: 0}});
    }
    if (p.header.id === 21) return Response.json({timestamp: now, body: {success: 0,
      car_status: {eng: 0, hood: 0, rvsRmng: 2, rvsRmngTmVld: false}}});
    assert.equal(p.header.id, 19, 'unexpected protocol operation');
    return Response.json({body: {success: 0, ...p.body}});
  });

  f.call = async (path, {method = 'GET', body} = {}) => {
    const headers = {cookie: `${COOKIE}=${SESSION_TOKEN}`};
    if (method !== 'GET') Object.assign(headers, {origin: ORIGIN, 'sec-fetch-site': 'same-origin',
      'content-type': 'application/json', 'x-csrf-token': 'fixture-csrf'});
    const response = await handle(new Request(ORIGIN + path, {method, headers,
      ...(body === undefined ? {} : {body: JSON.stringify(body)})}), env, {
      waitUntil() { assert.fail('unexpected background operation'); },
    });
    return {status: response.status, body: await response.json()};
  };
  f.command = (command = 'DOOR_LOCK', extra = {}) => {
    f.requestId = extra.requestId ?? REQUEST_ID;
    return f.call('/api/command', {method: 'POST', body: {command, confirmed: true, requestId: REQUEST_ID, ...extra}});
  };
  f.login = (email = EMAIL) => f.call('/api/account', {method: 'POST', body: {email, password: PASSWORD}});
  f.ops = () => f.protocolCalls.map(p => p.header.id);
  f.storedAccount = () => sql.prepare('SELECT account FROM sessions WHERE id=?').get(f.sessionId)?.account;
  return f;
}

function noSecrets(result) {
  for (const value of [OWNER.uuid, OWNER.vehicleId, account().token, PASSWORD]) {
    assert.ok(!JSON.stringify(result).includes(value), 'response must not contain account identifiers/credentials');
  }
}

test('parent stays disabled without exact enable flag and two lowercase SHA-256 pins', async t => {
  for (const patch of [{COMMANDS_ENABLED: undefined}, {COMMANDS_ENABLED: '0'}, {COMMANDS_ENABLED: 1},
    {GMONE_UUID_HASH: undefined}, {GMONE_VEHICLE_HASH: undefined}, {GMONE_UUID_HASH: 'a'.repeat(63)},
    {GMONE_VEHICLE_HASH: 'g'.repeat(64)}, {GMONE_UUID_HASH: 'A'.repeat(64)}]) {
    await t.test(JSON.stringify(patch), async t => {
      const f = await fixture(t, {env: patch});
      assert.equal((await f.login()).status, 403);
      assert.equal((await f.command()).status, 403);
      const info = await f.call('/api/session');
      assert.equal(info.body.capabilities.commands, false);
      assert.deepEqual(info.body.capabilities.supportedCommands.sort(), Object.keys(COMMAND_SPECS).sort());
      assert.equal(f.sql.prepare('SELECT count(*) AS n FROM command_claims').get().n, 0);
      assert.deepEqual(f.ops(), []); assert.deepEqual(f.cloudCalls, []);
    });
  }
});

test('wrong owner email is denied before mock login or account storage', async t => {
  const f = await fixture(t);
  assert.equal((await f.login('different@example.test')).status, 403);
  assert.equal(f.storedAccount(), f.initialCipher);
  assert.deepEqual(f.ops(), []); assert.deepEqual(f.cloudCalls, []);
});

for (const field of ['uuid', 'vehicleId']) {
  test(`login rejects a mismatched ${field} even with the correct email fingerprint`, async t => {
    const f = await fixture(t); f.loginAccount[field] = 'FIXTURE_OTHER_ID';
    const result = await f.login();
    assert.equal(result.status, 403); noSecrets(result);
    assert.equal(f.storedAccount(), f.initialCipher);
    assert.deepEqual(f.ops(), [8]); assert.deepEqual(f.cloudCalls, []);
  });
  test(`command revalidates the pinned ${field} in the stored encrypted account`, async t => {
    const f = await fixture(t, {account: {[field]: 'FIXTURE_OTHER_ID'}});
    // Request-body identity cannot override the authenticated server account.
    const result = await f.command('VEHICLE_START', {account: account(), liveState: feed()});
    assert.equal(result.status, 409); assert.equal(result.body.ok, false); noSecrets(result);
    assert.deepEqual(f.ops(), []); assert.deepEqual(f.cloudCalls, []);
    assert.equal(f.sql.prepare('SELECT count(*) AS n FROM command_claims WHERE result IS NOT NULL').get().n, 1);
  });
}

test('correct owner login persists only an encrypted server account and exposes no identity', async t => {
  const f = await fixture(t);
  const result = await f.login('  OWNER@example.test  ');
  assert.equal(result.status, 200); assert.equal(result.body.loggedIn, true); noSecrets(result);
  assert.notEqual(f.storedAccount(), f.initialCipher);
  assert.ok(!f.storedAccount().includes(OWNER.uuid));
  const stored = await decrypt(f.storedAccount(), f.env.ACCOUNT_ENCRYPTION_KEY);
  assert.equal(stored.uuid, OWNER.uuid); assert.equal(stored.vehicleId, OWNER.vehicleId);
  assert.equal(stored.expiresAtMs - stored.issuedAtMs, ACCOUNT_TTL_MS);
  assert.deepEqual(f.ops(), [8]); assert.deepEqual(f.cloudCalls, []);
});

test('wrong or missing device is rejected before any GMOne preflight/command', async t => {
  for (const command of ['DOOR_LOCK', 'VEHICLE_START']) {
    for (const missing of [false, true]) await t.test(`${command}: ${missing ? 'missing' : 'wrong'}`, async t => {
      const f = await fixture(t);
      // Both raw/row device IDs agree, so only the parent fixed-device guard denies.
      f.feed = feed('FIXTURE_OTHER_DEVICE');
      if (missing) delete f.feed.state.device_id;
      const result = await f.command(command);
      assert.equal(result.status, 409); assert.equal(result.body.ok, false); noSecrets(result);
      assert.deepEqual(f.ops(), []); assert.deepEqual(f.cloudCalls, ['/api/state']);
      assert.equal(f.sessionReads, 1);
      assert.ok(!f.events.includes('lease:renew'));
    });
  }
});

test('correct account/device reach the real guard and exactly one mocked command, with persisted dedupe', async t => {
  const f = await fixture(t);
  const result = await f.command();
  assert.equal(result.status, 200); assert.equal(result.body.ok, true);
  assert.equal(result.body.state, 'server_responded'); assert.equal(result.body.vehicleConfirmed, false);
  noSecrets(result); assert.deepEqual(f.ops(), [19]); assert.equal(f.sessionReads, 3);
  assert.ok(f.events.indexOf('claim:persist') < f.events.indexOf('cloud:/api/state'));
  assert.ok(f.events.indexOf('session:2') < f.events.indexOf('lease:renew'));
  assert.ok(f.events.indexOf('lease:renew') < f.events.indexOf('session:3'));
  assert.ok(f.events.indexOf('session:3') < f.events.indexOf('gmone:19'));
  assert.equal(f.sql.prepare('SELECT until_ms FROM command_lock').get().until_ms, NOW + 3000);
  const repeated = await f.command();
  assert.deepEqual(repeated, result); assert.deepEqual(f.ops(), [19]);
  assert.deepEqual(f.cloudCalls, ['/api/state', '/api/state']);
});

test('engine start orders direct status, session check, marker, renewal, final session check, then op19', async t => {
  const f = await fixture(t);
  const result = await f.command('VEHICLE_START');
  assert.equal(result.body.ok, true); assert.deepEqual(f.ops(), [21, 19]);
  assert.deepEqual(f.cloudCalls, ['/api/state', '/api/mobile/impact-suppression', '/api/state']);
  const stages = ['claim:persist', 'gmone:21', 'session:2', 'cloud:/api/mobile/impact-suppression', 'lease:renew', 'session:3', 'gmone:19', 'result:persist'];
  for (let i = 1; i < stages.length; i++) assert.ok(f.events.indexOf(stages[i - 1]) < f.events.indexOf(stages[i]));
});

test('logout, account removal or ciphertext replacement before beforeSend deny physical dispatch', async t => {
  for (const action of ['logout', 'remove', 'replace']) await t.test(action, async t => {
    const f = await fixture(t);
    f.onProtocol = async p => {
      if (p.header.id !== 21) return;
      if (action === 'logout') f.sql.prepare('DELETE FROM sessions WHERE id=?').run(f.sessionId);
      else f.sql.prepare('UPDATE sessions SET account=? WHERE id=?')
        .run(action === 'remove' ? null : await encrypt(account(), f.env.ACCOUNT_ENCRYPTION_KEY), f.sessionId);
    };
    const result = await f.command('VEHICLE_START');
    assert.equal(result.body.ok, false); assert.equal(result.body.state, 'blocked');
    assert.equal(result.body.code, 'before_send_failed'); assert.deepEqual(f.ops(), [21]);
    assert.deepEqual(f.cloudCalls, ['/api/state']);
  });
});

test('a lost lease cannot be renewed or released by the older invocation', async t => {
  const f = await fixture(t), otherLease = NOW + 240_000;
  f.onCloud = async (_request, path) => {
    if (path === '/api/state') f.sql.prepare('UPDATE command_lock SET until_ms=? WHERE id=1').run(otherLease);
  };
  const result = await f.command();
  assert.equal(result.body.state, 'blocked'); assert.equal(result.body.code, 'before_send_failed');
  assert.deepEqual(f.ops(), []);
  assert.equal(f.sql.prepare('SELECT until_ms FROM command_lock').get().until_ms, otherLease);
});

test('an expired lease blocks even if the offroad feed remains fresh', async t => {
  const f = await fixture(t);
  f.onSessionRead = async count => { if (count === 2) f.advance(180_001); };
  const result = await f.command();
  assert.equal(result.body.state, 'blocked'); assert.equal(result.body.code, 'before_send_failed');
  assert.deepEqual(f.ops(), []);
});

test('the single cloud snapshot can expire during fresh GMOne preflight and must deny', async t => {
  const f = await fixture(t); f.feed = feed(DEVICE, NOW - 599_000);
  f.onProtocol = async p => { if (p.header.id === 21) f.advance(1001); };
  const result = await f.command('VEHICLE_START');
  assert.equal(result.body.state, 'blocked'); assert.equal(result.body.code, 'live_state_not_fresh');
  assert.deepEqual(f.ops(), [21]); assert.deepEqual(f.cloudCalls, ['/api/state']);
  assert.equal(f.sessionReads, 1);
});

test('sessionInfo advertises exactly 15 commands but expiry disables execution without a network request', async t => {
  const f = await fixture(t, {account: {expiresAtMs: NOW}});
  const info = await f.call('/api/session');
  assert.equal(info.body.account.loggedIn, false); assert.equal(info.body.capabilities.commands, false);
  assert.equal(info.body.capabilities.supportedCommands.length, 15);
  assert.deepEqual(info.body.capabilities.supportedCommands.sort(), Object.keys(COMMAND_SPECS).sort());
  noSecrets(info); assert.deepEqual(f.ops(), []); assert.deepEqual(f.cloudCalls, []);
  const result = await f.command();
  assert.equal(result.body.state, 'blocked'); assert.equal(result.body.code, 'account_invalid_or_expired');
  assert.deepEqual(f.ops(), []);
});

test('ambiguous mocked command failure remains claimed and is never replayed', async t => {
  const f = await fixture(t);
  f.onProtocol = async () => { throw new Error('FIXTURE_UPSTREAM_FAILURE'); };
  const first = await f.command();
  assert.equal(first.body.state, 'unknown'); assert.equal(first.body.dispatched, true);
  assert.deepEqual(await f.command(), first); assert.deepEqual(f.ops(), [19]);
  assert.deepEqual(f.cloudCalls, ['/api/state', '/api/state']); noSecrets(first);
});

test('logout while the impact marker is in flight must still prevent engine dispatch', async t => {
  const f = await fixture(t);
  f.onCloud = async (_request, path) => {
    if (path === '/api/mobile/impact-suppression') {
      // The first beforeSend session check already passed. Model another request
      // revoking it during the marker await, using only this in-memory database.
      f.sql.prepare('DELETE FROM sessions WHERE id=?').run(f.sessionId);
    }
  };
  const result = await f.command('VEHICLE_START');
  assert.deepEqual(f.ops(), [21], 'revoked session must not reach operation 19 after the marker await');
  assert.equal(result.body.ok, false);
  assert.equal(result.body.state, 'blocked');
  assert.deepEqual(f.markerCalls, [{action: 'arm', requestId: REQUEST_ID}, {action: 'cancel', requestId: REQUEST_ID}]);
  assert.ok(f.events.indexOf('result:persist') < f.events.indexOf('marker:cancel'));
});

test('final session check rejects ciphertext replacement during marker even for the same owner', async t => {
  const f = await fixture(t);
  f.onCloud = async (_request, path) => {
    if (path === '/api/mobile/impact-suppression') {
      const replacement = await encrypt(account(), f.env.ACCOUNT_ENCRYPTION_KEY);
      assert.notEqual(replacement, f.initialCipher);
      f.sql.prepare('UPDATE sessions SET account=? WHERE id=?').run(replacement, f.sessionId);
    }
  };
  const result = await f.command('VEHICLE_START');
  assert.equal(result.body.state, 'blocked'); assert.equal(result.body.code, 'before_send_failed');
  assert.equal(result.body.dispatched, false); assert.equal(f.sessionReads, 3);
  assert.deepEqual(f.ops(), [21]);
  assert.deepEqual(f.markerCalls.map(m => m.action), ['arm', 'cancel']);
});

test('marker cleanup preserves definite results even when cleanup fails', async t => {
  for (const failure of ['throw', 'http', 'body']) await t.test(failure, async t => {
    const f = await fixture(t);
    f.onCloud = async (request, path) => {
      if (path !== '/api/mobile/impact-suppression') return;
      const marker = await request.json();
      if (marker.action === 'arm') {
        f.sql.prepare('DELETE FROM sessions WHERE id=?').run(f.sessionId);
        return;
      }
      if (failure === 'throw') throw new Error('FIXTURE_PRIVATE_CANCEL_ERROR');
      if (failure === 'http') return new Response('FIXTURE_PRIVATE_CANCEL_ERROR', {status: 503});
      return {body: {cancel: async () => { throw new Error('FIXTURE_PRIVATE_CANCEL_ERROR'); }}};
    };
    const result = await f.command('VEHICLE_START');
    assert.equal(result.status, 200); assert.equal(result.body.state, 'blocked');
    assert.equal(result.body.dispatched, false); assert.equal(result.body.code, 'before_send_failed');
    assert.deepEqual(f.ops(), [21]); assert.deepEqual(f.markerCalls.map(m => m.action), ['arm', 'cancel']);
    const stored = JSON.parse(f.sql.prepare('SELECT result FROM command_claims WHERE id=?').get(REQUEST_ID).result);
    assert.deepEqual(stored, result.body); assert.ok(!JSON.stringify(result).includes('FIXTURE_PRIVATE_CANCEL_ERROR'));
  });
});

test('marker cleanup after failed arm, lost lease or aged preflight never dispatches', async t => {
  for (const cause of ['arm-throw', 'arm-http', 'lease', 'stale']) await t.test(cause, async t => {
    const f = await fixture(t), otherLease = NOW + 240_000;
    f.onCloud = async (request, path) => {
      if (path !== '/api/mobile/impact-suppression' || (await request.json()).action !== 'arm') return;
      if (cause === 'arm-throw') throw new Error('SIMULATED_ARM_RESPONSE_LOSS');
      if (cause === 'arm-http') return new Response('', {status: 503});
      if (cause === 'lease') f.sql.prepare('UPDATE command_lock SET until_ms=? WHERE id=1').run(otherLease);
      if (cause === 'stale') f.advance(30_001);
    };
    const result = await f.command('VEHICLE_START');
    assert.equal(result.body.state, 'blocked'); assert.equal(result.body.dispatched, false);
    assert.deepEqual(f.ops(), [21]); assert.deepEqual(f.markerCalls.map(m => m.action), ['arm', 'cancel']);
    assert.ok(f.markerCalls.every(m => m.requestId === REQUEST_ID));
    if (cause === 'lease') assert.equal(f.sql.prepare('SELECT until_ms FROM command_lock').get().until_ms, otherLease);
    assert.deepEqual(await f.command('VEHICLE_START'), result);
    assert.equal(f.markerCalls.length, 2);
  });
});

test('accepted and ambiguous engine commands never cancel the suppression marker or resend', async t => {
  for (const cause of ['accepted', 'transport', 'rejected', 'invalid', 'auth']) await t.test(cause, async t => {
    const f = await fixture(t);
    f.onProtocol = async p => {
      if (p.header.id !== 19) return;
      if (cause === 'transport') throw new Error('FIXTURE_COMMAND_RESPONSE_LOSS');
      if (cause === 'rejected') return Response.json({body: {success: 12}});
      if (cause === 'invalid') return Response.json({body: {}});
      if (cause === 'auth') return Response.json({login: null, body: {success: 0}});
    };
    const result = await f.command('VEHICLE_START');
    assert.equal(result.body.state, cause === 'accepted' ? 'server_responded' : 'unknown');
    assert.equal(result.body.dispatched, true); assert.deepEqual(f.ops(), [21, 19]);
    assert.deepEqual(f.markerCalls, [{action: 'arm', requestId: REQUEST_ID}]);
    assert.deepEqual(await f.command('VEHICLE_START'), result); assert.deepEqual(f.ops(), [21, 19]);
    assert.equal(f.markerCalls.length, 1);
  });
});

test('original panic/sunroof commands retain fixed binding, CSRF, motion and at-most-once guards', async t => {
  for (const cmd of ['PANIC', 'SUNROOF_OPEN', 'SUNROOF_CLOSE', 'SUNROOF_TILT']) {
    for (const state of ['allowed', 'wrong-device', 'wrong-owner', 'moving', 'csrf']) await t.test(`${cmd}:${state}`, async t => {
      const f = await fixture(t, state === 'wrong-owner' ? {account: {uuid: 'WRONG_OWNER'}} : {});
      if (state === 'wrong-device') f.feed = feed('WRONG_DEVICE');
      if (state === 'moving') f.feed.state.speed_mps = 1;
      if (state === 'csrf') f.sql.prepare('UPDATE sessions SET csrf=? WHERE id=?').run('changed', f.sessionId);
      const result = await f.command(cmd);
      assert.equal(result.body.ok === true, state === 'allowed');
      assert.deepEqual(f.ops(), state === 'allowed' ? [19] : []);
      assert.deepEqual(f.markerCalls, []);
      if (state === 'allowed') {
        assert.deepEqual(f.protocolCalls[0].body, COMMAND_SPECS[cmd]);
        assert.deepEqual(await f.command(cmd), result); assert.deepEqual(f.ops(), [19]);
      }
    });
  }
});

test('account login exposes only stable sanitized protocol errors and preserves stored session', async t => {
  const cases = [
    ['login_rejected', 401, () => Response.json({login: {success: 1}, body: {success: 0}})],
    ['invalid_login_response', 502, () => Response.json({login: {success: 0}, body: {success: 0}})],
    ['single_vehicle_required', 403, () => Response.json({login: {success: 0, user_info_uuid: OWNER.uuid,
      token_key: account().token, car_info: {}}, body: {success: 0}})],
    ['transport_error', 502, () => { throw new Error(PASSWORD); }],
    ['upstream_http_error', 502, () => new Response(PASSWORD, {status: 503})],
    ['invalid_response', 502, () => new Response(PASSWORD)],
    ['response_too_large', 502, () => new Response('x'.repeat(512 * 1024 + 1))],
  ];
  for (const [code, status, reply] of cases) await t.test(code, async t => {
    const f = await fixture(t); f.onProtocol = async () => reply();
    const result = await f.login();
    assert.equal(result.status, status); assert.equal(result.body.code, code);
    assert.equal(result.body.ok, false); assert.equal(result.body.state, 'blocked');
    assert.match(result.body.message, /[\uac00-\ud7a3]/); noSecrets(result);
    assert.deepEqual(Object.keys(result.body).sort(), ['code', 'message', 'ok', 'state']);
    assert.equal(f.storedAccount(), f.initialCipher); assert.deepEqual(f.ops(), [8]);
  });
  const f = await fixture(t);
  const result = await f.call('/api/account', {method: 'POST', body: {email: EMAIL, password: ' \t '}});
  assert.equal(result.status, 400); assert.equal(result.body.code, 'invalid_credentials');
  assert.deepEqual(f.ops(), []); assert.equal(f.storedAccount(), f.initialCipher);
});

test('final session check catches logout after lease renewal for a non-engine command', async t => {
  const f = await fixture(t);
  f.onSessionRead = async count => {
    if (count === 3) {
      assert.ok(f.events.includes('lease:renew'));
      f.sql.prepare('DELETE FROM sessions WHERE id=?').run(f.sessionId);
    }
  };
  const result = await f.command();
  assert.equal(result.body.state, 'blocked'); assert.equal(result.body.code, 'before_send_failed');
  assert.equal(result.body.dispatched, false); assert.equal(f.sessionReads, 3);
  assert.deepEqual(f.ops(), []); assert.deepEqual(f.cloudCalls, ['/api/state', '/api/state']);
});

test('final cloud requery after 20s preflight blocks newly moving, engaged, stale or mismatched feed', async t => {
  for (const change of ['moving', 'engaged', 'unknown', 'stale', 'device', 'valid']) await t.test(change, async t => {
    const f = await fixture(t);
    f.onProtocol = async p => {
      if (p.header.id !== 21) return;
      f.advance(20_000);
      f.feed = feed(DEVICE, f.now());
      if (change === 'moving') f.feed.state.speed_mps = 1;
      if (change === 'engaged') {
        const raw = JSON.parse(f.feed.state.raw_json); raw.openpilot.active = true;
        f.feed.state.raw_json = JSON.stringify(raw);
      }
      if (change === 'unknown') delete f.feed.state.raw_json;
      if (change === 'stale') f.feed = feed(DEVICE, f.now() - 600_001);
      if (change === 'device') f.feed = feed('DIFFERENT_DEVICE', f.now());
    };
    const result = await f.command('VEHICLE_START');
    assert.equal(result.body.state, change === 'valid' ? 'server_responded' : 'blocked');
    assert.deepEqual(f.ops(), change === 'valid' ? [21, 19] : [21]);
    assert.equal(f.cloudCalls.filter(p => p === '/api/state').length, 2);
    assert.deepEqual(f.markerCalls.map(m => m.action), change === 'valid' ? ['arm'] : ['arm', 'cancel']);
  });
});

test('final feed failure, age during requery, or logout blocks without any command retry', async t => {
  for (const change of ['transport', 'http', 'json', 'age', 'logout']) await t.test(change, async t => {
    const f = await fixture(t); let reads = 0;
    f.onCloud = async (_request, path) => {
      if (path !== '/api/state' || ++reads !== 2) return;
      if (change === 'transport') throw new TypeError('FIXTURE_PRIVATE_TRANSPORT');
      if (change === 'http') return new Response('PRIVATE', {status: 503});
      if (change === 'json') return new Response('not json');
      if (change === 'age') f.advance(30_001);
      if (change === 'logout') f.sql.prepare('DELETE FROM sessions WHERE id=?').run(f.sessionId);
    };
    const result = await f.command('VEHICLE_START');
    assert.equal(result.body.state, 'blocked'); assert.equal(result.body.dispatched, false);
    assert.deepEqual(f.ops(), [21]); assert.deepEqual(f.markerCalls.map(m => m.action), ['arm', 'cancel']);
  });
});

test('known GMOne expiry clears only the exact old ciphertext and stays logged out on later session polls', async t => {
  for (const stage of ['preflight', 'command']) for (const replace of [false, true]) {
    await t.test(`${stage}:${replace}`, async t => {
      const f = await fixture(t); let replacement;
      f.onProtocol = async p => {
        if (p.header.id !== (stage === 'preflight' ? 21 : 19)) return;
        if (replace) {
          replacement = await encrypt(account(), f.env.ACCOUNT_ENCRYPTION_KEY);
          f.sql.prepare('UPDATE sessions SET account=? WHERE id=?').run(replacement, f.sessionId);
        }
        return Response.json({login: {success: '1'}, body: {success: 0}});
      };
      const result = await f.command('VEHICLE_START');
      assert.equal(result.body.code, 'session_expired');
      assert.equal(result.body.dispatched, stage === 'command');
      assert.equal(f.storedAccount(), replace ? replacement : null);
      if (!replace) assert.equal(f.sql.prepare('SELECT email FROM sessions WHERE id=?').get(f.sessionId).email, null);
      for (const delay of [0, 60_000]) {
        f.advance(delay);
        const info = await f.call('/api/session');
        assert.equal(info.body.account.loggedIn, replace);
        assert.equal(info.body.capabilities.commands, replace);
      }
      assert.deepEqual(f.ops(), stage === 'command' ? [21, 19] : [21]);
    });
  }
});

test('malformed auth and transient transport errors never clear an encrypted account', async t => {
  for (const kind of ['null', 'invalid', 'transport']) await t.test(kind, async t => {
    const f = await fixture(t);
    f.onProtocol = async () => {
      if (kind === 'transport') throw new Error('FIXTURE_TRANSPORT');
      return Response.json({login: kind === 'null' ? null : {success: false}, body: {success: 0}});
    };
    const result = await f.command('VEHICLE_START');
    assert.equal(result.body.state, 'blocked');
    assert.equal(f.storedAccount(), f.initialCipher);
    assert.equal((await f.call('/api/session')).body.account.loggedIn, true);
    assert.deepEqual(f.ops(), [21]);
  });
});

test('ambiguous dispatch retains 180 seconds from completion and blocks a new UUID', async t => {
  const f = await fixture(t), nextId = '33333333-3333-4333-8333-333333333333';
  f.onProtocol = async p => {
    if (p.header.id === 19) { f.advance(10_000); throw new Error('FIXTURE_AMBIGUOUS'); }
  };
  const result = await f.command();
  const until = f.now() + 180_000;
  assert.equal(result.body.state, 'unknown'); assert.equal(result.body.dispatched, true);
  assert.equal(result.body.retryAfterMs, 180_000); assert.equal(result.body.cooldownUntilMs, until);
  assert.equal(f.sql.prepare('SELECT until_ms FROM command_lock').get().until_ms, until);
  assert.deepEqual(await f.command(), result);
  for (const delta of [3001, 176_998]) {
    f.advance(delta);
    assert.equal((await f.command('DOOR_LOCK', {requestId: nextId})).status, 429);
    assert.deepEqual(f.ops(), [19]);
  }
  f.advance(2); f.onProtocol = undefined;
  assert.equal((await f.command('DOOR_LOCK', {requestId: nextId})).body.state, 'server_responded');
  assert.deepEqual(f.ops(), [19, 19]);
  assert.equal(f.sql.prepare('SELECT until_ms FROM command_lock').get().until_ms, f.now() + 3000);
});

test('ambiguous older invocation cannot overwrite another lease owner', async t => {
  const f = await fixture(t), otherLease = NOW + 400_000;
  f.onProtocol = async () => {
    f.sql.prepare('UPDATE command_lock SET until_ms=? WHERE id=1').run(otherLease);
    throw new Error('FIXTURE_AMBIGUOUS');
  };
  assert.equal((await f.command()).body.state, 'unknown');
  assert.equal(f.sql.prepare('SELECT until_ms FROM command_lock').get().until_ms, otherLease);
});

test('initial feed transport failure is a claimed definite non-dispatch with short release', async t => {
  const f = await fixture(t);
  f.onCloud = async () => { throw new TypeError('FIXTURE_PRIVATE_FAILURE'); };
  const result = await f.command('VEHICLE_START');
  assert.equal(result.status, 502); assert.equal(result.body.code, 'upstream_transport');
  assert.equal(result.body.state, 'blocked'); assert.equal(result.body.dispatched, false);
  assert.equal(result.body.retryable, false); assert.deepEqual(f.ops(), []);
  assert.equal(f.sql.prepare('SELECT until_ms FROM command_lock').get().until_ms, NOW + 3000);
  const replay = await f.command('VEHICLE_START');
  assert.deepEqual(replay.body, result.body); assert.deepEqual(f.cloudCalls, ['/api/state']);
});
