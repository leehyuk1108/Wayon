import assert from 'node:assert/strict';
import {test} from 'node:test';
import {readFileSync} from 'node:fs';
import {createHash, webcrypto} from 'node:crypto';
import {DatabaseSync} from 'node:sqlite';
import vm from 'node:vm';
import {patch} from './patch.mjs';

const baseline = readFileSync(process.env.WAYON_POWER_BASELINE, 'utf8');
const candidate = patch(baseline);
const KEY = 'wayon_' + 'a'.repeat(40), DEVICE = 'isolated-device';
const OTHER = 'wayon_' + 'b'.repeat(40);
const hash = text => createHash('sha256').update(text).digest('hex');
const payload = (extra = {}) => ({eventType:'automatic_shutdown', id:'shutdown-'+'a'.repeat(32),
  reason:'low_voltage', occurredAt:new Date().toISOString(), voltageV:11.2, offroadLimitMinutes:4320, ...extra});

class BodyRequest extends Request {
  constructor(input, init = {}) {
    super(input, {...init, ...(init.body ? {duplex: 'half'} : {})});
  }
}

function fixture({failure=false, hold=false}={}) {
  const sqlite = new DatabaseSync(':memory:');
  sqlite.exec(`CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT);
    CREATE TABLE vehicle_events(id TEXT PRIMARY KEY,device_id TEXT,event_type TEXT,occurred_at TEXT,received_at TEXT,
      locked INTEGER,notified_count INTEGER,raw_json TEXT);
    CREATE TABLE push_subscriptions(token TEXT PRIMARY KEY,device_id TEXT);`);
  for (const [id,key] of [[DEVICE,KEY],['other-device',OTHER]]) {
    sqlite.prepare('INSERT INTO wayon_devices VALUES(?,?,NULL)').run(id,hash(key));
    sqlite.prepare('INSERT INTO push_subscriptions VALUES(?,?)').run(id+'-fcm',id);
  }
  const DB={prepare(sql) {
    const wrap=(args=[])=>({
      bind(...a){return wrap(a);},
      async first(){return sqlite.prepare(sql).get(...args)||null;},
      async all(){return {results:sqlite.prepare(sql).all(...args)};},
      async run(){return {success:true,meta:{changes:Number(sqlite.prepare(sql).run(...args).changes)}};},
    }); return wrap();
  }};
  const pushes=[],pending=[];
  let release;
  const held=new Promise(resolve=>{release=resolve;});
  const context=vm.createContext({Request:BodyRequest,Response,Headers,URL,Date,TextEncoder,TextDecoder,Uint8Array,
    crypto:webcrypto,console:{warn(){},error(){}},
    fetch:async (url,options)=>{
      assert.match(url,/^https:\/\/fcm.googleapis.com\/v1\/projects\//);
      pushes.push(JSON.parse(options.body).message);
      if(hold) await held;
      if(failure) throw new Error('isolated failure');
      return new Response(JSON.stringify({name:'synthetic-receipt'}),{status:200});
    }});
  let executable=candidate
    .replace('import { createKeyDiagnostic, safeFailure } from "./key_diagnostics.mjs";',
      'const createKeyDiagnostic=()=>{};const safeFailure=()=>"isolated";')
    .replace('import { handleDeviceReissue } from "./device_reissue.mjs";', 'const handleDeviceReissue=()=>{};')
    .replace(/export \{[\s\S]*$/, '');
  executable+='\ngetFcmAccessToken=async()=>"isolated-oauth";globalThis.probe={worker:worker_default,shutdownNoticeData,visibleFcmNotification};';
  vm.runInContext(executable,context);
  const env={DB,SNAPSHOTS:{},FCM_PROJECT_ID:'isolated-project'};
  const ctx={waitUntil(p){pending.push(p);}};
  return {sqlite,pushes,pending,release,probe:context.probe,
    async call(body=payload(),key=KEY,extraHeaders={}){
      const request=new Request('https://isolated.test/api/vehicle-event',{method:'POST',
        headers:{authorization:`Bearer ${key}`,'content-type':'application/json',...extraHeaders},body:JSON.stringify(body)});
      const r=await context.probe.worker.fetch(request,env,ctx);
      return {status:r.status,body:await r.json()};
    },
    async drain(){await Promise.all(pending);},
  };
}

test('unknown/repeated bundles are rejected',()=>{
  assert.throws(()=>patch(baseline+' ')); assert.throws(()=>patch(candidate));
});

for (const reason of ['low_voltage','offroad_timeout']) test(`${reason}: accepted before delayed FCM, matching visible/data content`,async()=>{
  const f=fixture({hold:true});
  try {
    const r=await f.call(payload({reason}));
    assert.equal(r.status,202);assert.equal(r.body.accepted,true);
    f.release();await f.drain();
    assert.equal(f.pushes.length,1);
    const msg=f.pushes[0];
    assert.equal(msg.token,DEVICE+'-fcm');
    assert.equal(msg.data.type,'wayon_automatic_shutdown');assert.equal(msg.data.reason,reason);
    assert.equal(msg.notification.title,'콤마 자동 종료 예정');
    assert.equal(msg.notification.body,msg.data.notificationBody);
    assert.ok(msg.notification.body.includes(reason==='low_voltage'?'11.20V':'72시간'));
    assert.ok(msg.notification.body.includes('취소됩니다'));
    assert.equal(msg.android.notification.channel_id,'wayon_power_alerts');
    assert.equal(msg.android.notification.tag,payload().id);
    assert.equal(msg.android.ttl,'300s');
    assert.equal(f.sqlite.prepare('SELECT notified_count AS n FROM vehicle_events').get().n,1);
  } finally {f.release();f.sqlite.close();}
});

test('20 concurrent requests claim one notification',async()=>{
  const f=fixture();try{
    const rs=await Promise.all(Array.from({length:20},()=>f.call()));await f.drain();
    assert.ok(rs.every(r=>r.status===202));assert.equal(f.pushes.length,1);
  }finally{f.sqlite.close();}
});

test('auth, body device spoofing and cross-device collision stay scoped',async()=>{
  const f=fixture();try{
    assert.equal((await f.call(payload(),'invalid',{'x-wayon-auth-device':'other-device'})).status,401);
    assert.equal((await f.call(payload({deviceId:'other-device'}))).status,202);await f.drain();
    assert.equal(f.pushes[0].token,DEVICE+'-fcm');
    assert.equal((await f.call(payload(),OTHER)).status,409);
    assert.equal(f.pushes.length,1);
  }finally{f.sqlite.close();}
});

for (const extra of [
  {reason:'manual'},{id:'bad'},{id:42},{occurredAt:'nonsense'},
  {occurredAt:new Date(Date.now()-120000).toISOString()},
  {occurredAt:new Date(Date.now()+60000).toISOString()},
  {offroadLimitMinutes:-1},{offroadLimitMinutes:'4320'},{offroadLimitMinutes:1.5},
  {voltageV:0},{voltageV:40},{voltageV:'11.2'},
]) test(`reject bad notice ${JSON.stringify(extra)}`,async()=>{
  const f=fixture();try{
    assert.equal((await f.call(payload(extra))).status,400);
    assert.equal(f.pushes.length,0);assert.equal(f.pending.length,0);
    assert.equal(f.sqlite.prepare('SELECT COUNT(*) AS n FROM vehicle_events').get().n,0);
  }finally{f.sqlite.close();}
});

test('FCM failure records failed receipt and does not duplicate on retry',async()=>{
  const f=fixture({failure:true});try{
    assert.equal((await f.call()).status,202);await f.drain();
    assert.equal(f.sqlite.prepare('SELECT notified_count AS n FROM vehicle_events').get().n,-2);
    assert.equal((await f.call()).status,202);await f.drain();assert.equal(f.pushes.length,1);
  }finally{f.sqlite.close();}
});

test('test notice explicitly says the comma stays on; no caller secrets are saved',async()=>{
  const f=fixture();try{
    await f.call(payload({test:true,secret:'never-store'}));await f.drain();
    assert.match(f.pushes[0].notification.title,/테스트/);
    assert.match(f.pushes[0].notification.body,/실제 기기는 종료하지 않습니다/);
    assert.ok(!f.sqlite.prepare('SELECT raw_json FROM vehicle_events').get().raw_json.includes('never-store'));
  }finally{f.sqlite.close();}
});

test('door-lock renderer and handler stay unchanged',()=>{
  const section=s=>s.slice(s.indexOf('  const eventType ='),s.indexOf('__name(handleVehicleEvent'));
  assert.equal(section(candidate),section(baseline));
});
