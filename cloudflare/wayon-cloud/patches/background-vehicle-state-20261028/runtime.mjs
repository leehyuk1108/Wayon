import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {patch} from './patch.mjs';
import {candidate, COLLECTOR, DEVICE, executable, hash, KEY, OTHER_KEY, schema} from '../fast-vehicle-state-20261028/test-support.mjs';

const require=createRequire(import.meta.url);
const {Miniflare,convertV4MiniflareOptions}=require(process.env.MINIFLARE_MODULE || 'miniflare');
const options={modules:true,script:'const fetch=()=>{throw new Error("Remote fetch forbidden")};\n'+executable(patch(candidate)),
  compatibilityDate:'2026-05-14',d1Databases:{DB:'background-isolated'},kvNamespaces:['SNAPSHOTS'],
  bindings:{WAYON_GMONE_TOKEN:COLLECTOR,WAYON_LEGACY_FIREBASE_DEVICE_ID:DEVICE}};
const mf=new Miniflare(convertV4MiniflareOptions ? convertV4MiniflareOptions(options) : options);
let assertions=0;
const equal=(a,b)=>{assertions++;assert.deepEqual(a,b);};
const now=Date.now(), iso=d=>new Date(now+d).toISOString();
const body=(extra={})=>({schemaVersion:'wayon-gmone-v1',source:'gmone-official-cache',clientScope:'c'.repeat(64),
  vehicleUpdatedAt:iso(-10000),collectedAt:iso(-1000),status:{fuel:'63'},...extra});
async function call(method, payload, token=KEY) {
  const r=await mf.dispatchFetch('https://background.test/api/gmone/status',{
    method,headers:{authorization:`Bearer ${token}`,'content-type':'application/json'},
    ...(method==='POST'?{body:JSON.stringify(payload)}:{})});
  equal(r.headers.get('cache-control'),'no-store');
  return {status:r.status,data:await r.json()};
}
try {
  const db=await mf.getD1Database('DB');
  for (const sql of schema.split(';').map(x=>x.trim()).filter(Boolean)) await db.prepare(sql).run();
  await db.prepare('INSERT INTO wayon_devices VALUES (?, ?, NULL)').bind(DEVICE,hash(KEY)).run();
  await db.prepare('INSERT INTO wayon_devices VALUES (?, ?, NULL)').bind('other-device',hash(OTHER_KEY)).run();
  equal((await call('GET',null,'wrong')).status,401);
  equal((await call('POST',body(),'wrong')).status,401);
  await db.prepare('INSERT INTO gmone_refresh_requests VALUES (?, ?, NULL)').bind(DEVICE,iso(-50000)).run();
  const ack=async()=> (await db.prepare('SELECT completed_at FROM gmone_refresh_requests WHERE id=?').bind(DEVICE).first()).completed_at;
  equal((await call('POST',body(),COLLECTOR)).status,200);
  equal(await ack(),null);
  const read=(await call('GET')).data.vehicleStatus;
  equal(read.clientScope,'c'.repeat(64)); equal(read.updatedAt,iso(-10000)); equal(read.data.fuel,'63');
  equal((await call('GET',null,OTHER_KEY)).data.vehicleStatus,null);
  equal((await call('POST',body({source:'gmone-direct',refreshStartedAt:iso(-30000)}),COLLECTOR)).status,200);
  equal(typeof await ack(),'string');
  await db.prepare('UPDATE gmone_refresh_requests SET completed_at=NULL,requested_at=? WHERE id=?').bind(iso(-5000),DEVICE).run();
  equal((await call('POST',body({source:'gmone-direct',refreshStartedAt:iso(-30000)}),COLLECTOR)).status,200);
  equal(await ack(),null);
  equal((await call('POST',body({vehicleUpdatedAt:iso(-500000)}),COLLECTOR)).status,409);
  equal((await call('POST',body({vehicleUpdatedAt:iso(600000)}),COLLECTOR)).status,400);
  const results=await Promise.all(Array.from({length:40},(_,i)=>call('POST',body({vehicleUpdatedAt:iso(-1000+i),collectedAt:iso(0),status:{fuel:String(i)}}),COLLECTOR)));
  equal(results.every(r=>[200,409].includes(r.status)),true);
  equal((await call('GET')).data.vehicleStatus.data.fuel,'39');
  // A late valid active response may complete an earlier request without replacing newer data.
  await db.prepare('UPDATE gmone_refresh_requests SET requested_at=? WHERE id=?').bind(iso(-50000),DEVICE).run();
  equal((await call('POST',body({source:'gmone-direct',refreshStartedAt:iso(-30000)}),COLLECTOR)).status,409);
  equal(typeof await ack(),'string');
  equal((await call('GET')).data.vehicleStatus.data.fuel,'39');
  await db.prepare('UPDATE wayon_devices SET revoked_at=? WHERE device_id=?').bind(iso(0),DEVICE).run();
  equal((await call('GET')).status,401);
  console.log(JSON.stringify({runtime:'workerd + D1',assertions,concurrentUploads:40,remoteFetches:0}));
} finally {await mf.dispose();}
