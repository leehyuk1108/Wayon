import assert from 'node:assert/strict';
import {createHash, generateKeyPairSync, sign} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';
import {test} from 'node:test';
import {patch, unpatch, BASELINE_SHA256, OUTPUT_SHA256} from './patch.mjs';
import {sha256} from '../fast-vehicle-state-20261028/patch.mjs';

// Private copies of the active production modules and the production DDL (no data); not committed.
const root = process.env.WAYON_ACTIVE_MODULE_DIR || '/Users/hyuklee/Documents/my-traverse-web-20261110/self-register';
const require = createRequire(import.meta.url);
const {Miniflare} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/Documents/sunnypilot/apps/my-traverse-web/node_modules/miniflare');
const baseline = readFileSync(join(root, 'stage-baseline-worker.js'), 'utf8');
const candidate = patch(baseline);
const OWNER_KEY = 'wayon_' + 'a'.repeat(48), OWNER = '3e07889d79b48064';
const DEV = 'a1b2c3d4e5f60718', DEV_KEY = 'wayon_' + 'n'.repeat(64), OTHER_KEY = 'wayon_' + 'o'.repeat(64);
const hash = value => createHash('sha256').update(value).digest('hex');
const b64url = value => Buffer.from(value).toString('base64url');

const ec = generateKeyPairSync('ec', {namedCurve: 'P-256'});
const rsa = generateKeyPairSync('rsa', {modulusLength: 2048});
const attacker = generateKeyPairSync('ec', {namedCurve: 'P-256'});
const pem = pair => pair.publicKey.export({type: 'spki', format: 'pem'});
function opensshRsa(pair) {
  const jwk = pair.publicKey.export({format: 'jwk'});
  const field = buf => { const len = Buffer.alloc(4); len.writeUInt32BE(buf.length); return Buffer.concat([len, buf]); };
  const mpint = b => { const raw = Buffer.from(b, 'base64url'); return raw[0] & 0x80 ? Buffer.concat([Buffer.from([0]), raw]) : raw; };
  return 'ssh-rsa ' + Buffer.concat([field(Buffer.from('ssh-rsa')), field(mpint(jwk.e)), field(mpint(jwk.n))]).toString('base64');
}
function proof({pair = ec, alg = 'ES256', identity = DEV, purpose = 'wayon-key-register-v1', requestId = 'req-0123456789abcdef',
                key = DEV_KEY, iat = Math.floor(Date.now() / 1000), life = 240, header = {}} = {}) {
  const head = b64url(JSON.stringify({alg, typ: 'JWT', ...header}));
  const body = b64url(JSON.stringify({identity, nbf: iat, iat, exp: iat + life, wayon: {purpose, requestId, newKeyHash: hash(key)}}));
  const signature = alg === 'ES256'
    ? sign('sha256', Buffer.from(head + '.' + body), {key: pair.privateKey, dsaEncoding: 'ieee-p1363'})
    : sign('sha256', Buffer.from(head + '.' + body), pair.privateKey);
  return head + '.' + body + '.' + signature.toString('base64url');
}

test('patch is byte-exact and reversible', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  if (OUTPUT_SHA256 !== 'PENDING') assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
});

