import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {Miniflare} from 'miniflare';
import {createHash} from 'node:crypto';

const origin='https://traverse.test', code='local-test-only-never-production';
const schema=readFileSync(new URL('../server/schema.sql',import.meta.url),'utf8');
let upstreamCalls=[];
const mf=new Miniflare({modules:true,scriptPath:new URL('../output/bundle/worker.js',import.meta.url).pathname,
  compatibilityDate:'2025-10-01',compatibilityFlags:['nodejs_compat'],d1Databases:['DB'],
  bindings:{PUBLIC_ORIGIN:origin,LOGIN_CODE_HASH:createHash('sha256').update(code).digest('hex'),
    ACCOUNT_ENCRYPTION_KEY:'t'.repeat(48),WAYON_DEVICE_KEY:'fixture-device-key',DEVICE_ID:'fixture-owner',MY_TRAVERSE_WEB_PUSH_TOKEN:'fixture-webhook'},
  serviceBindings:{ASSETS:()=>new Response('<!doctype html><title>Test</title><script>window.test=true</script>',{headers:{'content-type':'text/html'}}),WAYON:async request=>{
    upstreamCalls.push({path:new URL(request.url).pathname,method:request.method,auth:request.headers.get('authorization')});
    const path=new URL(request.url).pathname;
    if (path==='/api/state') return Response.json({state:{device_id:'fixture-owner',onroad:0},vehicleStatus:null,vehicleLock:null,healthTimeline:[]});
    if (path==='/api/mobile/web-trips') return Response.json({trips:[]});
    if (path==='/api/snapshots') return Response.json({snapshots:[]});
    return Response.json({ok:true,state:{onroad:false},protocol:'test-protocol',websocketUrl:'wss://wayon-cloud.hyuklee.workers.dev/api/live/stream'});
  }}});
let cookie,csrf;
test.before(async()=>{
  const db=await mf.getD1Database('DB');
  await db.exec(schema.replaceAll('\n',' '));
});
test.after(()=>mf.dispose());
async function call(path,{method='GET',body,auth=true,originHeader=origin,csrfHeader=csrf}={}) {
  const headers={...(auth&&cookie?{cookie}:{})};
  if(method!=='GET') Object.assign(headers,{'content-type':'application/json',origin:originHeader,...(csrfHeader?{'x-csrf-token':csrfHeader}:{})});
  const response=await mf.dispatchFetch(origin+path,{method,headers,...(body===undefined?{}:{body:JSON.stringify(body)})});
  return {response,data:await response.json()};
}
test('unauthenticated API has no private data and all arbitrary proxy paths fail closed',async()=>{
  const result=await call('/api/wayon/json',{auth:false}); assert.equal(result.response.status,401); assert.equal(upstreamCalls.length,0);
  assert.equal((await call('/api/session',{auth:false})).data.authenticated,false);
});
test('document scripts use per-response nonces instead of unrestricted inline execution',async()=>{
  const response=await mf.dispatchFetch(origin+'/');
  const csp=response.headers.get('content-security-policy');
  const nonce=csp.match(/script-src[^;]*'nonce-([^']+)'/)[1];
  assert.ok(!csp.match(/script-src[^;]*'unsafe-inline'/));
  assert.ok((await response.text()).includes(`nonce="${nonce}"`));
  assert.equal(response.headers.get('cache-control'),'no-store');
});
test('login origin and wrong credentials denied, valid session remains server-side',async()=>{
  assert.equal((await call('/api/login',{method:'POST',body:{password:code},originHeader:'https://evil.test'})).response.status,403);
  assert.equal((await call('/api/login',{method:'POST',body:{password:'wrong'}})).response.status,401);
  const result=await call('/api/login',{method:'POST',body:{password:code}});
  assert.equal(result.response.status,200); cookie=result.response.headers.get('set-cookie').split(';')[0];
  assert.ok(cookie.startsWith('__Host-traverse=')); assert.equal(result.data.token,undefined);
  const current=await call('/api/session'); csrf=current.data.csrfToken;
  assert.equal(current.data.authenticated,true); assert.equal(current.data.capabilities.commands,false); assert.ok(csrf);
});
test('same-origin proxy retains only intended read paths and hides privileged key',async()=>{
  assert.equal((await call('/api/wayon/json')).response.status,200);
  assert.equal(upstreamCalls.at(-1).auth,'Bearer fixture-device-key');
  assert.equal((await call('/api/wayon/devices/reissue',{method:'POST',body:{}})).response.status,403);
  assert.equal((await call('/api/wayon/remote/session',{method:'POST',body:{}})).response.status,403);
  assert.equal((await call('/api/wayon/../remote/session')).response.status,404);
});
test('mutations require csrf and exact origin even with valid cookies',async()=>{
  const before=upstreamCalls.length;
  for(const path of ['/api/command','/api/account','/api/ambient','/api/live/session','/api/push/subscribe']) {
    assert.equal((await call(path,{method:'POST',body:{},csrfHeader:'wrong'})).response.status,403);
  }
  assert.equal(upstreamCalls.length,before);
});
test('live only issues a same-origin websocket URL; does not send vehicle commands',async()=>{
  const result=await call('/api/live/session',{method:'POST',body:{}});
  assert.equal(result.response.status,200);assert.equal(result.data.websocketUrl,'wss://traverse.test/api/live/stream');
  assert.equal(upstreamCalls.at(-1).path,'/api/live/session');
});
test('commands without an account and malformed command requests do not call upstream',async()=>{
  const before=upstreamCalls.length;
  assert.equal((await call('/api/command',{method:'POST',body:{command:'DOOR_LOCK',requestId:crypto.randomUUID(),confirmed:true}})).response.status,403);
  assert.equal((await call('/api/command',{method:'POST',body:{command:'DOOR_LOCK'}})).response.status,400);
  assert.equal(upstreamCalls.length,before);
});
test('internal push endpoint rejects session cookies and wrong owner',async()=>{
  assert.equal((await call('/api/internal/notify',{method:'POST',body:{}})).response.status,401);
  const response=await mf.dispatchFetch(origin+'/api/internal/notify',{method:'POST',headers:{'content-type':'application/json',authorization:'Bearer fixture-webhook'},body:JSON.stringify({deviceId:'wrong'})});
  assert.equal(response.status,400);
});
test('logout removes server grants and cookie, subsequent reads denied',async()=>{
  const result=await call('/api/logout',{method:'POST',body:{}});
  assert.equal(result.response.status,200); assert.match(result.response.headers.get('set-cookie'),/Max-Age=0/);
  assert.equal((await call('/api/wayon/json')).response.status,401);
  assert.equal((await call('/api/session')).data.authenticated,false);
});
