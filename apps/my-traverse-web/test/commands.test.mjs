import {test, after} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {
  ACCOUNT_TTL_MS, CLOUD_FRESHNESS_MS, COMMAND_SPECS, CommandError,
  accountLogin, executeCommand, validateCommandGuard,
} from "../server/commands.mjs";

// No test may escape to the network, even if an injection is accidentally omitted.
const originalFetch = globalThis.fetch;
let networkAttempts = 0;
globalThis.fetch = () => { networkAttempts++; throw new Error("NETWORK FORBIDDEN IN UNIT TESTS"); };
after(() => { globalThis.fetch = originalFetch; assert.equal(networkAttempts, 0); });

const NOW = 1_800_000_000_000;
const ACCOUNT = Object.freeze({version: 1, uuid: "TEST_USER", token: "TEST_TOKEN_NOT_REAL",
  vehicleId: "TEST_VEHICLE", vehicleCount: 1, issuedAtMs: NOW - 1000, expiresAtMs: NOW + ACCOUNT_TTL_MS - 1000});
const RAW = Object.freeze({eng: 0, hood: 0, rvsRmng: 2, rvsRmngTmVld: false});
function parked(now = NOW) {
  const updatedAt = new Date(now).toISOString();
  return {generatedAt: new Date(NOW).toISOString(), state: {
    device_id: "TEST_DEVICE", updated_at: updatedAt, onroad: 1, enabled: 0, speed_mps: 0,
    raw_json: JSON.stringify({schemaVersion: "wayon-telemetry-v2", deviceId: "TEST_DEVICE", updatedAt,
      onroad: true, enabled: false, vehicleSpeedMps: 0, vehicleSpeedSource: "vEgoCluster",
      vehicle: {available: true, speedMps: 0, rawSpeedMps: 0, speedSource: "vEgoCluster", standstill: true,
        gear: "park", can: {valid: true, timeout: false}}, openpilot: {available: true, enabled: false, active: false}}),
  }, vehicleStatus: {ok: true, stale: false, data: {gmone_details: {rawStatus: RAW}}}};
}
function mutateRaw(feed, mutate) {
  const raw = JSON.parse(feed.state.raw_json);
  mutate(raw); feed.state.raw_json = JSON.stringify(raw); return feed;
}
function offroad(now = NOW) {
  const feed = parked(now);
  feed.state.onroad = 0;
  return mutateRaw(feed, raw => {
    raw.onroad = false; raw.vehicleSpeedSource = "offroad";
    raw.vehicle = {available: false, reason: "offroad"};
    raw.openpilot = {available: false};
  });
}
const observation = (raw = RAW, now = NOW) => ({source: "gmone-direct", accountUuid: ACCOUNT.uuid,
  requestedAtMs: now, receivedAtMs: now, serverResponseAtMs: now, rawStatus: {...raw}});
const status = (raw = RAW, timestamp = NOW / 1000) => ({timestamp, body: {success: 0, car_status: {...raw}}});
const pending = (ticket = "TEST_TICKET") => ({body: {success: 13, wait_response: true, ticket_uuid: ticket}});
const fetched = data => ({body: {success: 0, fetched_data: data}});
const commandSuccess = command => ({body: {success: 0, ...COMMAND_SPECS[command]}});
const loginReply = () => ({login: {success: 0, user_info_uuid: "TEST_USER", token_key: "TEST_TOKEN_NOT_REAL",
  car_info: {TEST_VEHICLE: {}}, ignoredSecret: "DO_NOT_RETURN"}, body: {success: 0}});

function fixture(handler = p => p.header.id === 21 ? status() : commandSuccess("DOOR_LOCK")) {
  let now = NOW;
  const calls = [], waits = [];
  const request = async (url, options) => {
    const payload = JSON.parse(options.body);
    calls.push(payload);
    assert.equal(url, `https://mp.gmone.co.kr:28354/${payload.header.id === 8 ? "b1_init" : "b1_connect_m"}`);
    assert.equal(options.method, "POST"); assert.equal(options.redirect, "manual");
    assert.equal(options.cache, "no-store"); assert.equal(options.credentials, "omit");
    assert.equal(options.headers["content-type"], "application/json");
    assert.ok(options.signal instanceof AbortSignal);
    assert.equal(payload.header.revision, 0);
    assert.equal(payload.header.ticket_id, calls.length - 1);
    if (payload.header.id !== 8) assert.deepEqual(payload.login, {uuid: ACCOUNT.uuid, token_key: ACCOUNT.token});
    const result = await handler(payload, calls.length, options);
    return result instanceof Response ? result : Response.json(result);
  };
  return {request, calls, waits, advance: ms => { now += ms; }, now: () => now,
    input: (command = "DOOR_LOCK", overrides = {}) => ({command, account: ACCOUNT, liveState: parked(), now: () => now,
      sleep: async ms => { waits.push(ms); now += ms; }, ...overrides})};
}
const ops = f => f.calls.map(p => p.header.id);
const assertBlocked = (result, code) => {
  assert.equal(result.state, "blocked"); assert.equal(result.dispatched, false);
  assert.equal(result.ok, false); assert.equal(typeof result.message, "string");
  assert.equal(result.vehicleConfirmed, false); assert.equal(result.retryable, false);
  if (code) assert.equal(result.code, code);
};
const assertUnknown = (result, f, code) => {
  assert.equal(result.state, "unknown"); assert.equal(result.dispatched, true);
  assert.equal(result.ok, false); assert.equal(typeof result.message, "string");
  assert.equal(result.vehicleConfirmed, false); assert.equal(result.retryable, false);
  assert.equal(f.calls.filter(p => p.header.id === 19).length, 1);
  assert.ok(!ops(f).includes(8));
  if (code) assert.equal(result.code, code);
  for (const secret of [ACCOUNT.token, ACCOUNT.uuid, "LEAK_FROM_UPSTREAM", "TEST_TICKET"]) {
    assert.ok(!JSON.stringify(result).includes(secret));
  }
};

