import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';
import {test} from 'node:test';
import {patch, unpatch, BASELINE_SHA256, OUTPUT_SHA256} from './patch.mjs';
import {sha256} from '../fast-vehicle-state-20261028/patch.mjs';

// Private copies of the active production modules (downloaded read-only); not committed.
const root = process.env.WAYON_ACTIVE_MODULE_DIR || '/Users/hyuklee/Documents/my-traverse-web-20261110/device-invite';
const require = createRequire(import.meta.url);
const {Miniflare} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/Documents/sunnypilot/apps/my-traverse-web/node_modules/miniflare');
const baseline = readFileSync(join(root, 'stage-baseline-worker.js'), 'utf8');
const candidate = patch(baseline);
const OWNER_KEY = 'wayon_' + 'a'.repeat(48), OWNER = '3e07889d79b48064';
const NEW_KEY = 'wayon_' + 'n'.repeat(64), NEW = 'a1b2c3d4e5f60718';
const OTHER_KEY = 'wayon_' + 'o'.repeat(64), OTHER = 'b1b2c3d4e5f60718';
const hash = value => createHash('sha256').update(value).digest('hex');

test('patch is byte-exact and reversible', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  if (OUTPUT_SHA256 !== 'PENDING') assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
});

async function fixture(script, {migrated = true, legacy = 'fixture-legacy'} = {}) {
  const modules = [{type: 'ESModule', path: '/isolated/worker.js', contents: script}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type: 'ESModule', path: '/isolated/' + name, contents: readFileSync(join(root, 'stage-baseline-' + name), 'utf8')});
  }
  const logs = [];
  const mf = new Miniflare({modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14',
    d1Databases: {DB: 'device-invite-isolated-' + Math.random().toString(36).slice(2)}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {WAYON_UPLOAD_TOKEN: legacy, WAYON_SERVER_SYNC_TOKEN: 'fixture-sync', WAYON_VIEW_TOKEN: 'fixture-view',
      WAYON_AI_READ_TOKEN: 'fixture-ai', WAYON_AI_DEVICE_ID: OWNER, WAYON_GMONE_TOKEN: 'fixture-gmone',
      WAYON_PARKING_NOTIFY_TOKEN: 'fixture-notify'},
    serviceBindings: {ASSETS: () => new Response(null, {status: 404}),
      WAYON_SERVER_API: () => new Response('down', {status: 503})},
    outboundService: () => new Response(null, {status: 599}),
    handleRuntimeStdio(stdout, stderr) { for (const s of [stdout, stderr]) s.on('data', d => logs.push(String(d))); }});
  const db = await mf.getD1Database('DB');
  await db.exec('CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY, key_hash TEXT NOT NULL, created_at TEXT, updated_at TEXT, last_seen_at TEXT, revoked_at TEXT);');
  await db.prepare('INSERT INTO wayon_devices VALUES(?,?,?,?,?,NULL)').bind(OWNER, hash(OWNER_KEY), 'c', 'u', 'unchanged').run();
  await db.exec('CREATE TABLE trips(id TEXT PRIMARY KEY, device_id TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT NOT NULL, ' +
    'duration_s INTEGER, distance_m REAL, start_lat REAL, start_lon REAL, end_lat REAL, end_lon REAL, ' +
    'route_point_count INTEGER NOT NULL DEFAULT 0, route_json TEXT NOT NULL, source TEXT, route_name TEXT, segment_count INTEGER, ' +
    "avg_speed_mps REAL, max_speed_mps REAL, analysis_json TEXT NOT NULL DEFAULT '{}', report_json TEXT, " +
    "health_json TEXT NOT NULL DEFAULT '{}', health_updated_at TEXT, created_at TEXT NOT NULL, speed_stats INTEGER);");
  await db.prepare('INSERT INTO trips(id,device_id,started_at,ended_at,duration_s,distance_m,route_point_count,route_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)')
    .bind(OWNER + '-00000001', OWNER, '2026-11-09T01:00:00Z', '2026-11-09T01:10:00Z', 600, 3000, 0, '[]', '2026-11-09T01:10:00Z').run();
  if (migrated) await db.exec(readFileSync(new URL('./migration.sql', import.meta.url), 'utf8').replace(/--.*\n/g, '').replace(/\n/g, ' '));
  const call = async (path, {method = 'POST', key, body} = {}) => {
    const r = await mf.dispatchFetch('https://isolated.test' + path, {method,
      headers: {...(key ? {authorization: 'Bearer ' + key} : {}), ...(body ? {'content-type': 'application/json'} : {})},
      ...(body ? {body: JSON.stringify(body)} : {})});
    const text = await r.text();
    let json = null; try { json = JSON.parse(text); } catch {}
    return {status: r.status, body: json, text};
  };
  const invite = async (key = OWNER_KEY) => call('/api/devices/invites', {key});
  const register = (deviceId, key, code) => call('/api/devices/register', {body: {deviceId, key, ...(code === undefined ? {} : {invite: code})}});
  const device = id => db.prepare('SELECT device_id, key_hash, revoked_at FROM wayon_devices WHERE device_id = ?').bind(id).first();
  const invites = () => db.prepare('SELECT * FROM wayon_device_invites ORDER BY created_at').all().then(r => r.results);
  return {mf, db, call, invite, register, device, invites, logs, dispose: () => mf.dispose()};
}

