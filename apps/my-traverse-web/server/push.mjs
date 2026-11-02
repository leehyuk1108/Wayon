import webpush from 'web-push';
import {digest, json, readJson, equal, rateLimit} from './security.mjs';

export function validateSubscription(value) {
  if (!value || typeof value.endpoint !== 'string' || value.endpoint.length > 2048) throw new Error('invalid_subscription');
  const url = new URL(value.endpoint);
  const allowed = url.hostname === 'web.push.apple.com' || url.hostname.endsWith('.push.apple.com') ||
    url.hostname === 'fcm.googleapis.com' || url.hostname === 'updates.push.services.mozilla.com';
  if (!allowed || url.protocol !== 'https:' || url.port || url.username || url.password || url.hash) throw new Error('invalid_push_endpoint');
  const {p256dh, auth} = value.keys || {};
  if (typeof p256dh !== 'string' || !/^[\w-]{87}=?$/.test(p256dh) || typeof auth !== 'string' || !/^[\w-]{22}={0,2}$/.test(auth)) throw new Error('invalid_push_keys');
  if (Buffer.from(p256dh,'base64url').length !== 65 || Buffer.from(p256dh,'base64url')[0] !== 4 || Buffer.from(auth,'base64url').length !== 16) throw new Error('invalid_push_keys');
  return {endpoint:url.toString(),keys:{p256dh,auth}};
}

export async function deliver(env, payload, sessionId = null, request = fetch) {
  if (!env.VAPID_PUBLIC_KEY || !env.VAPID_PRIVATE_KEY) return {sent:0,failed:0,unconfigured:true};
  const query = sessionId ? env.DB.prepare('SELECT * FROM web_subscriptions WHERE expires > ? AND session_id = ?').bind(Date.now(),sessionId)
    : env.DB.prepare('SELECT * FROM web_subscriptions WHERE expires > ? LIMIT 16').bind(Date.now());
  const {results} = await query.all();
  let sent=0,failed=0; const failures=[];
  for (const row of results) {
    let stage='encryption';
    try {
      const subscription = validateSubscription(JSON.parse(row.subscription));
      const details = webpush.generateRequestDetails(subscription, JSON.stringify(payload), {
        TTL:300, urgency:'high', vapidDetails:{subject:env.PUBLIC_ORIGIN,publicKey:env.VAPID_PUBLIC_KEY,privateKey:env.VAPID_PRIVATE_KEY},
      });
      stage='transport';
      const response = await request(details.endpoint, {method:'POST',headers:details.headers,body:details.body,redirect:'manual',signal:AbortSignal.timeout(4000)});
      if (response.status === 404 || response.status === 410) await env.DB.prepare('DELETE FROM web_subscriptions WHERE id = ?').bind(row.id).run();
      if (response.ok) sent++; else { failed++; failures.push({stage:'provider',code:'http_'+response.status}); }
      await response.body?.cancel();
    } catch (error) { failed++; failures.push({stage,code:String(error?.code || error?.name || 'unknown').replace(/[^A-Za-z0-9_]/g,'').slice(0,60),
      detail:String(error?.message || '').replace(/https?:\/\/\S+/g,'[endpoint]').replace(/[A-Za-z0-9_=-]{40,}/g,'[redacted]').slice(0,180)}); }
  }
  return {sent,failed,...(failures.length?{failures}:{})};
}

export async function internalNotify(request, env, ctx) {
  if (request.method !== 'POST') return json({error:'method_not_allowed'},405);
  if (!await equal(request.headers.get('authorization'), `Bearer ${env.MY_TRAVERSE_WEB_PUSH_TOKEN || ''}`) || !env.MY_TRAVERSE_WEB_PUSH_TOKEN) return json({error:'unauthorized'},401);
  const p = await readJson(request,8192);
  if (p.deviceId !== env.DEVICE_ID || !['wayon_parking_sign','wayon_impact','wayon_door_lock','wayon_parking_unlocked','wayon_automatic_shutdown'].includes(p.type) ||
      typeof p.id !== 'string' || !/^[\w:.-]{1,180}$/.test(p.id) || typeof p.title !== 'string' || Array.from(p.title).length > 128 ||
      typeof p.body !== 'string' || Array.from(p.body).length > 2048 || typeof p.test !== 'boolean') return json({error:'invalid_event'},400);
  const time = Date.parse(p.occurredAt);
  if (!Number.isFinite(time) || time > Date.now()+120000 || Date.now()-time > 600000) return json({error:'expired_event'},400);
  const id = `${p.type}:${p.id}:${p.test}`;
  const claim = await env.DB.prepare('INSERT OR IGNORE INTO push_claims(id,created) VALUES(?,?)').bind(id,Date.now()).run();
  if (!claim.meta.changes) return json({ok:true,duplicate:true},202);
  // Keep the encrypted Web Push record below providers' 4 KiB limit, including Unicode.
  const body=Array.from(p.body).length>600 ? Array.from(p.body).slice(0,600).join('')+'...' : p.body;
  ctx.waitUntil(deliver(env,{id,title:p.title,body,expiresAt:Date.now()+300000})
    .then(result=>env.DB.prepare('UPDATE push_claims SET result=? WHERE id=?').bind(JSON.stringify(result),id).run()));
  return json({ok:true,accepted:true},202);
}

export async function pushRoute(path, request, env, session, ctx) {
  if (path === '/api/push/key' && request.method === 'GET') return env.VAPID_PUBLIC_KEY
    ? json({publicKey:env.VAPID_PUBLIC_KEY}) : json({message:'알림 설정이 준비되지 않았습니다.'},503);
  if (path === '/api/push/subscribe' && request.method === 'POST') {
    const subscription = validateSubscription((await readJson(request)).subscription);
    const count = await env.DB.prepare('SELECT COUNT(*) AS n FROM web_subscriptions WHERE expires > ?').bind(Date.now()).first();
    const id = await digest(subscription.endpoint);
    const old = await env.DB.prepare('SELECT id FROM web_subscriptions WHERE id = ?').bind(id).first();
    if (!old && count.n >= 16) return json({message:'등록 가능한 알림 기기 수를 초과했습니다.'},409);
    await env.DB.prepare(`INSERT INTO web_subscriptions(id,session_id,subscription,expires) VALUES(?,?,?,?)
      ON CONFLICT(id) DO UPDATE SET session_id=excluded.session_id,subscription=excluded.subscription,expires=excluded.expires`)
      .bind(id,session.id,JSON.stringify(subscription),session.expires).run();
    return json({ok:true});
  }
  if (path === '/api/push/unsubscribe' && request.method === 'POST') {
    const {endpoint} = await readJson(request);
    if (typeof endpoint !== 'string') return json({error:'invalid_endpoint'},400);
    await env.DB.prepare('DELETE FROM web_subscriptions WHERE id = ? AND session_id = ?').bind(await digest(endpoint),session.id).run();
    return json({ok:true});
  }
  if (path === '/api/push/test' && request.method === 'POST') {
    if (!await rateLimit(env,'push-test:'+session.id,3,60)) return json({message:'잠시 후 다시 시도해 주세요.'},429);
    const result = await deliver(env,{id:'test:'+crypto.randomUUID(),title:'My Traverse 테스트 알림',body:'아이폰 웹앱 알림 연결을 확인합니다.',expiresAt:Date.now()+300000},session.id);
    return json(result);
  }
  return json({error:'not_found'},404);
}
