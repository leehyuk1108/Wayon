/**
 * Server-only GMOne account commands. No persistence, REST fallback or renewal.
 * Protocol attribution: apps/my-traverse-next/.../GmoneAccountClient.kt,
 * RemoteEngineCommandPolicy.kt and VehicleSnapshotPolicy.kt; bounded transport
 * and op66 pending-code handling adapted from cloudflare/multipack-mcp/src/gmone.mjs.
 * The latter is NOT a runtime or test dependency. Only ops 8/21/19/66 are ported.
 *
 * Parent contract: authenticate/authorize the user, bind cloud telemetry to this
 * account's vehicle, enforce CSRF/rate limits, and atomically claim the D1 request
 * BEFORE executeCommand. Persist even an unknown result; never replay that claim.
 * A claim must also serialize conflicting commands for the same vehicle. This
 * module cannot provide cross-request/process idempotency or verify that binding.
 * Store typed credentials, if retained, ONLY in the parent's encrypted server
 * session. Never serialize accountLogin's return to the PWA, logs or a plain cookie.
 *
 * liveState is the trusted Wayon GET /api/state payload (also /api/json-compatible). Its state row must
 * include updated_at, device_id, onroad, enabled, speed_mps and raw_json (JSON
 * string of wayon-telemetry-v2 or wayon-telemetry-v3). Require fresh row AND raw timestamps and matching
 * device/onroad/enabled fields. Current moving/engaged signals always block.
 * A known offroad heartbeat does not require CAN, gear or available vehicle data;
 * onroad needs known stationary data. No generatedAt/vehicleStatus/
 * vehicleLock/GPS/display defaults can substitute for those fields.
 * Offroad synthetic speed zero is NOT a sensor observation. Offroad authorization
 * uses the explicit offroad state, never missing values defaulted to false/zero.
 * Cloud freshness follows candidate Worker's 45s onroad / 600s offroad contract
 * (300s heartbeat). Direct GMOne engine replies use 30s, NOT gmone_latest's 24h.
 * Unknown, future and contradictory data deny; no P-gear requirement is added.
 *
 * validateCommandGuard({command, account, liveState, gmoneStatus?}, nowMs?)
 * returns {allowed, code}. For engines, a missing gmoneStatus returns
 * gmone_status_required. A SERVER-CREATED gmoneStatus has source:"gmone-direct",
 * accountUuid, requestedAtMs, receivedAtMs, serverResponseAtMs, rawStatus.
 * executeCommand always performs its OWN op21 read for engines, never accepts a
 * caller-supplied GMOne snapshot or merged/display cache as preflight evidence.
 * GMOne timestamps describe a server reply, NOT a proven sensor observation time.
 * An engine reply at most 2000ms ahead at receipt may wait once for local time
 * to catch up. No timestamp is changed; all original freshness limits still apply.
 *
 * executeCommand({command, account, liveState, beforeSend?, now=Date.now, sleep?}, fetchFn=fetch)
 * invokes beforeSend() only AFTER guards, immediately before op19; rejection
 * blocks dispatch. The hook may return {liveState} with a newly queried trusted
 * feed; it is snapshotted and fully revalidated before op19. Recheck ages/session
 * after the hook (e.g. impact marker).
 * returns {ok, state, message, command, code, dispatched, vehicleConfirmed:false,
 * retryable:false, failureStage, resultCode?}. state: blocked (no op19),
 * server_responded (protocol success, NOT physical confirmation), or unknown
 * (op19 attempted, including auth/HTTP errors). now/sleep are server test seams.
 */
if (typeof window !== "undefined") throw new Error("GMOne commands are server-only.");

export const ACCOUNT_TTL_MS = 15 * 60 * 1000;
export const COMMAND_FRESHNESS_MS = 30_000;
export const CLOUD_FRESHNESS_MS = Object.freeze({onroad: 45_000, offroad: 600_000});
const REQUEST_TIMEOUT_MS = 10_000;
const MAX_SERVER_FUTURE_WAIT_MS = 2000;
const MAX_RESPONSE_BYTES = 512 * 1024;
const BASE_URL = "https://mp.gmone.co.kr:28354";