test('an owner invite registers exactly one new comma, stores only hashes and never logs the code', async () => {
  const f = await fixture(candidate);
  try {
    const made = await f.invite();
    assert.equal(made.status, 200);
    assert.match(made.body.code, /^[A-Z2-7]{32}$/);
    const ttl = Date.parse(made.body.expiresAt) - Date.now();
    assert.ok(ttl > 29 * 60e3 && ttl <= 30 * 60e3, String(ttl));
    const stored = await f.invites();
    assert.equal(stored.length, 1);
    assert.equal(stored[0].code_hash, hash(made.body.code));
    assert.equal(stored[0].created_by, OWNER);
    assert.ok(!JSON.stringify(stored).includes(made.body.code));

    const done = await f.register(NEW, NEW_KEY, made.body.code);
    assert.deepEqual([done.status, done.body], [200, {ok: true, deviceId: NEW}]);
    assert.equal((await f.device(NEW)).key_hash, hash(NEW_KEY));
    const used = (await f.invites())[0];
    assert.equal(used.used_by, NEW);
    assert.equal(used.used_key_hash, hash(NEW_KEY));

    // The same code cannot register a second comma.
    const again = await f.register(OTHER, OTHER_KEY, made.body.code);
    assert.deepEqual([again.status, again.body], [403, {error: 'invalid_device_invite'}]);
    assert.equal(await f.device(OTHER), null);

    // A retry by the comma that already registered (lost response) takes the same-key path.
    const retry = await f.register(NEW, NEW_KEY, made.body.code);
    assert.deepEqual([retry.status, retry.body], [200, {ok: true, deviceId: NEW}]);

    // The new key works and sees only its own (empty) data, not the owner's trips.
    const trips = await f.call('/api/trips?limit=5', {method: 'GET', key: NEW_KEY});
    assert.equal(trips.status, 200);
    assert.ok(!trips.text.includes(OWNER + '-00000001'), trips.text.slice(0, 200));
    const ownerTrips = await f.call('/api/trips?limit=5', {method: 'GET', key: OWNER_KEY});
    assert.ok(ownerTrips.text.includes(OWNER + '-00000001'));
    await new Promise(r => setTimeout(r, 200));
    const logText = f.logs.join('');
    assert.ok(!logText.includes(made.body.code) && !logText.includes(NEW_KEY));
  } finally { await f.dispose(); }
});

test('wrong, malformed, expired and missing invites are refused without side effects', async () => {
  const f = await fixture(candidate);
  try {
    const made = await f.invite();
    for (const code of ['A'.repeat(32), made.body.code.toLowerCase(), made.body.code + 'A', '', 12, null, {}]) {
      const r = await f.register(NEW, NEW_KEY, code);
      assert.deepEqual([r.status, r.body], [403, {error: 'invalid_device_invite'}], JSON.stringify(code));
    }
    // No invite field and no legacy token: unchanged provisioning refusal.
    const none = await f.register(NEW, NEW_KEY);
    assert.deepEqual([none.status, none.body], [403, {error: 'device_provisioning_required'}]);
    assert.equal(await f.device(NEW), null);
    assert.equal((await f.invites())[0].used_at, null);

    await f.db.prepare('UPDATE wayon_device_invites SET expires_at = ?').bind(new Date(Date.now() - 1000).toISOString()).run();
    const expired = await f.register(NEW, NEW_KEY, made.body.code);
    assert.deepEqual([expired.status, expired.body], [403, {error: 'invalid_device_invite'}]);
    assert.equal(await f.device(NEW), null);
  } finally { await f.dispose(); }
});

