import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {builtinModules} from 'node:module';
import {fileURLToPath} from 'node:url';
import {build} from 'esbuild';
import {Miniflare} from 'miniflare';
import {COOKIE, digest, encrypt, decrypt} from '../server/security.mjs';
import {ACCOUNT_TTL_MS, COMMAND_SPECS} from '../server/commands.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const ORIGIN = 'https://command-runtime.test', DEVICE = 'RUNTIME_DEVICE';
const EMAIL = 'runtime@example.test', PASSWORD = 'RUNTIME_PASSWORD_NOT_REAL';
const TOKEN = 'r'.repeat(43), SECRET = 'RUNTIME_ENCRYPTION_KEY_NOT_REAL_0123456789';
const ID = '22222222-2222-4222-8222-222222222222';
const OWNER = {uuid: 'RUNTIME_OWNER_UUID', vehicleId: 'RUNTIME_VEHICLE_ID'};
const schema = readFileSync(new URL('../server/schema.sql', import.meta.url), 'utf8');
let mf, db, sessionId, storedCipher, protocol = [], markers = [], events = [];
let reply, markerReply, feedReply, cloudReply, feedReads = 0, wayonCalls = [], unexpected = [];

const loginReply = () => ({login: {success: '0', user_info_uuid: OWNER.uuid,
  token_key: 'RUNTIME_TOKEN_NOT_REAL', car_info: {[OWNER.vehicleId]: {}}}, body: {success: '0'}});
const statusReply = () => ({timestamp: String(Date.now()), body: {success: '0',
  car_status: {eng: 0, hood: 0, rvsRmng: 2, rvsRmngTmVld: false}}});
function feed() {
  const updatedAt = new Date(Date.now() - 300_000).toISOString();
  return {vehicleStatus:{stale:true,updatedAt:'2020-01-01T00:00:00Z'},vehicleLock:null,healthTimeline:[],
    state: {device_id: DEVICE, updated_at: updatedAt, onroad: 0, enabled: 0, speed_mps: 0,
    raw_json: JSON.stringify({schemaVersion: 'wayon-telemetry-v2', deviceId: DEVICE, updatedAt,
      onroad: false, enabled: false, vehicleSpeedMps: 0,
      vehicle: {available: false}, openpilot: {available: false}})}};
}

