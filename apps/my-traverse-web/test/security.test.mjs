import test from 'node:test';
import assert from 'node:assert/strict';
import {digest,equal,encrypt,decrypt,readJson,sameOrigin,sessionCookie} from '../server/security.mjs';
import {validateSubscription,deliver} from '../server/push.mjs';
import webpush from 'web-push';
import {createECDH,randomBytes} from 'node:crypto';

test('hash comparison rejects missing credentials; cookie is protected',async()=>{
  assert.equal(await equal('',''),false); assert.equal(await equal('a','a'),true); assert.equal(await equal('a','b'),false);
  assert.match(await digest('a'),/^[0-9a-f]{64}$/);
  for(const flag of ['__Host-','HttpOnly','Secure','SameSite=Strict','Path=/']) assert.ok(sessionCookie('abc').includes(flag));
});
test('account encryption is randomized, authenticated and scoped',async()=>{
  const key='x'.repeat(48), value={uuid:'private',token:'secret'};
  const a=await encrypt(value,key), b=await encrypt(value,key);
  assert.notEqual(a,b); assert.ok(!a.includes('private')); assert.deepEqual(await decrypt(a,key),value);
  await assert.rejects(()=>decrypt(a,'y'.repeat(48))); await assert.rejects(()=>encrypt(value,''));
});
test('same origin rejects sibling sites, null and missing Origin',()=>{
  const env={PUBLIC_ORIGIN:'https://test.example'};
  const req=(origin,site='same-origin')=>new Request(env.PUBLIC_ORIGIN+'/api/login',{headers:{...(origin?{origin}:{}),'sec-fetch-site':site}});
  assert.equal(sameOrigin(req(env.PUBLIC_ORIGIN),env),true);
  for(const origin of [null,'null','https://evil.example']) assert.equal(sameOrigin(req(origin),env),false);
  assert.equal(sameOrigin(req(env.PUBLIC_ORIGIN,'same-site'),env),false);
});
test('JSON byte cap counts streamed bytes without Content-Length',async()=>{
  const request=new Request('https://test.example',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({x:'x'.repeat(100)})});
  await assert.rejects(()=>readJson(request,50),/body_too_large/);
  await assert.rejects(()=>readJson(new Request('https://x',{method:'POST',body:'{}'})),/json_required/);
});
function subscription(endpoint='https://web.push.apple.com/test') {
  const ecdh=createECDH('prime256v1'); ecdh.generateKeys();
  return {endpoint,keys:{p256dh:ecdh.getPublicKey().toString('base64url'),auth:randomBytes(16).toString('base64url')}};
}
test('push endpoint prevents SSRF and malformed subscription keys',()=>{
  assert.ok(validateSubscription(subscription()));
  for(const url of ['http://web.push.apple.com/x','https://web.push.apple.com.evil.com/x','https://127.0.0.1/','https://evil.push.apple.com:444/x','https://u:p@web.push.apple.com/x']) {
    assert.throws(()=>validateSubscription(subscription(url)));
  }
  assert.throws(()=>validateSubscription({...subscription(),keys:{p256dh:'a',auth:'b'}}));
});
test('real web-push encryption produces VAPID POST and never exposes payload plain',async()=>{
  const keys=webpush.generateVAPIDKeys(), sub=subscription(); let requests=0;
  const env={VAPID_PUBLIC_KEY:keys.publicKey,VAPID_PRIVATE_KEY:keys.privateKey,PUBLIC_ORIGIN:'https://test.example',
    DB:{prepare(){return{bind(){return this},async all(){return{results:[{id:'one',subscription:JSON.stringify(sub)}]}},async run(){}}}}};
  const result=await deliver(env,{title:'TEST',body:'private text',expiresAt:Date.now()+1000},null,async(url,options)=>{
    requests++; assert.equal(url,sub.endpoint); assert.equal(options.method,'POST');
    assert.equal(options.redirect,'manual');
    assert.equal(options.headers['Content-Encoding'],'aes128gcm');
    assert.ok(options.headers.Authorization.startsWith('vapid '));
    assert.ok(!Buffer.from(options.body).includes(Buffer.from('private text')));
    return new Response(null,{status:201});
  });
  assert.equal(requests,1); assert.deepEqual(result,{sent:1,failed:0});
});
