import {SESSION_SECONDS, digest, equal, randomToken, json, readJson, readBytes, sameOrigin, sessionCookie, sessionFor, encrypt, decrypt, rateLimit} from './security.mjs';
import {internalNotify, pushRoute} from './push.mjs';
import {accountLogin, executeCommand, COMMAND_SPECS} from './commands.mjs';

const UPSTREAM = 'https://wayon-cloud.hyuklee.workers.dev';
const GET_PATHS = new Set(['json','state','gmone/status','gmone/refresh','trips','snapshots','snapshot','live-captures','live-capture','impacts','ambient/status']);
const MESSAGE = '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.';
const commandsEnabled=env=>env.COMMANDS_ENABLED==='1' && /^[a-f0-9]{64}$/.test(env.GMONE_UUID_HASH || '') && /^[a-f0-9]{64}$/.test(env.GMONE_VEHICLE_HASH || '');
async function accountMatches(account,env) {
  return typeof account?.uuid==='string' && typeof account?.vehicleId==='string' &&
    await equal(await digest(account.uuid),env.GMONE_UUID_HASH) && await equal(await digest(account.vehicleId),env.GMONE_VEHICLE_HASH);
}

export async function upstream(env, path, options = {}) {
  const headers = new Headers(options.headers);
  headers.set('authorization', `Bearer ${env.WAYON_DEVICE_KEY}`);
  headers.set('user-agent','MyTraverse-PWA/1');
  return env.WAYON.fetch(new Request(UPSTREAM + path, {...options,headers,redirect:'manual',signal:AbortSignal.timeout(15000)}));
}

function cleanResponse(response) {
  const headers = new Headers(response.headers);
  for (const name of [...headers.keys()]) if (name.startsWith('access-control-') || name === 'set-cookie') headers.delete(name);
  headers.set('cache-control','no-store'); headers.set('x-content-type-options','nosniff');
  return new Response(response.body,{status:response.status,headers});
}

async function sessionInfo(session,env) {
  let loggedIn=false;
  if (session.account) {
    try { loggedIn=(await decrypt(session.account,env.ACCOUNT_ENCRYPTION_KEY)).expiresAtMs>Date.now(); }
    catch { loggedIn=false; }
  }
  return {authenticated:true,csrfToken:session.csrf,account:{loggedIn,email:session.email || ''},
    capabilities:{commands:loggedIn && commandsEnabled(env),supportedCommands:Object.keys(COMMAND_SPECS),live:true,ambient:true,push:true}};
}

async function accountRoute(request, env, session) {
  if (request.method === 'DELETE') {
    await env.DB.prepare('UPDATE sessions SET account=NULL,email=NULL WHERE id=?').bind(session.id).run();
    return json({loggedIn:false,email:''});
  }
  if (request.method !== 'POST') return json({error:'method_not_allowed'},405);
  if (!commandsEnabled(env)) return json({ok:false,state:'blocked',message:'웹앱의 차량 제어를 검증 중입니다. 기존 안드로이드 앱을 이용해 주세요.'},403);
  if (!await rateLimit(env,'account:'+session.id,5,300)) return json({message:'로그인 시도가 많습니다. 잠시 후 다시 시도해 주세요.'},429);
  const {email,password} = await readJson(request,2048);
  if (typeof email !== 'string' || email.length > 254 || typeof password !== 'string' || !password || password.length > 256) return json({message:'계정을 확인해 주세요.'},400);
  // This personal gateway must never attach a different vehicle account to its owner's cloud data.
  if (!await equal(await digest(email.trim().toLowerCase()),env.ACCOUNT_FINGERPRINT)) return json({message:'이 웹앱에 등록된 차량 계정이 아닙니다.'},403);
  const account = await accountLogin(email,password);
  if (!await accountMatches(account,env)) return json({message:'등록된 차량 계정과 일치하지 않습니다.'},403);
  await env.DB.prepare('UPDATE sessions SET account=?,email=? WHERE id=?')
    .bind(await encrypt(account,env.ACCOUNT_ENCRYPTION_KEY),email.trim(),session.id).run();
  return json({loggedIn:true,email:email.trim(),message:'로그인되었습니다.'});
}