test.before(async () => {
  // Current source only; no generated bundle, production config, or real outbound transport.
  const builtins = new Set(builtinModules.map(name => name.replace(/^node:/, '')));
  const bundle = await build({
    entryPoints: [root + 'server/worker.mjs'], bundle: true, write: false, format: 'esm',
    platform: 'node', target: 'es2022', logLevel: 'silent',
    plugins: [{name: 'workerd-native-builtins', setup(builder) {
      builder.onResolve({filter: /.*/}, args => {
        if (!builtins.has(args.path.replace(/^node:/, ''))) return;
        if (args.namespace === 'workerd-builtin') return {path: args.path, external: true};
        return {path: args.path.replace(/^node:/, ''), namespace: 'workerd-builtin'};
      });
      builder.onLoad({filter: /.*/, namespace: 'workerd-builtin'}, args => ({
        contents: `import native from ${JSON.stringify(args.path === 'tty' ? 'unenv/node/tty' : 'node:' + args.path)}; module.exports = native;`,
        loader: 'js', resolveDir: root,
      }));
    }}],
  });
  sessionId = await digest(TOKEN);
  mf = new Miniflare({modules: true, script: bundle.outputFiles[0].text,
    compatibilityDate: '2025-10-01', compatibilityFlags: ['nodejs_compat'], d1Databases: ['DB'],
    bindings: {PUBLIC_ORIGIN: ORIGIN, COMMANDS_ENABLED: '1', DEVICE_ID: DEVICE,
      ACCOUNT_FINGERPRINT: await digest(EMAIL), GMONE_UUID_HASH: await digest(OWNER.uuid),
      GMONE_VEHICLE_HASH: await digest(OWNER.vehicleId), ACCOUNT_ENCRYPTION_KEY: SECRET,
      WAYON_DEVICE_KEY: 'RUNTIME_WAYON_KEY_NOT_REAL'},
    outboundService: async request => {
      const url = new URL(request.url);
      if (url.origin !== 'https://mp.gmone.co.kr:28354' || request.method !== 'POST' ||
          !['/b1_init', '/b1_connect_m'].includes(url.pathname)) {
        unexpected.push(url.origin); throw new Error('OUTBOUND_FORBIDDEN');
      }
      const p = await request.json(); protocol.push(p); events.push('gmone:' + p.header.id);
      assert.equal(url.pathname, p.header.id === 8 ? '/b1_init' : '/b1_connect_m');
      assert.ok([8, 21, 19, 66].includes(p.header.id));
      const response = await reply?.(p);
      if (response !== undefined) return response;
      if (p.header.id === 8) return Response.json(loginReply());
      if (p.header.id === 21) return Response.json(statusReply());
      assert.equal(p.header.id, 19, 'unexpected result poll');
      return Response.json({body: {success: '0', control_type: String(p.body.control_type),
        request_option: String(p.body.request_option)}});
    },
    serviceBindings: {ASSETS: () => new Response('fixture'), WAYON: async request => {
      const url = new URL(request.url);
      assert.equal(url.origin, 'https://wayon-cloud.hyuklee.workers.dev');
      assert.equal(request.headers.get('authorization'), 'Bearer RUNTIME_WAYON_KEY_NOT_REAL');
      wayonCalls.push(url.pathname + url.search);
      const custom=await cloudReply?.(url.pathname + url.search);
      if (custom !== undefined) return custom;
      if (url.pathname === '/api/state') {
        feedReads++;
        return await feedReply?.(feedReads) ?? Response.json(feed());
      }
      if (url.pathname === '/api/mobile/web-trips') {
        assert.equal(url.search, '?limit=25');
        return Response.json({trips:Array.from({length:25}, (_,i)=>({id:'trip-'+i,device_id:DEVICE}))});
      }
      if (url.pathname === '/api/mobile/web-snapshots') {
        assert.equal(url.search, '?limit=24');
        return Response.json({snapshots:Array.from({length:24}, (_,i)=>({id:'snapshot-'+i,device_id:DEVICE}))});
      }
      assert.equal(url.pathname, '/api/mobile/impact-suppression');
      const marker = await request.json(); markers.push(marker); events.push('marker:' + marker.action);
      assert.equal(marker.requestId, ID); assert.ok(['arm', 'cancel'].includes(marker.action));
      return await markerReply?.(marker) ?? Response.json({ok: true});
    }},
  });
  db = await mf.getD1Database('DB');
  await db.exec(schema.replaceAll('\n', ' '));
});

test.after(async () => { await mf?.dispose(); assert.deepEqual(unexpected, []); });

async function reset() {
  protocol = []; markers = []; events = []; reply = undefined; markerReply = undefined; feedReply = undefined;
  cloudReply = undefined; feedReads = 0; wayonCalls = [];
  await db.exec('DELETE FROM sessions; DELETE FROM rate_limits; DELETE FROM command_claims; UPDATE command_lock SET until_ms=0;');
  const now = Date.now();
  storedCipher = await encrypt({version: 1, ...OWNER, token: 'RUNTIME_TOKEN_NOT_REAL', vehicleCount: 1,
    issuedAtMs: now - 1000, expiresAtMs: now - 1000 + ACCOUNT_TTL_MS}, SECRET);
  await db.prepare('INSERT INTO sessions(id,csrf,expires,account,email) VALUES(?,?,?,?,?)')
    .bind(sessionId, 'runtime-csrf', now + 3_600_000, storedCipher, EMAIL).run();
}