test("explicit, immutable PWA subset matches the tracked Android protocol", async () => {
  const expected = {DOOR_LOCK: [1, 0], DOOR_UNLOCK: [1, 1], DRIVER_DOOR_UNLOCK: [1, 2],
    VEHICLE_START: [0, 2], VEHICLE_STOP: [0, 0], WINDOW_OPEN: [5, 1], WINDOW_CLOSE: [5, 0],
    TRUNK_OPEN: [2, 1], TRUNK_CLOSE: [2, 0], MAIN_LIGHT_ON: [4, 1], MAIN_LIGHT_OFF: [4, 0]};
  assert.deepEqual(Object.keys(COMMAND_SPECS).sort(), Object.keys(expected).sort());
  const android = await readFile(new URL("../../my-traverse-next/app/src/main/java/com/example/carcontroller/GmoneAccountClient.kt", import.meta.url), "utf8");
  for (const [command, [type, option]] of Object.entries(expected)) {
    assert.deepEqual(COMMAND_SPECS[command], {control_type: type, request_option: option});
    assert.match(android, new RegExp(`"${command}"\\s*->\\s*ExtendedControlSpec\\(${type},\\s*${option},`));
    assert.ok(Object.isFrozen(COMMAND_SPECS[command]));
  }
  assert.ok(Object.isFrozen(COMMAND_SPECS));
  const source = await readFile(new URL("../server/commands.mjs", import.meta.url), "utf8");
  assert.doesNotMatch(source, /(?:import|export)\s.*\bfrom\s/);
});

test("login uses exact op8 and returns only a bounded server-only session", async () => {
  const f = fixture(() => loginReply()), before = Date.now();
  const session = await accountLogin("  driver@example.test  ", " TEST_PASSWORD ", f.request);
  assert.deepEqual(f.calls[0], {header: {id: 8, ticket_id: 0, revision: 0},
    login: {email: "driver@example.test", password: " TEST_PASSWORD "}, body: {}});
  assert.deepEqual(Object.keys(session).sort(), ["version", "uuid", "token", "vehicleId", "vehicleCount", "issuedAtMs", "expiresAtMs"].sort());
  assert.equal(session.uuid, ACCOUNT.uuid); assert.equal(session.token, ACCOUNT.token);
  assert.equal(session.vehicleCount, 1); assert.equal(session.vehicleId, "TEST_VEHICLE");
  assert.equal(session.expiresAtMs - session.issuedAtMs, ACCOUNT_TTL_MS);
  assert.ok(session.issuedAtMs >= before && session.issuedAtMs <= Date.now());
  assert.ok(Object.isFrozen(session));
  for (const secret of ["TEST_PASSWORD", "driver@example.test", "DO_NOT_RETURN"]) assert.ok(!JSON.stringify(session).includes(secret));
});

test("nested UUID compatibility does not retain the raw login response", async () => {
  const f = fixture(() => {
    const reply = loginReply(); delete reply.login.user_info_uuid;
    reply.login.user_info = {user_uuid: "TEST_USER", password: "DO_NOT_RETURN"}; return reply;
  });
  assert.equal((await accountLogin("test@example.test", "TEST_PASSWORD", f.request)).uuid, ACCOUNT.uuid);
});

test("invalid typed credentials cannot issue any request", async () => {
  const f = fixture();
  for (const [email, password] of [[null, "x"], ["", "x"], [" ", "x"], ["x".repeat(321), "x"],
    ["x\n@y.test", "x"], ["x@y.test", null], ["x@y.test", ""], ["x@y.test", "   "],
    ["x@y.test", "x".repeat(1025)], ["x@y.test", "x\u0000y"]]) {
    await assert.rejects(accountLogin(email, password, f.request), {code: "invalid_credentials"});
  }
  assert.deepEqual(ops(f), []);
});

