import test from 'node:test';
import assert from 'node:assert/strict';
import {createECDH, randomBytes} from 'node:crypto';
import {builtinModules} from 'node:module';
import {fileURLToPath} from 'node:url';
import {build} from 'esbuild';
import {Miniflare, createFetchMock, fetch as mockTransportFetch} from 'miniflare';
import webpush from 'web-push';

const root = fileURLToPath(new URL('../', import.meta.url));
const provider = 'https://web.push.apple.com';
const payload = {id:'runtime-fixture', title:'Test', body:'private-runtime-fixture', expiresAt:2000000000000};
const vapid = webpush.generateVAPIDKeys();
const recipient = createECDH('prime256v1');
recipient.generateKeys();
const keys = {p256dh:recipient.getPublicKey().toString('base64url'), auth:randomBytes(16).toString('base64url')};
const mock = createFetchMock();
mock.disableNetConnect();
const calls = [];
const captures = [];
let mf;

// Bundle current source in memory, independent of the parent's generated worker.
// CJS dependencies must resolve to actual workerd built-ins, not Node host shims.
const builtins = new Set(builtinModules.map(name => name.replace(/^node:/, '')));
const fixture = `
import webpush from 'web-push';
import {deliver} from './server/push.mjs';

export default {async fetch(request) {
  const input = await request.json();
  const deleted = [];
  const env = {
    PUBLIC_ORIGIN:'https://runtime.test',
    VAPID_PUBLIC_KEY:input.vapid.publicKey,
    VAPID_PRIVATE_KEY:input.vapid.privateKey,
    DB:{prepare(sql) {return {
      bind(...args) {this.args=args; return this;},
      async all() {return {results:[{id:'fixture-subscription',subscription:JSON.stringify(input.subscription)}]};},
      async run() {if (sql.startsWith('DELETE')) deleted.push(...this.args); return {meta:{changes:1}};},
    };}},
  };
  if (input.action === 'deliver' || input.action === 'validated-deliver') {
    const validatingFetch = (url, options) => fetch(new Request(url, {...options,redirect:input.redirect}));
    const result = input.action === 'deliver'
      ? await deliver(env, input.payload)
      : await deliver(env, input.payload, null, validatingFetch);
    return Response.json({result,deleted});
  }
  let stage = 'encryption';
  try {
    const details = webpush.generateRequestDetails(input.subscription, JSON.stringify(input.payload), {
      TTL:300,urgency:'high',vapidDetails:{subject:env.PUBLIC_ORIGIN,publicKey:env.VAPID_PUBLIC_KEY,privateKey:env.VAPID_PRIVATE_KEY},
    });
    const headers = new Headers(details.headers);
    const summary = {
      encoding:headers.get('content-encoding'),
      vapid:headers.get('authorization')?.startsWith('vapid ') === true,
      encrypted:!Buffer.from(details.body).includes(Buffer.from(input.payload.body)),
      bytes:details.body.byteLength,
    };
    if (input.action === 'generate') return Response.json({ok:true,...summary});
    stage = 'transport';
    const options = {method:'POST',headers:details.headers,body:details.body,redirect:input.redirect,signal:AbortSignal.timeout(4000)};
    if (input.action === 'request') {
      const outgoing = new Request(details.endpoint, options);
      return Response.json({ok:true,redirect:outgoing.redirect,...summary});
    }
    const unboundFetch = fetch;
    const response = await unboundFetch(details.endpoint, options);
    await response.body?.cancel();
    return Response.json({ok:response.ok,status:response.status,...summary});
  } catch(error) {
    // Only synthetic test inputs enter this handler. Never return keys or headers.
    return Response.json({ok:false,stage,name:error.name,message:error.message});
  }
}};
`;

test.before(async () => {
  const bundle = await build({
    stdin:{contents:fixture,resolveDir:root,sourcefile:'push-runtime-fixture.mjs'},
    bundle:true,write:false,format:'esm',platform:'node',target:'es2022',logLevel:'silent',
    plugins:[{name:'workerd-native-builtins',setup(builder) {
      builder.onResolve({filter:/.*/}, args => {
        if (!builtins.has(args.path.replace(/^node:/, ''))) return;
        if (args.namespace === 'workerd-builtin') return {path:args.path,external:true};
        return {path:args.path.replace(/^node:/, ''),namespace:'workerd-builtin'};
      });
      builder.onLoad({filter:/.*/,namespace:'workerd-builtin'}, args => ({
        // Match Wrangler's terminal-only shim; crypto/fetch remain native.
        contents:`import native from ${JSON.stringify(args.path === 'tty' ? 'unenv/node/tty' : 'node:'+args.path)}; module.exports = native;`,
        loader:'js',resolveDir:root,
      }));
    }}],
  });
  mf = new Miniflare({
    modules:true,script:bundle.outputFiles[0].text,
    compatibilityDate:'2025-10-01',compatibilityFlags:['nodejs_compat'],
    // Miniflare's stock fetchMock adapter follows redirects in the host fetch.
    // Return each mocked response untouched so workerd enforces redirect mode.
    outboundService:request => mockTransportFetch(request,{dispatcher:mock,redirect:'manual'}),
  });
});

test.after(async () => {
  try { await mf?.dispose(); }
  finally { await mock.close(); }
});

async function run(action, path, redirect='manual') {
  const response = await mf.dispatchFetch('https://runtime.test/fixture', {
    method:'POST',headers:{'content-type':'application/json'},
    body:JSON.stringify({action,redirect,payload,vapid,subscription:{endpoint:provider+path,keys}}),
  });
  assert.equal(response.status, 200);
  const result = await response.json();
  await Promise.all(captures);
  return result;
}