async function call(path, body, extraHeaders = {}) {
  const response = await mf.dispatchFetch(ORIGIN + path, {method: body ? 'POST' : 'GET',
    headers: {cookie: `${COOKIE}=${TOKEN}`, origin: ORIGIN, 'sec-fetch-site': 'same-origin',
      'content-type': 'application/json', 'x-csrf-token': 'runtime-csrf', ...extraHeaders},
    ...(body ? {body: JSON.stringify(body)} : {})});
  return {status: response.status, body: await response.json()};
}
const command = cmd => call('/api/command', {command: cmd, requestId: ID, confirmed: true});
const ops = () => protocol.map(p => p.header.id);

test('workerd login uses native fetch with canonical integer fields and encrypted persistence', async () => {
  await reset();
  const result = await call('/api/account', {email: EMAIL, password: PASSWORD});
  assert.equal(result.status, 200); assert.equal(result.body.loggedIn, true); assert.deepEqual(ops(), [8]);
  assert.deepEqual(protocol[0].login, {email: EMAIL, password: PASSWORD});
  const row = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
  assert.notEqual(row.account, storedCipher); assert.equal((await decrypt(row.account, SECRET)).uuid, OWNER.uuid);
  const session = await call('/api/session');
  assert.equal(session.body.capabilities.commands, true);
  assert.equal(session.body.capabilities.supportedCommands.length, 15);
  assert.deepEqual(session.body.capabilities.supportedCommands.sort(), Object.keys(COMMAND_SPECS).sort());
});

test('workerd accepts Android pending envelopes only with a successful nested result', async () => {
  await reset(); let polls = 0;
  reply = async p => {
    if (p.header.id === 19) return Response.json({body: {wait_response: true, ticket_uuid: 'RUNTIME_TICKET'}});
    assert.equal(p.header.id, 66); assert.deepEqual(p.body, {ticket_uuid: 'RUNTIME_TICKET'});
    return Response.json(++polls === 1 ? {body: {}} : {body: {fetched_data: {
      body: {success: '0', control_type: '1', request_option: '0'}}}});
  };
  const result = await command('DOOR_LOCK');
  assert.equal(result.body.state, 'server_responded'); assert.equal(result.body.vehicleConfirmed, false);
  assert.deepEqual(ops(), [19, 66, 66]);
  assert.deepEqual(await command('DOOR_LOCK'), result); assert.deepEqual(ops(), [19, 66, 66]);
});

test('workerd rejects null authentication and missing nested success without retry', async t => {
  for (const invalid of [{login: null, body: {success: 0}}, {body: {}}]) await t.test(JSON.stringify(invalid), async () => {
    await reset();
    reply = async p => Response.json(p.header.id === 19
      ? {body: {wait_response: true, ticket_uuid: 'RUNTIME_TICKET'}} : {body: {fetched_data: invalid}});
    const result = await command('DOOR_LOCK');
    assert.equal(result.body.state, 'unknown'); assert.equal(result.body.dispatched, true);
    assert.deepEqual(ops(), [19, 66]);
    assert.deepEqual(await command('DOOR_LOCK'), result); assert.deepEqual(ops(), [19, 66]);
  });
});

test('workerd final logout guard cancels only its marker and keeps the saved blocked result', async t => {
  for (const cleanupFails of [false, true]) await t.test(String(cleanupFails), async () => {
    await reset();
    markerReply = async marker => {
      if (marker.action === 'arm') await db.prepare('DELETE FROM sessions WHERE id=?').bind(sessionId).run();
      else {
        const row = await db.prepare('SELECT result FROM command_claims WHERE id=?').bind(ID).first();
        assert.equal(JSON.parse(row.result).dispatched, false);
        if (cleanupFails) return new Response('PRIVATE_CLEANUP_FAILURE', {status: 503});
      }
    };
    const result = await command('VEHICLE_START');
    assert.equal(result.status, 200); assert.equal(result.body.state, 'blocked');
    assert.equal(result.body.dispatched, false); assert.equal(result.body.code, 'before_send_failed');
    assert.deepEqual(ops(), [21]);
    assert.deepEqual(markers, [{action: 'arm', requestId: ID}, {action: 'cancel', requestId: ID}]);
    assert.deepEqual(events, ['gmone:21', 'marker:arm', 'marker:cancel']);
    const row = await db.prepare('SELECT result FROM command_claims WHERE id=?').bind(ID).first();
    assert.deepEqual(JSON.parse(row.result), result.body);
  });
});