// Original Android remote controls only; no DTC, settings writes or timers.
export const COMMAND_SPECS = Object.freeze(Object.fromEntries(Object.entries({
  DOOR_LOCK: [1, 0], DOOR_UNLOCK: [1, 1], DRIVER_DOOR_UNLOCK: [1, 2],
  VEHICLE_START: [0, 2], VEHICLE_STOP: [0, 0],
  WINDOW_OPEN: [5, 1], WINDOW_CLOSE: [5, 0],
  TRUNK_OPEN: [2, 1], TRUNK_CLOSE: [2, 0],
  MAIN_LIGHT_ON: [4, 1], MAIN_LIGHT_OFF: [4, 0],
  PANIC: [3, 1], SUNROOF_OPEN: [6, 1], SUNROOF_CLOSE: [6, 0], SUNROOF_TILT: [6, 3],
}).map(([key, [control_type, request_option]]) => [key, Object.freeze({control_type, request_option})])));

export class CommandError extends Error {
  constructor(code) {
    super(code);
    this.name = "CommandError";
    this.code = code;
  }
}

const fail = code => { throw new CommandError(code); };
const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
const supported = command => typeof command === "string" && Object.hasOwn(COMMAND_SPECS, command);
const engineCommand = command => command === "VEHICLE_START" || command === "VEHICLE_STOP";
const boundedString = (value, max) => typeof value === "string" && value.trim().length > 0 &&
  value.length <= max && !/[\u0000-\u001f\u007f]/.test(value);
const time = value => Number.isSafeInteger(value) && value > 0;
const fresh = (value, now, maxAge = COMMAND_FRESHNESS_MS) => time(value) && time(now) && now >= value && now - value <= maxAge;
const decision = code => ({allowed: code === null, code: code ?? "allowed"});

function validAccount(account, now) {
  return object(account) && account.version === 1 && account.vehicleCount === 1 &&
    boundedString(account.uuid, 128) && boundedString(account.token, 4096) &&
    boundedString(account.vehicleId, 128) && time(now) && time(account.issuedAtMs) &&
    time(account.expiresAtMs) && account.issuedAtMs <= now && now < account.expiresAtMs &&
    account.expiresAtMs - account.issuedAtMs <= ACCOUNT_TTL_MS;
}

function cloudBlockReason(state, now) {
  const row = state?.state;
  if (!row || ![0, 1].includes(row.onroad)) return "motion_unknown";
  const maxAge = row.onroad ? CLOUD_FRESHNESS_MS.onroad : CLOUD_FRESHNESS_MS.offroad;
  if (!fresh(isoTime(row.updated_at), now, maxAge)) return "live_state_not_fresh";
  if (typeof row.raw_json !== "string" || row.raw_json.length > MAX_RESPONSE_BYTES) return "motion_unknown";
  let raw;
  try { raw = JSON.parse(row.raw_json); } catch { return "motion_unknown"; }
  if (!object(raw) || !["wayon-telemetry-v2", "wayon-telemetry-v3"].includes(raw.schemaVersion)) return "motion_unknown";
  if (!fresh(isoTime(raw.updatedAt), now, maxAge)) return "live_state_not_fresh";
  const vehicle = raw.vehicle, controls = raw.openpilot;
  if (!boundedString(row.device_id, 128) || row.device_id !== raw.deviceId ||
      typeof raw.onroad !== "boolean" || row.onroad !== Number(raw.onroad) ||
      ![0, 1].includes(row.enabled) || typeof raw.enabled !== "boolean" || row.enabled !== Number(raw.enabled)) return "motion_unknown";
  if (raw.enabled || controls?.enabled === true || controls?.active === true) return "controls_active";
  const speeds = [row.speed_mps, raw.vehicleSpeedMps, vehicle?.speedMps, vehicle?.rawSpeedMps];
  if (speeds.some(v => number(v) !== null && number(v) !== 0) || vehicle?.standstill === false) return "vehicle_not_stationary";
  if (!raw.onroad) return null;
  if (vehicle?.available !== true || controls?.available !== true || controls.enabled !== false || controls.active !== false ||
      raw.vehicleSpeedMps !== 0 || vehicle.speedMps !== 0 ||
      !["vEgo", "vEgoCluster"].includes(raw.vehicleSpeedSource) ||
      vehicle.can?.valid === false || vehicle.can?.timeout === true) return "motion_unknown";
  return null;
}

