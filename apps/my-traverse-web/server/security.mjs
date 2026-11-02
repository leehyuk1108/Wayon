const encoder = new TextEncoder();
export const SESSION_SECONDS = 30 * 24 * 3600;
export const COOKIE = '__Host-traverse';

export async function digest(value) {
  return Buffer.from(await crypto.subtle.digest('SHA-256', encoder.encode(value))).toString('hex');
}

export async function equal(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || !a || !b) return false;
  const [aa, bb] = await Promise.all([digest(a), digest(b)]);
  let result = 0;
  for (let i = 0; i < aa.length; i++) result |= aa.charCodeAt(i) ^ bb.charCodeAt(i);
  return result === 0;
}

export function randomToken() { return Buffer.from(crypto.getRandomValues(new Uint8Array(32))).toString('base64url'); }
export function json(value, status = 200, headers = {}) {
  return new Response(JSON.stringify(value), {status, headers: {
    'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store',
    'x-content-type-options': 'nosniff', ...headers,
  }});
}

export async function readJson(request, limit = 16384) {
  if (!request.headers.get('content-type')?.startsWith('application/json')) throw new Error('json_required');
  return JSON.parse((await readBytes(request,limit)).toString('utf8'));
}

export async function readBytes(request, limit) {
  if (Number(request.headers.get('content-length')) > limit) throw new Error('body_too_large');
  const reader = request.body?.getReader();
  if (!reader) throw new Error('body_required');
  const parts = []; let length = 0;
  while (true) {
    const {value, done} = await reader.read();
    if (done) break;
    length += value.length;
    if (length > limit) { await reader.cancel(); throw new Error('body_too_large'); }
    parts.push(value);
  }
  return Buffer.concat(parts);
}

export function sameOrigin(request, env) {
  const origin = env.PUBLIC_ORIGIN;
  return !!origin && new URL(request.url).origin === origin && request.headers.get('origin') === origin &&
    !['cross-site', 'same-site'].includes(request.headers.get('sec-fetch-site'));
}

export function sessionCookie(token, seconds = SESSION_SECONDS) {
  return `${COOKIE}=${token}; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=${seconds}`;
}

export async function sessionFor(request, env) {
  const token = (request.headers.get('cookie') || '').split(';').map(x => x.trim())
    .find(x => x.startsWith(COOKIE + '='))?.slice(COOKIE.length + 1);
  if (!token || !/^[\w-]{43}$/.test(token)) return null;
  return env.DB.prepare('SELECT * FROM sessions WHERE id = ? AND expires > ?')
    .bind(await digest(token), Date.now()).first();
}

export async function encrypt(value, secret) {
  const key = await encryptionKey(secret);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt({name:'AES-GCM',iv,additionalData:encoder.encode('traverse-account-v1')}, key, encoder.encode(JSON.stringify(value)));
  return Buffer.concat([iv, new Uint8Array(encrypted)]).toString('base64url');
}
export async function decrypt(value, secret) {
  const bytes = Buffer.from(value, 'base64url');
  const clear = await crypto.subtle.decrypt({name:'AES-GCM',iv:bytes.subarray(0,12),additionalData:encoder.encode('traverse-account-v1')}, await encryptionKey(secret), bytes.subarray(12));
  return JSON.parse(new TextDecoder().decode(clear));
}
async function encryptionKey(secret) {
  if (typeof secret !== 'string' || secret.length < 32) throw new Error('missing_encryption_key');
  return crypto.subtle.importKey('raw', await crypto.subtle.digest('SHA-256', encoder.encode(secret)), 'AES-GCM', false, ['encrypt','decrypt']);
}

export async function rateLimit(env, key, max, seconds) {
  const now = Date.now();
  const row = await env.DB.prepare(`INSERT INTO rate_limits(id,count,expires) VALUES(?,1,?)
    ON CONFLICT(id) DO UPDATE SET count=CASE WHEN expires < ? THEN 1 ELSE count+1 END,
      expires=CASE WHEN expires < ? THEN excluded.expires ELSE expires END RETURNING count`)
    .bind(key, now + seconds * 1000, now, now).first();
  return row.count <= max;
}