test('workerd accepted and unknown engine results never cancel or replay', async t => {
  for (const accepted of [true, false]) await t.test(String(accepted), async () => {
    await reset();
    reply = async p => { if (p.header.id === 19 && !accepted) return new Response('PRIVATE_FAILURE', {status: 503}); };
    const result = await command('VEHICLE_START');
    assert.equal(result.body.state, accepted ? 'server_responded' : 'unknown');
    assert.equal(result.body.dispatched, true); assert.deepEqual(ops(), [21, 19]);
    assert.deepEqual(markers, [{action: 'arm', requestId: ID}]);
    assert.deepEqual(events, ['gmone:21', 'marker:arm', 'gmone:19']);
    assert.deepEqual(await command('VEHICLE_START'), result); assert.deepEqual(ops(), [21, 19]);
  });
});

test('workerd original panic and sunroof mappings send exactly once through the real parent', async t => {
  for (const cmd of ['PANIC', 'SUNROOF_OPEN', 'SUNROOF_CLOSE', 'SUNROOF_TILT']) await t.test(cmd, async () => {
    await reset();
    const result = await command(cmd);
    assert.equal(result.body.state, 'server_responded'); assert.equal(result.body.vehicleConfirmed, false);
    assert.deepEqual(ops(), [19]); assert.deepEqual(protocol[0].body, COMMAND_SPECS[cmd]);
    assert.deepEqual(markers, []); assert.deepEqual(await command(cmd), result); assert.deepEqual(ops(), [19]);
  });
});

test('workerd account errors retain stable codes without raw upstream text or session changes', async t => {
  const cases = [
    ['login_rejected', 401, {login: null, body: {success: 0}}],
    ['invalid_login_response', 502, {login: {success: '0'}, body: {success: '0'}}],
    ['single_vehicle_required', 403, {login: {...loginReply().login, car_info: {}}, body: {success: '0'}}],
    ['upstream_http_error', 502, new Response(PASSWORD, {status: 503})],
    ['invalid_response', 502, new Response(PASSWORD)],
  ];
  for (const [code, status, response] of cases) await t.test(code, async () => {
    await reset(); reply = async () => response instanceof Response ? response : Response.json(response);
    const result = await call('/api/account', {email: EMAIL, password: PASSWORD});
    assert.equal(result.status, status); assert.equal(result.body.code, code); assert.equal(result.body.ok, false);
    assert.deepEqual(Object.keys(result.body).sort(), ['code', 'message', 'ok', 'state']);
    assert.ok(!JSON.stringify(result).includes(PASSWORD)); assert.deepEqual(ops(), [8]);
    const row = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
    assert.equal(row.account, storedCipher);
  });
});

test('workerd composes the UI feed from authenticated lightweight endpoints for each browser encoding', async t => {
  for (const encoding of ['identity', 'gzip', 'br', 'gzip, deflate, br, zstd']) await t.test(encoding, async () => {
    await reset();
    const result = await call('/api/wayon/json', undefined, {'accept-encoding': encoding});
    assert.equal(result.status, 200); assert.equal(result.body.state.device_id, DEVICE);
    assert.equal(feedReads, 1); assert.deepEqual(ops(), []);
    assert.deepEqual(wayonCalls.sort(), ['/api/mobile/web-snapshots?limit=24','/api/mobile/web-trips?limit=25','/api/state']);
    assert.equal(result.body.snapshots.length, 24); assert.equal(result.body.trips.length, 25);
    assert.equal(result.body.generatedAt, null); assert.equal(result.body.vehicleStatus.stale, true);
    assert.equal(result.body.vehicleStatus.updatedAt, '2020-01-01T00:00:00Z');
  });
});

