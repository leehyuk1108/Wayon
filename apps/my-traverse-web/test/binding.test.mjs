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
  const f = {sql, events: [], cloudCalls: [], protocolCalls: [], sessionReads: 0,
    feed: feed(), loginAccount: account(), advance: ms => { now += ms; }, now: () => now};
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
    assert.equal(request.redirect, 'manual');
    assert.ok(request.signal instanceof AbortSignal);
    f.cloudCalls.push(url.pathname); f.events.push('cloud:' + url.pathname);
    const custom = await f.onCloud?.(request, url.pathname);
    if (custom !== undefined) return custom;
    if (url.pathname === '/api/json') {
      assert.equal(request.method, 'GET'); return Response.json(f.feed);
    }
    assert.equal(url.pathname, '/api/mobile/impact-suppression');
    assert.equal(request.method, 'POST');
    assert.deepEqual(await request.json(), {action: 'arm', requestId: REQUEST_ID});
    return Response.json({ok: true});
  }};

  t.mock.method(globalThis, 'fetch', async (url, init) => {
    const p = JSON.parse(init.body);
    f.protocolCalls.push(p); f.events.push('gmone:' + p.header.id);
    assert.equal(url, 'https://mp.gmone.co.kr:28354/' + (p.header.id === 8 ? 'b1_init' : 'b1_connect_m'));
    assert.equal(init.method, 'POST'); assert.equal(init.redirect, 'manual');
    assert.ok(init.signal instanceof AbortSignal);
    if (p.header.id !== 8) {
      const claim = sql.prepare('SELECT * FROM command_claims WHERE id=?').get(REQUEST_ID);
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
  f.command = (command = 'DOOR_LOCK', extra = {}) => f.call('/api/command', {method: 'POST',
    body: {command, confirmed: true, requestId: REQUEST_ID, ...extra}});
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
      assert.deepEqual(f.ops(), []); assert.deepEqual(f.cloudCalls, ['/api/json']);
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
  assert.ok(f.events.indexOf('claim:persist') < f.events.indexOf('cloud:/api/json'));
  assert.ok(f.events.indexOf('session:2') < f.events.indexOf('lease:renew'));
  assert.ok(f.events.indexOf('lease:renew') < f.events.indexOf('session:3'));
  assert.ok(f.events.indexOf('session:3') < f.events.indexOf('gmone:19'));
  assert.equal(f.sql.prepare('SELECT until_ms FROM command_lock').get().until_ms, NOW + 3000);
  const repeated = await f.command();
  assert.deepEqual(repeated, result); assert.deepEqual(f.ops(), [19]);
  assert.deepEqual(f.cloudCalls, ['/api/json']);
});

test('engine start orders direct status, session check, marker, renewal, final session check, then op19', async t => {
  const f = await fixture(t);
  const result = await f.command('VEHICLE_START');
  assert.equal(result.body.ok, true); assert.deepEqual(f.ops(), [21, 19]);
  assert.deepEqual(f.cloudCalls, ['/api/json', '/api/mobile/impact-suppression']);
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
    assert.deepEqual(f.cloudCalls, ['/api/json']);
  });
});

test('a lost lease cannot be renewed or released by the older invocation', async t => {
  const f = await fixture(t), otherLease = NOW + 240_000;
  f.onCloud = async (_request, path) => {
    if (path === '/api/json') f.sql.prepare('UPDATE command_lock SET until_ms=? WHERE id=1').run(otherLease);
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
  assert.deepEqual(f.ops(), [21]); assert.deepEqual(f.cloudCalls, ['/api/json']);
  assert.equal(f.sessionReads, 1);
});

test('sessionInfo advertises exactly 11 commands but expiry disables execution without a network request', async t => {
  const f = await fixture(t, {account: {expiresAtMs: NOW}});
  const info = await f.call('/api/session');
  assert.equal(info.body.account.loggedIn, false); assert.equal(info.body.capabilities.commands, false);
  assert.equal(info.body.capabilities.supportedCommands.length, 11);
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
  assert.deepEqual(f.cloudCalls, ['/api/json']); noSecrets(first);
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
  assert.deepEqual(f.ops(), []); assert.deepEqual(f.cloudCalls, ['/api/json']);
});
