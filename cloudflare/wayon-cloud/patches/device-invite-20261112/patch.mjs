import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

// Applied on top of trip-vehicle-speed-20261111 (the active bundle since 2026-11-11).
export const BASELINE_SHA256 = '23c4a22573ef958fc57a513752553865c40514798009b69d1c57f9d32f399811';
export const OUTPUT_SHA256 = '351b044dbcd0e295fb7da59839d2a12e19eeede2a898034b577c1f3c38b42532';

// Lets another comma register itself from Carrot Web with a one-time invite that an owner device creates.
// - POST /api/devices/invites (device key): a random 32-character base32 code (160 bits), valid for
//   30 minutes and usable once. Only its SHA-256 is stored (migration.sql). A device registered with an
//   invite (recorded for good in wayon_device_origins) cannot create invites; a device holds at most three
//   unused codes and creates at most ten a day, checked in the same statement that stores the code.
// - POST /api/devices/register {deviceId, key, invite}: for a device ID that does not exist yet, spends the
//   invite and creates the device and its origin in one D1 batch whose later statements depend on the
//   spend, so a code registers exactly one device, a refused request writes nothing, and a code from a
//   revoked creator no longer works. Existing devices, the legacy upload token and the reissue path are
//   unchanged; a retry with the same device ID and key keeps taking the existing same-key path, whatever
//   happened to the code. An invite authorizes a registration; it does not prove the comma owns the ID.
// Codes and keys are never logged; every lookup is by primary key or index on small tables.
const helpers = String.raw`var DEVICE_INVITE_PATH = "/api/devices/invites";
var DEVICE_INVITE_TTL_MS = 30 * 60 * 1e3;
var DEVICE_INVITE_ACTIVE_LIMIT = 3;
var DEVICE_INVITE_DAILY_LIMIT = 10;
var DEVICE_INVITE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
function validDeviceInvite(value) {
  return typeof value === "string" && /^[A-Z2-7]{32}$/.test(value);
}
__name(validDeviceInvite, "validDeviceInvite");
function newDeviceInviteCode() {
  // 256 is a multiple of 32, so masking each random byte keeps every character uniform.
  return Array.from(crypto.getRandomValues(new Uint8Array(32)), (byte) => DEVICE_INVITE_ALPHABET[byte & 31]).join("");
}
__name(newDeviceInviteCode, "newDeviceInviteCode");
async function handleDeviceInviteCreate(request, env) {
  try {
    const identity = await authenticateDeviceKey(request, env);
    if (!identity) return json({ error: "unauthorized" }, 401);
    const invited = await env.DB.prepare(
      "SELECT 1 AS invited FROM wayon_device_origins WHERE device_id = ?"
    ).bind(identity.deviceId).first();
    if (invited) return json({ error: "invite_not_allowed" }, 403);
    const now = Date.now();
    const nowText = new Date(now).toISOString();
    const code = newDeviceInviteCode();
    const expiresAt = new Date(now + DEVICE_INVITE_TTL_MS).toISOString();
    // One statement, so concurrent requests cannot pass the limits together.
    const written = await env.DB.prepare(
      "INSERT INTO wayon_device_invites (code_hash, created_by, created_at, expires_at) SELECT ?, ?, ?, ? " +
      "WHERE (SELECT COUNT(*) FROM wayon_device_invites WHERE created_by = ? AND used_at IS NULL AND expires_at > ?) < ? " +
      "AND (SELECT COUNT(*) FROM wayon_device_invites WHERE created_by = ? AND created_at > ?) < ?"
    ).bind(await sha256Hex(code), identity.deviceId, nowText, expiresAt,
      identity.deviceId, nowText, DEVICE_INVITE_ACTIVE_LIMIT,
      identity.deviceId, new Date(now - 864e5).toISOString(), DEVICE_INVITE_DAILY_LIMIT).run();
    if (written.meta?.changes !== 1) return json({ error: "invite_limit" }, 429);
    return json({ ok: true, code, expiresAt });
  } catch {
    return json({ error: "invite_unavailable" }, 503);
  }
}
__name(handleDeviceInviteCreate, "handleDeviceInviteCreate");
async function registerInvitedDevice(env, deviceId, keyHash, invite, diagnostic) {
  if (!validDeviceInvite(invite)) {
    diagnostic.cause = "invite_invalid";
    return [{ error: "invalid_device_invite" }, 403];
  }
  const now = new Date().toISOString();
  const codeHash = await sha256Hex(invite);
  diagnostic.stage = "invite_write";
  // One transaction. The invite is spent only while it is unused and unexpired, its creator is still an
  // active device and this device ID is free; the device and its origin rows are created only from the
  // invite this request just spent with this device ID and key, so a refused request writes nothing.
  const spent = "SELECT 1 FROM wayon_device_invites WHERE code_hash = ? AND used_by = ? AND used_key_hash = ? AND used_at = ?";
  const results = await env.DB.batch([
    env.DB.prepare(
      "UPDATE wayon_device_invites SET used_at = ?, used_by = ?, used_key_hash = ? " +
      "WHERE code_hash = ? AND used_at IS NULL AND expires_at > ? " +
      "AND EXISTS (SELECT 1 FROM wayon_devices WHERE device_id = wayon_device_invites.created_by AND revoked_at IS NULL) " +
      "AND NOT EXISTS (SELECT 1 FROM wayon_devices WHERE device_id = ?)"
    ).bind(now, deviceId, keyHash, codeHash, now, deviceId),
    env.DB.prepare(
      "INSERT INTO wayon_devices (device_id, key_hash, created_at, updated_at, last_seen_at, revoked_at) " +
      "SELECT ?, ?, ?, ?, ?, NULL WHERE EXISTS (" + spent + ") ON CONFLICT(device_id) DO NOTHING"
    ).bind(deviceId, keyHash, now, now, now, codeHash, deviceId, keyHash, now),
    env.DB.prepare(
      "INSERT INTO wayon_device_origins (device_id, invited_by, invited_at) " +
      "SELECT ?, created_by, ? FROM wayon_device_invites WHERE code_hash = ? AND used_by = ? AND used_key_hash = ? AND used_at = ? " +
      "ON CONFLICT(device_id) DO NOTHING"
    ).bind(deviceId, now, codeHash, deviceId, keyHash, now),
  ]);
  if (results[1]?.meta?.changes !== 1) {
    diagnostic.cause = "invite_rejected";
    return [{ error: "invalid_device_invite" }, 403];
  }
  diagnostic.committed = true;
  diagnostic.stage = "complete";
  return [{ ok: true, deviceId }, 200];
}
__name(registerInvitedDevice, "registerInvitedDevice");
`;

