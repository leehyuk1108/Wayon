import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import {patch, patchModules, sha256, BASELINE_SHA256, OUTPUT_SHA256} from './patch.mjs';
import {baseline, retained} from './fixture.mjs';
const require = createRequire(import.meta.url);
const {Miniflare, convertV4MiniflareOptions} = require(process.env.MINIFLARE_MODULE ||
  '/Users/hyuklee/.npm/_npx/32026684e21afda6/node_modules/miniflare');
const hash = value => createHash('sha256').update(value).digest('hex');
const KEY = 'wayon_' + 'a'.repeat(48), OTHER_KEY = 'wayon_' + 'b'.repeat(48);
const REVOKED_KEY = 'wayon_' + 'c'.repeat(48), PATH = '/api/mobile/web-snapshots';
const time = n => new Date(Date.UTC(2026, 10, 1) + n * 60000).toISOString();

async function fixture() {
  let outbound = 0;
  const modules = Object.entries(patchModules(baseline, retained)).map(([name, contents]) =>
    ({type:'ESModule',path:'/isolated/' + name,contents}));
  const options = {modules, modulesRoot:'/isolated', compatibilityDate:'2026-05-14', cf:false,
    d1Databases:{DB:'gallery-isolated'},kvNamespaces:['SNAPSHOTS'],
    bindings:{WAYON_VIEW_TOKEN:'isolated-view',WAYON_GMONE_TOKEN:'isolated-collector',
      WAYON_AI_TOKEN:'isolated-ai',WAYON_AI_DEVICE_ID:'owner',WAYON_SERVER_SYNC_TOKEN:'isolated-sync'},
    serviceBindings:{ASSETS:() => new Response('',{status:404})},
    outboundService:() => {outbound++; return new Response(null,{status:599});},
  };
  const mf = new Miniflare(convertV4MiniflareOptions ? convertV4MiniflareOptions(options) : options);
  try {
    const db = await mf.getD1Database('DB'), kv = await mf.getKVNamespace('SNAPSHOTS');
    await db.exec('CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT,last_seen_at TEXT); ' +
      'CREATE TABLE snapshots(id TEXT PRIMARY KEY,device_id TEXT,camera TEXT,captured_at TEXT,kv_key TEXT,size_bytes INTEGER,created_at TEXT); ' +
      'CREATE INDEX snapshots_device_time ON snapshots(device_id,captured_at DESC); ' +
      'CREATE TABLE impact_events(id TEXT PRIMARY KEY,device_id TEXT,wide_snapshot_id TEXT,driver_snapshot_id TEXT,severity TEXT,peak_dynamic_g REAL,peak_total_g REAL,detected_at TEXT); ' +
      'CREATE INDEX impact_wide ON impact_events(wide_snapshot_id); ' +
      'CREATE INDEX impact_driver ON impact_events(driver_snapshot_id);');
    for (const [id,key,revoked] of [['owner',KEY,null],['other',OTHER_KEY,null],['revoked',REVOKED_KEY,time(0)]]) {
      await db.prepare('INSERT INTO wayon_devices VALUES(?,?,?,?)').bind(id,hash(key),revoked,'unchanged').run();
    }
    for (const table of ['wayon_devices','snapshots','impact_events']) for (const action of ['UPDATE','DELETE']) {
      await db.exec(`CREATE TRIGGER no_${table}_${action} BEFORE ${action} ON ${table} BEGIN SELECT RAISE(ABORT,'read_only_violation'); END;`);
    }
    return {db,kv,dispose:() => mf.dispose(),outbound:() => outbound,
      async insert(count, owner='owner', start=0) {
        for (let begin=0; begin<count; begin+=100) {
          await db.batch(Array.from({length:Math.min(100,count-begin)},(_,i) => {
            const n = start + begin + i;
            return db.prepare('INSERT INTO snapshots VALUES(?,?,?,?,?,?,?)').bind(
              owner+'-'+n,owner,'wide',time(n),'image/'+owner+'/'+n,123,time(n));
          }));
        }
      },
      async call(query='',{key=KEY,method='GET',path=PATH,headers={}}={}) {
        const h = new Headers(headers); if (key !== null) h.set('authorization','Bearer '+key);
        const r = await mf.dispatchFetch('https://isolated.test'+path+query,{method,headers:h});
        const text = await r.text();
        return {status:r.status,headers:r.headers,body:text ? JSON.parse(text) : null};
      },
    };
  } catch(error) {await mf.dispose(); throw error;}
}

test('pinned patch changes only gallery handler and the new authenticated route', () => {
  assert.equal(sha256(baseline),BASELINE_SHA256);
  const out = patch(baseline); assert.equal(sha256(out),OUTPUT_SHA256);
  const start = 'async function handleSnapshotsList(request, env) {';
  const end = '__name(handleSnapshotsList, "handleSnapshotsList");';
  const old = baseline.slice(baseline.indexOf(start),baseline.indexOf(end));
  const restored = (out.slice(0,out.indexOf('const SNAPSHOT_STATS_HOUR_MS =')) + old + out.slice(out.indexOf(end)))
    .replace('    if (pathname === "/api/mobile/web-snapshots") {\n      return handleWebSnapshots(request, env);\n    }\n','');
  assert.equal(restored,baseline);
  assert.throws(() => patch(baseline+'\n'),/unknown/);
  for (const name of Object.keys(retained)) assert.throws(() => patchModules(baseline,{...retained,[name]:retained[name]+'\n'}));
  assert.deepEqual(patchModules(baseline,retained),{'worker.js':out,...retained});
});