test('workerd final feed is queried again and newly moving or failed reads block op19', async t => {
  for (const change of ['moving', 'wrong-device', 'http', 'valid']) await t.test(change, async () => {
    await reset();
    feedReply = async count => {
      if (count !== 2) return;
      if (change === 'http') return new Response('PRIVATE_UPSTREAM_FAILURE', {status: 503});
      const payload = feed();
      if (change === 'moving') payload.state.speed_mps = 2;
      if (change === 'wrong-device') payload.state.device_id = 'OTHER_DEVICE';
      return Response.json(payload);
    };
    const result = await command('VEHICLE_START');
    assert.equal(result.body.state, change === 'valid' ? 'server_responded' : 'blocked');
    assert.deepEqual(ops(), change === 'valid' ? [21, 19] : [21]); assert.equal(feedReads, 2);
    assert.deepEqual(markers.map(m => m.action), change === 'valid' ? ['arm'] : ['arm', 'cancel']);
  });
});

test('workerd explicit session expiry clears matching ciphertext without erasing a replacement', async t => {
  for (const replace of [false, true]) await t.test(String(replace), async () => {
    await reset(); let replacement;
    reply = async p => {
      assert.equal(p.header.id, 21);
      if (replace) {
        const current = await decrypt(storedCipher, SECRET);
        replacement = await encrypt(current, SECRET);
        await db.prepare('UPDATE sessions SET account=? WHERE id=?').bind(replacement, sessionId).run();
      }
      return Response.json({login: {success: 1}, body: {success: 0}});
    };
    const result = await command('VEHICLE_START');
    assert.equal(result.body.code, 'session_expired'); assert.equal(result.body.dispatched, false);
    const row = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
    assert.equal(row.account, replace ? replacement : null);
    assert.equal((await call('/api/session')).body.account.loggedIn, replace);
    assert.deepEqual(ops(), [21]); assert.deepEqual(markers, []);
  });
});

test('workerd unknown dispatch keeps the full cooldown and prevents a new request UUID', async () => {
  await reset();
  reply = async p => { assert.equal(p.header.id, 19); return new Response('PRIVATE', {status: 503}); };
  const result = await command('DOOR_LOCK');
  assert.equal(result.body.state, 'unknown'); assert.equal(result.body.dispatched, true);
  assert.equal(result.body.retryAfterMs, 180_000);
  const row = await db.prepare('SELECT until_ms FROM command_lock WHERE id=1').first();
  assert.equal(row.until_ms, result.body.cooldownUntilMs); assert.ok(row.until_ms > Date.now() + 170_000);
  const next = await call('/api/command', {command: 'DOOR_LOCK', confirmed: true, requestId: '33333333-3333-4333-8333-333333333333'});
  assert.equal(next.status, 429); assert.deepEqual(ops(), [19]);
});

test('workerd upstream HTTP errors become sanitized 502 instead of forwarding HTML or generic 400', async t => {
  for (const status of [400, 401, 403, 429, 503]) await t.test(String(status), async () => {
    await reset(); feedReply = async () => new Response('PRIVATE_UPSTREAM_BODY', {status});
    const result = await call('/api/wayon/state');
    assert.equal(result.status, 502); assert.equal(result.body.upstreamStatus, status);
    assert.equal(result.body.code, [401, 403].includes(status) ? 'upstream_auth' : 'upstream_http');
    assert.ok(!JSON.stringify(result).includes('PRIVATE_UPSTREAM_BODY')); assert.deepEqual(ops(), []);
  });
});