test("login rejects ambiguous vehicle selection and malformed auth, without retry", async () => {
  for (const mutate of [
    r => { r.login.success = 1; }, r => { r.body.success = 1; }, r => { r.login.success = "0"; },
    r => { r.login.token_key = ""; }, r => { r.login.token_key = "x".repeat(4097); },
    r => { r.login.user_info_uuid = "x".repeat(129); }, r => { r.login.car_info = []; },
    r => { r.login.car_info = {}; }, r => { r.login.car_info.extra = {}; },
    r => { r.login.car_info = {["x".repeat(129)]: {}}; }, r => { delete r.login; },
  ]) {
    const f = fixture(() => { const r = loginReply(); mutate(r); return r; });
    await assert.rejects(accountLogin("x@y.test", "TEST_PASSWORD", f.request), CommandError);
    assert.deepEqual(ops(f), [8]);
  }
});

test("login HTTP/JSON/transport failures have bounded, secret-free errors", async () => {
  for (const respond of [() => new Response("LEAK_FROM_UPSTREAM", {status: 401}),
    () => new Response("LEAK_FROM_UPSTREAM"), () => { throw new Error("LEAK_FROM_UPSTREAM"); },
    () => null, () => [], () => new Response("x".repeat(512 * 1024 + 1))]) {
    const f = fixture(respond);
    await assert.rejects(accountLogin("x@y.test", "TEST_PASSWORD", f.request), error => {
      assert.ok(error instanceof CommandError);
      assert.doesNotMatch(error.message, /LEAK_FROM_UPSTREAM|TEST_PASSWORD/); return true;
    });
    assert.deepEqual(ops(f), [8]);
  }
});

test("every allowed command sends the pinned operation19 pair once", async () => {
  for (const command of Object.keys(COMMAND_SPECS)) {
    const f = fixture(p => p.header.id === 21 ? status({...RAW, eng: command === "VEHICLE_STOP" ? 1 : 0,
      rvsRmngTmVld: command === "VEHICLE_STOP"}) : commandSuccess(command));
    const result = await executeCommand(f.input(command), f.request);
    assert.equal(result.state, "server_responded"); assert.equal(result.resultCode, 0);
    assert.equal(result.ok, true); assert.equal(typeof result.message, "string");
    assert.equal(result.vehicleConfirmed, false); assert.equal(result.retryable, false);
    assert.equal(result.dispatched, true); assert.equal(result.failureStage, null);
    assert.deepEqual(ops(f), command.startsWith("VEHICLE_") ? [21, 19] : [19]);
    assert.deepEqual(f.calls.at(-1).body, COMMAND_SPECS[command]);
    if (command.startsWith("VEHICLE_")) assert.deepEqual(f.calls[0].body, {refresh_dtc: false, last_received_time: 0});
  }
});

test("unsupported commands and attempted protocol/body overrides cannot send", async () => {
  for (const command of [undefined, null, 19, {}, ["DOOR_LOCK"], "toString", "__proto__", "constructor", "lock",
    "PANIC", "SUNROOF_OPEN", "SUNROOF_CLOSE", "SUNROOF_TILT", "CLEAR_DTC", "WRITE_OPTIONS", "DRIVE", "BRAKE"]) {
    const f = fixture();
    assertBlocked(await executeCommand(f.input(command, {command}), f.request), "unsupported_command");
    assert.deepEqual(ops(f), []);
  }
  const f = fixture();
  await executeCommand(f.input("DOOR_LOCK", {operation: 47, body: {control_type: 99}, url: "https://evil.test"}), f.request);
  assert.deepEqual(ops(f), [19]); assert.deepEqual(f.calls[0].body, COMMAND_SPECS.DOOR_LOCK);
});

test("expired/malformed/multi-vehicle sessions fail before even a status read", async () => {
  for (const account of [null, {}, {...ACCOUNT, version: 2}, {...ACCOUNT, vehicleCount: 2},
    {...ACCOUNT, uuid: ""}, {...ACCOUNT, token: "x".repeat(4097)}, {...ACCOUNT, vehicleId: null},
    {...ACCOUNT, issuedAtMs: NOW + 1}, {...ACCOUNT, expiresAtMs: NOW},
    {...ACCOUNT, expiresAtMs: NOW + ACCOUNT_TTL_MS}, {...ACCOUNT, expiresAtMs: Infinity}]) {
    const f = fixture();
    assertBlocked(await executeCommand(f.input("VEHICLE_START", {account}), f.request), "account_invalid_or_expired");
    assert.deepEqual(ops(f), []);
  }
});

