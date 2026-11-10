import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';
import {test} from 'node:test';
import {patch, unpatch, BASELINE_SHA256, OUTPUT_SHA256} from './patch.mjs';
import {sha256} from '../fast-vehicle-state-20261028/patch.mjs';
import {payload} from '../parking-display-20261104/fixture.mjs';

// Private copies of the active production modules (downloaded read-only); not committed.
const root = process.env.WAYON_ACTIVE_MODULE_DIR || '/Users/hyuklee/Documents/my-traverse-web-20261110';
const require = createRequire(import.meta.url);
const {Miniflare} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/Documents/sunnypilot/apps/my-traverse-web/node_modules/miniflare');
const baseline = readFileSync(join(root, 'stage-candidate.worker.js'), 'utf8');
const KEY = 'wayon_' + 'a'.repeat(48);
const hash = value => createHash('sha256').update(value).digest('hex');

test('patch is byte-exact and reversible against the active bundle', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  const candidate = patch(baseline);
  assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
});

async function fixture(script) {
  const modules = [{type: 'ESModule', path: '/isolated/worker.js', contents: script}];
  for (const name of ['key_diagnostics.mjs', 'device_reissue.mjs']) {
    modules.push({type: 'ESModule', path: '/isolated/' + name, contents: readFileSync(join(root, 'stage-baseline-' + name), 'utf8')});
  }
  const mf = new Miniflare({modules, modulesRoot: '/isolated', compatibilityDate: '2026-05-14',
    d1Databases: {DB: 'parking-place-isolated'}, kvNamespaces: ['SNAPSHOTS'],
    bindings: {WAYON_SERVER_SYNC_TOKEN: 'fixture-sync', WAYON_VIEW_TOKEN: 'fixture-view', WAYON_AI_READ_TOKEN: 'fixture-ai',
      WAYON_AI_DEVICE_ID: 'owner', WAYON_GMONE_TOKEN: 'fixture-gmone', WAYON_PARKING_NOTIFY_TOKEN: 'fixture-notify'},
    serviceBindings: {ASSETS: () => new Response(null, {status: 404})},
    outboundService: () => new Response(null, {status: 599})});
  const db = await mf.getD1Database('DB');
  await db.exec('CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT,last_seen_at TEXT);');
  await db.prepare('INSERT INTO wayon_devices VALUES(?,?,NULL,?)').bind('owner', hash(KEY), 'unchanged').run();
  const call = async (path, key, method = 'GET', value) => {
    const headers = {authorization: 'Bearer ' + key, ...(value ? {'content-type': 'application/json'} : {})};
    const r = await mf.dispatchFetch('https://isolated.test' + path, {method, headers, ...(value ? {body: JSON.stringify(value)} : {})});
    const raw = await r.text();
    return {status: r.status, body: raw ? JSON.parse(raw) : null};
  };
  return {dispose: () => mf.dispose(),
    publish: value => call('/api/parking/display', 'fixture-notify', 'POST', value),
    latest: () => call('/api/parking/latest', KEY)};
}

const withPlace = (place, generatedAt) => {
  const value = payload('owner');
  value.generatedAt = generatedAt;
  if (place !== undefined) value.observation.result.inspection.place = place;
  return value;
};

test('the patched worker keeps a valid place, rejects an invalid one and still accepts results without it', async () => {
  const f = await fixture(patch(baseline));
  try {
    const place = {setting: 'indoor', level: 'underground', area: 'parking_structure'};
    let r = await f.publish(withPlace({...place, private: 'dropped'}, '2026-11-10T08:00:00.000+00:00'));
    assert.equal(r.status, 200);
    r = await f.latest();
    assert.equal(r.status, 200);
    assert.deepEqual(r.body.observation.result.inspection.place, place);
    for (const bad of [{...place, area: 'garage'}, {setting: 'indoor'}, 'street', null]) {
      r = await f.publish(withPlace(bad, '2026-11-10T08:01:00.000+00:00'));
      assert.notEqual(r.status, 200, JSON.stringify(bad));
    }
    assert.deepEqual((await f.latest()).body.observation.result.inspection.place, place, 'a rejected display never replaces the stored one');
    r = await f.publish(withPlace(undefined, '2026-11-10T08:02:00.000+00:00'));
    assert.equal(r.status, 200);
    const inspection = (await f.latest()).body.observation.result.inspection;
    assert.equal(Object.hasOwn(inspection, 'place'), false);
    assert.equal(inspection.readings[0].text, '203');
  } finally { await f.dispose(); }
});

test('without the patch the active worker silently drops the place', async () => {
  const f = await fixture(baseline);
  try {
    const r = await f.publish(withPlace({setting: 'outdoor', level: 'ground', area: 'street'}, '2026-11-10T08:00:00.000+00:00'));
    assert.equal(r.status, 200);
    assert.equal(Object.hasOwn((await f.latest()).body.observation.result.inspection, 'place'), false);
  } finally { await f.dispose(); }
});