test('workerd composition preserves state byte-for-byte without synthetic freshness or history fallback', async () => {
  await reset();
  const original=feed(); original.state.updated_at='2020-01-01T00:00:00Z';
  original.state.raw_json='{"opaque":"unchanged","updatedAt":"2020-01-01T00:00:00Z"}';
  original.vehicleLock={stale:true}; original.healthTimeline=[{id:'original'}];
  original.snapshots=[{id:'must-not-use-12-row-state-gallery'}];
  feedReply=async()=>Response.json(original);
  const result=await call('/api/wayon/json');
  assert.equal(result.status,200); assert.deepEqual(result.body.state,original.state);
  assert.deepEqual(result.body.vehicleStatus,original.vehicleStatus);
  assert.deepEqual(result.body.vehicleLock,original.vehicleLock);
  assert.deepEqual(result.body.healthTimeline,original.healthTimeline);
  assert.equal(result.body.snapshots.length,24); assert.equal(result.body.snapshots[0].id,'snapshot-0');
  assert.equal(result.body.generatedAt,null); assert.deepEqual(ops(),[]);
});

test('workerd composition requires real state and explicitly marks unavailable optional history', async t => {
  const cases=[
    ['/api/state',{}],['/api/state',{...feed(),state:null}],
    ['/api/state',{...feed(),state:{device_id:'OTHER_DEVICE'}}],
    ['/api/state',{state:feed().state}],['/api/mobile/web-trips?limit=25',{}],
    ['/api/mobile/web-trips?limit=25',{trips:null}],['/api/mobile/web-snapshots?limit=24',{}],
    ['/api/mobile/web-snapshots?limit=24',{snapshots:null}],
  ];
  for (const path of ['/api/state','/api/mobile/web-trips?limit=25','/api/mobile/web-snapshots?limit=24']) {
    cases.push([path,new Response('PRIVATE_COMPONENT_FAILURE',{status:503})]);
    cases.push([path,new Response('PRIVATE_NON_JSON')]);
  }
  for (const [path,value] of cases) await t.test(path,async()=>{
    await reset(); cloudReply=async current=>current===path
      ? value instanceof Response ? value : Response.json(value) : undefined;
    const result=await call('/api/wayon/json');
    if (path === '/api/state') {
      assert.equal(result.status,502); assert.equal(result.body.ok,false);
      assert.ok(['upstream_http','upstream_response'].includes(result.body.code));
      assert.equal(result.body.state,undefined);
    } else {
      const key=path.startsWith('/api/mobile/web-trips') ? 'trips' : 'snapshots';
      assert.equal(result.status,200); assert.equal(result.body.state.device_id,DEVICE);
      assert.equal(result.body[key],null);
      assert.ok(['upstream_http','upstream_response'].includes(result.body.historyErrors[key].code));
      assert.equal(result.body.historyErrors[key].ok,false);
    }
    assert.ok(!JSON.stringify(result).includes('PRIVATE_'));
    assert.ok(!wayonCalls.includes('/api/json')); assert.deepEqual(ops(),[]);
  });
});

test('workerd optional history failures never fabricate empty history or replace actual vehicle freshness',async()=>{
  await reset(); const original=feed();
  feedReply=async()=>Response.json(original);
  cloudReply=async path=>path.startsWith('/api/mobile/web-trips') || path.startsWith('/api/mobile/web-snapshots')
    ? new Response('PRIVATE_HISTORY_FAILURE',{status:503}) : undefined;
  const result=await call('/api/wayon/json');
  assert.equal(result.status,200); assert.deepEqual(result.body.state,original.state);
  assert.deepEqual(result.body.vehicleStatus,original.vehicleStatus);
  assert.equal(result.body.trips,null); assert.equal(result.body.snapshots,null);
  assert.deepEqual(Object.keys(result.body.historyErrors).sort(),['snapshots','trips']);
  assert.equal(result.body.historyErrors.trips.upstreamStatus,503);
  assert.equal(result.body.historyErrors.snapshots.upstreamStatus,503);
  assert.deepEqual(ops(),[]);
});