function isoTime(value) {
  return typeof value === "string" &&
    /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)$/.test(value)
    ? Date.parse(value) : NaN;
}

// Accept the wire protocol's numeric strings, but never JS null/blank/boolean coercion.
function number(value) {
  if (typeof value === "string" && /^-?\d+(?:\.\d+)?$/.test(value)) value = Number(value);
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

// Match integer wire fields without JSON/JS coercion or precision loss.
function integer(value) {
  if (typeof value === "string" && /^(?:0|-?[1-9]\d*)$/.test(value)) value = Number(value);
  return Number.isSafeInteger(value) ? value : null;
}

function binary(value) {
  if (value === true || value === 1 || value === "1" || value === "true") return true;
  if (value === false || value === 0 || value === "0" || value === "false") return false;
  return null;
}

function engineBlockReason(command, raw) {
  // RemoteEngineCommandPolicy parity: STOP must never stop an ordinary engine.
  if (command === "VEHICLE_STOP") {
    return binary(raw.rvsRmngTmVld) === true ? null : "not_remote_running";
  }
  const engine = number(raw.eng);
  if (engine === null) return "engine_unknown";
  if (engine !== 0) return "engine_already_running";
  const hood = binary(raw.hood);
  if (hood === null) return "hood_unknown";
  if (hood) return "hood_open";
  const starts = number(raw.rvsRmng);
  if (!Number.isSafeInteger(starts) || starts < 0) return "remaining_starts_unknown";
  return starts > 0 ? null : "no_remaining_starts";
}

export function validateCommandGuard({command, account, liveState, gmoneStatus} = {}, nowMs = Date.now()) {
  if (!supported(command)) return decision("unsupported_command");
  if (!validAccount(account, nowMs)) return decision("account_invalid_or_expired");
  const cloudReason = cloudBlockReason(liveState, nowMs);
  if (cloudReason) return decision(cloudReason);
  if (!engineCommand(command)) return decision(null);
  if (gmoneStatus == null) return decision("gmone_status_required");
  if (gmoneStatus.source !== "gmone-direct" || gmoneStatus.accountUuid !== account.uuid ||
      !fresh(gmoneStatus.requestedAtMs, nowMs) || !fresh(gmoneStatus.receivedAtMs, nowMs) ||
      !fresh(gmoneStatus.serverResponseAtMs, nowMs) ||
      gmoneStatus.receivedAtMs < gmoneStatus.requestedAtMs || !object(gmoneStatus.rawStatus)) {
    return decision("gmone_status_not_fresh");
  }
  return decision(engineBlockReason(command, gmoneStatus.rawStatus));
}

async function boundedJson(response) {
  if (!response?.ok) {
    await response?.body?.cancel().catch(() => {});
    fail("upstream_http_error");
  }
  const reader = response.body?.getReader();
  if (!reader) fail("invalid_response");
  const parts = [];
  let length = 0;
  try {
    for (;;) {
      const {done, value} = await reader.read();
      if (done) break;
      length += value.byteLength;
      if (length > MAX_RESPONSE_BYTES) fail("response_too_large");
      parts.push(value);
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
  const data = new Uint8Array(length);
  let offset = 0;
  for (const part of parts) { data.set(part, offset); offset += part.byteLength; }
  try {
    const parsed = JSON.parse(new TextDecoder().decode(data));
    if (!object(parsed)) fail("invalid_response");
    return parsed;
  } catch { fail("invalid_response"); }
}

function checkSession(response) {
  if (!Object.hasOwn(response, "login")) return;
  if (!object(response.login)) fail("invalid_auth_response");
  if (Object.hasOwn(response.login, "success")) {
    const success = integer(response.login.success);
    if (success === null) fail("invalid_auth_response");
    if (success !== 0) fail("session_expired");
  }
}

function operationBody(response, allowMissingSuccess = false) {
  checkSession(response);
  if (!object(response.body)) fail("invalid_response");
  if (!Object.hasOwn(response.body, "success") && allowMissingSuccess) return response.body;
  const success = integer(response.body.success);
  if (success === null) fail("invalid_response");
  return {...response.body, success};
}

class Protocol {
  constructor(account, fetchFn, now, sleep) {
    this.account = account;
    this.fetchFn = fetchFn;
    this.now = now;
    this.sleep = sleep;
    this.ticket = 0;
  }

  async post(operation, body, login, timeoutMs = REQUEST_TIMEOUT_MS) {
    if (![8, 19, 21, 66].includes(operation)) fail("unsupported_operation");
    try {
      // workerd's native fetch cannot receive this Protocol instance as its receiver.
      const fetchFn = this.fetchFn;
      const response = await fetchFn(`${BASE_URL}/${operation === 8 ? "b1_init" : "b1_connect_m"}`, {
        method: "POST", redirect: "manual", cache: "no-store", credentials: "omit",
        signal: AbortSignal.timeout(Math.max(1, Math.min(REQUEST_TIMEOUT_MS, Math.floor(timeoutMs)))),
        headers: {"content-type": "application/json", accept: "application/json"},
        body: JSON.stringify({header: {id: operation, ticket_id: this.ticket++ % 256, revision: 0},
          login: login ?? {uuid: this.account.uuid, token_key: this.account.token}, body}),
      });
      return await boundedJson(response);
    } catch (error) {
      if (error instanceof CommandError) throw error;
      // Never propagate a fetch error, response text, URL, token or account details.
      fail("transport_error");
    }
  }

  async resolve(initial) {
    const body = operationBody(initial, true);
    if (body.success !== undefined && ![0, 13].includes(body.success)) fail("upstream_rejected");
    if (body.wait_response !== true) {
      if (body.success !== 0 || (body.wait_response != null && body.wait_response !== false)) fail("invalid_response");
      return initial;
    }
    if (!boundedString(body.ticket_uuid, 256)) fail("invalid_ticket");
    const ticket = body.ticket_uuid, started = this.now(), deadline = started + 30_000;
    for (let attempt = 0; attempt < 20; attempt++) {
      const elapsed = this.now() - started;
      if (elapsed < 0 || this.now() >= deadline) break;
      const interval = attempt === 0 ? 250 : elapsed < 12_000 ? 1000 : elapsed < 20_000 ? 2000 : 5000;
      await this.sleep(Math.min(interval, deadline - this.now()));
      if (this.now() < started || this.now() >= deadline) break;
      const next = await this.post(66, {ticket_uuid: ticket}, undefined, deadline - this.now());
      if (this.now() < started || this.now() >= deadline) break;
      const poll = operationBody(next, true);
      // 66's code 2 means pending; nested code 2 means the original operation failed.
      // Missing outer success is only an envelope, never evidence of completion.
      if (poll.success !== undefined && ![0, 2, 13].includes(poll.success)) fail("invalid_poll_result");
      if (poll.fetched_data != null) {
        if ((poll.success !== undefined && poll.success !== 0) || !object(poll.fetched_data)) fail("invalid_poll_result");
        const resolved = operationBody(poll.fetched_data);
        if (resolved.success !== 0) fail("upstream_rejected");
        if (resolved.wait_response != null && resolved.wait_response !== false) fail("invalid_poll_result");
        return poll.fetched_data;
      }
    }
    fail("result_timeout");
  }

  async engineStatus() {
    const requestedAtMs = this.now();
    const response = await this.resolve(await this.post(21, {refresh_dtc: false, last_received_time: 0}));
    if (!object(response.body.car_status)) fail("gmone_status_missing");
    const timestamp = integer(response.timestamp);
    return {source: "gmone-direct", accountUuid: this.account.uuid, requestedAtMs,
      receivedAtMs: this.now(), serverResponseAtMs: timestamp !== null
        ? (timestamp < 1e11 ? timestamp * 1000 : timestamp) : null,
      rawStatus: response.body.car_status};
  }
}

const sleepMs = ms => new Promise(resolve => setTimeout(resolve, ms));

/** Returns ONLY a bounded server session, not credentials or the raw login response. */
export async function accountLogin(email, password, fetchFn = fetch) {
  if (typeof email !== "string" || !boundedString(email.trim(), 320) ||
      !boundedString(password, 1024)) fail("invalid_credentials");
  const client = new Protocol(null, fetchFn, Date.now, sleepMs);
  const response = await client.post(8, {}, {email: email.trim(), password});
  const login = response.login;
  if (!object(login) || !object(response.body) || integer(login.success) !== 0 || integer(response.body.success) !== 0) {
    // Same code as before; `explicit` marks a well-formed refusal (both success fields are integers) so a
    // remembered login is erased only for a real refusal, not for a damaged or incomplete reply.
    const error = new CommandError("login_rejected");
    error.explicit = object(login) && object(response.body) && integer(login.success) !== null && integer(response.body.success) !== null;
    throw error;
  }
  const uuid = boundedString(login.user_info_uuid, 128) ? login.user_info_uuid : login.user_info?.user_uuid;
  if (!boundedString(uuid, 128) || !boundedString(login.token_key, 4096) || !object(login.car_info)) fail("invalid_login_response");
  const vehicles = Object.keys(login.car_info);
  if (vehicles.length !== 1 || !boundedString(vehicles[0], 128)) fail("single_vehicle_required");
  const issuedAtMs = Date.now();
  return Object.freeze({version: 1, uuid, token: login.token_key, vehicleId: vehicles[0], vehicleCount: 1,
    issuedAtMs, expiresAtMs: issuedAtMs + ACCOUNT_TTL_MS});
}

function outcome(command, state, code, dispatched, failureStage) {
  const message = state === "server_responded"
    ? "멀티팩에서 명령 처리 성공을 반환했습니다. 실제 차량 동작은 별도로 확인해 주세요."
    : state === "unknown" ? "명령 완료를 확인하지 못했습니다. 이미 동작했을 수 있으므로 재전송하지 않고 차량 상태를 확인해 주세요." +
      (code === "session_expired" ? " 멀티팩 인증이 만료되어 다시 로그인해야 합니다." : "")
      : ({
        account_invalid_or_expired: "명령을 보내지 않았습니다. 멀티팩에 다시 로그인해 주세요.",
        session_expired: "명령을 보내지 않았습니다. 멀티팩 인증이 만료되어 다시 로그인해야 합니다.",
        unsupported_command: "지원하지 않는 차량 명령입니다.",
        live_state_not_fresh: "주행 상태 정보가 오래되었거나 시각을 확인할 수 없어 명령을 보내지 않았습니다.",
        motion_unknown: "주행 여부를 확인할 수 없어 명령을 보내지 않았습니다.",
        vehicle_not_stationary: "차량이 움직이는 상태이므로 명령을 보내지 않았습니다.",
        controls_active: "차량 제어가 활성화된 상태이므로 명령을 보내지 않았습니다.",
        engine_unknown: "시동 상태를 확인하지 못해 명령을 보내지 않았습니다.",
        engine_already_running: "이미 시동이 켜져 있어 원격 시동을 시작하지 않았습니다.",
        hood_unknown: "후드 상태를 확인하지 못해 원격 시동을 시작하지 않았습니다.",
        hood_open: "후드가 열려 있어 원격 시동을 시작하지 않았습니다.",
        remaining_starts_unknown: "원격 시동 가능 횟수를 확인하지 못했습니다.",
        no_remaining_starts: "원격 시동 가능 횟수가 없습니다.",
        not_remote_running: "원격 시동 상태가 아니므로 시동 종료 명령을 보내지 않았습니다.",
        before_send_failed: "명령 전 준비 작업에 실패하여 차량 명령을 보내지 않았습니다.",
        gmone_status_not_fresh: "멀티팩의 최근 직접 상태 응답을 확인하지 못해 명령을 보내지 않았습니다.",
      }[code] ?? "필요한 상태 또는 통신 응답을 확인하지 못해 차량 명령을 보내지 않았습니다.");
  return {ok: state === "server_responded", state, message, command: supported(command) ? command : null, code, dispatched,
    vehicleConfirmed: false, retryable: false, failureStage};
}

export async function executeCommand({command, account, liveState, beforeSend, now = Date.now, sleep = sleepMs} = {}, fetchFn = fetch) {
  let dispatched = false, stage = "guard";
  try {
    // Freeze inputs across awaits; parent must supply new trusted state on a new claim.
    account = object(account) ? {...account} : account;
    liveState = structuredClone(liveState);
    let guard = validateCommandGuard({command, account, liveState}, now());
    if (!guard.allowed && guard.code !== "gmone_status_required") return outcome(command, "blocked", guard.code, false, stage);
    const client = new Protocol(account, fetchFn, now, sleep);
    let gmoneStatus;
    if (engineCommand(command)) {
      stage = "preflight";
      gmoneStatus = await client.engineStatus();
      const waitStarted = now();
      if (!time(waitStarted) || !time(gmoneStatus.receivedAtMs) ||
          gmoneStatus.receivedAtMs < gmoneStatus.requestedAtMs || waitStarted < gmoneStatus.receivedAtMs ||
          gmoneStatus.serverResponseAtMs - gmoneStatus.receivedAtMs > MAX_SERVER_FUTURE_WAIT_MS) fail("gmone_status_not_fresh");
      // Wait for a small observed server lead, never grant clock-skew tolerance.
      if (time(gmoneStatus.serverResponseAtMs) && gmoneStatus.serverResponseAtMs > waitStarted) {
        await sleep(gmoneStatus.serverResponseAtMs - waitStarted);
        const afterWait = now();
        if (!time(afterWait) || afterWait < waitStarted || afterWait < gmoneStatus.serverResponseAtMs) fail("gmone_status_not_fresh");
      }
    }
    // A pending status read may have outlived either the telemetry or the session.
    stage = "guard";
    guard = validateCommandGuard({command, account, liveState, gmoneStatus}, now());
    if (!guard.allowed) return outcome(command, "blocked", guard.code, false, stage);
    if (beforeSend !== undefined) {
      stage = "before-send";
      if (typeof beforeSend !== "function") fail("before_send_invalid");
      try {
        const prepared = await beforeSend();
        if (prepared === false) fail("before_send_failed");
        if (object(prepared) && Object.hasOwn(prepared, "liveState")) liveState = structuredClone(prepared.liveState);
      }
      catch { fail("before_send_failed"); }
      stage = "guard";
      guard = validateCommandGuard({command, account, liveState, gmoneStatus}, now());
      if (!guard.allowed) return outcome(command, "blocked", guard.code, false, stage);
    }
    stage = "command-response";
    dispatched = true;
    const initial = await client.post(19, COMMAND_SPECS[command]);
    stage = "result-poll";
    const resolved = await client.resolve(initial);
    const body = resolved.body, spec = COMMAND_SPECS[command];
    for (const key of ["control_type", "request_option"]) {
      if (Object.hasOwn(body, key) && integer(body[key]) !== spec[key]) fail("command_response_mismatch");
    }
    return {...outcome(command, "server_responded", "command_accepted", true, null), resultCode: 0};
  } catch (error) {
    return outcome(command, dispatched ? "unknown" : "blocked",
      error instanceof CommandError ? error.code : "command_error", dispatched, stage);
  }
}
