import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../client/pwa.js', import.meta.url), 'utf8');
const fixtureSession = {authenticated:true, csrfToken:'synthetic-csrf', account:{loggedIn:true}};
const tick = () => new Promise(resolve => setImmediate(resolve));

function element() {
  const children = new Map();
  return {dataset:{}, handlers:{}, value:'', hidden:false,
    addEventListener(name, fn) { this.handlers[name] = fn; },
    querySelector(selector) {
      if (!children.has(selector)) children.set(selector, element());
      return children.get(selector);
    },
    append() {}, prepend() {},
  };
}

function harness(sessionResponse = fixtureSession, sessionStatus = 200) {
  const login = element(), actions = element(), body = element(), created = [login, actions];
  const events = {}, calls = [], routes = new Map(), notices = [];
  let starts = 0, stops = 0, rechecks = 0, token = '', replacements = 0;
  let unsubscribe = async () => true;
  const subscription = {toJSON:() => ({endpoint:'https://fixture.invalid'}), unsubscribe:() => unsubscribe()};
  const registration = {pushManager:{getSubscription:async () => subscription}};
  const window = {PushManager:{}, Notification:{},
    TraverseWeb:{
      start:async session => { starts++; token = session.csrfToken; return true; },
      stop:() => { stops++; token = ''; },
      refreshSession:async () => { rechecks++; return true; },
      csrfToken:() => token,
    },
    showStatus:(...args) => notices.push(args), addEventListener:(name, fn) => { events[name] = fn; },
  };
  const document = {body, createElement:() => created.shift(), querySelector:() => element(), querySelectorAll:() => [],
    getElementById:id => id === 'pwa-error' ? login.querySelector('#pwa-error') : null};
  routes.set('/api/session', async () => ({ok:sessionStatus === 200, status:sessionStatus, json:async () => sessionResponse}));
  const context = {window, document,
    navigator:{userAgent:'fixture', serviceWorker:{register:async () => registration, ready:Promise.resolve(), addEventListener() {}}},
    Notification:{permission:'granted'}, location:{replace:() => { replacements++; }},
    fetch:async (path, options) => {
      calls.push({path, ...options});
      return routes.has(path) ? routes.get(path)(options) : {ok:true, status:200, json:async () => ({ok:true})};
    },
  };
  vm.runInNewContext(source, context, {filename:'pwa.js'});
  return {login, actions, body, events, calls, routes, notices,
    get counts() { return {starts, stops, rechecks, replacements}; },
    setUnsubscribe(fn) { unsubscribe = fn; }, setToken(value) { token = value; },
    reply(path, result, status = 200) { routes.set(path, async () => ({ok:status >= 200 && status < 300, status, json:async () => result})); },
    click:id => actions.querySelector(id).handlers.click(),
  };
}

test('PWA authenticated API 401 locks immediately even when its JSON body is malformed', async () => {
  const h = harness(); await tick();
  h.routes.set('/api/push/test', async () => ({ok:false, status:401, json:async () => { throw Error('invalid JSON'); }}));
  await h.click('#pwa-test');
  assert.equal(h.body.dataset.pwa, 'locked');
  assert.equal(h.login.hidden, false);
  assert.equal(h.counts.stops, 1);
});

test('wrong web login does not repeatedly stop the bridge and displays the server error', async () => {
  const h = harness({authenticated:false}); await tick();
  const stops = h.counts.stops;
  h.reply('/api/login', {message:'Wrong fixture password'}, 401);
  h.login.querySelector('input').value = 'synthetic-wrong-password';
  await h.login.querySelector('form').handlers.submit({preventDefault() {}});
  assert.equal(h.counts.stops, stops);
  assert.equal(h.login.querySelector('#pwa-error').textContent, 'Wrong fixture password');
  assert.equal(h.login.querySelector('button').disabled, false);
});