test('an existing device ID is refused and the invite stays unused', async () => {
  const f = await fixture(candidate);
  try {
    const made = await f.invite();
    const taken = await f.register(OWNER, NEW_KEY, made.body.code);
    assert.deepEqual([taken.status, taken.body], [409, {error: 'device_already_registered'}]);
    assert.equal((await f.device(OWNER)).key_hash, hash(OWNER_KEY));
    assert.equal((await f.invites())[0].used_at, null);
    const ok = await f.register(NEW, NEW_KEY, made.body.code);
    assert.equal(ok.status, 200);
  } finally { await f.dispose(); }
});

test('two commas racing for one invite: exactly one is registered', async () => {
  const f = await fixture(candidate);
  try {
    const made = await f.invite();
    const results = await Promise.all([f.register(NEW, NEW_KEY, made.body.code), f.register(OTHER, OTHER_KEY, made.body.code)]);
    assert.deepEqual(results.map(r => r.status).sort(), [200, 403]);
    const registered = [await f.device(NEW), await f.device(OTHER)].filter(Boolean);
    assert.equal(registered.length, 1);
  } finally { await f.dispose(); }
});

test('only authenticated, non-invited devices create invites, within the active and daily limits', async () => {
  const f = await fixture(candidate);
  try {
    for (const key of [null, 'wrong', 'wayon_' + 'z'.repeat(48), 'fixture-legacy', 'fixture-view']) {
      const r = await f.call('/api/devices/invites', {key: key || undefined});
      assert.equal(r.status, 401, String(key));
    }
    assert.equal((await f.invites()).length, 0);
    // Concurrent requests cannot pass the active limit together.
    const burst = await Promise.all(Array.from({length: 8}, () => f.invite()));
    assert.equal(burst.filter(r => r.status === 200).length, 3);
    assert.ok(burst.filter(r => r.status !== 200).every(r => r.status === 429 && r.body.error === 'invite_limit'));
    const codes = burst.filter(r => r.status === 200).map(r => r.body.code);
    assert.equal((await f.register(NEW, NEW_KEY, codes[0])).status, 200);
    assert.equal((await f.invite()).status, 200);
    // The invited comma cannot invite others, even after its invite rows are cleaned up.
    const chained = await f.invite(NEW_KEY);
    assert.deepEqual([chained.status, chained.body], [403, {error: 'invite_not_allowed'}]);
    await f.db.prepare('DELETE FROM wayon_device_invites WHERE used_by = ?').bind(NEW).run();
    assert.equal((await f.invite(NEW_KEY)).status, 403);
    assert.equal((await f.register(NEW, NEW_KEY, codes[0])).status, 200, 'same-key retry survives the cleanup');
    // Expired codes stop counting as active, but at most ten are created a day.
    let refused = null;
    for (let i = 0; i < 20 && !refused; i += 1) {
      await f.db.prepare('UPDATE wayon_device_invites SET expires_at = ? WHERE used_at IS NULL').bind(new Date(Date.now() - 1000).toISOString()).run();
      const r = await f.invite();
      if (r.status !== 200) refused = r;
    }
    assert.deepEqual([refused?.status, refused?.body], [429, {error: 'invite_limit'}]);
    const today = (await f.db.prepare('SELECT COUNT(*) AS n FROM wayon_device_invites WHERE created_by = ?').bind(OWNER).first()).n;
    assert.equal(today, 10);
    // A revoked owner key cannot invite.
    await f.db.prepare('UPDATE wayon_devices SET revoked_at = ? WHERE device_id = ?').bind('now', OWNER).run();
    assert.equal((await f.invite()).status, 401);
  } finally { await f.dispose(); }
});

test('a code from a creator revoked after making it no longer registers anything', async () => {
  const f = await fixture(candidate);
  try {
    const made = await f.invite();
    await f.db.prepare('UPDATE wayon_devices SET revoked_at = ? WHERE device_id = ?').bind('now', OWNER).run();
    const r = await f.register(NEW, NEW_KEY, made.body.code);
    assert.deepEqual([r.status, r.body], [403, {error: 'invalid_device_invite'}]);
    assert.equal(await f.device(NEW), null);
    assert.equal((await f.invites())[0].used_at, null);
    assert.equal((await f.db.prepare('SELECT COUNT(*) AS n FROM wayon_device_origins').first()).n, 0);
  } finally { await f.dispose(); }
});

