import {SESSION_SECONDS, digest, equal, randomToken, json, readJson, readBytes, sameOrigin, sessionCookie, sessionFor, encrypt, decrypt, rateLimit} from './security.mjs';
import {internalNotify, pushRoute} from './push.mjs';
import {accountLogin, executeCommand, COMMAND_SPECS, CommandError} from './commands.mjs';
import {databaseLimitResponse} from './database-error.mjs';

const UPSTREAM = 'https://wayon-cloud.hyuklee.workers.dev';
const GET_PATHS = new Set(['json','state','gmone/status','gmone/refresh','trips','snapshots','snapshot','live-captures','live-capture','impacts','ambient/status','parking/latest']);
const MESSAGE = '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.';
const UPSTREAM_MESSAGES = Object.freeze({
  upstream_binding:'차량 정보 서비스 연결 설정을 확인해 주세요.',
  upstream_credentials:'차량 정보 서비스 인증 설정이 누락되었습니다.',
  upstream_request:'차량 정보 서비스 요청을 구성하지 못했습니다.',
  upstream_transport:'차량 정보 서비스와 통신을 완료하지 못했습니다.',
  upstream_timeout:'차량 정보 서비스 응답 대기 시간이 초과되었습니다.',
  upstream_auth:'차량 정보 서비스가 서버 인증을 거부했습니다.',
  upstream_http:'차량 정보 서비스가 정상 HTTP 응답을 반환하지 않았습니다.',
  upstream_response:'차량 정보 서비스 응답을 전달하지 못했습니다.',
});
class UpstreamError extends Error {
  constructor(code, upstreamStatus) { super(code); this.code=code; this.upstreamStatus=upstreamStatus; }
}
function upstreamFailure(error) {
  return {ok:false,error:error.code,code:error.code,message:UPSTREAM_MESSAGES[error.code],
    ...(Number.isInteger(error.upstreamStatus) ? {upstreamStatus:error.upstreamStatus} : {})};
}
const commandsEnabled=env=>env.COMMANDS_ENABLED==='1' && /^[a-f0-9]{64}$/.test(env.GMONE_UUID_HASH || '') && /^[a-f0-9]{64}$/.test(env.GMONE_VEHICLE_HASH || '');
async function accountMatches(account,env) {
  return typeof account?.uuid==='string' && typeof account?.vehicleId==='string' &&
    await equal(await digest(account.uuid),env.GMONE_UUID_HASH) && await equal(await digest(account.vehicleId),env.GMONE_VEHICLE_HASH);
}

export async function upstream(env, path, options = {}) {
  if (typeof env.WAYON?.fetch !== 'function') throw new UpstreamError('upstream_binding');
  if (typeof env.WAYON_DEVICE_KEY !== 'string' || !env.WAYON_DEVICE_KEY.trim()) throw new UpstreamError('upstream_credentials');
  let request;
  try {
    const headers = new Headers(options.headers);
    headers.set('authorization', `Bearer ${env.WAYON_DEVICE_KEY}`);
    headers.set('user-agent','MyTraverse-PWA/1');
    request=new Request(UPSTREAM + path, {...options,headers,redirect:'manual',signal:AbortSignal.timeout(15000)});
  } catch { throw new UpstreamError('upstream_request'); }
  let response;
  try { response=await env.WAYON.fetch(request); }
  catch (error) {
    throw new UpstreamError(request.signal.aborted || error?.name === 'TimeoutError' ? 'upstream_timeout' : 'upstream_transport');
  }
  if (!(response instanceof Response)) throw new UpstreamError('upstream_response');
  if (!response.ok) {
    try { await response.body?.cancel(); } catch { /* Never expose an upstream error body. */ }
    throw new UpstreamError([401,403].includes(response.status) ? 'upstream_auth' : 'upstream_http',response.status);
  }
  return response;
}

function cleanResponse(response) {
  try {
    const headers = new Headers(response.headers);
    for (const name of [...headers.keys()]) if (name.startsWith('access-control-') || name === 'set-cookie') headers.delete(name);
    headers.set('cache-control','no-store'); headers.set('x-content-type-options','nosniff');
    return new Response(response.body,{status:response.status,headers});
  } catch { throw new UpstreamError('upstream_response'); }
}

async function upstreamJson(env,path) {
  const response=await upstream(env,path);
  try {
    const payload=await response.json();
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) throw new Error('invalid_payload');
    return payload;
  } catch { throw new UpstreamError('upstream_response'); }
}