const steps = [
  ['async function handleDeviceRegistration(request, env) {\n',
   helpers + 'async function handleDeviceRegistration(request, env) {\n'],
  ['    // New identities require explicit provisioning; re-keying an existing\n' +
   '    // device must use the separately verified device-proof reissue endpoint.\n' +
   '    if (!existing && !legacyAuthorized) {\n',
   '    // New identities require explicit provisioning (an owner device\'s one-time invite or the legacy\n' +
   '    // upload token); re-keying an existing device must use the separately verified device-proof\n' +
   '    // reissue endpoint.\n' +
   '    if (!existing && !legacyAuthorized && payload.invite !== undefined) {\n' +
   '      const [body, status] = await registerInvitedDevice(env, deviceId, keyHash, payload.invite, diagnostic);\n' +
   '      return finish(body, status);\n' +
   '    }\n' +
   '    if (!existing && !legacyAuthorized) {\n'],
  ['    if (request.method === "POST" && pathname === DEVICE_REGISTER_PATH) {\n',
   '    if (request.method === "POST" && pathname === DEVICE_INVITE_PATH) {\n' +
   '      return handleDeviceInviteCreate(request, env);\n' +
   '    }\n' +
   '    if (request.method === "POST" && pathname === DEVICE_REGISTER_PATH) {\n'],
];

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  let output = source;
  for (const [anchor, replacement] of steps) output = replaceOnce(output, anchor, replacement);
  if (OUTPUT_SHA256 !== 'PENDING') assert.equal(sha256(output), OUTPUT_SHA256, 'Unexpected candidate bundle');
  return output;
}

export function unpatch(source) {
  if (OUTPUT_SHA256 !== 'PENDING') assert.equal(sha256(source), OUTPUT_SHA256, 'Refusing unknown candidate bundle');
  let output = source;
  for (const [anchor, replacement] of [...steps].reverse()) output = replaceOnce(output, replacement, anchor);
  assert.equal(sha256(output), BASELINE_SHA256, 'Baseline restoration mismatch');
  return output;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, output] = process.argv.slice(2);
  assert.ok(input && output && resolve(input) !== resolve(output), 'Specify distinct baseline and new output paths');
  const result = patch(readFileSync(input, 'utf8'));
  writeFileSync(output, result, {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({baseline: BASELINE_SHA256, candidate: sha256(result)}));
}