test('a registration records the origin once and refused ones record nothing', async () => {
  const f = await fixture(candidate);
  try {
    const made = await f.invite();
    assert.equal((await f.register(OWNER, NEW_KEY, made.body.code)).status, 409);
    assert.equal((await f.register(NEW, NEW_KEY, 'A'.repeat(32))).status, 403);
    assert.equal((await f.db.prepare('SELECT COUNT(*) AS n FROM wayon_device_origins').first()).n, 0);
    assert.equal((await f.register(NEW, NEW_KEY, made.body.code)).status, 200);
    assert.equal((await f.register(NEW, NEW_KEY, made.body.code)).status, 200);
    const origins = (await f.db.prepare('SELECT * FROM wayon_device_origins').all()).results;
    assert.equal(origins.length, 1);
    assert.equal(origins[0].device_id, NEW);
    assert.equal(origins[0].invited_by, OWNER);
  } finally { await f.dispose(); }
});

test('same device ID with two keys and two codes at once: one key wins and the other code stays usable', async () => {
  const f = await fixture(candidate);
  try {
    const a = (await f.invite()).body.code, b = (await f.invite()).body.code;
    const results = await Promise.all([f.register(NEW, NEW_KEY, a), f.register(NEW, OTHER_KEY, b)]);
    const statuses = results.map(r => r.status).sort();
    assert.equal(statuses[0], 200);
    assert.ok([403, 409].includes(statuses[1]), String(statuses));
    const winner = await f.device(NEW);
    assert.ok([hash(NEW_KEY), hash(OTHER_KEY)].includes(winner.key_hash));
    const used = (await f.invites()).filter(r => r.used_at !== null);
    assert.equal(used.length, 1);
    const leftover = winner.key_hash === hash(NEW_KEY) ? b : a;
    assert.equal((await f.register(OTHER, OTHER_KEY, leftover)).status, 200);
  } finally { await f.dispose(); }
});

test('legacy provisioning and same-key re-registration behave exactly as before', async () => {
  for (const script of [baseline, candidate]) {
    const f = await fixture(script);
    try {
      const legacy = await f.call('/api/devices/register', {key: 'fixture-legacy', body: {deviceId: NEW, key: NEW_KEY}});
      assert.deepEqual([legacy.status, legacy.body], [200, {ok: true, deviceId: NEW}]);
      const same = await f.register(OWNER, OWNER_KEY);
      assert.deepEqual([same.status, same.body], [200, {ok: true, deviceId: OWNER}]);
      const other = await f.register(OWNER, NEW_KEY);
      assert.deepEqual([other.status, other.body], [409, {error: 'device_already_registered'}]);
    } finally { await f.dispose(); }
  }
});

test('owner responses are identical before and after the patch, and the migration alone changes nothing', async () => {
  const paths = ['/api/state', '/api/trips?limit=5', '/api/trips/' + OWNER + '-00000001', '/api/parking/latest'];
  const snapshot = async (script, migrated) => {
    const f = await fixture(script, {migrated});
    try {
      const out = [];
      for (const path of paths) {
        const r = await f.call(path, {method: 'GET', key: OWNER_KEY});
        out.push([path, r.status, r.text.replace(/"(generatedAt|serverTime|now|checkedAt)":"[^"]*"/g, '"$1":"T"')]);
      }
      return out;
    } finally { await f.dispose(); }
  };
  const before = await snapshot(baseline, false);
  assert.deepEqual(await snapshot(baseline, true), before);
  assert.deepEqual(await snapshot(candidate, true), before);
});

test('without the migration the invite endpoints fail closed and registration stays refused', async () => {
  const f = await fixture(candidate, {migrated: false});
  try {
    const made = await f.invite();
    assert.deepEqual([made.status, made.body], [503, {error: 'invite_unavailable'}]);
    const r = await f.register(NEW, NEW_KEY, 'A'.repeat(32));
    assert.equal(r.status, 503);
    assert.equal(await f.device(NEW), null);
  } finally { await f.dispose(); }
});