async function composedFeed(env) {
  // Avoid Wayon's full-route export. Preserve actual state and observation clocks.
  const history=async(path,key,limit)=>{
    try {
      const payload=await upstreamJson(env,path);
      if (!Array.isArray(payload[key])) throw new UpstreamError('upstream_response');
      return {items:payload[key].slice(0,limit)};
    } catch (error) {
      return {items:null,error:upstreamFailure(error instanceof UpstreamError ? error : new UpstreamError('upstream_response'))};
    }
  };
  const [state,trips,snapshots]=await Promise.all([
    upstreamJson(env,'/api/state'),
    history('/api/mobile/web-trips?limit=25','trips',25),
    history('/api/mobile/web-snapshots?limit=24','snapshots',24),
  ]);
  if (!state.state || typeof state.state !== 'object' || Array.isArray(state.state) ||
      state.state.device_id !== env.DEVICE_ID ||
      !['vehicleStatus','vehicleLock','healthTimeline'].every(key=>Object.hasOwn(state,key))) throw new UpstreamError('upstream_response');
  return json({generatedAt:state.generatedAt ?? null,state:state.state,
    vehicleStatus:state.vehicleStatus,vehicleLock:state.vehicleLock,healthTimeline:state.healthTimeline,
    trips:trips.items,snapshots:snapshots.items,
    historyErrors:{...(trips.error ? {trips:trips.error} : {}),...(snapshots.error ? {snapshots:snapshots.error} : {})}});
}

async function sessionInfo(session,env) {
  let loggedIn=false;
  if (session.account) {
    try {
      const stored=await decrypt(session.account,env.ACCOUNT_ENCRYPTION_KEY);
      // A remembered account (this device's encrypted session only) logs in again before each command.
      loggedIn=stored.expiresAtMs>Date.now() || rememberedCredentials(stored)!==null;
    }
    catch { loggedIn=false; }
  }
  return {authenticated:true,csrfToken:session.csrf,account:{loggedIn,email:session.email || ''},
    capabilities:{commands:loggedIn && commandsEnabled(env),supportedCommands:Object.keys(COMMAND_SPECS),live:true,ambient:true,push:true}};
}

async function accountRoute(request, env, session) {
  if (request.method === 'DELETE') {
    await env.DB.prepare('UPDATE sessions SET account=NULL,email=NULL,account_rev=account_rev+1 WHERE id=?').bind(session.id).run();
    return json({loggedIn:false,email:''});
  }
  if (request.method !== 'POST') return json({error:'method_not_allowed'},405);
  if (!commandsEnabled(env)) return json({ok:false,state:'blocked',message:'웹앱의 차량 제어를 검증 중입니다. 기존 안드로이드 앱을 이용해 주세요.'},403);
  if (!await rateLimit(env,'account:'+session.id,5,300)) return json({message:'로그인 시도가 많습니다. 잠시 후 다시 시도해 주세요.'},429);
  const {email,password} = await readJson(request,2048);
  if (typeof email !== 'string' || email.length > 254 || typeof password !== 'string' || !password || password.length > 256) return json({message:'계정을 확인해 주세요.'},400);
  // This personal gateway must never attach a different vehicle account to its owner's cloud data.
  if (!await equal(await digest(email.trim().toLowerCase()),env.ACCOUNT_FINGERPRINT)) return json({message:'이 웹앱에 등록된 차량 계정이 아닙니다.'},403);
  let account;
  try { account = await accountLogin(email,password); }
  catch (error) {
    if (!(error instanceof CommandError)) throw error;
    const failures = {
      invalid_credentials:[400,'계정과 비밀번호 입력 형식을 확인해 주세요.'],
      login_rejected:[401,'멀티팩 로그인이 거부되었습니다. 계정과 비밀번호를 확인해 주세요.'],
      invalid_login_response:[502,'멀티팩 로그인 응답의 계정 정보를 확인하지 못했습니다.'],
      single_vehicle_required:[403,'등록 차량이 정확히 한 대인 멀티팩 계정만 연결할 수 있습니다.'],
      transport_error:[502,'멀티팩 서버와 통신을 완료하지 못했습니다. 잠시 후 다시 로그인해 주세요.'],
      upstream_http_error:[502,'멀티팩 서버가 정상 HTTP 응답을 반환하지 않았습니다.'],
      invalid_response:[502,'멀티팩 서버 응답 형식을 확인하지 못했습니다.'],
      response_too_large:[502,'멀티팩 서버 응답이 허용 크기를 초과했습니다.'],
    };
    const code=Object.hasOwn(failures,error.code) ? error.code : 'account_login_failed';
    const [status,message]=failures[code] || [502,'멀티팩 로그인 처리를 완료하지 못했습니다.'];
    return json({ok:false,state:'blocked',code,message},status);
  }
  if (!await accountMatches(account,env)) return json({message:'등록된 차량 계정과 일치하지 않습니다.'},403);
  // Like the Android app, keep the multipack login on this device: the credentials live only in this
  // web session's encrypted row (deleted on logout, account sign-out or session expiry), never in the browser.
  // Store only if no sign-out or other login happened meanwhile (revision) and the web session is still valid.
  const stored = await env.DB.prepare('UPDATE sessions SET account=?,email=?,account_rev=account_rev+1 WHERE id=? AND account_rev=? AND expires>? RETURNING id')
    .bind(await encrypt({...account,renew:{email:email.trim(),password}},env.ACCOUNT_ENCRYPTION_KEY),email.trim(),session.id,session.account_rev ?? 0,Date.now()).first();
  if (!stored) return json({ok:false,state:'blocked',code:'account_changed',message:'로그인 중에 계정 상태가 바뀌었습니다. 다시 로그인해 주세요.'},409);
  return json({loggedIn:true,email:email.trim(),message:'로그인되었습니다. 이 기기에서 로그인이 유지됩니다.'});
}