test("all commands deny current moving/engaged signals and unknown onroad data", async () => {
  const mutations = [
    s => { s.vehicle.speedMps = 0.01; }, s => { s.vehicle.speedMps = -0.01; },
    s => { s.vehicle.speedMps = null; }, s => { s.vehicle.speedMps = "0"; },
    s => { s.vehicle.speedMps = NaN; }, s => { s.vehicle.standstill = false; },
    s => { s.openpilot.enabled = true; }, s => { delete s.openpilot; },
    s => { delete s.onroad; }, s => { s.vehicle.available = false; s.onroad = false; },
    s => { delete s.vehicle; }, s => { s.vehicle.available = "true"; },
    s => { s.vehicle.rawSpeedMps = 1; }, s => { s.vehicleSpeedMps = 1; },
    s => { s.vehicleSpeedSource = "offroad"; },
    s => { s.vehicle.can.valid = false; }, s => { s.vehicle.can.timeout = true; },
    s => { s.openpilot.available = false; },
    s => { s.openpilot.active = true; }, s => { delete s.openpilot.active; },
    s => { s.deviceId = "OTHER_DEVICE"; }, s => { delete s.enabled; },
  ];
  for (const command of Object.keys(COMMAND_SPECS)) {
    for (const mutate of mutations) {
      const liveState = mutateRaw(parked(), mutate); const f = fixture();
      assertBlocked(await executeCommand(f.input(command, {liveState}), f.request));
      assert.deepEqual(ops(f), []);
    }
  }
});

test("feed freshness is independently recomputed, never trusts a fresh display flag", async () => {
  for (const liveState of [null, {}, parked(NOW - CLOUD_FRESHNESS_MS.onroad - 1), parked(NOW + 1),
    {...parked(), state: {...parked().state, updated_at: "2027-01-15 08:00:00"}},
    {...parked(), state: {...parked().state, updated_at: NOW}},
    mutateRaw(parked(), s => { s.updatedAt = new Date(NOW - CLOUD_FRESHNESS_MS.onroad - 1).toISOString(); }),
    mutateRaw(parked(), s => { delete s.updatedAt; }),
    mutateRaw(parked(), s => { s.updatedAt = new Date(NOW + 1).toISOString(); }),
  ]) {
    const f = fixture();
    assertBlocked(await executeCommand(f.input("DOOR_LOCK", {liveState}), f.request));
    assert.deepEqual(ops(f), []);
  }
  assert.equal(validateCommandGuard({command: "DOOR_LOCK", account: ACCOUNT, liveState: parked(NOW - 45_000)}, NOW).allowed, true);
});

test("exported guard requires provenance, matching account and both direct-reply clocks", () => {
  const input = {command: "VEHICLE_START", account: ACCOUNT, liveState: parked()};
  assert.equal(validateCommandGuard(input, NOW).code, "gmone_status_required");
  assert.deepEqual(validateCommandGuard({...input, gmoneStatus: observation()}, NOW), {allowed: true, code: "allowed"});
  for (const patch of [{source: "gmone_latest"}, {source: "firebase+gmone"}, {accountUuid: "OTHER_USER"},
    {requestedAtMs: NOW - 30_001}, {receivedAtMs: NOW - 30_001}, {serverResponseAtMs: NOW - 30_001},
    {requestedAtMs: NOW + 1}, {receivedAtMs: NOW + 1}, {serverResponseAtMs: NOW + 1},
    {requestedAtMs: NOW, receivedAtMs: NOW - 1}, {serverResponseAtMs: null}, {rawStatus: []}]) {
    assert.equal(validateCommandGuard({...input, gmoneStatus: {...observation(), ...patch}}, NOW).code, "gmone_status_not_fresh");
  }
});

test("start ports known engine-off, hood-closed and remaining-start guards", async () => {
  for (const [raw, code] of [
    [{}, "engine_unknown"], [{...RAW, eng: null}, "engine_unknown"], [{...RAW, eng: ""}, "engine_unknown"],
    [{...RAW, eng: false}, "engine_unknown"], [{...RAW, eng: 1}, "engine_already_running"],
    [{...RAW, hood: null}, "hood_unknown"], [{...RAW, hood: 2}, "hood_unknown"], [{...RAW, hood: 1}, "hood_open"],
    [{...RAW, rvsRmng: null}, "remaining_starts_unknown"], [{...RAW, rvsRmng: ""}, "remaining_starts_unknown"],
    [{...RAW, rvsRmng: 1.5}, "remaining_starts_unknown"], [{...RAW, rvsRmng: -1}, "remaining_starts_unknown"],
    [{...RAW, rvsRmng: 0}, "no_remaining_starts"],
  ]) {
    const f = fixture(() => status(raw));
    assertBlocked(await executeCommand(f.input("VEHICLE_START"), f.request), code);
    assert.deepEqual(ops(f), [21]);
  }
  const f = fixture(p => p.header.id === 21 ? status({eng: "0", hood: "0", rvsRmng: "2"}, NOW) : commandSuccess("VEHICLE_START"));
  assert.equal((await executeCommand(f.input("VEHICLE_START"), f.request)).state, "server_responded");
});