async function fixture(script, {comma = {[DEV]: {public_key: pem(ec)}}, commaStatus = 200} = {}) {
  const modules = [{type: 'ESModule', path: '/isolated/worker.js', contents: script}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type: 'ESModule', path: '/isolated/' + name, contents: readFileSync(join(root, 'stage-baseline-' + name), 'utf8')});
  }
  const outbound = [];
  const logs = [];
  const mf = new Miniflare({modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14',
    d1Databases: {DB: 'self-register-' + Math.random().toString(36).slice(2)}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {WAYON_UPLOAD_TOKEN: 'fixture-legacy', WAYON_SERVER_SYNC_TOKEN: 'fixture-sync', WAYON_VIEW_TOKEN: 'fixture-view',
      WAYON_AI_READ_TOKEN: 'fixture-ai', WAYON_AI_DEVICE_ID: OWNER, WAYON_GMONE_TOKEN: 'fixture-gmone', WAYON_PARKING_NOTIFY_TOKEN: 'fixture-notify'},
    serviceBindings: {ASSETS: () => new Response(null, {status: 404}), WAYON_SERVER_API: () => new Response('down', {status: 503})},
    outboundService: request => {
      const url = new URL(request.url);
      outbound.push({url: url.href, auth: request.headers.get('authorization')});
      const match = url.hostname === 'api.commadotai.com' && url.pathname.match(/^\/v1\.1\/devices\/([0-9a-f]{16})\/$/);
      if (!match) return new Response(null, {status: 599});
      if (commaStatus !== 200) return new Response('{}', {status: commaStatus, headers: commaStatus === 302 ? {location: 'https://elsewhere.example/'} : {}});
      const info = comma[match[1]];
      // comma answers with text/html content type even for JSON.
      return info ? new Response(JSON.stringify({dongle_id: match[1], last_gps_lat: 37.5, ...info}), {headers: {'content-type': 'text/html; charset=utf-8'}})
        : new Response('{}', {status: 404});
    },
    handleRuntimeStdio(stdout, stderr) { for (const s of [stdout, stderr]) s.on('data', d => logs.push(String(d))); }});
  const db = await mf.getD1Database('DB');
  for (const statement of readFileSync(join(root, 'prod-schema-20261112.sql'), 'utf8').split(/;\n/).map(x => x.trim()).filter(Boolean)) {
    await db.prepare(statement).run();
  }
  await db.exec(readFileSync(new URL('../device-invite-20261112/migration.sql', import.meta.url), 'utf8').replace(/--.*\n/g, '').replace(/\n/g, ' '));
  await db.prepare('INSERT INTO wayon_devices VALUES(?,?,?,?,?,NULL)').bind(OWNER, hash(OWNER_KEY), 'c', 'u', 'unchanged').run();
  await db.prepare('INSERT INTO trips(id,device_id,started_at,ended_at,duration_s,distance_m,route_point_count,route_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)')
    .bind(OWNER + '-00000001', OWNER, '2026-11-09T01:00:00Z', '2026-11-09T01:10:00Z', 600, 3000, 0, '[]', '2026-11-09T01:10:00Z').run();
  await db.prepare("INSERT INTO latest_state(device_id,updated_at,onroad,ignition,enabled,voltage_v,raw_json) VALUES(?,?,0,0,1,12.34,'{}')")
    .bind(OWNER, '2026-11-12T01:00:00.000Z').run();
  const call = async (path, {method = 'POST', key, body} = {}) => {
    const r = await mf.dispatchFetch('https://isolated.test' + path, {method,
      headers: {...(key ? {authorization: 'Bearer ' + key} : {}), ...(body ? {'content-type': 'application/json'} : {})},
      ...(body ? {body: JSON.stringify(body)} : {})});
    const text = await r.text();
    let json = null; try { json = JSON.parse(text); } catch {}
    return {status: r.status, body: json, text};
  };
  const register = (fields = {}) => call('/api/devices/self-register', {body: {deviceId: DEV, key: DEV_KEY, requestId: 'req-0123456789abcdef', proof: proof(), ...fields}});
  const device = id => db.prepare('SELECT key_hash, revoked_at FROM wayon_devices WHERE device_id = ?').bind(id).first();
  const origins = () => db.prepare('SELECT * FROM wayon_device_origins').all().then(r => r.results);
  return {mf, db, call, register, device, origins, outbound, logs, dispose: () => mf.dispose()};
}

test('a real comma registers itself with its own key, proven by its comma device key (ES256, PEM)', async () => {
  const f = await fixture(candidate);
  try {
    const p = proof();
    const r = await f.register({proof: p});
    assert.deepEqual([r.status, r.body], [200, {ok: true, deviceId: DEV}]);
    assert.equal((await f.device(DEV)).key_hash, hash(DEV_KEY));
    const [origin] = await f.origins();
    assert.deepEqual([origin.device_id, origin.invited_by], [DEV, 'self']);
    assert.equal(f.outbound.length, 1);
    assert.equal(f.outbound[0].url, 'https://api.commadotai.com/v1.1/devices/' + DEV + '/');
    assert.equal(f.outbound[0].auth, 'JWT ' + p);
    // The new key works and sees only its own data.
    const trips = await f.call('/api/trips?limit=5', {method: 'GET', key: DEV_KEY});
    assert.equal(trips.status, 200);
    assert.ok(!trips.text.includes(OWNER + '-00000001'));
    // It cannot create invites for others.
    assert.equal((await f.call('/api/devices/invites', {key: DEV_KEY})).status, 403);
    await new Promise(resolve => setTimeout(resolve, 200));
    const logText = f.logs.join('');
    assert.ok(!logText.includes(DEV_KEY) && !logText.includes(p.split('.')[2]) && !logText.includes('37.5'));
  } finally { await f.dispose(); }
});