test('native workerd authenticates, isolates vehicles, preserves impacts and refuses mutation', async t => {
  const f = await fixture();
  try {
    await f.insert(30); await f.insert(2,'other',100);
    await f.db.prepare('INSERT INTO impact_events VALUES(?,?,?,?,?,?,?,?)')
      .bind('impact','owner','owner-29',null,'moderate',0.4,1.2,time(29)).run();
    await t.test('invalid credentials and forged ownership deny',async () => {
      for (const key of [null,'wrong',REVOKED_KEY,'isolated-view','isolated-collector','isolated-ai','isolated-sync']) {
        const r = await f.call('?deviceId=owner',{key,headers:{'x-wayon-auth-device':'owner'}});
        assert.equal(r.status,401); assert.deepEqual(r.body,{error:'unauthorized'});
      }
    });
    await t.test('24 fresh photos, never the old state limit of 12, and impact fields unchanged',async () => {
      const r = await f.call('?deviceId=other',{headers:{'x-wayon-auth-device':'other'}});
      assert.equal(r.status,200); assert.equal(r.body.snapshots.length,24);
      assert.ok(r.body.snapshots.every(s => s.device_id === 'owner'));
      assert.equal(r.body.snapshots[0].id,'owner-29');
      assert.equal(r.body.snapshots[0].impact_id,'impact');
      assert.equal(r.body.snapshots[0].impact_severity,'moderate');
      assert.equal(r.body.snapshots.at(-1).impact_id,null);
      assert.equal(r.headers.get('cache-control'),'no-store');
      assert.equal((await f.kv.list()).keys.length,0);
      assert.equal(f.outbound(),0);
      assert.ok((await f.call('',{key:OTHER_KEY})).body.snapshots.every(s => s.device_id === 'other'));
    });
    await t.test('write verbs deny without deleting, changing or sending anything',async () => {
      for (const method of ['POST','PUT','DELETE','HEAD']) assert.equal((await f.call('',{method})).status,405);
      assert.equal((await f.call('',{method:'OPTIONS',key:null})).status,204);
      assert.ok((await f.db.prepare('SELECT last_seen_at FROM wayon_devices').all()).results.every(r => r.last_seen_at==='unchanged'));
      assert.equal((await f.db.prepare('SELECT COUNT(*) AS n FROM snapshots').first()).n,32);
      assert.equal(f.outbound(),0);
    });
    await t.test('old gallery fallback caches summary but new images remain immediate, with KST filter retained',async () => {
      const a = await f.call('?date=2026-11-01',{path:'/api/snapshots'});
      assert.equal(a.status,200); assert.equal(a.body.total,30);
      assert.deepEqual(a.body.days,[{date:'2026-11-01',count:30}]);
      assert.equal((await f.kv.list({prefix:'meta/snapshot-stats/'})).keys.length,1);
      await f.insert(1,'owner',31);
      const b = await f.call('',{path:'/api/snapshots'});
      assert.equal(b.body.total,30); assert.equal(b.body.snapshots.length,31);
      assert.equal(b.body.snapshots[0].id,'owner-31');
      assert.equal(b.body.statsComputedAt,a.body.statsComputedAt);
      assert.equal((await f.call('?date=2026-11-02',{path:'/api/snapshots'})).body.snapshots.length,0);
    });
    await t.test('unknown database failure stays sanitized',async () => {
      await f.db.exec('DROP TABLE snapshots;');
      const r = await f.call(); assert.equal(r.status,503);
      assert.deepEqual(r.body,{error:'web_snapshots_unavailable'});
    });
  } finally {await f.dispose();}
});

test('native limits are bounded; recent photo reads scale with page size on indexed schema',async () => {
  const f = await fixture();
  try {
    await f.insert(1005);
    for (let offset = 0; offset < 3000; offset += 100) {
      await f.db.batch(Array.from({length:100},(_,i) => {
        const n = offset+i;
        return f.db.prepare('INSERT INTO impact_events VALUES(?,?,?,?,?,?,?,?)').bind('impact-'+n,'owner',
          n < 1005 ? 'owner-'+n : 'old-wide-'+n,'old-driver-'+n,'light',0.1,1.1,time(n));
      }));
    }
    for (const [value,count] of [['1',1],['1000',1000],['1001',1000],['-1',24],['bad',24]]) {
      const r = await f.call('?limit='+value); assert.equal(r.status,200); assert.equal(r.body.snapshots.length,count);
    }
    const plan = await f.db.prepare('EXPLAIN QUERY PLAN SELECT * FROM snapshots WHERE device_id=? ORDER BY captured_at DESC LIMIT ?')
      .bind('owner',24).all();
    assert.ok(plan.results.some(r => r.detail.includes('snapshots_device_time')));
    const readList = vm.runInNewContext(readFileSync(new URL('./snapshots.js',import.meta.url),'utf8') + '\nreadSnapshotList');
    const measurements = [];
    const env = {DB:{prepare(sql) {return {bind(...args) {return {async all() {
      const result = await f.db.prepare(sql).bind(...args).all();
      const plan = await f.db.prepare('EXPLAIN QUERY PLAN '+sql).bind(...args).all();
      measurements.push({rowsRead:result.meta.rows_read,plan:plan.results.map(r => r.detail)});
      return result;
    }};}};}}};
    const page = await readList(env,'owner',24);
    assert.equal(page.length,24); assert.ok(page.every(p => p.impact_id));
    assert.ok(measurements[0].rowsRead <= 150);
    for (const name of ['snapshots_device_time','impact_wide','impact_driver']) {
      assert.ok(measurements[0].plan.some(p => p.includes(name)));
    }
    assert.ok(measurements[0].plan.every(p => !/SCAN |AUTOMATIC|TEMP B-TREE/.test(p)));
    console.log('isolated exact joined photo query: '+JSON.stringify(measurements[0]));
    assert.equal((await f.kv.list()).keys.length,0); assert.equal(f.outbound(),0);
  } finally {await f.dispose();}
});