async function command(request, env, session) {
  if (request.method !== 'POST') return json({error:'method_not_allowed'},405);
  const {command:cmd,requestId,confirmed} = await readJson(request,1024);
  if (confirmed !== true || typeof cmd !== 'string' || !/^[A-Z_]{3,40}$/.test(cmd) || typeof requestId !== 'string' || !/^[0-9a-f-]{36}$/i.test(requestId)) return json({message:'명령을 확인해 주세요.'},400);
  if (!commandsEnabled(env)) return json({ok:false,state:'blocked',command:cmd,message:'웹앱의 차량 제어를 검증 중입니다. 기존 안드로이드 앱을 이용해 주세요.'},403);
  if (!session.account) return json({message:'멀티팩 로그인이 필요합니다.'},403);
  if (!Object.hasOwn(COMMAND_SPECS,cmd)) return json({ok:false,state:'blocked',command:cmd,message:'웹앱에서 아직 지원하지 않는 명령입니다.'},400);
  const existing = await env.DB.prepare('SELECT * FROM command_claims WHERE id=?').bind(requestId).first();
  if (existing) {
    if (existing.session_id !== session.id || existing.command !== cmd) return json({error:'request_conflict'},409);
    return json(existing.result ? JSON.parse(existing.result) : {ok:false,state:'unknown',message:'이 명령은 이미 처리 중입니다. 상태를 확인해 주세요.'});
  }
  const now = Date.now();
  let lease=now+180000;
  const lock = await env.DB.prepare('UPDATE command_lock SET until_ms=? WHERE id=1 AND until_ms < ? RETURNING id').bind(lease,now).first();
  if (!lock) return json({message:'다른 명령을 처리 중입니다.'},429);
  try {
    const claim = await env.DB.prepare('INSERT OR IGNORE INTO command_claims(id,session_id,command,created) VALUES(?,?,?,?)')
      .bind(requestId,session.id,cmd,now).run();
    if (!claim.meta.changes) return json({error:'request_conflict'},409);
    const account = await decrypt(session.account,env.ACCOUNT_ENCRYPTION_KEY);
    if (!await accountMatches(account,env)) throw new Error('account_binding_mismatch');
    const feedResponse = await upstream(env,'/api/json');
    if (!feedResponse.ok) throw new Error('state_unavailable');
    const liveState = await feedResponse.json();
    if (liveState?.state?.device_id !== env.DEVICE_ID) throw new Error('device_binding_mismatch');
    const result = await executeCommand({command:cmd,account,liveState,
      beforeSend: async () => {
        const current=await sessionFor(request,env);
        if (!current || current.account !== session.account) throw new Error('account_revoked');
        if (cmd === 'VEHICLE_START') {
          const marker = await upstream(env,'/api/mobile/impact-suppression',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({action:'arm',requestId})});
          if (!marker.ok) throw new Error('impact_guard_unavailable');
          await marker.body?.cancel();
        }
        const renewed=Date.now()+180000;
        const owned=await env.DB.prepare('UPDATE command_lock SET until_ms=? WHERE id=1 AND until_ms=? AND until_ms>? RETURNING id')
          .bind(renewed,lease,Date.now()).first();
        if (!owned) throw new Error('command_lease_expired');
        lease=renewed;
        const finalSession=await sessionFor(request,env);
        if (!finalSession || finalSession.account !== session.account) throw new Error('account_revoked');
      },
    });
    await env.DB.prepare('UPDATE command_claims SET result=? WHERE id=?').bind(JSON.stringify(result),requestId).run();
    return json(result);
  } catch {
    const result={ok:false,state:'unknown',message:'명령 완료를 확인하지 못했습니다. 재전송하지 않고 차량 상태를 확인해 주세요.'};
    await env.DB.prepare('UPDATE command_claims SET result=? WHERE id=? AND result IS NULL').bind(JSON.stringify(result),requestId).run();
    return json(result,409);
  } finally {
    await env.DB.prepare('UPDATE command_lock SET until_ms=? WHERE id=1 AND until_ms=?').bind(Date.now()+3000,lease).run();
  }
}