test('an RS256 comma with an OpenSSH public key registers too', async () => {
  const f = await fixture(candidate, {comma: {[DEV]: {public_key: opensshRsa(rsa)}}});
  try {
    const r = await f.register({proof: proof({pair: rsa, alg: 'RS256'})});
    assert.deepEqual([r.status, r.body], [200, {ok: true, deviceId: DEV}]);
  } finally { await f.dispose(); }
});

test('malformed, unbound, stale or unsafe proofs are refused before asking comma', async () => {
  const f = await fixture(candidate);
  try {
    const now = Math.floor(Date.now() / 1000);
    const bad = [
      proof({identity: 'ffffffffffffffff'}), proof({purpose: 'key-reissue-v1'}), proof({key: OTHER_KEY}),
      proof({requestId: 'req-ffffffffffffffff'}), proof({iat: now - 400}), proof({life: 3600}), proof({iat: now + 120}),
      proof({header: {jwk: {kty: 'EC'}}}), proof({header: {x5u: 'https://evil.example/'}}),
      'a.b', 'not-a-jwt', '', 'e30.e30.' + 'A'.repeat(10),
      b64url(JSON.stringify({alg: 'none'})) + '.' + proof().split('.')[1] + '.',
      b64url(JSON.stringify({alg: 'HS256'})) + '.' + proof().split('.')[1] + '.' + proof().split('.')[2],
    ];
    for (const p of bad) {
      const r = await f.register({proof: p});
      assert.deepEqual([r.status, r.body], [403, {error: 'device_proof_rejected'}], p.slice(0, 40));
    }
    assert.equal(f.outbound.length, 0);
    assert.equal(await f.device(DEV), null);
    assert.equal((await f.origins()).length, 0);
  } finally { await f.dispose(); }
});

test('a proof signed by any other key, or for another dongle, is refused after asking comma', async () => {
  const f = await fixture(candidate);
  try {
    const forged = await f.register({proof: proof({pair: attacker})});
    assert.deepEqual([forged.status, forged.body], [403, {error: 'device_proof_rejected'}]);
    assert.equal(f.outbound.length, 1);
    assert.equal(await f.device(DEV), null);
  } finally { await f.dispose(); }
  const g = await fixture(candidate, {comma: {[DEV]: {public_key: pem(ec), dongle_id: 'ffffffffffffffff'}}});
  try {
    const mismatch = await g.register();
    assert.deepEqual([mismatch.status, mismatch.body], [403, {error: 'device_proof_rejected'}]);
  } finally { await g.dispose(); }
});

test('comma refusing the JWT rejects; comma failing or redirecting is a retryable 503', async () => {
  for (const [status, expected] of [[401, 403], [403, 403], [404, 403], [500, 503], [302, 503]]) {
    const f = await fixture(candidate, {commaStatus: status});
    try {
      const r = await f.register();
      assert.equal(r.status, expected, String(status));
      assert.equal(await f.device(DEV), null);
      assert.ok(f.outbound.every(o => o.url.startsWith('https://api.commadotai.com/')), 'redirect not followed');
    } finally { await f.dispose(); }
  }
});