// Expired web sessions keep no multipack login (token or remembered password).
async function forgetExpiredAccounts(env) {
  await env.DB.prepare('UPDATE sessions SET account=NULL,email=NULL,account_rev=account_rev+1 WHERE expires<=? AND account IS NOT NULL')
    .bind(Date.now()).run();
}

function rememberedCredentials(stored) {
  const renew=stored?.renew;
  return renew && typeof renew.email==='string' && typeof renew.password==='string' && renew.email && renew.password
    && renew.email.length<=254 && renew.password.length<=256 ? {email:renew.email,password:renew.password} : null;
}

// Fresh multipack token for a remembered account, swapped in only if the session still holds the same ciphertext.
async function renewAccount(env, session, stored, credentials) {
  try {
    const fresh=await accountLogin(credentials.email,credentials.password);
    if (!await accountMatches(fresh,env)) return {failure:'account_binding_mismatch',clear:true};
    const cipher=await encrypt({...fresh,renew:credentials},env.ACCOUNT_ENCRYPTION_KEY);
    const swapped=await env.DB.prepare('UPDATE sessions SET account=? WHERE id=? AND account=? AND expires>? RETURNING id')
      .bind(cipher,session.id,session.account,Date.now()).first();
    if (!swapped) return {failure:'account_revoked',clear:false};
    return {account:fresh,cipher};
  } catch (error) {
    if (error instanceof CommandError && error.code==='login_rejected' && error.explicit===true) return {failure:'account_login_rejected',clear:true};
    if (error instanceof CommandError) return {failure:'account_refresh_failed',clear:false};
    throw error;
  }
}