test('database outage is visible on restore and login without logout or subscription deletion', async () => {
  const message = 'Database daily limit fixture; retry after reset.';
  const h = harness({message, code:'database_daily_limit'}, 503);
  let unsubscribed = 0;
  h.setUnsubscribe(async () => { unsubscribed++; });
  await tick();
  assert.equal(h.login.querySelector('#pwa-error').textContent, message);
  assert.equal(h.login.hidden, false);
  assert.equal(h.counts.starts, 0);
  h.reply('/api/login', {ok:true});
  await h.login.querySelector('form').handlers.submit({preventDefault() {}});
  assert.equal(h.login.querySelector('#pwa-error').textContent, message);
  assert.equal(h.login.querySelector('button').disabled, false);
  assert.equal(unsubscribed, 0);
  assert.equal(h.counts.replacements, 0);
  assert.ok(!h.calls.some(call => /logout|unsubscribe|command/.test(call.path)));
  // A server recovery reuses the existing cookie; no credential clearing is required.
  h.reply('/api/session', fixtureSession);
  h.events.pageshow({persisted:true}); await tick();
  assert.equal(h.login.hidden, true);
  assert.equal(h.counts.starts, 1);
});

test('WebKit transport failures show Korean guidance without logging out or deleting subscriptions', async () => {
  const h = harness({authenticated:false}); await tick();
  let unsubscribed = 0; h.setUnsubscribe(async () => { unsubscribed++; });
  for (const path of ['/api/session','/api/login']) h.routes.set(path,async () => {throw new TypeError('Load failed');});
  h.events.pageshow({persisted:true}); await tick();
  assert.equal(h.login.querySelector('#pwa-error').textContent,'서버 연결을 확인해 주세요.');
  await h.login.querySelector('form').handlers.submit({preventDefault() {}});
  assert.equal(h.login.querySelector('#pwa-error').textContent,'서버 연결을 확인해 주세요.');
  assert.equal(h.login.querySelector('button').disabled,false);
  assert.equal(h.counts.starts,0); assert.equal(unsubscribed,0);
  assert.ok(!h.calls.some(c => /logout|unsubscribe|command/.test(c.path)));
});

test('successful logout locks before push cleanup; a cleanup failure cannot leave the app unlocked', async () => {
  const h = harness(); await tick();
  h.setUnsubscribe(async () => {
    assert.equal(h.body.dataset.pwa, 'locked');
    assert.equal(h.login.hidden, false);
    throw Error('Synthetic unsubscribe failure');
  });
  await h.click('#pwa-logout');
  assert.equal(h.counts.stops, 1);
  assert.equal(h.counts.replacements, 1);
  assert.equal(h.body.dataset.pwa, 'locked');
});

test('failed logout is visible; expired logout still locks', async () => {
  for (const status of [503, 401]) {
    const h = harness(); await tick();
    h.reply('/api/logout', {message:'Synthetic logout failure'}, status);
    await h.click('#pwa-logout');
    assert.equal(h.body.dataset.pwa, status === 401 ? 'locked' : 'ready');
    assert.equal(h.notices.at(-1)[0], 'Synthetic logout failure');
  }
});

test('bfcache restoration rechecks rather than restarting bridge/live', async () => {
  const h = harness(); await tick();
  h.events.pageshow({persisted:true}); await tick();
  assert.deepEqual(h.counts, {starts:1, stops:0, rechecks:1, replacements:0});
  assert.equal(h.calls.filter(call => call.path === '/api/session').length, 1);
});

test('PWA mutations use the current bridge CSRF and session-update notifications', async () => {
  const h = harness(); await tick();
  h.setToken('rotated-fixture');
  h.events['traverseweb:sessionupdated']({detail:{csrfToken:'rotated-fixture'}});
  await h.click('#pwa-test');
  const request = h.calls.at(-1);
  assert.equal(request.headers['x-csrf-token'], 'rotated-fixture');
  assert.equal(request.credentials, 'same-origin');
  assert.equal(request.cache, 'no-store');
});

test('late bootstrap cannot reopen the app after an expiry event', async () => {
  const h = harness({authenticated:false}); await tick();
  let finish;
  h.routes.set('/api/session', () => new Promise(resolve => { finish = resolve; }));
  h.events.pageshow({persisted:true});
  h.events['traverseweb:sessionlost']();
  finish({ok:true, status:200, json:async () => fixtureSession}); await tick();
  assert.equal(h.body.dataset.pwa, 'locked');
  assert.equal(h.login.hidden, false);
  assert.equal(h.counts.starts, 0);
});