test('an existing device keeps the existing contract and needs no proof for a same-key retry', async () => {
  const f = await fixture(candidate);
  try {
    assert.equal((await f.register()).status, 200);
    const calls = f.outbound.length;
    const retry = await f.register({proof: 'garbage'});
    assert.deepEqual([retry.status, retry.body], [200, {ok: true, deviceId: DEV}]);
    const other = await f.register({key: OTHER_KEY, proof: proof({key: OTHER_KEY})});
    assert.deepEqual([other.status, other.body], [409, {error: 'device_already_registered'}]);
    assert.equal(f.outbound.length, calls, 'no comma call for an existing device');
    assert.equal((await f.device(DEV)).key_hash, hash(DEV_KEY));
    const owner = await f.call('/api/devices/self-register', {body: {deviceId: OWNER, key: DEV_KEY, requestId: 'req-0123456789abcdef', proof: proof({identity: OWNER})}});
    assert.deepEqual([owner.status, owner.body], [409, {error: 'device_already_registered'}]);
    await f.db.prepare('UPDATE wayon_devices SET revoked_at = ? WHERE device_id = ?').bind('now', DEV).run();
    assert.equal((await f.register({proof: 'garbage'})).status, 409);
  } finally { await f.dispose(); }
});

test('bad fields are 400 and a key already used by another device rolls back with 503', async () => {
  const f = await fixture(candidate);
  try {
    for (const fields of [{deviceId: 'UnregisteredDevice'}, {deviceId: 'A1B2C3D4E5F60718'}, {key: 'short'}, {requestId: 'x'}, {requestId: 5}]) {
      assert.equal((await f.register(fields)).status, 400, JSON.stringify(fields));
    }
    const dup = await f.register({key: OWNER_KEY, proof: proof({key: OWNER_KEY})});
    assert.equal(dup.status, 503);
    assert.equal(await f.device(DEV), null);
    assert.equal((await f.origins()).length, 0);
  } finally { await f.dispose(); }
});

test('two requests for one comma with different keys at once: one key wins, the other is told it exists', async () => {
  const f = await fixture(candidate);
  try {
    const results = await Promise.all([f.register(), f.register({key: OTHER_KEY, proof: proof({key: OTHER_KEY})})]);
    assert.deepEqual(results.map(r => r.status).sort(), [200, 409]);
    assert.equal((await f.origins()).length, 1);
  } finally { await f.dispose(); }
});

test('at most five commas register themselves (shared D1 budget); the sixth is told to wait', async () => {
  const ids = Array.from({length: 6}, (_, i) => 'a1b2c3d4e5f6071' + i);
  const f = await fixture(candidate, {comma: Object.fromEntries(ids.map(id => [id, {public_key: pem(ec)}]))});
  try {
    for (const id of ids.slice(0, 5)) {
      const key = 'wayon_' + id.repeat(4);
      assert.equal((await f.register({deviceId: id, key, proof: proof({identity: id, key})})).status, 200, id);
    }
    const key = 'wayon_' + ids[5].repeat(4);
    const sixth = await f.register({deviceId: ids[5], key, proof: proof({identity: ids[5], key})});
    assert.deepEqual([sixth.status, sixth.body], [429, {error: 'self_register_limit'}]);
    assert.equal(await f.device(ids[5]), null);
    await f.db.prepare('UPDATE wayon_device_origins SET invited_at = ?').bind(new Date(Date.now() - 2 * 864e5).toISOString()).run();
    assert.equal((await f.register({deviceId: ids[5], key, proof: proof({identity: ids[5], key})})).status, 429, 'the total still holds');
    await f.db.prepare('DELETE FROM wayon_device_origins WHERE device_id = ?').bind(ids[0]).run();
    assert.equal((await f.register({deviceId: ids[5], key, proof: proof({identity: ids[5], key})})).status, 200);
  } finally { await f.dispose(); }
});

test('owner responses are identical before and after the patch', async () => {
  const paths = ['/api/state', '/api/trips?limit=5', '/api/trips/' + OWNER + '-00000001', '/api/parking/latest'];
  const snapshot = async script => {
    const f = await fixture(script);
    try {
      const out = [];
      for (const path of paths) {
        const r = await f.call(path, {method: 'GET', key: OWNER_KEY});
        assert.equal(r.status, 200, path + ' ' + r.text.slice(0, 160));
        out.push([path, r.text.replace(/"(vehicleStatus":\{"ok":false,"source":"unavailable","updatedAt)":"[^"]*"/g, '"$1":"T"')]);
      }
      assert.match(out[0][1], /12\.34/);
      return out;
    } finally { await f.dispose(); }
  };
  assert.deepEqual(await snapshot(candidate), await snapshot(baseline));
});
