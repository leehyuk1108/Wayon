import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';

const source = readFileSync(new URL('./snapshots.js', import.meta.url), 'utf8');
const HOUR = 3600000;
function fixture() {
  let now = Date.parse('2026-11-02T10:30:00Z'), reads = 0, puts = 0;
  let failGet = false, failPut = false, failDb = false;
  const store = new Map(), queries = [], photos = [{id: 'first'}];
  const days = [{date: '2026-11-02', count: 3}, {date: null, count: 1}];
  const context = vm.createContext({crypto, TextEncoder, URL, Request, Response,
    Date: class extends Date {static now() {return now;}}, console,
    authorize: () => true, authenticatedDeviceId: () => 'owner',
    boundedLimit: (v, d) => Number(v) || d, nowIso: () => new Date(now).toISOString(),
    json: (value, status = 200) => Response.json(value, {status}),
    historyJson: (value, type) => Response.json({...value, type}),
    fetchServerSnapshotList: async () => {throw Error('test server unavailable');},
  });
  vm.runInContext(source, context);
  const env = {SNAPSHOTS: {
    async get(key, type) {assert.equal(type, 'json'); if (failGet) throw Error('kv_get'); return store.get(key);},
    async put(key, value, options) {puts++; assert.equal(options.expirationTtl, 7200);
      if (failPut) throw Error('kv_put'); store.set(key, JSON.parse(value));},
  }, DB: {prepare(sql) {return {bind(...args) {return {async all() {
    queries.push({sql, args});
    if (sql.includes('GROUP BY')) {reads++; if (failDb) throw Error('db'); return {results: structuredClone(days)};}
    return {results: structuredClone(photos)};
  }};}};}}};
  return {context, env, store, days, photos, queries, stats: () => ({reads, puts}),
    setNow: value => {now = value;}, now: () => now,
    failures: (get, put, db) => {failGet = get; failPut = put; failDb = db;},
    call: (owner = 'owner') => context.snapshotListStats(env, owner),
  };
}

test('cache coalesces concurrent reads, includes NULL dates, and expires at the UTC hour', async () => {
  const f = fixture();
  const values = await Promise.all(Array.from({length: 30}, () => f.call()));
  assert.equal(f.stats().reads, 1);
  assert.equal(f.stats().puts, 1);
  assert.ok(values.every(v => v.total === 4 && v.days[1].date === null));
  await f.call(); assert.equal(f.stats().reads, 1);
  f.setNow(Math.floor(f.now() / HOUR) * HOUR + HOUR - 1);
  await f.call(); assert.equal(f.stats().reads, 1);
  f.setNow(f.now() + 1);
  await f.call(); assert.equal(f.stats().reads, 2);
  assert.equal(f.store.size, 2);
});

test('per-owner cache cannot leak another device summary and keys use a metadata namespace', async () => {
  const f = fixture();
  await f.call('owner-a'); f.days[0].count = 10; await f.call('owner-b');
  assert.equal((await f.call('owner-a')).total, 4);
  assert.equal((await f.call('owner-b')).total, 11);
  assert.equal(f.stats().reads, 2);
  assert.ok([...f.store.keys()].every(k => /^meta\/snapshot-stats\/v1\/[a-f0-9]{64}\/\d+$/.test(k)));
});

test('fresh isolates reuse valid KV and reject malformed, expired, future or wrong-owner summaries', async () => {
  const seed = fixture(); await seed.call();
  const [key, value] = [...seed.store.entries()][0];
  const cases = [value, {...value, deviceId:'other'}, {...value, version:2},
    {...value, computedAtMs: value.computedAtMs - HOUR}, {...value, computedAtMs: value.computedAtMs + 1},
    {...value, total:100}, {...value, days:[{date:'2026-11-02',count:-1}]},
    {...value, days:[{date:['2026-11-02'],count:4}]}, {...value, days:[value.days[0], value.days[0]], total:6},
    {...value, days:null}, {...value, days:[{date:null,count:1.5}], total:1.5}, null];
  for (const [i, item] of cases.entries()) {
    const f = fixture(); f.store.set(key, item);
    const result = await f.call();
    assert.equal(result.total, 4);
    assert.equal(f.stats().reads, i === 0 ? 0 : 1);
  }
});

test('KV outage does not amplify DB reads; failed puts retain local aggregates; DB failure is retryable', async () => {
  const f = fixture(); f.failures(true, false, false);
  await assert.rejects(f.call(), /kv_get/); await assert.rejects(f.call(), /kv_get/);
  assert.equal(f.stats().reads, 0);
  f.failures(false, true, false);
  assert.equal((await f.call()).total, 4); await f.call();
  assert.equal(f.stats().reads, 1);
  const g = fixture(); g.failures(false, false, true);
  await assert.rejects(g.call(), /db/);
  g.failures(false, false, false);
  assert.equal((await g.call()).total, 4);
  assert.equal(g.stats().reads, 2);
});

test('summary cache is bounded and empty galleries have a valid zero total', async () => {
  const f = fixture(); f.days.splice(0);
  for (let i = 0; i < 40; i++) assert.equal((await f.call('owner-' + i)).total, 0);
  assert.equal(vm.runInContext('snapshotStatsMemory.size', f.context), 32);
});

test('fresh photo list never aggregates or reads metadata KV, and cached summaries do not hide new photos', async () => {
  const f = fixture(); f.failures(true, false, false);
  const req = new Request('https://test/api/mobile/web-snapshots');
  assert.deepEqual(await (await f.context.handleWebSnapshots(req, f.env)).json(), {snapshots:[{id:'first'}]});
  assert.equal(f.stats().reads, 0);
  assert.equal(f.queries.length, 1);
  f.failures(false, false, false);
  const gallery = new Request('https://test/api/snapshots?date=2026-11-02');
  const before = await (await f.context.handleSnapshotsList(gallery, f.env)).json();
  f.photos.push({id:'new'}); f.days[0].count++;
  const after = await (await f.context.handleSnapshotsList(gallery, f.env)).json();
  assert.equal(after.snapshots.length, 2);
  assert.equal(after.total, before.total);
  assert.equal(after.statsComputedAt, before.statsComputedAt);
  assert.equal(after.statsExpiresAt, '2026-11-02T11:00:00.000Z');
  assert.equal(f.stats().reads, 1);
  assert.ok(f.queries.every(q => !/SELECT COUNT\(\*\) AS count FROM/.test(q.sql)));
  assert.ok(f.queries.filter(q => !q.sql.includes('GROUP BY')).every(q => q.args[0] === 'owner'));
});

test('legacy server-first path stays unchanged and never reads D1/KV on success', async () => {
  const f = fixture(); const value = {snapshots:[{id:'server'}],days:[],total:1};
  f.context.fetchServerSnapshotList = async () => value;
  assert.deepEqual(await (await f.context.handleSnapshotsList(new Request('https://test/api/snapshots'), f.env)).json(),
    {...value,type:'server'});
  assert.equal(f.queries.length,0); assert.equal(f.store.size,0);
});
