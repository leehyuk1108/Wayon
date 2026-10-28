import assert from 'node:assert/strict';
import {createHash, webcrypto} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {DatabaseSync} from 'node:sqlite';
import vm from 'node:vm';
import {patch, replaceOnce} from './patch.mjs';

export const baselinePath = process.env.WAYON_FAST_STATE_BASELINE;
assert.ok(baselinePath, 'Set WAYON_FAST_STATE_BASELINE to the private pinned export');
export const baseline = readFileSync(baselinePath, 'utf8');
export const candidate = patch(baseline);
export const NOW = Date.parse('2026-10-28T11:00:00.000Z');
export const DEVICE = 'test-device-one';
export const KEY = 'wayon_' + 'a'.repeat(40);
export const OTHER_KEY = 'wayon_' + 'b'.repeat(40);
export const COLLECTOR = 'synthetic-collector-token';
export const hash = value => createHash('sha256').update(value).digest('hex');
export const iso = delta => new Date(NOW + delta).toISOString();
export const payload = (overrides = {}) => ({
  schemaVersion: 'wayon-gmone-v1', source: 'gmone-direct-android',
  collectedAt: iso(-1000), vehicleUpdatedAt: iso(-10000), status: {fuel: '63', locked: false},
  ...overrides,
});

// Only unrelated private companion-module imports are stubbed. The production
// router, header stripping, SHA256 device-key lookup and GMOne handlers execute.
export function executable(source) {
  source = replaceOnce(source,
    'import { createKeyDiagnostic, safeFailure } from "./key_diagnostics.mjs";',
    'const createKeyDiagnostic = () => { throw new Error("unrelated path"); }; const safeFailure = () => "test-only";');
  source = replaceOnce(source,
    'import { handleDeviceReissue } from "./device_reissue.mjs";',
    'const handleDeviceReissue = () => { throw new Error("unrelated path"); };');
  return source;
}

class BodyRequest extends Request {
  constructor(input, init = {}) { super(input, {...init, ...(init.body ? {duplex: 'half'} : {})}); }
}

export function load(source = candidate, jsonOverride = undefined) {
  class Clock extends Date { static now() { return NOW; } }
  const context = vm.createContext({
    Request: BodyRequest, Response, Headers, URL, Date: Clock,
    TextEncoder, TextDecoder, Uint8Array, crypto: webcrypto,
    fetch: () => { throw new Error('Remote fetch is forbidden in fast-state tests'); },
    ...(jsonOverride ? {JSON: jsonOverride} : {}),
  });
  const script = executable(source).replace(/export \{[\s\S]*$/, '') +
    '\nglobalThis.probe = {worker: worker_default, handleGmoneStatus, latestGmoneStatus};';
  vm.runInContext(script, context);
  return context.probe;
}

export function request(method = 'POST', body = payload(), headers = {}, query = '') {
  return new BodyRequest(`https://fast-state.test/api/gmone/status${query}`, {
    method,
    headers: {authorization: `Bearer ${KEY}`, 'content-type': 'application/json', ...headers},
    ...(method === 'POST' ? {body: typeof body === 'string' || body instanceof ReadableStream || body instanceof Uint8Array ? body : JSON.stringify(body)} : {}),
  });
}

export const schema = `
CREATE TABLE wayon_devices (device_id TEXT PRIMARY KEY, key_hash TEXT, revoked_at TEXT);
CREATE TABLE gmone_latest (id TEXT PRIMARY KEY, source TEXT NOT NULL, collected_at TEXT NOT NULL,
  vehicle_updated_at TEXT, payload_json TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE gmone_refresh_requests (id TEXT PRIMARY KEY, requested_at TEXT NOT NULL, completed_at TEXT);
`;

export function sqliteEnv() {
  const sqlite = new DatabaseSync(':memory:');
  sqlite.exec(schema);
  sqlite.prepare('INSERT INTO wayon_devices VALUES (?, ?, NULL)').run(DEVICE, hash(KEY));
  sqlite.prepare('INSERT INTO wayon_devices VALUES (?, ?, NULL)').run('other-device', hash(OTHER_KEY));
  const calls = [];
  const DB = {prepare(sql) {
    return {bind(...args) {
      return {
        async first() { calls.push({sql, args, method: 'first'}); return sqlite.prepare(sql).get(...args) || null; },
        async run() {
          calls.push({sql, args, method: 'run'});
          const result = sqlite.prepare(sql).run(...args);
          return {success: true, meta: {changes: Number(result.changes)}};
        },
      };
    }};
  }};
  return {
    env: {DB, SNAPSHOTS: {}, WAYON_GMONE_TOKEN: COLLECTOR, WAYON_LEGACY_FIREBASE_DEVICE_ID: 'collector-device'},
    sqlite, calls,
    stored: (device = DEVICE) => sqlite.prepare('SELECT * FROM gmone_latest WHERE id = ?').get(device),
    refresh: (device = DEVICE) => sqlite.prepare('SELECT * FROM gmone_refresh_requests WHERE id = ?').get(device),
  };
}

export function mockEnv({writeResult = {success: true, meta: {changes: 1}}, writeError = false, ackError = false, ackResult = {success: true, meta: {changes: 1}}, authError = false, readError = false, row = null} = {}) {
  const calls = [];
  const DB = {prepare(sql) { return {bind(...args) {
    return {
      async first() {
        calls.push({sql, args, method: 'first'});
        if (sql.includes('FROM wayon_devices')) {
          if (authError) throw new Error('private auth DB failure');
          return args[0] === hash(KEY) ? {device_id: DEVICE} : null;
        }
        if (sql.includes('FROM gmone_latest')) { if (readError) throw new Error('private DB failure'); return row; }
        throw new Error('Unexpected read');
      },
      async run() {
        calls.push({sql, args, method: 'run'});
        if (sql.includes('INSERT INTO gmone_latest')) {
          if (writeError) throw new Error('private DB failure');
          return writeResult;
        }
        if (sql.includes('UPDATE gmone_refresh_requests')) {
          if (ackError) throw new Error('private DB failure');
          return ackResult;
        }
        throw new Error('Unexpected write');
      },
    };
  }}; }};
  return {env: {DB, SNAPSHOTS: {}, WAYON_GMONE_TOKEN: COLLECTOR, WAYON_LEGACY_FIREBASE_DEVICE_ID: 'collector-device'}, calls};
}