test("stop never stops an ordinary running engine, even with engineRunning:true", async () => {
  for (const remote of [undefined, null, false, 0, "0", "false", "", 2, "yes", {}, []]) {
    const f = fixture(() => status({...RAW, eng: 1, rvsRmngTmVld: remote}));
    assertBlocked(await executeCommand(f.input("VEHICLE_STOP"), f.request), "not_remote_running");
    assert.deepEqual(ops(f), [21]);
  }
  for (const remote of [true, 1, "1", "true"]) {
    const f = fixture(p => p.header.id === 21 ? status({eng: 1, rvsRmngTmVld: remote}) : commandSuccess("VEHICLE_STOP"));
    assert.equal((await executeCommand(f.input("VEHICLE_STOP"), f.request)).state, "server_responded");
  }
});

test("stale, future and missing GMOne timestamps block; caller cache cannot bypass op21", async () => {
  for (const timestamp of [NOW - 30_001, NOW + 1, 0, -1, null, "1800000000"]) {
    const f = fixture(() => status(RAW, timestamp));
    assertBlocked(await executeCommand(f.input("VEHICLE_START", {gmoneStatus: observation()}), f.request), "gmone_status_not_fresh");
    assert.deepEqual(ops(f), [21]);
  }
});

test("status response failures never fall back to cache, REST or op19", async () => {
  for (const respond of [() => { throw new Error("LEAK_FROM_UPSTREAM"); },
    () => ({body: {success: 2}}), () => fetched(status()), () => ({body: {success: 0}}),
    () => ({body: {success: 0, car_status: []}}), () => ({login: {success: 1}, ...status()}),
    () => new Response("redirect", {status: 302, headers: {location: "https://evil.test"}})]) {
    const f = fixture(respond);
    assertBlocked(await executeCommand(f.input("VEHICLE_START", {gmoneStatus: observation()}), f.request));
    assert.deepEqual(ops(f), [21]);
  }
});

test("engine preflight polls only its ticket, then uses a separate command result ticket", async () => {
  const f = fixture(p => {
    if (p.header.id === 21) return pending("STATUS_TICKET");
    if (p.header.id === 19) return pending("COMMAND_TICKET");
    assert.equal(p.header.id, 66);
    return fetched(p.body.ticket_uuid === "STATUS_TICKET" ? status(RAW, f.now()) : commandSuccess("VEHICLE_START"));
  });
  const result = await executeCommand(f.input("VEHICLE_START"), f.request);
  assert.equal(result.state, "server_responded"); assert.deepEqual(ops(f), [21, 66, 19, 66]);
  assert.deepEqual(f.calls.filter(p => p.header.id === 66).map(p => p.body.ticket_uuid), ["STATUS_TICKET", "COMMAND_TICKET"]);
});

test("cloud/session expiry during preflight is rechecked immediately before dispatch", async () => {
  for (const expireSession of [false, true]) {
    const f = fixture(p => {
      if (p.header.id === 21) return pending();
      f.advance(1500); return fetched(status(RAW, f.now()));
    });
    const overrides = expireSession ? {account: {...ACCOUNT, expiresAtMs: NOW + 1000}} : {liveState: parked(NOW - 44_000)};
    const result = await executeCommand(f.input("VEHICLE_START", overrides), f.request);
    assertBlocked(result, expireSession ? "account_invalid_or_expired" : "live_state_not_fresh");
    assert.deepEqual(ops(f), [21, 66]);
  }
});

test("wire input is snapshotted across awaits, preventing account substitution", async () => {
  const account = {...ACCOUNT}, liveState = parked();
  const f = fixture(p => {
    if (p.header.id === 21) {
      account.token = "CHANGED"; account.uuid = "CHANGED";
      return status();
    }
    return commandSuccess("VEHICLE_START");
  });
  assert.equal((await executeCommand(f.input("VEHICLE_START", {account, liveState}), f.request)).state, "server_responded");
  assert.equal(f.calls[1].login.uuid, ACCOUNT.uuid); assert.equal(f.calls[1].login.token_key, ACCOUNT.token);
});

