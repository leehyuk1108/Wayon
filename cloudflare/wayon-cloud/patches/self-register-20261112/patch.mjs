import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

// Applied on top of device-invite-20261112 (active since 2026-11-12, uses its wayon_device_origins table).
export const BASELINE_SHA256 = '255084947ea55d92f6e54d8629ce24a641029b71a0f7d6b15160e498909b7b46';
export const OUTPUT_SHA256 = '2e8bb89f8dfeb7f0d658d0f133ddfeb2c60d73d3b9fa1ecff6199cbb4237997e';

// Lets a comma register itself and get its own key, with no owner involved.
// POST /api/devices/self-register {deviceId, key, requestId, proof}:
// - proof is a short-lived JWT the comma signs with its own comma device key (openpilot Api.get_token),
//   naming this purpose, request and the SHA-256 of the new key. The Worker asks comma's device API with
//   that JWT for the device (which also checks it), requires the same dongle ID and verifies the signature
//   with the public key comma returns (PEM SPKI or OpenSSH, RS256 or ES256). So only a real comma, holding
//   its private key, can register its own ID, and a copied proof is useless without the matching key.
// - A device ID that exists keeps the existing contract: same active key 200 (a retry), otherwise 409.
// - At most five devices register this way in any 24 hours and five in total (the account-wide D1 free
//   tier is shared), counted in the same statement that creates the device; the origin is recorded as
//   'self' in wayon_device_origins, so such a device cannot create invites either.
// Nothing from comma's answer is stored or logged except the check result; keys and proofs are never logged.
const helpers = String.raw`var DEVICE_SELF_REGISTER_PATH = "/api/devices/self-register";
var SELF_REGISTER_PURPOSE = "wayon-key-register-v1";
var SELF_REGISTER_DAILY_LIMIT = 5;
var SELF_REGISTER_TOTAL_LIMIT = 5;
function selfRegisterBytes(value) {
  return Uint8Array.from(atob(value.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));
}
__name(selfRegisterBytes, "selfRegisterBytes");
function selfRegisterJson(value) {
  return JSON.parse(new TextDecoder().decode(selfRegisterBytes(value)));
}
__name(selfRegisterJson, "selfRegisterJson");
async function selfRegisterPublicKey(publicKey, alg) {
  if (typeof publicKey !== "string" || publicKey.length > 8192) throw new Error("key");
  const algorithm = alg === "RS256" ? { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" } : { name: "ECDSA", namedCurve: "P-256", hash: "SHA-256" };
  const pem = publicKey.match(/^-----BEGIN PUBLIC KEY-----\s*([A-Za-z0-9+/=\s]+?)\s*-----END PUBLIC KEY-----\s*$/);
  if (pem) {
    const der = Uint8Array.from(atob(pem[1].replace(/\s+/g, "")), (c) => c.charCodeAt(0));
    return [await crypto.subtle.importKey("spki", der, algorithm, false, ["verify"]), algorithm];
  }
  const [type, encoded] = publicKey.trim().split(/\s+/);
  const bytes = Uint8Array.from(atob(encoded || ""), (c) => c.charCodeAt(0));
  let offset = 0;
  const field = () => {
    if (offset + 4 > bytes.length) throw new Error("key");
    const size = new DataView(bytes.buffer).getUint32(offset);
    offset += 4;
    if (offset + size > bytes.length) throw new Error("key");
    const out = bytes.slice(offset, offset + size);
    offset += size;
    return out;
  };
  const b64url = (value) => btoa(String.fromCharCode(...value)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  if (new TextDecoder().decode(field()) !== type) throw new Error("key");
  let jwk;
  if (type === "ssh-rsa" && alg === "RS256") {
    const exponent = field(), modulus = field();
    const n = modulus[0] === 0 ? modulus.slice(1) : modulus;
    if (offset !== bytes.length || n.length < 256 || n.length > 512) throw new Error("key");
    jwk = { kty: "RSA", e: b64url(exponent), n: b64url(n), alg, ext: true };
  } else if (type === "ecdsa-sha2-nistp256" && alg === "ES256") {
    const curve = new TextDecoder().decode(field()), point = field();
    if (offset !== bytes.length || curve !== "nistp256" || point.length !== 65 || point[0] !== 4) throw new Error("key");
    jwk = { kty: "EC", crv: "P-256", x: b64url(point.slice(1, 33)), y: b64url(point.slice(33)), ext: true };
  } else {
    throw new Error("key");
  }
  return [await crypto.subtle.importKey("jwk", jwk, algorithm, false, ["verify"]), algorithm];
}
__name(selfRegisterPublicKey, "selfRegisterPublicKey");
async function verifySelfRegisterProof(proof, deviceId, requestId, keyHash, diagnostic) {
  const reject = (cause) => { diagnostic.cause = cause; return "rejected"; };
  diagnostic.stage = "proof_claims";
  let parts, header, payload;
  try {
    if (typeof proof !== "string" || proof.length > 4096 || !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(proof)) return reject("proof_format");
    parts = proof.split(".");
    header = selfRegisterJson(parts[0]);
    payload = selfRegisterJson(parts[1]);
  } catch {
    return reject("proof_parse");
  }
  if (!["RS256", "ES256"].includes(header?.alg) || header.crit || header.jku || header.jwk || header.x5u || header.x5c) return reject("proof_header");
  const claims = payload?.wayon;
  if (payload?.identity !== deviceId || claims?.purpose !== SELF_REGISTER_PURPOSE || claims.requestId !== requestId || claims.newKeyHash !== keyHash) {
    return reject("proof_binding");
  }
  const now = Date.now() / 1e3;
  const { iat, nbf, exp } = payload;
  if (![iat, nbf, exp].every(Number.isFinite) || exp <= now || iat > now + 30 || nbf > now + 30 || exp <= iat || exp - iat > 300 || now - iat > 300) {
    return reject("proof_time");
  }
  let info;
  try {
    diagnostic.stage = "authority_fetch";
    // Never follow redirects carrying the device JWT; non-2xx answers fail closed.
    const response = await fetch("https://api.commadotai.com/v1.1/devices/" + deviceId + "/", {
      headers: { Authorization: "JWT " + proof }, redirect: "manual", signal: AbortSignal.timeout(8e3)
    });
    diagnostic.authorityStatus = response.status;
    if ([401, 403, 404].includes(response.status)) return reject("authority_rejected");
    if (!response.ok) {
      diagnostic.cause = "authority_http";
      return "unavailable";
    }
    const text = await response.text();
    if (text.length > 32768) throw new Error("size");
    info = JSON.parse(text);
  } catch {
    if (diagnostic.cause === "none") diagnostic.cause = "authority_unavailable";
    return "unavailable";
  }
  try {
    diagnostic.stage = "authority_identity";
    if (info?.dongle_id !== deviceId) return reject("authority_identity_mismatch");
    diagnostic.stage = "authority_key";
    const [key, algorithm] = await selfRegisterPublicKey(info.public_key, header.alg);
    diagnostic.stage = "proof_signature";
    const ok = await crypto.subtle.verify(algorithm, key, selfRegisterBytes(parts[2]), new TextEncoder().encode(parts[0] + "." + parts[1]));
    return ok ? "verified" : reject("signature_mismatch");
  } catch {
    return reject(diagnostic.stage === "authority_key" ? "authority_key_invalid" : "signature_error");
  }
}
__name(verifySelfRegisterProof, "verifySelfRegisterProof");
async function handleDeviceSelfRegister(request, env) {
  const audit = createKeyDiagnostic("register");
  const diagnostic = audit.state;
  const finish = (body, status = 200) => audit.finish(json(body, status), body.error || "ok");
  try {
    const payload = await request.json().catch(() => null);
    diagnostic.stage = "request_fields";
    const deviceId = String(payload?.deviceId || "").trim();
    const key = String(payload?.key || "").trim();
    const requestId = String(payload?.requestId || "");
    if (!payload || typeof payload !== "object" || Array.isArray(payload) || !/^[0-9a-f]{16}$/.test(deviceId)
        || !validWayonKey(key) || !/^[A-Za-z0-9_-]{16,64}$/.test(requestId)) {
      diagnostic.cause = "invalid_fields";
      return finish({ error: "invalid_device_registration" }, 400);
    }
    await audit.identify(deviceId);
    const keyHash = await sha256Hex(key);
    diagnostic.stage = "device_lookup";
    const existing = await env.DB.prepare("SELECT key_hash, revoked_at FROM wayon_devices WHERE device_id = ?").bind(deviceId).first();
    if (existing) {
      // A retry after a lost reply: the comma already holds this exact active key.
      if (!existing.revoked_at && constantTimeEqual(existing.key_hash || "", keyHash)) return finish({ ok: true, deviceId });
      diagnostic.cause = "registered_key_mismatch";
      return finish({ error: "device_already_registered" }, 409);
    }
    const verdict = await verifySelfRegisterProof(payload.proof, deviceId, requestId, keyHash, diagnostic);
    if (verdict === "unavailable") return finish({ error: "device_proof_unavailable" }, 503);
    if (verdict !== "verified") return finish({ error: "device_proof_rejected" }, 403);
    const now = new Date().toISOString();
    diagnostic.stage = "registration_write";
    const results = await env.DB.batch([
      env.DB.prepare(
        "INSERT INTO wayon_devices (device_id, key_hash, created_at, updated_at, last_seen_at, revoked_at) SELECT ?, ?, ?, ?, ?, NULL " +
        "WHERE (SELECT COUNT(*) FROM wayon_device_origins WHERE invited_by = 'self') < ? " +
        "AND (SELECT COUNT(*) FROM wayon_device_origins WHERE invited_by = 'self' AND invited_at > ?) < ? " +
        "ON CONFLICT(device_id) DO NOTHING"
      ).bind(deviceId, keyHash, now, now, now, SELF_REGISTER_TOTAL_LIMIT, new Date(Date.now() - 864e5).toISOString(), SELF_REGISTER_DAILY_LIMIT),
      env.DB.prepare(
        "INSERT INTO wayon_device_origins (device_id, invited_by, invited_at) SELECT ?, 'self', ? " +
        "WHERE EXISTS (SELECT 1 FROM wayon_devices WHERE device_id = ? AND key_hash = ? AND created_at = ?) ON CONFLICT(device_id) DO NOTHING"
      ).bind(deviceId, now, deviceId, keyHash, now),
    ]);
    if (results[0]?.meta?.changes === 1) {
      diagnostic.committed = true;
      diagnostic.stage = "complete";
      return finish({ ok: true, deviceId });
    }
    // Not created: another request created this ID meanwhile, or the limits hold.
    const raced = await env.DB.prepare("SELECT key_hash, revoked_at FROM wayon_devices WHERE device_id = ?").bind(deviceId).first();
    if (raced) {
      if (!raced.revoked_at && constantTimeEqual(raced.key_hash || "", keyHash)) return finish({ ok: true, deviceId });
      diagnostic.cause = "registered_key_mismatch";
      return finish({ error: "device_already_registered" }, 409);
    }
    diagnostic.cause = "self_register_limit";
    return finish({ error: "self_register_limit" }, 429);
  } catch (error) {
    diagnostic.cause = safeFailure(error);
    return finish({ error: "registration_unavailable" }, 503);
  }
}
__name(handleDeviceSelfRegister, "handleDeviceSelfRegister");
`;

const steps = [
  ['async function handleDeviceRegistration(request, env) {\n', helpers + 'async function handleDeviceRegistration(request, env) {\n'],
  ['    if (request.method === "POST" && pathname === DEVICE_INVITE_PATH) {\n',
   '    if (request.method === "POST" && pathname === DEVICE_SELF_REGISTER_PATH) {\n' +
   '      return handleDeviceSelfRegister(request, env);\n' +
   '    }\n' +
   '    if (request.method === "POST" && pathname === DEVICE_INVITE_PATH) {\n'],
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