const RENEW_MESSAGES={
  account_login_rejected:'명령을 보내지 않았습니다. 멀티팩 비밀번호가 바뀌었거나 로그인이 거부되었습니다. 설정에서 다시 로그인해 주세요.',
  account_binding_mismatch:'명령을 보내지 않았습니다. 등록된 차량 계정과 일치하지 않아 로그인을 해제했습니다.',
  account_revoked:'명령을 보내지 않았습니다. 멀티팩 로그인이 바뀌었습니다. 다시 시도해 주세요.',
  account_refresh_failed:'명령을 보내지 않았습니다. 멀티팩 로그인을 갱신하지 못했습니다. 잠시 후 다시 시도해 주세요.',
};

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
  let executionStarted=false, dispatchPossible=false, cooldownUntilMs=0;
  try {
    const claim = await env.DB.prepare('INSERT OR IGNORE INTO command_claims(id,session_id,command,created) VALUES(?,?,?,?)')
      .bind(requestId,session.id,cmd,now).run();
    if (!claim.meta.changes) return json({error:'request_conflict'},409);
    const stored = await decrypt(session.account,env.ACCOUNT_ENCRYPTION_KEY);
    const credentials = rememberedCredentials(stored);
    let account = stored;
    if (credentials) {
      const renewed = await renewAccount(env,session,stored,credentials);
      if (renewed.failure) {
        const blocked={ok:false,state:'blocked',command:cmd,code:renewed.failure,message:RENEW_MESSAGES[renewed.failure],
          dispatched:false,vehicleConfirmed:false,retryable:false,failureStage:'account-refresh'};
        await env.DB.prepare('UPDATE command_claims SET result=? WHERE id=?').bind(JSON.stringify(blocked),requestId).run();
        if (renewed.clear) await env.DB.prepare('UPDATE sessions SET account=NULL,email=NULL,account_rev=account_rev+1 WHERE id=? AND account=?')
          .bind(session.id,session.account).run();
        return json(blocked);
      }
      session = {...session,account:renewed.cipher};
      account = renewed.account;
    }
    if (!await accountMatches(account,env)) throw new Error('account_binding_mismatch');
    const liveState = await upstreamJson(env,'/api/state');
    if (liveState?.state?.device_id !== env.DEVICE_ID) throw new Error('device_binding_mismatch');
    let markerAttempted=false;
    executionStarted=true;
    dispatchPossible=true;
    let result = await executeCommand({command:cmd,account,liveState,
      beforeSend: async () => {
        const current=await sessionFor(request,env);
        if (!current || current.account !== session.account) throw new Error('account_revoked');
        if (cmd === 'VEHICLE_START') {
          markerAttempted=true;
          const marker = await upstream(env,'/api/mobile/impact-suppression',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({action:'arm',requestId})});
          if (!marker.ok) throw new Error('impact_guard_unavailable');
          await marker.body?.cancel();
        }
        const finalFeed=await upstreamJson(env,'/api/state');
        if (finalFeed?.state?.device_id !== env.DEVICE_ID) throw new Error('device_binding_mismatch');
        const renewed=Date.now()+180000;
        const owned=await env.DB.prepare('UPDATE command_lock SET until_ms=? WHERE id=1 AND until_ms=? AND until_ms>? RETURNING id')
          .bind(renewed,lease,Date.now()).first();
        if (!owned) throw new Error('command_lease_expired');
        lease=renewed;
        const finalSession=await sessionFor(request,env);
        if (!finalSession || finalSession.account !== session.account) throw new Error('account_revoked');
        return {liveState:finalFeed};
      },
    });
    dispatchPossible=result.dispatched !== false;
    if (result.state === 'unknown' && dispatchPossible) {
      cooldownUntilMs=Date.now()+180000;
      result={...result,cooldownUntilMs,retryAfterMs:180000};
    }
    await env.DB.prepare('UPDATE command_claims SET result=? WHERE id=?').bind(JSON.stringify(result),requestId).run();
    if (result.code === 'session_expired' && !credentials) {
      await env.DB.prepare('UPDATE sessions SET account=NULL,email=NULL,account_rev=account_rev+1 WHERE id=? AND account=?')
        .bind(session.id,session.account).run();
    }
    // Only definite non-dispatch can release this request's suppression marker.
    if (markerAttempted && result.dispatched === false && result.state !== 'unknown') {
      try {
        const cancelled=await upstream(env,'/api/mobile/impact-suppression',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({action:'cancel',requestId})});
        await cancelled.body?.cancel();
      } catch { /* Best effort: the persisted command result remains definitive. */ }
    }
    return json(result);
  } catch (error) {
    const unsent=!executionStarted && error instanceof UpstreamError;
    if (dispatchPossible) cooldownUntilMs=Date.now()+180000;
    const result=unsent
      ? {...upstreamFailure(error),state:'blocked',command:cmd,dispatched:false,vehicleConfirmed:false,retryable:false,failureStage:'cloud-preflight',
        message:'차량 명령을 보내지 않았습니다. '+UPSTREAM_MESSAGES[error.code]}
      : {ok:false,state:'unknown',message:'명령 완료를 확인하지 못했습니다. 재전송하지 않고 차량 상태를 확인해 주세요.',
        ...(cooldownUntilMs ? {cooldownUntilMs,retryAfterMs:180000} : {})};
    await env.DB.prepare('UPDATE command_claims SET result=? WHERE id=? AND result IS NULL').bind(JSON.stringify(result),requestId).run();
    return json(result,unsent ? 502 : 409);
  } finally {
    await env.DB.prepare('UPDATE command_lock SET until_ms=? WHERE id=1 AND until_ms=?').bind(cooldownUntilMs || Date.now()+3000,lease).run();
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
    await forgetExpiredAccounts(env);
    await env.DB.prepare('INSERT INTO sessions(id,csrf,expires) VALUES(?,?,?)').bind(await digest(token),csrf,Date.now()+SESSION_SECONDS*1000).run();
    return json({ok:true},200,{'set-cookie':sessionCookie(token)});
  }
  const session = await sessionFor(request,env);
  if (path === '/api/session' && request.method === 'GET') {
    await forgetExpiredAccounts(env);
    return json(session ? await sessionInfo(session,env) : {authenticated:false});
  }
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
    if (suffix==='json' && request.method==='GET') return composedFeed(env);
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
    const upstreamPath=suffix==='trips' ? '/api/mobile/web-trips' : '/api/'+suffix;
    return cleanResponse(await upstream(env, upstreamPath+(query.size?'?'+query:''),{method:request.method}));
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
  catch (error) {
    const limit = databaseLimitResponse(error);
    if (limit) return secure(json(limit.body,503,limit.headers));
    if (error instanceof UpstreamError) return secure(json(upstreamFailure(error),502));
    return secure(json({error:'request_failed',message:MESSAGE},400));
  }
},
// Daily cleanup: expired web sessions lose their multipack login even if no device opens the app again.
async scheduled(controller,env,ctx) {
  ctx.waitUntil(forgetExpiredAccounts(env));
}};