test('workerd maps only trip lists to web-trips, retaining allowed query parameters and fixed service origin',async()=>{
  await reset();
  cloudReply=async path=>path.startsWith('/api/mobile/web-trips') ? Response.json({trips:[]}) : undefined;
  const result=await call('/api/wayon/trips?limit=1000&offset=7&cursor=next&before=old&url=https://untrusted.invalid/&origin=https://untrusted.invalid/&secret=hidden');
  assert.equal(result.status,200); assert.deepEqual(result.body,{trips:[]});
  assert.deepEqual(wayonCalls,['/api/mobile/web-trips?limit=1000&offset=7&cursor=next&before=old']);
  assert.deepEqual(ops(),[]);
  assert.equal((await call('/api/wayon/mobile/web-trips')).status,403);
  assert.equal((await call('/api/wayon/trips',{operation:'write'})).status,403);
  assert.equal(wayonCalls.length,1);
});

test('workerd keeps existing trip detail paths unchanged rather than routing them to the compact list',async()=>{
  await reset();
  cloudReply=async path=>path==='/api/trips/trip-0?limit=3' ? Response.json({id:'trip-0',route:[]}) : undefined;
  const result=await call('/api/wayon/trips/trip-0?limit=3&url=https://untrusted.invalid/');
  assert.equal(result.status,200); assert.deepEqual(result.body,{id:'trip-0',route:[]});
  assert.deepEqual(wayonCalls,['/api/trips/trip-0?limit=3']); assert.deepEqual(ops(),[]);
});

async function rememberAccount(overrides = {}) {
  const now = Date.now();
  const cipher = await encrypt({version: 1, ...OWNER, token: 'RUNTIME_OLD_TOKEN_NOT_REAL', vehicleCount: 1,
    issuedAtMs: now - ACCOUNT_TTL_MS - 60_000, expiresAtMs: now - 60_000,
    renew: {email: EMAIL, password: PASSWORD}, ...overrides}, SECRET);
  await db.prepare('UPDATE sessions SET account=? WHERE id=?').bind(cipher, sessionId).run();
  return cipher;
}

test('workerd remembers the multipack login on this session and keeps controls available after token expiry', async () => {
  await reset();
  const login = await call('/api/account', {email: EMAIL, password: PASSWORD});
  assert.equal(login.body.loggedIn, true);
  const row = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
  const stored = await decrypt(row.account, SECRET);
  assert.deepEqual(stored.renew, {email: EMAIL, password: PASSWORD}, 'credentials stay inside the encrypted row');
  assert.ok(!JSON.stringify(login.body).includes(PASSWORD), 'never returned to the browser');
  await rememberAccount();
  const session = await call('/api/session');
  assert.equal(session.body.account.loggedIn, true);
  assert.equal(session.body.capabilities.commands, true);
  assert.ok(!JSON.stringify(session.body).includes(PASSWORD));
});

test('workerd logs a remembered account in again before the command and swaps only its own row', async () => {
  await reset();
  const old = await rememberAccount();
  const result = await command('DOOR_LOCK');
  assert.equal(result.body.ok, true, JSON.stringify(result.body));
  assert.deepEqual(ops().slice(0, 1), [8], 'fresh login first');
  assert.ok(ops().includes(19));
  assert.equal(protocol.find(p => p.header.id === 19).login.token_key, 'RUNTIME_TOKEN_NOT_REAL', 'command uses the fresh token');
  const row = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
  assert.notEqual(row.account, old);
  const stored = await decrypt(row.account, SECRET);
  assert.equal(stored.token, 'RUNTIME_TOKEN_NOT_REAL');
  assert.deepEqual(stored.renew, {email: EMAIL, password: PASSWORD});
});

test('workerd rejected remembered password clears the login without sending the command', async () => {
  await reset();
  await rememberAccount();
  reply = async p => p.header.id === 8 ? Response.json({login: {success: '1'}, body: {success: '1'}}) : undefined;
  const result = await command('DOOR_LOCK');
  assert.equal(result.body.code, 'account_login_rejected');
  assert.equal(result.body.dispatched, false);
  assert.deepEqual(ops(), [8], 'no command after a rejected login');
  const row = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
  assert.equal(row.account, null);
  assert.equal((await call('/api/session')).body.account.loggedIn, false);
});