test("pending code2/13 polls original ticket beyond six polls, never replays op19", async () => {
  let polls = 0;
  const f = fixture(p => {
    if (p.header.id === 19) return pending();
    assert.equal(p.header.id, 66); assert.deepEqual(p.body, {ticket_uuid: "TEST_TICKET"});
    if (++polls <= 7) return {body: {success: polls % 2 ? 2 : 13}};
    return fetched(commandSuccess("DOOR_LOCK"));
  });
  assert.equal((await executeCommand(f.input(), f.request)).state, "server_responded");
  assert.equal(polls, 8); assert.deepEqual(ops(f), [19, ...Array(8).fill(66)]);
  assert.equal(f.waits[0], 250);
});

test("bounded poll deadline and count stop without inferring offline or replaying", async () => {
  for (const slow of [false, true]) {
    const f = fixture(p => {
      if (p.header.id === 19) return pending();
      if (slow) f.advance(4000);
      return {body: {success: 2}};
    });
    const result = await executeCommand(f.input(), f.request);
    assertUnknown(result, f, "result_timeout");
    assert.ok(f.calls.length <= 21); assert.ok(f.now() >= NOW + 30_000);
    if (slow) assert.ok(f.calls.length < 10);
  }
  const f = fixture(p => p.header.id === 19 ? pending() : {body: {success: 2}});
  assertUnknown(await executeCommand(f.input("DOOR_LOCK", {sleep: async () => {}}), f.request), f, "result_timeout");
  assert.equal(f.calls.length, 21);
});

test("late success and backwards poll clock are not accepted", async () => {
  for (const delta of [30_000, -1000]) {
    const f = fixture(p => {
      if (p.header.id === 19) return pending();
      f.advance(delta); return fetched(commandSuccess("DOOR_LOCK"));
    });
    assertUnknown(await executeCommand(f.input(), f.request), f, "result_timeout");
  }
});

test("all ambiguous immediate command failures remain unknown and never retry/auth renew", async () => {
  for (const respond of [
    () => { throw new Error(`LEAK_FROM_UPSTREAM ${ACCOUNT.token}`); },
    () => { throw new DOMException("LEAK_FROM_UPSTREAM", "TimeoutError"); },
    () => new Response("LEAK_FROM_UPSTREAM", {status: 503}),
    () => new Response("LEAK_FROM_UPSTREAM", {status: 307, headers: {location: "https://evil.test"}}),
    () => new Response("not json"), () => [], () => null, () => ({}),
    () => ({login: {success: 1}, body: {success: 0}}), () => ({login: null, body: {success: 0}}),
    () => ({body: {success: 2}}), () => ({body: {success: "0"}}),
    () => ({body: {success: 0, wait_response: "true"}}), () => ({body: {success: 13}}),
    () => pending(""), () => pending("x".repeat(257)),
    () => ({body: {success: 0, control_type: 99}}), () => ({body: {success: 0, request_option: 1}}),
    () => ({body: {success: 0, control_type: "1"}}), () => ({body: {success: 0, request_option: null}}),
  ]) {
    const f = fixture(respond);
    assertUnknown(await executeCommand(f.input(), f.request), f);
    assert.deepEqual(ops(f), [19]);
  }
});

test("malformed/nested rejected/auth-expired poll results never imply command success", async () => {
  for (const invalid of [
    {login: {success: 1}, body: {success: 2}}, {body: {success: 7}}, {body: {success: "0"}},
    {body: {success: 0, fetched_data: []}}, {body: {success: 0, fetched_data: "bad"}},
    {body: {success: 2, fetched_data: commandSuccess("DOOR_LOCK")}},
    fetched({body: {success: 2}}), fetched({login: {success: 1}, body: {success: 0}}),
    fetched(pending()), fetched({body: {success: 0, request_option: 1}}),
  ]) {
    const f = fixture(p => p.header.id === 19 ? pending() : invalid);
    assertUnknown(await executeCommand(f.input(), f.request), f);
    assert.deepEqual(ops(f), [19, 66]);
  }
  const f = fixture(p => { if (p.header.id === 19) return pending(); throw new Error("LEAK_FROM_UPSTREAM"); });
  assertUnknown(await executeCommand(f.input(), f.request), f, "transport_error");
  assert.deepEqual(ops(f), [19, 66]);
});

test("optional echo omission matches Android protocol but is not physical confirmation", async () => {
  const f = fixture(() => ({body: {success: 0}}));
  const result = await executeCommand(f.input(), f.request);
  assert.equal(result.state, "server_responded"); assert.equal(result.vehicleConfirmed, false);
});

test("streamed oversized and interrupted responses are bounded and cancelled", async () => {
  for (const oversized of [true, false]) {
    let cancelled = false, chunks = 0;
    const f = fixture(() => new Response(new ReadableStream({
      pull(controller) {
        if (!oversized && chunks++ > 0) { controller.error(new Error("LEAK_FROM_UPSTREAM")); return; }
        controller.enqueue(new Uint8Array(64 * 1024));
      },
      cancel() { cancelled = true; },
    })));
    assertUnknown(await executeCommand(f.input(), f.request), f, oversized ? "response_too_large" : "transport_error");
    if (oversized) assert.equal(cancelled, true);
    assert.deepEqual(ops(f), [19]);
  }
});