export async function handle(request, env, ctx) {
  const url = new URL(request.url), path = url.pathname;
  if (path === '/api/internal/notify') return internalNotify(request,env,ctx);
  if (!path.startsWith('/api/')) return env.ASSETS.fetch(request);
  if (request.method === 'OPTIONS') return json({error:'cross_origin_denied'},403);
  if (['POST','DELETE','PUT','PATCH'].includes(request.method) && !sameOrigin(request,env)) return json({error:'origin_rejected'},403);
  if (path === '/api/login' && request.method === 'POST') {
    const ip = await digest(request.headers.get('cf-connecting-ip') || 'local');
    if (!await rateLimit(env,'login:'+ip,8,300)) return json({message:'로그인 시도가 많습니다. 5분 뒤 다시 시도해 주세요.'},429);
    const {password} = await readJson(request,1024);
    if (typeof password !== 'string' || password.length > 128 || !await equal(await digest(password), env.LOGIN_CODE_HASH)) return json({message:'비밀번호가 맞지 않습니다.'},401);
    const token = randomToken(), csrf=randomToken();
    await env.DB.prepare('INSERT INTO sessions(id,csrf,expires) VALUES(?,?,?)').bind(await digest(token),csrf,Date.now()+SESSION_SECONDS*1000).run();
    return json({ok:true},200,{'set-cookie':sessionCookie(token)});
  }
  const session = await sessionFor(request,env);
  if (path === '/api/session' && request.method === 'GET') return json(session ? await sessionInfo(session,env) : {authenticated:false});
  if (!session) return json({error:'unauthorized',message:'로그인이 필요합니다.'},401);
  if (request.method !== 'GET' && !await equal(request.headers.get('x-csrf-token'),session.csrf)) return json({error:'csrf_rejected'},403);
  if (path === '/api/logout' && request.method === 'POST') {
    await env.DB.batch([
      env.DB.prepare('DELETE FROM web_subscriptions WHERE session_id=?').bind(session.id),
      env.DB.prepare('DELETE FROM sessions WHERE id=?').bind(session.id),
    ]);
    return json({ok:true},200,{'set-cookie':sessionCookie('',0),'clear-site-data':'"cache"'});
  }
  if (path === '/api/account') return accountRoute(request,env,session);
  if (path === '/api/command') return command(request,env,session);
  if (path.startsWith('/api/push/')) return pushRoute(path,request,env,session,ctx);
  if (path === '/api/live/session' && request.method === 'POST') {
    if (!await rateLimit(env,'live:'+session.id,10,60)) return json({error:'rate_limited'},429);
    const response = await upstream(env,'/api/live/session',{method:'POST'});
    if (!response.ok) return cleanResponse(response);
    const payload=await response.json();
    const socketUrl = new URL('/api/live/stream',env.PUBLIC_ORIGIN);
    socketUrl.protocol=socketUrl.protocol==='https:'?'wss:':'ws:';
    return json({...payload,websocketUrl:socketUrl.toString()});
  }
  if (path === '/api/live/stream' && request.method === 'GET') {
    if (!sameOrigin(request,env) || request.headers.get('upgrade')?.toLowerCase()!=='websocket') return json({error:'websocket_required'},403);
    const headers=new Headers({upgrade:'websocket','sec-websocket-protocol':request.headers.get('sec-websocket-protocol') || ''});
    return env.WAYON.fetch(new Request(UPSTREAM+'/api/live/stream',{headers}));
  }
  if (path === '/api/ambient' && request.method === 'POST') {
    if (!await rateLimit(env,'ambient:'+session.id,10,60)) return json({error:'rate_limited'},429);
    const payload=await readJson(request,16384);
    return cleanResponse(await upstream(env,'/api/ambient/command',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(payload)}));
  }
  if (path.startsWith('/api/wayon/')) {
    const suffix=path.slice('/api/wayon/'.length);
    if (suffix==='live-capture' && request.method==='POST') {
      if (request.headers.get('content-type') !== 'image/jpeg') return json({error:'jpeg_required'},415);
      if (!await rateLimit(env,'photo:'+session.id,6,60)) return json({error:'rate_limited'},429);
      // Count bytes even if Content-Length is absent or forged. Never queue an upload for later.
      const bytes = await readBytes(request,4*1024*1024);
      if (!bytes.byteLength || bytes.byteLength>4*1024*1024) return json({error:'photo_too_large'},413);
      return cleanResponse(await upstream(env,'/api/live-capture',{method:'POST',headers:{'content-type':'image/jpeg'},body:bytes}));
    }
    const readAllowed = GET_PATHS.has(suffix) || /^trips\/[A-Za-z0-9_%:.-]{1,200}$/.test(suffix);
    const refreshAllowed = suffix==='gmone/refresh' && request.method==='POST';
    if (!((request.method==='GET' && readAllowed) || refreshAllowed)) return json({error:'endpoint_not_allowed'},403);
    if (refreshAllowed && !await rateLimit(env,'refresh:'+session.id,6,60)) return json({error:'rate_limited'},429);
    const query = new URLSearchParams();
    for (const key of ['limit','key','id','part','offset','cursor','camera','before','kind']) {
      const value=url.searchParams.get(key);
      if (value && value.length<=1500) query.set(key,value);
    }
    return cleanResponse(await upstream(env, '/api/'+suffix+(query.size?'?'+query:''),{method:request.method}));
  }
  return json({error:'not_found'},404);
}

function secure(response) {
  if (response.status === 101) return response;
  const nonce=randomToken();
  if (response.headers.get('content-type')?.includes('text/html')) {
    response=new HTMLRewriter().on('script',{element(element){element.setAttribute('nonce',nonce);}}).transform(response);
  }
  const headers=new Headers(response.headers);
  headers.set('x-content-type-options','nosniff'); headers.set('referrer-policy','no-referrer');
  headers.set('x-frame-options','DENY');
  headers.set('permissions-policy','camera=(), microphone=(), geolocation=(self)');
  headers.set('content-security-policy', `default-src 'self'; script-src 'self' 'nonce-${nonce}' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://server.arcgisonline.com https://*.tile.openstreetmap.org https://*.basemaps.cartocdn.com https://tiles.openfreemap.org; font-src 'self' data:; connect-src 'self' https://server.arcgisonline.com https://tiles.openfreemap.org https://*.basemaps.cartocdn.com https://*.tile.openstreetmap.org; worker-src 'self' blob:; media-src 'self' blob:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`);
  if (headers.get('content-type')?.includes('text/html')) headers.set('cache-control','no-store');
  else if (headers.get('content-type')?.includes('javascript')) headers.set('cache-control','no-cache');
  return new Response(response.body,{status:response.status,headers});
}

export default {async fetch(request,env,ctx) {
  try { return secure(await handle(request,env,ctx)); }
  catch { return secure(json({error:'request_failed',message:MESSAGE},400)); }
}};