test('workerd transport failure while renewing keeps the remembered login and sends nothing', async () => {
  await reset();
  const old = await rememberAccount();
  reply = async p => p.header.id === 8 ? new Response('down', {status: 503}) : undefined;
  const result = await command('DOOR_LOCK');
  assert.equal(result.body.code, 'account_refresh_failed');
  assert.equal(result.body.dispatched, false);
  assert.deepEqual(ops(), [8]);
  const row = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
  assert.equal(row.account, old);
  assert.equal((await call('/api/session')).body.account.loggedIn, true);
});

test('workerd malformed renewal reply keeps the remembered login and sends nothing', async () => {
  await reset();
  const old = await rememberAccount();
  reply = async p => p.header.id === 8 ? Response.json({}) : undefined;
  const result = await command('DOOR_LOCK');
  assert.equal(result.body.code, 'account_refresh_failed');
  assert.deepEqual(ops(), [8]);
  const row = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
  assert.equal(row.account, old, 'a damaged reply is not a password refusal');
});

test('workerd account sign-out during an in-flight login wins; the late login is not stored', async () => {
  await reset();
  await db.prepare('UPDATE sessions SET account=NULL,email=NULL WHERE id=?').bind(sessionId).run();
  reply = async p => {
    if (p.header.id !== 8) return undefined;
    const out = await mf.dispatchFetch(ORIGIN + '/api/account', {method: 'DELETE',
      headers: {cookie: `${COOKIE}=${TOKEN}`, origin: ORIGIN, 'sec-fetch-site': 'same-origin', 'x-csrf-token': 'runtime-csrf'}});
    assert.equal(out.status, 200); await out.json();
    return Response.json(loginReply());
  };
  const result = await call('/api/account', {email: EMAIL, password: PASSWORD});
  assert.equal(result.status, 409);
  assert.equal(result.body.code, 'account_changed');
  const row = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
  assert.equal(row.account, null);
});

test('workerd clears multipack logins of expired web sessions on the next session check', async () => {
  await reset();
  const expiredId = await digest('e'.repeat(43));
  const cipher = await encrypt({version: 1, ...OWNER, token: 'RUNTIME_TOKEN_NOT_REAL', vehicleCount: 1,
    issuedAtMs: Date.now() - 1000, expiresAtMs: Date.now() + 60_000, renew: {email: EMAIL, password: PASSWORD}}, SECRET);
  await db.prepare('INSERT INTO sessions(id,csrf,expires,account,email) VALUES(?,?,?,?,?)')
    .bind(expiredId, 'expired-csrf', Date.now() - 1, cipher, EMAIL).run();
  assert.equal((await call('/api/session')).body.authenticated, true);
  const expired = await db.prepare('SELECT account,email FROM sessions WHERE id=?').bind(expiredId).first();
  assert.equal(expired.account, null); assert.equal(expired.email, null);
  const live = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
  assert.equal(live.account, storedCipher, 'valid sessions are untouched');
});

test('workerd daily scheduled cleanup clears expired multipack logins without any request', async () => {
  await reset();
  const expiredId = await digest('s'.repeat(43));
  const cipher = await encrypt({version: 1, ...OWNER, token: 'RUNTIME_TOKEN_NOT_REAL', vehicleCount: 1,
    issuedAtMs: Date.now() - 1000, expiresAtMs: Date.now() + 60_000, renew: {email: EMAIL, password: PASSWORD}}, SECRET);
  await db.prepare('INSERT INTO sessions(id,csrf,expires,account,email) VALUES(?,?,?,?,?)')
    .bind(expiredId, 'expired-csrf', Date.now() - 1, cipher, EMAIL).run();
  const worker = await mf.getWorker();
  await worker.scheduled({cron: '23 18 * * *', scheduledTime: new Date()});
  const expired = await db.prepare('SELECT account,email FROM sessions WHERE id=?').bind(expiredId).first();
  assert.equal(expired.account, null); assert.equal(expired.email, null);
  const live = await db.prepare('SELECT account FROM sessions WHERE id=?').bind(sessionId).first();
  assert.equal(live.account, storedCipher);
});