test("parent claim-before-call contract can persist unknown and suppress duplicates", async () => {
  // In-memory contract harness only, NOT a claim about a real D1 implementation.
  const claims = new Map();
  const f = fixture(() => { throw new Error("ambiguous write"); });
  const parent = async id => {
    if (claims.has(id)) return {duplicate: true};
    claims.set(id, "claimed");
    const result = await executeCommand(f.input(), f.request);
    claims.set(id, result); return result;
  };
  const [first, duplicate] = await Promise.all([parent("test-claim"), parent("test-claim")]);
  assertUnknown(first, f); assert.equal(duplicate.duplicate, true);
  assert.equal((await parent("test-claim")).duplicate, true);
  assert.deepEqual(ops(f), [19]);
});

test("actual offroad feed with 300s heartbeat permits controls without CAN or P gear", async () => {
  for (const command of Object.keys(COMMAND_SPECS)) {
    const f = fixture(p => p.header.id === 21 ? status({...RAW, eng: command === "VEHICLE_STOP" ? 1 : 0,
      rvsRmngTmVld: command === "VEHICLE_STOP"}) : commandSuccess(command));
    const result = await executeCommand(f.input(command, {liveState: offroad(NOW - 300_000)}), f.request);
    assert.equal(result.ok, true); assert.equal(result.state, "server_responded");
    assert.equal(result.vehicleConfirmed, false);
    assert.deepEqual(ops(f), command.startsWith("VEHICLE_") ? [21, 19] : [19]);
  }
  assert.equal(validateCommandGuard({command: "DOOR_LOCK", account: ACCOUNT, liveState: offroad(NOW - 600_000)}, NOW).allowed, true);
  const f = fixture();
  assertBlocked(await executeCommand(f.input("DOOR_LOCK", {liveState: offroad(NOW - 600_001)}), f.request), "live_state_not_fresh");
  assert.deepEqual(ops(f), []);
});

test("no invented P-gear or active-CAN requirement for a known stationary car", async () => {
  for (const gear of [undefined, "park", "neutral", "drive", "unknown"]) {
    const liveState = mutateRaw(parked(), r => { r.vehicle.gear = gear; delete r.vehicle.can; delete r.vehicle.standstill; });
    const f = fixture();
    assert.equal((await executeCommand(f.input("DOOR_LOCK", {liveState}), f.request)).ok, true);
  }
});

test("offroad cannot hide explicit current moving or engaged evidence", async () => {
  for (const mutate of [r => { r.vehicleSpeedMps = 1; }, r => { r.openpilot.enabled = true; },
    r => { r.openpilot.active = true; }, r => { r.vehicle = {available: true, speedMps: 1}; },
    r => { r.vehicle = {available: true, standstill: false}; }]) {
    const f = fixture();
    assertBlocked(await executeCommand(f.input("DOOR_LOCK", {liveState: mutateRaw(offroad(), mutate)}), f.request));
    assert.deepEqual(ops(f), []);
  }
  const f = fixture(), feed = offroad(); feed.state.speed_mps = 1;
  assertBlocked(await executeCommand(f.input("DOOR_LOCK", {liveState: feed}), f.request), "vehicle_not_stationary");
});

test("display cache, generatedAt and missing default-filled state cannot authorize", async () => {
  for (const liveState of [
    {...offroad(), state: null}, {...offroad(), state: {...offroad().state, raw_json: "{}"}},
    {...offroad(), state: {...offroad().state, raw_json: "invalid"}},
    {...offroad(), state: {...offroad().state, raw_json: "null"}},
    {...offroad(), state: {...offroad().state, raw_json: {onroad: false}}},
    mutateRaw(offroad(), r => { delete r.onroad; }), mutateRaw(offroad(), r => { delete r.enabled; }),
    mutateRaw(offroad(), r => { r.schemaVersion = "display-cache"; }),
    mutateRaw(offroad(), r => { r.deviceId = "OTHER_DEVICE"; }),
    {...offroad(), state: {...offroad().state, enabled: null}},
    {...offroad(), state: {...offroad().state, onroad: null}},
  ]) {
    const f = fixture();
    assertBlocked(await executeCommand(f.input("DOOR_LOCK", {liveState}), f.request));
    assert.deepEqual(ops(f), []);
  }
});

