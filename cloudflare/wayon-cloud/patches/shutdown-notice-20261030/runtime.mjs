import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {patch} from './patch.mjs';

const require = createRequire(import.meta.url);
const {Miniflare, convertV4MiniflareOptions} = require(process.env.MINIFLARE_MODULE || 'miniflare');
const KEY = 'wayon_' + 'a'.repeat(40), DEVICE = 'isolated-shutdown';
const hash = value => createHash('sha256').update(value).digest('hex');
let source = patch(readFileSync(process.env.WAYON_POWER_BASELINE, 'utf8'))
  .replace('import { createKeyDiagnostic, safeFailure } from "./key_diagnostics.mjs";',
    'const createKeyDiagnostic=()=>{}; const safeFailure=()=>"isolated";')
  .replace('import { handleDeviceReissue } from "./device_reissue.mjs";', 'const handleDeviceReissue=()=>{};')
  .replace(/export \{[\s\S]*$/, '');
source = `const testMessages=[];
  const fetch=async (url, options)=>{
    if(!url.startsWith('https://fcm.googleapis.com/v1/projects/')) throw new Error('Remote fetch forbidden');
    testMessages.push(JSON.parse(options.body).message);
    return new Response('{"name":"isolated"}');
  };
` + source + `
getFcmAccessToken=async()=>"isolated";
export default {fetch(request,env,ctx){
  if(new URL(request.url).pathname==='/__test/messages') return Response.json(testMessages);
  return worker_default.fetch(request,env,ctx);
}};`;
const options = {modules:true, script:source, compatibilityDate:'2026-05-14',
  d1Databases:{DB:'shutdown-isolated'}, kvNamespaces:['SNAPSHOTS'], bindings:{FCM_PROJECT_ID:'isolated-project'}};
const mf = new Miniflare(convertV4MiniflareOptions ? convertV4MiniflareOptions(options) : options);
let assertions=0;
const equal=(a,b)=>{assertions++;assert.deepEqual(a,b);};
try {
  const db=await mf.getD1Database('DB');
  for(const sql of [
    'CREATE TABLE wayon_devices(device_id TEXT PRIMARY KEY,key_hash TEXT,revoked_at TEXT)',
    'CREATE TABLE vehicle_events(id TEXT PRIMARY KEY,device_id TEXT,event_type TEXT,occurred_at TEXT,received_at TEXT,locked INTEGER,notified_count INTEGER,raw_json TEXT)',
    'CREATE TABLE push_subscriptions(token TEXT PRIMARY KEY,device_id TEXT)',
  ]) await db.prepare(sql).run();
  await db.prepare('INSERT INTO wayon_devices VALUES(?,?,NULL)').bind(DEVICE,hash(KEY)).run();
  await db.prepare('INSERT INTO push_subscriptions VALUES(?,?)').bind('isolated-fcm',DEVICE).run();
  const call=async (body,key=KEY)=>{
    const r=await mf.dispatchFetch('https://isolated.test/api/vehicle-event',{method:'POST',
      headers:{authorization:`Bearer ${key}`,'content-type':'application/json'},body:JSON.stringify(body)});
    return {status:r.status,data:await r.json()};
  };
  for(const [index,reason] of ['low_voltage','offroad_timeout'].entries()) {
    const body={eventType:'automatic_shutdown',id:'shutdown-'+String(index).repeat(32),reason,
      occurredAt:new Date().toISOString(),voltageV:11.2,offroadLimitMinutes:4320,test:true};
    equal((await call(body,'invalid')).status,401);
    equal((await call({...body,reason:'manual'})).status,400);
    const results=await Promise.all(Array.from({length:10},()=>call(body)));
    equal(results.every(r=>r.status===202 && r.data.accepted),true);
    let row;
    for(let i=0;i<50;i++) {
      row=await db.prepare('SELECT notified_count FROM vehicle_events WHERE id=?').bind(body.id).first();
      if(row.notified_count===1) break;
      await new Promise(resolve=>setTimeout(resolve,20));
    }
    equal(row.notified_count,1);
  }
  const messages=await (await mf.dispatchFetch('https://isolated.test/__test/messages')).json();
  equal(messages.length,2);
  equal(messages.every(m=>m.android.notification.channel_id==='wayon_power_alerts'),true);
  equal(messages.every(m=>m.notification.body.includes('실제 기기는 종료하지 않습니다')),true);
  console.log(JSON.stringify({runtime:'workerd + D1',assertions,remoteFetches:0}));
} finally {await mf.dispose();}