function intercept(path, status=201, headers={}) {
  mock.get(provider).intercept({path,method:'POST'}).reply(options => {
    const requestHeaders = new Headers(options.headers);
    captures.push((async () => {
      const bytes = Buffer.from(await new Response(options.body).arrayBuffer());
      calls.push({
        path,method:options.method,bytes:bytes.length,
        encrypted:!bytes.includes(Buffer.from(payload.body)),
        encoding:requestHeaders.get('content-encoding'),
        vapid:requestHeaders.get('authorization')?.startsWith('vapid ') === true,
      });
    })());
    return {statusCode:status,data:'',responseOptions:{headers}};
  });
}

test('real workerd web-push encryption and VAPID generation succeed', async () => {
  const result = await run('generate', '/generate');
  assert.equal(result.ok, true, JSON.stringify(result));
  assert.equal(result.encoding, 'aes128gcm');
  assert.equal(result.vapid, true);
  assert.equal(result.encrypted, true);
  assert.ok(result.bytes > 103 && result.bytes <= 4096);
  assert.equal(calls.length, 0);
});

test('real workerd Request rejects error redirect and accepts manual with encrypted options', async () => {
  const rejected = await run('request', '/constructor-error', 'error');
  assert.equal(rejected.ok, false);
  assert.equal(rejected.stage, 'transport');
  assert.equal(rejected.name, 'TypeError');
  assert.match(rejected.message, /Invalid redirect value.*follow.*manual/);
  const accepted = await run('request', '/constructor-manual');
  assert.equal(accepted.ok, true, JSON.stringify(accepted));
  assert.equal(accepted.redirect, 'manual');
  assert.equal(calls.length, 0);
});

test('unbound global fetch rejects error before network and sends manual through fetchMock', async () => {
  const before = calls.length;
  const rejected = await run('transport', '/fetch-error', 'error');
  assert.equal(rejected.name, 'TypeError');
  assert.equal(rejected.stage, 'transport');
  assert.match(rejected.message, /Invalid redirect value/);
  assert.equal(calls.length, before);
  intercept('/fetch-manual');
  const accepted = await run('transport', '/fetch-manual');
  assert.equal(accepted.ok, true, JSON.stringify(accepted));
  assert.equal(accepted.status, 201);
  assert.equal(calls.length, before+1);
});

test('deliver with Request-validating adapter reproduces old transport failure, then manual succeeds', async () => {
  const before = calls.length;
  const rejected = await run('validated-deliver', '/deliver-error', 'error');
  assert.equal(rejected.result.sent, 0);
  assert.equal(rejected.result.failed, 1);
  assert.equal(calls.length, before);
  intercept('/deliver-validated-manual');
  const accepted = await run('validated-deliver', '/deliver-validated-manual');
  assert.equal(accepted.result.sent, 1, JSON.stringify(accepted.result));
  assert.equal(accepted.result.failed, 0);
  assert.equal(calls.length, before+1);
});

test('current deliver uses actual global fetch and sends encrypted VAPID POST without a JS fetch stub', async () => {
  intercept('/deliver-default');
  const result = await run('deliver', '/deliver-default');
  assert.equal(result.result.sent, 1, JSON.stringify(result.result));
  assert.equal(result.result.failed, 0);
  assert.deepEqual(result.deleted, []);
  const sent = calls.at(-1);
  assert.equal(sent.path, '/deliver-default');
  assert.equal(sent.method, 'POST');
  assert.equal(sent.encoding, 'aes128gcm');
  assert.equal(sent.vapid, true);
  assert.equal(sent.encrypted, true);
  assert.ok(sent.bytes > 103 && sent.bytes <= 4096);
});

test('manual redirect responses fail without forwarding VAPID or ciphertext to Location', async () => {
  for (const status of [301,302,303,307,308]) {
    let followed = 0;
    const target = '/redirect-target-'+status;
    mock.get('https://redirect.invalid').intercept({path:target,method:/.*/}).reply(() => {
      followed++;
      return {statusCode:201,data:''};
    }).persist();
    const path = '/redirect-'+status;
    intercept(path, status, {location:'https://redirect.invalid'+target});
    const before = calls.length;
    const result = await run('deliver', path);
    assert.equal(result.result.sent, 0);
    assert.equal(result.result.failed, 1);
    assert.deepEqual(result.deleted, []);
    assert.equal(calls.length, before+1);
    assert.equal(followed, 0, 'must not follow provider redirect');
  }
});

test('provider rejection preserves subscription; terminal expiry removes only that subscription', async () => {
  for (const status of [400,403,404,410,429,500]) {
    const path = '/provider-'+status;
    intercept(path, status);
    const result = await run('deliver', path);
    assert.equal(result.result.sent, 0);
    assert.equal(result.result.failed, 1);
    assert.deepEqual(result.deleted, [404,410].includes(status) ? ['fixture-subscription'] : []);
    assert.equal(calls.at(-1).path, path);
  }
});

test('positive control: workerd itself follows Location only with explicit follow mode', async () => {
  let followed = 0;
  mock.get('https://redirect.invalid').intercept({path:'/positive-control',method:'POST'}).reply(() => {
    followed++;
    return {statusCode:201,data:''};
  });
  intercept('/follow-positive-control', 307, {location:'https://redirect.invalid/positive-control'});
  const result = await run('transport', '/follow-positive-control', 'follow');
  assert.equal(result.ok, true, JSON.stringify(result));
  assert.equal(result.status, 201);
  assert.equal(followed, 1);
});