test("beforeSend runs once after engine status/guards and immediately before op19", async () => {
  for (const command of Object.keys(COMMAND_SPECS)) {
    const events = [];
    const f = fixture(p => {
      events.push(p.header.id);
      return p.header.id === 21 ? status({...RAW, rvsRmngTmVld: command === "VEHICLE_STOP"}) : commandSuccess(command);
    });
    const result = await executeCommand(f.input(command, {liveState: offroad(NOW - 300_000),
      beforeSend: async () => { events.push("hook"); }}), f.request);
    assert.equal(result.ok, true);
    assert.deepEqual(events, command.startsWith("VEHICLE_") ? [21, "hook", 19] : ["hook", 19]);
  }
});

test("denied or failed preflight never calls beforeSend", async () => {
  let hooks = 0;
  for (const [command, liveState, reply] of [
    ["CLEAR_DTC", offroad(), status()], ["DOOR_LOCK", null, status()],
    ["VEHICLE_START", offroad(), status({...RAW, hood: 1})],
    ["VEHICLE_START", offroad(), {body: {success: 2}}],
    ["VEHICLE_STOP", offroad(), status({...RAW, eng: 1})],
  ]) {
    const f = fixture(() => reply);
    assertBlocked(await executeCommand(f.input(command, {liveState, beforeSend: async () => { hooks++; }}), f.request));
    assert.ok(!ops(f).includes(19));
  }
  assert.equal(hooks, 0);
});

test("beforeSend failure blocks physical command and strips exception details", async () => {
  for (const beforeSend of [null, false, async () => false, async () => { throw new Error("LEAK_FROM_UPSTREAM"); }]) {
    const f = fixture(() => status());
    const result = await executeCommand(f.input("VEHICLE_START", {beforeSend}), f.request);
    assertBlocked(result); assert.equal(result.failureStage, "before-send");
    assert.deepEqual(ops(f), [21]); assert.doesNotMatch(JSON.stringify(result), /LEAK_FROM_UPSTREAM/);
  }
});

test("hook delay rechecks cloud age, direct status age and account expiry", async () => {
  for (const scenario of ["cloud", "status", "account"]) {
    const f = fixture(() => status());
    const result = await executeCommand(f.input("VEHICLE_START", {
      liveState: offroad(scenario === "cloud" ? NOW - 599_000 : NOW),
      account: scenario === "account" ? {...ACCOUNT, expiresAtMs: NOW + 1000} : ACCOUNT,
      beforeSend: async () => { f.advance(scenario === "status" ? 30_001 : 1001); },
    }), f.request);
    assertBlocked(result, {cloud: "live_state_not_fresh", status: "gmone_status_not_fresh", account: "account_invalid_or_expired"}[scenario]);
    assert.deepEqual(ops(f), [21]);
  }
});

test("transport timeout aborts a mock fetch or response stream, without command replay", async t => {
  const nativeTimeout = AbortSignal.timeout.bind(AbortSignal), budgets = [];
  t.mock.method(AbortSignal, "timeout", ms => { budgets.push(ms); return nativeTimeout(1); });
  for (const stream of [false, true]) {
    const f = fixture((_payload, _count, options) => stream
      ? new Response(new ReadableStream({start(controller) {
        options.signal.addEventListener("abort", () => controller.error(options.signal.reason), {once: true});
      }}))
      : new Promise((_resolve, reject) => options.signal.addEventListener("abort", () => reject(options.signal.reason), {once: true})));
    // Native AbortSignal timers are unref'ed in Node; this local timer keeps the test alive.
    const keepAlive = setTimeout(() => {}, 1000);
    try { assertUnknown(await executeCommand(f.input(), f.request), f, "transport_error"); }
    finally { clearTimeout(keepAlive); }
    assert.deepEqual(ops(f), [19]);
  }
  assert.deepEqual(budgets, [10_000, 10_000]);
});

test("result polling clamps each HTTP timeout to the remaining 30s budget", async t => {
  const nativeTimeout = AbortSignal.timeout.bind(AbortSignal), budgets = [];
  t.mock.method(AbortSignal, "timeout", ms => { budgets.push(ms); return nativeTimeout(ms); });
  const f = fixture(p => {
    if (p.header.id === 19) return pending();
    f.advance(6000); return {body: {success: 2}};
  });
  assertUnknown(await executeCommand(f.input(), f.request), f, "result_timeout");
  assert.ok(budgets.every(ms => ms > 0 && ms <= 10_000));
  assert.ok(budgets.at(-1) < 10_000);
});

test("upstream auth expiry requests relogin but never implies an attempted command was unsent", async () => {
  for (const command of ["DOOR_LOCK", "VEHICLE_START"]) {
    const f = fixture(() => ({login: {success: 1}, body: {success: 0}}));
    const result = await executeCommand(f.input(command), f.request);
    assert.match(result.message, /다시 로그인/);
    if (command === "DOOR_LOCK") assertUnknown(result, f, "session_expired");
    else assertBlocked(result, "session_expired");
    assert.deepEqual(ops(f), command === "DOOR_LOCK" ? [19] : [21]);
  }
});
