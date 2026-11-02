const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, 'client/bridge.js'), 'utf8');
const NOW = Date.parse('2026-11-02T03:00:00Z');
const iso = offset => new Date(NOW + offset).toISOString();
const SUPPORTED_COMMANDS = ['DOOR_LOCK', 'DOOR_UNLOCK', 'DRIVER_DOOR_UNLOCK', 'VEHICLE_START', 'VEHICLE_STOP',
  'WINDOW_OPEN', 'WINDOW_CLOSE', 'TRUNK_OPEN', 'TRUNK_CLOSE', 'MAIN_LIGHT_ON', 'MAIN_LIGHT_OFF'];
const SESSION = { authenticated: true, csrfToken: 'test-csrf', capabilities: {
  commands: false, supportedCommands: SUPPORTED_COMMANDS, live: true, ambient: true,
} };
const COMMAND_SESSION = { ...SESSION, capabilities: { ...SESSION.capabilities, commands: true } };
const CALLBACKS = [
  'showStatus', 'updateWayonCloudKeyInput', 'updateGmoneAccountState', 'updateVehicleCommandReady',
  'setVehicleDataState', 'updateCarStatus', 'updateGmoneDetails', 'updateWayonCloudState',
  'updateWayonLiveState', 'updateSavedLocation', 'markWayonCloudUnavailable', 'updateWayonCloudSnapshots',
  'onWayonCloudDataUpdated', 'onWayonCloudHistoryUpdated', 'setButtonFeedback', 'updateGmoneExtendedControlState',
  'applyGmoneCommandOptimistic', 'onWayonLiveSession', 'onWayonLiveSessionError', 'onAmbientCommandResult',
  'stopWayonLiveView', 'updateHeroLocationMap', 'updateMyLocation', 'updateWayonImpactState',
  'updateWindowPositionSensorsVisibility', 'updateGmoneSettingsSaveState', 'updateGmoneDiagnosticActionState', 'updateDeviceList',
];
function snapshot(overrides = {}) {
  return { ok: true, source: 'gmone', updatedAt: iso(-10000), stale: false, data: {
    range: '450', battery: '12.5', battery_level: '80', mileage: '12345', fuel: '50', oil: '90',
    last_update: iso(-10000), tire_pressure: '60 kPa', tire_pressure_all: 'FL: 60 kPa, FR: 240 kpa',
    gmone_details: { rawStatus: { fCap: 80, fLvl: 50 }, vehicleState: { engineRunning: false } },
  }, ...overrides };
}
function combined(overrides = {}) {
  return { vehicleStatus: snapshot(), state: {
    updated_at: iso(-5000), onroad: 1, ignition: 1, enabled: 0, thermal_status: 'green',
    voltage_v: '13.1', latitude: 37.5, longitude: 127.1, speed_mps: 10,
    raw_json: JSON.stringify({ gps: { updatedAt: iso(-6000), fresh: true },
      openpilot: { active: false, engageable: true, state: 'disabled' },
      vehicleInput: { source: 'vehicle' }, deviceInput: { source: 'device' } }),
  }, vehicleLock: { locked: true, occurredAt: iso(-5000) }, trips: [], snapshots: [], ...overrides };
}
function harness() {
  let now = NOW, nextTimer = 0, uuid = 0;
  const timers = new Map(), routes = new Map(), calls = [], outputs = [], events = [];
  const documentListeners = {}, windowListeners = {};
  const root = {
    document: { hidden: false, addEventListener: (name, fn) => { documentListeners[name] = fn; } },
    navigator: {}, location: { href: 'https://traverse.example/main.html', protocol: 'https:', host: 'traverse.example' },
    crypto: { randomUUID: () => `test-request-${++uuid}` },
    addEventListener: (name, fn) => { windowListeners[name] = fn; },
    dispatchEvent: event => { events.push(event.type); },
    open: (...args) => { outputs.push(['open', ...args]); },
    setTimeout: (fn, delay) => { timers.set(++nextTimer, { fn, at: now + delay }); return nextTimer; },
    clearTimeout: id => { timers.delete(id); },
    fetch: async (url, options) => {
      calls.push({ url, ...options });
      const route = routes.get(`${options.method} ${url}`);
      if (!route?.length) throw new Error(`Unexpected request: ${options.method} ${url}`);
      const item = route.length > 1 ? route.shift() : route[0];
      const result = typeof item === 'function' ? await item(options) : item;
      if (result instanceof Error) throw result;
      return { ok: result.status >= 200 && result.status < 300, status: result.status, json: async () => result.body };
    },
  };
  for (const name of CALLBACKS) root[name] = (...args) => { outputs.push([name, ...args]); };
  class Clock extends Date { constructor(...args) { super(...(args.length ? args : [now])); } static now() { return now; } }
  const context = vm.createContext({ window: root, Date: Clock, AbortController, URL, CustomEvent: class { constructor(type) { this.type = type; } } });
  vm.runInContext(source, context, { filename: 'bridge.js' });
  const h = {
    root, context, calls, outputs, events, timers, documentListeners, windowListeners,
    reply(url, body, method = 'GET', status = 200) {
      const key = `${method} ${url}`;
      routes.set(key, [...(routes.get(key) || []), { body, status }]);
      return h;
    },
    route(url, fn, method = 'GET') { routes.set(`${method} ${url}`, [fn]); return h; },
    last: name => outputs.filter(item => item[0] === name).at(-1)?.slice(1),
    all: name => outputs.filter(item => item[0] === name).map(item => item.slice(1)),
    async start(payload = combined(), session = SESSION) {
      h.reply('/api/wayon/json', payload);
      return root.TraverseWeb.start(session);
    },
    async advance(ms) {
      const until = now + ms;
      for (;;) {
        const entry = [...timers].filter(([, timer]) => timer.at <= until).sort((a, b) => a[1].at - b[1].at)[0];
        if (!entry) break;
        now = entry[1].at;
        timers.delete(entry[0]);
        await entry[1].fn();
        for (let i = 0; i < 10; i++) await Promise.resolve();
      }
      now = until;
    },
  };
  return h;
}

test('shim covers all 35 native methods and does not bootstrap or persist data on its own', () => {
  const h = harness();
  const kotlin = fs.readFileSync(path.join(__dirname, '../my-traverse-next/app/src/main/java/com/example/carcontroller/MainActivity.kt'), 'utf8');
  const names = [...kotlin.matchAll(/@JavascriptInterface\s+fun\s+(\w+)/g)].map(match => match[1]).sort();
  assert.equal(names.length, 35);
  assert.deepEqual(Object.keys(h.root.Android).sort(), names);
  assert.equal(h.calls.length, 0);
  assert.doesNotMatch(source, /localStorage|sessionStorage|indexedDB/);
});

test('session bootstrap uses cookies, no bearer secret, and server snapshots are cached, not live', async () => {
  const h = harness();
  h.reply('/api/session', SESSION).reply('/api/wayon/json', combined());
  assert.equal(await h.root.TraverseWeb.start(), true);
  assert.deepEqual(h.calls.map(call => call.url), ['/api/session', '/api/wayon/json']);
  for (const call of h.calls) {
    assert.equal(call.credentials, 'same-origin');
    assert.equal(call.cache, 'no-store');
    assert.equal(call.headers.Authorization, undefined);
  }
  assert.deepEqual(h.last('updateWayonCloudKeyInput'), ['session']);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
  assert.deepEqual(h.last('setVehicleDataState'), ['cached', iso(-10000), false]);
  assert.deepEqual(h.last('updateCarStatus'), ['450', '12.5', '80', '12345', '40.0', iso(-10000), '90', '240 kpa', 'FL: 240 kpa, FR: 240 kpa']);
  const details = JSON.parse(h.last('updateGmoneDetails')[0]);
  assert.equal(details.meta.cached, true);
  assert.equal(details.meta.stale, false);
  assert.equal(details.fuel.levelLiters, 40);
});

test('Firebase wins only when newer; GMOne details and supplemental fields survive the merge', async () => {
  const h = harness();
  const status = snapshot({ sources: {
    firebase: { updatedAt: iso(-1000), data: { range: '999', last_update: iso(-1000), source: 'firebase-new' } },
    gmone: { updatedAt: iso(-10000), data: snapshot().data, module: { settings: { test: 1 } },
      health: { dtcCount: 2 }, diagnostic: { pending: false }, collectedAt: iso(-5000) },
  } });
  const original = JSON.stringify(status);
  await h.start(combined({ vehicleStatus: status }));
  const details = JSON.parse(h.last('updateGmoneDetails')[0]);
  assert.equal(h.last('updateCarStatus')[0], '999');
  assert.equal(details.meta.source, 'firebase-new');
  assert.equal(details.meta.updatedAt, iso(-1000));
  assert.equal(details.meta.collectedAt, iso(-5000));
  assert.equal(details.module.settings.test, 1);
  assert.equal(details.diagnostics.dtcCount, 2);
  assert.equal(details.refresh.collector.pending, false);
  assert.equal(JSON.stringify(status), original);
});

test('GMOne wins ties and older Firebase; stale and impossible fuel remain explicit', async () => {
  const h = harness();
  const data = { ...snapshot().data, fuel: '500', gmone_details: { fuel: { capacityLiters: 80, levelLiters: 500 } } };
  await h.start(combined({ vehicleStatus: snapshot({ stale: true, data, sources: {
    firebase: { updatedAt: iso(-10000), data: { range: '999' } }, gmone: { updatedAt: iso(-10000), data },
  } }) }));
  assert.equal(h.last('updateCarStatus')[0], '450');
  assert.equal(h.last('updateCarStatus')[4], '--');
  const details = JSON.parse(h.last('updateGmoneDetails')[0]);
  assert.equal(details.meta.stale, true);
  assert.equal(details.fuel.levelLiters, undefined);
});

test('missing, failed, old and future snapshots never produce synthetic status', async () => {
  for (const status of [null, { ok: false }, snapshot({ updatedAt: null, data: {} }),
    snapshot({ data: { last_update: iso(-8 * 86400000), range: '123' } }),
    snapshot({ data: { last_update: iso(121000), range: '123' } })]) {
    const h = harness();
    await h.start(combined({ vehicleStatus: status }));
    assert.equal(h.all('updateCarStatus').length, 0);
    assert.deepEqual(h.last('setVehicleDataState'), ['unavailable', '', false]);
    assert.deepEqual(h.last('updateGmoneDetails'), [null]);
  }
});

test('Korean wall timestamps are interpreted as Asia/Seoul, not the phone timezone', async () => {
  const h = harness();
  const stamp = '2026-11-02 11:59:50';
  await h.start(combined({ vehicleStatus: snapshot({ updatedAt: stamp, data: { ...snapshot().data, last_update: stamp } }) }));
  assert.equal(h.last('setVehicleDataState')[0], 'cached');
});

test('an older valid snapshot cannot roll back a newer observation; explicit missing clears it', async () => {
  const h = harness();
  await h.start();
  h.route('/api/wayon/json', () => ({ status: 200, body: combined({ vehicleStatus: snapshot({
    updatedAt: iso(-100000), data: { ...snapshot().data, last_update: iso(-100000), range: '1' },
  }) }) }));
  await h.root.Android.refreshWayonCloudData();
  assert.equal(h.last('updateCarStatus')[0], '450');
  h.route('/api/wayon/json', () => ({ status: 200, body: combined({ vehicleStatus: null }) }));
  await h.root.Android.refreshWayonCloudData();
  assert.equal(h.last('setVehicleDataState')[0], 'unavailable');
});

test('state mapping retains GPS timestamp, zero/false, provenance and nullable inputs', async () => {
  const h = harness();
  await h.start();
  assert.deepEqual(h.last('updateWayonCloudState'), ['13.1', '11:59', 'ONROAD', '36 km/h', 37.5, 127.1, '37.50000, 127.10000', NOW - 6000]);
  const state = JSON.parse(h.last('updateWayonLiveState')[0]);
  assert.equal(state.openpilotEnabled, false);
  assert.equal(state.openpilotActive, false);
  assert.equal(state.openpilotEngageable, true);
  assert.equal(state.doorLocked, true);
  assert.deepEqual(state.vehicleInput, { source: 'vehicle' });
  assert.deepEqual(state.deviceInput, { source: 'device' });
  h.route('/api/wayon/json', () => ({ status: 200, body: combined({ state: {
    updated_at: iso(-1000), onroad: false, raw_json: {}, speed_mps: 0,
  } }) }));
  await h.root.Android.refreshWayonCloudData();
  const missing = JSON.parse(h.last('updateWayonLiveState')[0]);
  assert.equal(missing.ignition, null);
  assert.equal(missing.latitude, null);
  assert.equal(missing.longitude, null);
  assert.equal(missing.voltageV, null);
  assert.equal(missing.gpsUpdatedAtEpochMs, null);
  assert.equal(missing.speedKph, 0);
});

test('missing telemetry does not manufacture parked state or suppress independent gallery', async () => {
  for (const state of [null, { updated_at: iso(-1000) }, { onroad: false }]) {
    const h = harness();
    const snapshots = [{ id: 'snapshot-1', kv_key: 'fixture-image', captured_at: iso(-5000), camera: 'wide' }];
    await h.start(combined({ state, snapshots }));
    assert.equal(h.all('updateWayonCloudState').length, 0);
    assert.deepEqual(JSON.parse(h.last('updateWayonCloudSnapshots')[0]), snapshots);
    assert.match(h.last('markWayonCloudUnavailable')[0], /unavailable/);
  }
});

test('history getter stays synchronous; trip units, route fallback, KST and full history work', async () => {
  const h = harness();
  const trip = { id: 'trip-1', started_at: '2026-11-01T23:00:00Z', ended_at: iso(-5000),
    distance_m: 1200, duration_s: 120, route: JSON.stringify([{ speedMps: 12 }]),
    start_lat: 0, start_lon: 0, end_lat: 37.5, end_lon: 127.1, analysis: { score: 1 }, health: { samples: 2 } };
  await h.start(combined({ trips: [trip] }));
  assert.equal(typeof h.root.Android.getDrivingHistory(), 'string');
  const [item] = JSON.parse(h.root.Android.getDrivingHistory());
  assert.equal(item.date, '2026-11-02');
  assert.equal(item.time, '08:00');
  assert.equal(item.distance, '1.20 km');
  assert.equal(item.duration, '00:02:00');
  assert.equal(item.avgSpeed, '36 km/h');
  assert.equal(item.topSpeed, '43 km/h');
  assert.equal(item.startAddress, '0.00000, 0.00000');
  assert.equal(item.routePointCount, 1);
  h.reply('/api/wayon/trips?limit=1000', { trips: [trip, { ...trip, id: 'trip-2', started_at: iso(-10000) }] });
  await h.root.Android.refreshWayonCloudTrips();
  await h.root.Android.refreshWayonCloudData();
  assert.equal(JSON.parse(h.root.Android.getDrivingHistory()).length, 2);
  assert.equal(JSON.parse(h.root.Android.getDrivingHistory())[0].id, 'trip-2');
});

test('failed feed is unavailable, not a success containing the previous snapshot', async () => {
  const h = harness();
  await h.start();
  h.route('/api/wayon/json', () => ({ status: 503, body: { error: 'not displayed upstream detail' } }));
  assert.equal(await h.root.Android.refreshWayonCloudData(), false);
  assert.equal(h.last('setVehicleDataState')[0], 'unavailable');
  assert.equal(h.last('showStatus')[1], 'danger');
});

test('overlapping feed reads are coalesced and late data after stop is ignored', async () => {
  const h = harness();
  await h.start();
  let resolve;
  h.route('/api/wayon/json', () => new Promise(done => { resolve = done; }));
  const one = h.root.Android.refreshWayonCloudData();
  const two = h.root.Android.refreshVehicleScreen();
  assert.equal(one, two);
  const pendingSignal = h.calls.at(-1).signal;
  h.root.TraverseWeb.stop();
  assert.equal(pendingSignal.aborted, true);
  const count = h.all('updateCarStatus').length;
  resolve({ status: 200, body: combined() });
  assert.equal(await one, false);
  assert.equal(h.all('updateCarStatus').length, count);
  assert.equal(h.root.Android.getDrivingHistory(), '[]');
  assert.equal(h.timers.size, 0);
});

test('401 clears grants and informs the parent login overlay', async () => {
  const h = harness();
  await h.start(combined(), COMMAND_SESSION);
  h.route('/api/wayon/json', () => ({ status: 401, body: {} }));
  await h.root.Android.refreshWayonCloudData();
  assert.deepEqual(h.events, ['traverseweb:sessionlost']);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
  assert.deepEqual(h.last('updateWayonCloudKeyInput'), ['']);
});

test('commands require matching protocol success, CSRF and a request id without asserting physical success', async () => {
  const h = harness();
  await h.start();
  assert.equal(await h.root.Android.handleLongPress('DOOR_LOCK', 'Lock', 'door'), false);
  assert.equal(h.calls.some(call => call.url === '/api/command'), false);
  await h.root.TraverseWeb.start(COMMAND_SESSION);
  h.route('/api/command', options => {
    const body = JSON.parse(options.body);
    return { status: 200, body: { ok: true, state: 'server_responded', command: body.command, requestId: body.requestId,
      vehicleConfirmed: false, message: 'Physical vehicle success must not be displayed' } };
  }, 'POST');
  assert.equal(await h.root.Android.handleLongPress('DOOR_LOCK', 'Lock', 'door'), true);
  const call = h.calls.find(call => call.url === '/api/command');
  assert.equal(call.headers['X-CSRF-Token'], 'test-csrf');
  assert.equal(call.credentials, 'same-origin');
  assert.deepEqual(JSON.parse(call.body), { command: 'DOOR_LOCK', requestId: 'test-request-1', confirmed: true });
  assert.equal(h.all('applyGmoneCommandOptimistic').length, 0);
  assert.deepEqual(h.last('setButtonFeedback'), ['door', '', 'DOOR_LOCK']);
  assert.equal(h.last('showStatus')[1], 'info');
  assert.match(h.last('showStatus')[0], /\uC11C\uBC84/);
  assert.match(h.last('showStatus')[0], /\uBCC4\uB3C4\uB85C \uD655\uC778/);
  assert.doesNotMatch(h.last('showStatus')[0], /Physical vehicle success/);
  assert.equal(await h.root.Android.handleClick('DOOR_UNLOCK', 'Unlock', 'door'), false);
  assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1);
});

test('ambiguous and failed commands never retry or optimistically report success', async () => {
  for (const body of [{}, { ok: false }, { ok: true, command: 'DOOR_LOCK' },
    { ok: true, state: 'server_responded' }, { ok: true, state: 'server_responded', command: 'DIFFERENT' },
    { ok: true, state: 'acknowledged', command: 'DOOR_LOCK' }, { ok: true, state: 'unknown', command: 'DOOR_LOCK' },
    { ok: true, state: 'blocked', command: 'DOOR_LOCK' }, { ok: false, state: 'server_responded', command: 'DOOR_LOCK' },
    { ok: true, state: 'server_responded', command: 'DOOR_LOCK', requestId: 'mismatched' },
    { ok: true, state: 'server_responded', command: 'DOOR_LOCK', requestId: '' }]) {
    const h = harness();
    await h.start(combined(), COMMAND_SESSION);
    h.reply('/api/command', body, 'POST');
    assert.equal(await h.root.Android.sendGmoneExtendedControl('DOOR_LOCK', 'door'), false);
    await h.advance(5000);
    assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1);
    assert.equal(h.all('applyGmoneCommandOptimistic').length, 0);
    assert.deepEqual(h.last('updateGmoneExtendedControlState'), ['door', false, null]);
  }
});

test('missing CSRF prevents every mutation without a network call', async () => {
  const h = harness();
  await h.start(combined(), { authenticated: true, capabilities: COMMAND_SESSION.capabilities });
  await h.root.Android.handleClick('DOOR_LOCK', 'Lock', 'door');
  assert.equal(h.calls.some(call => call.method !== 'GET'), false);
});

test('account login/logout use specified routes and derive capability from the account response', async () => {
  const h = harness();
  await h.start();
  h.reply('/api/account', { loggedIn: true, email: 'test@example.invalid', message: 'Connected' }, 'POST');
  assert.equal(await h.root.Android.loginGmone(' test@example.invalid ', 'fixture-password'), true);
  const login = h.calls.find(call => call.url === '/api/account');
  assert.deepEqual(JSON.parse(login.body), { email: 'test@example.invalid', password: 'fixture-password' });
  assert.equal(login.headers['X-CSRF-Token'], 'test-csrf');
  assert.deepEqual(h.last('updateGmoneAccountState'), [true, 'test@example.invalid', 'Connected', false]);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [true]);
  h.reply('/api/account', { loggedIn: false, email: '', message: 'Logged out' }, 'DELETE');
  assert.equal(await h.root.Android.logoutGmone(), true);
  const logout = h.calls.find(call => call.url === '/api/account' && call.method === 'DELETE');
  assert.equal(logout.body, undefined);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
  assert.equal(h.calls.some(call => call.url === '/api/session'), false);
});

test('CSRF accessor is available for the original JPEG uploader and clears on stop', async () => {
  const h = harness();
  assert.equal(h.root.TraverseWeb.csrfToken(), '');
  await h.start();
  assert.equal(h.root.TraverseWeb.csrfToken(), 'test-csrf');
  h.root.TraverseWeb.stop();
  assert.equal(h.root.TraverseWeb.csrfToken(), '');
  await h.root.TraverseWeb.start({ authenticated: false });
  assert.equal(h.root.TraverseWeb.csrfToken(), '');
});

test('account fields from session initialize the existing settings UI', async () => {
  const h = harness();
  await h.start(combined(), { ...COMMAND_SESSION, account: { loggedIn: true, email: 'test@example.invalid' } });
  assert.equal(h.last('updateGmoneAccountState')[0], true);
  assert.equal(h.last('updateGmoneAccountState')[1], 'test@example.invalid');
  assert.deepEqual(h.last('updateVehicleCommandReady'), [true]);
  await h.root.TraverseWeb.start({ ...COMMAND_SESSION, account: { loggedIn: false, email: '' } });
  assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
});

test('account switch cancels old reads and cannot accept their snapshots', async () => {
  const h = harness();
  await h.start();
  let resolve;
  h.route('/api/wayon/json', () => new Promise(done => { resolve = done; }));
  const oldRead = h.root.Android.refreshWayonCloudData();
  const oldSignal = h.calls.at(-1).signal;
  h.reply('/api/account', { loggedIn: true, email: 'new@example.invalid', message: 'Connected' }, 'POST');
  h.route('/api/wayon/json', () => ({ status: 200, body: combined({ vehicleStatus: null }) }));
  await h.root.Android.loginGmone('new@example.invalid', 'fixture-password');
  assert.equal(oldSignal.aborted, true);
  const count = h.all('updateCarStatus').length;
  resolve({ status: 200, body: combined() });
  await oldRead;
  assert.equal(h.all('updateCarStatus').length, count);
  assert.equal(h.last('setVehicleDataState')[0], 'unavailable');
});

test('late session bootstrap after stop cannot resurrect authentication', async () => {
  const h = harness();
  let resolve;
  h.route('/api/session', () => new Promise(done => { resolve = done; }));
  const pending = h.root.TraverseWeb.start();
  h.root.TraverseWeb.stop();
  resolve({ status: 200, body: SESSION });
  assert.equal(await pending, false);
  assert.equal(h.root.TraverseWeb.csrfToken(), '');
  assert.equal(h.calls.some(call => call.url === '/api/wayon/json'), false);
});

test('visibility pauses polling and a visible foreground refresh does not reset the key input', async () => {
  const h = harness();
  await h.start();
  const keyUpdates = h.all('updateWayonCloudKeyInput').length;
  h.root.document.hidden = true;
  h.documentListeners.visibilitychange();
  await h.advance(30000);
  assert.equal(h.calls.length, 1);
  h.root.document.hidden = false;
  h.documentListeners.visibilitychange();
  await h.root.Android.refreshWayonCloudData();
  assert.equal(h.calls.length, 2);
  assert.equal(h.all('updateWayonCloudKeyInput').length, keyUpdates);
});

test('read timeout aborts the transport and leaves an explicit unavailable state', async () => {
  const h = harness();
  await h.start();
  h.route('/api/wayon/json', options => new Promise((resolve, reject) => {
    options.signal.addEventListener('abort', () => { const error = new Error('aborted'); error.name = 'AbortError'; reject(error); });
  }));
  const pending = h.root.Android.refreshWayonCloudData();
  await h.advance(20000);
  assert.equal(await pending, false);
  assert.equal(h.last('setVehicleDataState')[0], 'unavailable');
  assert.match(h.last('showStatus')[0], /timed out/);
});

test('live session supplies the same-origin stream URL and protocol; external URLs are rejected', async () => {
  const h = harness();
  await h.start();
  h.reply('/api/live/session', { websocketUrl: '/api/live/stream?session=fixture', protocol: 'fixture-protocol' }, 'POST');
  assert.equal(await h.root.Android.requestWayonLiveSession(), true);
  assert.deepEqual(h.last('onWayonLiveSession'), ['wss://traverse.example/api/live/stream?session=fixture', 'fixture-protocol']);
  h.route('/api/live/session', () => ({ status: 200, body: { websocketUrl: 'wss://other.invalid/api/live/stream', protocol: 'fixture' } }), 'POST');
  assert.equal(await h.root.Android.requestWayonLiveSession(), false);
  assert.match(h.last('onWayonLiveSessionError')[0], /Invalid/);
});

test('live close invalidates a pending session and pauses/resumes foreground polling', async () => {
  const h = harness();
  await h.start();
  h.root.Android.setWayonLiveActive(true);
  const count = h.calls.length;
  await h.advance(16000);
  assert.equal(h.calls.length, count);
  let resolve;
  h.route('/api/live/session', () => new Promise(done => { resolve = done; }), 'POST');
  const pending = h.root.Android.requestWayonLiveSession();
  h.root.Android.setWayonLiveActive(false);
  resolve({ status: 200, body: { websocketUrl: '/api/live/stream', protocol: 'fixture' } });
  await pending;
  assert.equal(h.all('onWayonLiveSession').length, 0);
  assert.equal(h.calls.at(-1).url, '/api/wayon/json');
});

test('manual refresh posts once and only reports completion after matching collector result', async () => {
  const h = harness();
  await h.start();
  h.reply('/api/wayon/gmone/refresh', { requestedAt: iso(0) }, 'POST');
  h.reply('/api/wayon/gmone/refresh', { pending: true, completedAt: iso(-1000) });
  h.reply('/api/wayon/gmone/refresh', { pending: false, completedAt: iso(1000) });
  assert.equal(await h.root.Android.refreshCarData(), true);
  assert.equal(await h.root.Android.refreshCarData(), false);
  await h.advance(2500);
  assert.equal(h.all('showStatus').some(args => args[0] === 'Vehicle refresh completed.'), false);
  await h.advance(2500);
  assert.deepEqual(h.last('showStatus').slice(0, 2), ['Vehicle refresh completed.', 'success']);
  assert.equal(h.calls.filter(call => call.url.endsWith('/gmone/refresh') && call.method === 'POST').length, 1);
});

test('ambient posts JSON with CSRF and waits for matching acknowledgement', async () => {
  const h = harness();
  await h.start();
  h.reply('/api/ambient', { id: 'ambient-1' }, 'POST');
  h.reply('/api/wayon/ambient/status', { command: { id: 'ambient-1', status: 'acknowledged' } });
  assert.equal(await h.root.Android.applyAmbientOverride('{"mode":"auto"}'), true);
  assert.equal(h.last('onAmbientCommandResult')[1], 'pending');
  await h.advance(1000);
  assert.equal(h.last('onAmbientCommandResult')[1], 'acknowledged');
  const call = h.calls.find(call => call.url === '/api/ambient');
  assert.deepEqual(JSON.parse(call.body), { mode: 'auto' });
  assert.equal(call.headers['X-CSRF-Token'], 'test-csrf');
});

test('geolocation is permission-based, ignores late replies and never invents coordinates', async () => {
  const h = harness();
  await h.start(combined({ state: null }));
  assert.equal(h.root.Android.openSavedLocationMap(), false);
  assert.equal(h.all('open').length, 0);
  let success;
  h.root.navigator.geolocation = { getCurrentPosition: callback => { success = callback; } };
  h.root.Android.refreshMyLocation();
  h.root.TraverseWeb.stop();
  success({ coords: { latitude: 37, longitude: 127, accuracy: 10 }, timestamp: NOW });
  assert.deepEqual(h.last('updateMyLocation'), [null, null, null, '']);
});

test('unsupported native features report failure, do not make requests or simulate Bluetooth', async () => {
  const h = harness();
  await h.start();
  const count = h.calls.length;
  for (const name of ['clearDrivingHistory', 'saveApiUrl', 'saveWayonCloudKey', 'refreshGmoneSettings',
    'saveGmoneSettings', 'refreshGmoneDiagnostics', 'clearGmoneDiagnosticCodes', 'setDtcNotificationExcluded',
    'setAutoRefresh', 'handleVentilationToggle', 'handleHeatEjectToggle', 'showPairedDeviceList',
    'refreshDeviceList', 'toggleBluetoothTest', 'checkBluetoothStatusForDebug']) {
    assert.equal(h.root.Android[name](), false, name);
    assert.equal(h.last('showStatus')[1], 'danger', name);
    assert.match(h.last('showStatus')[0], /\uC6F9\uC571\uC5D0\uC11C\uB294/);
    assert.match(h.last('showStatus')[0], /\uC9C0\uC6D0\uD558\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4/);
    assert.doesNotMatch(h.last('showStatus')[0].replace(/\bAPI\b/g, ''), /[A-Za-z]{3,}/);
  }
  assert.equal(h.calls.length, count);
});

test('server command subset excludes panic and sunroof even though Android supports them', async () => {
  const h = harness();
  await h.start(combined(), COMMAND_SESSION);
  for (const name of ['PANIC', 'SUNROOF_OPEN', 'SUNROOF_CLOSE', 'SUNROOF_TILT', 'NOT_A_COMMAND']) {
    assert.equal(await h.root.Android.handleClick(name, name, 'button'), false);
  }
  assert.equal(h.calls.some(call => call.url === '/api/command'), false);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [true]);
});

test('missing, malformed or empty supportedCommands never grants commands', async () => {
  for (const supportedCommands of [undefined, null, false, [], 'DOOR_LOCK', { DOOR_LOCK: true }, ['NOT_A_COMMAND']]) {
    const h = harness();
    await h.start(combined(), { ...COMMAND_SESSION, capabilities: { commands: true, supportedCommands } });
    assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
    assert.equal(await h.root.Android.handleClick('DOOR_LOCK', 'Lock', 'door'), false);
    assert.equal(h.calls.some(call => call.url === '/api/command'), false);
  }
});

test('supportedCommands is snapshotted at start and every supported command accepts only a matching server response', async () => {
  for (const command of SUPPORTED_COMMANDS) {
    const h = harness();
    const supportedCommands = [command];
    await h.start(combined(), { ...COMMAND_SESSION, capabilities: { commands: true, supportedCommands } });
    supportedCommands.push('PANIC');
    assert.equal(await h.root.Android.handleClick('PANIC', 'Find', 'find'), false);
    h.reply('/api/command', { ok: true, state: 'server_responded', command, vehicleConfirmed: false }, 'POST');
    assert.equal(await h.root.Android.sendGmoneExtendedControl(command, 'button'), true, command);
    assert.equal(h.all('applyGmoneCommandOptimistic').length, 0, command);
    assert.deepEqual(h.last('updateGmoneExtendedControlState'), ['button', false, null]);
  }
});

test('blocked is not success and an expired account loses its command grant without replay', async () => {
  for (const state of ['blocked', 'unknown']) {
    const h = harness();
    await h.start(combined(), { ...COMMAND_SESSION, account: { loggedIn: true, email: 'test@example.invalid' } });
    h.reply('/api/command', { ok: false, state, command: 'DOOR_LOCK', code: 'session_expired' }, 'POST');
    assert.equal(await h.root.Android.handleClick('DOOR_LOCK', 'Lock', 'door'), false);
    assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
    assert.equal(h.last('updateGmoneAccountState')[0], false);
    await h.advance(4000);
    assert.equal(await h.root.Android.handleClick('DOOR_LOCK', 'Lock', 'door'), false);
    assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1);
    assert.equal(h.all('applyGmoneCommandOptimistic').length, 0);
  }
});

test('actual Android feedback clears sending without a completion label or opposite engine button feedback', async () => {
  const h = harness();
  const html = fs.readFileSync(path.join(__dirname, '../my-traverse-next/app/src/main/assets/main.html'), 'utf8');
  const buttons = Object.fromEntries(['btnEngineStart', 'btnEngineStop'].map(id => [id, {
    dataset: {}, classes: new Set(), removeAttribute(name) { if (name === 'data-feedback-label') delete this.dataset.feedbackLabel; },
  }]));
  for (const button of Object.values(buttons)) button.classList = {
    add: (...names) => names.forEach(name => button.classes.add(name)),
    remove: (...names) => names.forEach(name => button.classes.delete(name)),
  };
  h.root.document.getElementById = id => buttons[id];
  h.context.document = h.root.document;
  h.context.setTimeout = h.root.setTimeout;
  for (const name of ['commandResultButtonId', 'setButtonFeedback']) {
    const fn = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
    assert.ok(fn, name);
    vm.runInContext(fn[0], h.context);
  }
  h.root.setButtonFeedback = h.context.setButtonFeedback;
  await h.start(combined(), COMMAND_SESSION);
  h.reply('/api/command', { ok: true, state: 'server_responded', command: 'VEHICLE_START', vehicleConfirmed: false }, 'POST');
  assert.equal(await h.root.Android.handleLongPress('VEHICLE_START', 'Start', 'btnEngineStart'), true);
  assert.equal(buttons.btnEngineStart.dataset.feedbackLabel, undefined);
  assert.equal(buttons.btnEngineStart.classes.has('sending'), false);
  assert.equal(buttons.btnEngineStart.classes.has('success'), false);
  assert.equal(buttons.btnEngineStop.dataset.feedbackSequence, undefined);
  assert.equal(h.all('applyGmoneCommandOptimistic').length, 0);
});

test('all scalar vehicle HTML arguments reject markup, coercible objects, nondecimal and out-of-range values', async () => {
  const attack = '<img src=x onerror="window.__bridgeXss=1">';
  const fields = { range: 0, battery: 1, battery_level: 2, mileage: 3, fuel: 4, oil: 6 };
  for (const value of [attack, '12<img src=x>', '&#60;img src=x&#62;', ['55'], { valueOf: '55' }, true,
    'Infinity', 'NaN', '0x20', '2e4', '20%', '12 V', '-1', 1e100]) {
    const h = harness();
    const data = { ...snapshot().data, gmone_details: {} };
    for (const name of Object.keys(fields)) data[name] = value;
    data.last_update = attack;
    data.tire_pressure = data.tire_pressure_all = attack;
    await h.start(combined({ vehicleStatus: snapshot({ data }) }));
    const args = h.last('updateCarStatus');
    for (const [name, index] of Object.entries(fields)) assert.equal(args[index], '--', `${name}: ${JSON.stringify(value)}`);
    assert.equal(args[5], iso(-10000));
    assert.equal(args[7], '--');
    assert.equal(args[8], '--');
    assert.equal(h.last('setVehicleDataState')[0], 'cached');
  }
});

test('validated numeric zero remains zero; percent bounds and invalid mileage clear instead of keeping a previous value', async () => {
  const h = harness();
  const element = { textContent: 'old mileage' };
  h.root.document.getElementById = id => id === 'val-mileage' ? element : null;
  await h.start(combined({ vehicleStatus: snapshot({ data: {
    range: 0, battery: '0.0', battery_level: 0, mileage: '<svg/onload=alert(1)>', fuel: 0, oil: '101',
    last_update: iso(-10000), tire_pressure: 'FL: -5 kpa', tire_pressure_all: '9999 psi',
  } }) }));
  assert.deepEqual(h.last('updateCarStatus'), ['0', '0.0', '0', '--', '0', iso(-10000), '--', '--', '--']);
  assert.equal(element.textContent, '--');
});

test('trip numeric/time fields cannot carry HTML or coerced numeric values into history templates', async () => {
  const attack = '<svg/onload=window.__bridgeXss=1>';
  const h = harness();
  await h.start(combined({ trips: [{
    id: 'trip-bad', started_at: attack, ended_at: attack, distance_m: attack, duration_s: [60],
    avg_speed_mps: '1e99', max_speed_mps: true, route_point_count: '-1',
    start_lat: [37.5], start_lon: true, end_lat: '999', end_lon: attack,
    route: [{ latitude: attack, longitude: [127], speedMps: attack, time: attack }],
    start_address: attack, end_address: attack,
  }] }));
  const [trip] = JSON.parse(h.root.Android.getDrivingHistory());
  assert.equal(trip.distance, '-- km');
  assert.equal(trip.duration, '--:--:--');
  assert.equal(trip.avgSpeed, '-- km/h');
  assert.equal(trip.topSpeed, '-- km/h');
  assert.equal(trip.date, '----.--.--');
  assert.equal(trip.time, '--:--');
  assert.equal(trip.startedAt, null);
  assert.equal(trip.endedAt, null);
  assert.equal(trip.routePointCount, 1);
  assert.deepEqual(trip.route, [{ speedMps: null, time: null }]);
  const html = fs.readFileSync(path.join(__dirname, '../my-traverse-next/app/src/main/assets/main.html'), 'utf8');
  const reader = html.match(/        function extractTripPoint\([^]*?\n        }/)[0];
  const extractTripPoint = vm.runInNewContext(`(${reader})`);
  assert.equal(extractTripPoint(trip.route[0]), null, 'missing coordinates must not become a synthetic 0,0');
  assert.equal(trip.startLatitude, null);
  assert.equal(trip.startLongitude, null);
  assert.equal(trip.endLatitude, null);
  assert.equal(trip.endLongitude, null);
});

test('cloud numeric/time fields reject markup, invalid types and overflowing epoch values', async () => {
  const h = harness();
  await h.start(combined({ state: { updated_at: iso(-1000), onroad: false, voltage_v: '<img src=x>',
    speed_mps: [10], latitude: true, longitude: { value: 127 }, raw_json: {
      gps: { updatedAt: '2026-11-02T03:00:00Z<img src=x>', timestampMillis: 1e100 },
    } }, vehicleLock: { occurredAt: '<svg/onload=alert(1)>', locked: false } }));
  const state = JSON.parse(h.last('updateWayonLiveState')[0]);
  for (const key of ['voltageV', 'speedMps', 'speedKph', 'latitude', 'longitude', 'gpsUpdatedAtEpochMs', 'doorLockUpdatedAt']) {
    assert.equal(state[key], null, key);
  }
  assert.equal(h.last('updateWayonCloudState')[0], '--');
});

test('real Chromium: original mileage/battery sinks reproduce XSS, bridge blocks it and history escapes strings', {
  skip: !process.env.TRAVERSE_PLAYWRIGHT_MODULE,
}, async () => {
  const { chromium } = require(process.env.TRAVERSE_PLAYWRIGHT_MODULE);
  const browser = await chromium.launch({ headless: true,
    ...(process.env.TRAVERSE_BROWSER_EXECUTABLE ? { executablePath: process.env.TRAVERSE_BROWSER_EXECUTABLE } : {}),
    args: ['--disable-background-networking'],
  });
  try {
    const context = await browser.newContext({ offline: true, serviceWorkers: 'block' });
    await context.route('**/*', route => route.abort());
    const page = await context.newPage();
    const html = fs.readFileSync(path.join(__dirname, '../my-traverse-next/app/src/main/assets/main.html'), 'utf8');
    const rendererNames = ['hasMetricValue', 'renderBatterySummary', 'updateCarStatus', 'escapeHtml',
      'tripTimestamp', 'normalizeHistoryItems', 'simplifyTripAddress', 'parseDistanceKm', 'parseDurationSec',
      'parseSpeedKmh', 'formatTripTimeRange', 'loadHistory', 'reportNumber', 'reportClock', 'reportMoments',
      'renderDriveReportMoments'];
    const functions = rendererNames.map(name => {
      const match = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
      assert.ok(match, name);
      return match[0];
    }).join('\n');
    const ids = ['val-range', 'val-mileage', 'val-battery', 'history-container', 'today-date-display',
      'total-dist-val', 'total-top-speed', 'total-max-dist', 'total-time', 'total-max-time', 'today-dist', 'today-time', 'today-avg',
      'drive-report-moments', 'drive-report-moment-count'];
    await page.setContent(ids.map(id => `<div id="${id}"></div>`).join(''));
    await page.addScriptTag({ content: `
      let latestFirebaseBatteryLevel = null, latestFirebaseBatteryVoltage = null, latestWayonCloudVoltage = null;
      let currentHistoryItems = [], tripDetailMap = null, tripDetailOverlay = null;
      const historyContainer = document.getElementById('history-container');
      function hasWayonCloudKey() { return false; }
      function validatedFuelLevel() { return null; }
      function renderHomeFuelSummary() {}
      function updateInfoVoltsDisplay() {}
      ${functions}
    ` });
    await page.evaluate(({ callbacks, now }) => {
      const Clock = Date;
      window.Date = class extends Clock { constructor(...args) { super(...(args.length ? args : [now])); } static now() { return now; } };
      for (const name of callbacks) if (name !== 'updateCarStatus') window[name] = () => {};
      window.__mutations = [];
      window.__executed = 0;
      window.TraverseWeb = { csrfToken: () => 'synthetic-csrf' };
      window.fetch = async (url, options = {}) => {
        if (options.method === 'POST') window.__mutations.push({ url, headers: options.headers });
        return new Response('{}', { headers: { 'content-type': 'application/json' } });
      };
      window.__probe = () => {
        window.__executed++;
        window.fetch('/api/command', { method: 'POST', headers: { 'X-CSRF-Token': window.TraverseWeb.csrfToken() } });
      };
    }, { callbacks: CALLBACKS, now: NOW });
    const attack = '<img src="x" onerror="window.__probe()">';
    for (const index of [1, 2, 3]) {
      await page.evaluate(({ attack, index }) => {
        const values = ['450', '12', '80', '123', '40', '', '90', '', ''];
        values[index] = attack;
        window.__executed = 0;
        updateCarStatus(...values);
      }, { attack, index });
      await page.waitForFunction(() => window.__executed > 0);
    }
    assert.ok((await page.evaluate(() => window.__mutations)).length >= 3, 'positive control: unsafe original sinks can invoke a CSRF-bearing synthetic mutation');
    const maliciousTrip = { id: 'trip-xss', started_at: attack, ended_at: attack, distance_m: attack,
      duration_s: attack, avg_speed_mps: attack, max_speed_mps: attack, route_point_count: attack,
      start_address: attack, end_address: attack, analysis: { moments: [{ title: attack, detail: attack, severity: attack, time: attack }] },
      health: { topStressMoments: [{ title: attack, detail: attack, severity: attack, time: attack }] } };
    const data = { ...snapshot().data, gmone_details: {}, range: attack, battery: attack, battery_level: attack,
      mileage: attack, fuel: attack, last_update: attack, oil: attack, tire_pressure: attack, tire_pressure_all: attack };
    await page.evaluate(({ payload, trip }) => {
      for (const id of ['val-range', 'val-mileage', 'val-battery']) document.getElementById(id).replaceChildren();
      window.__executed = 0;
      window.__mutations = [];
      window.fetch = async (url, options = {}) => {
        if (options.method === 'POST') window.__mutations.push({ url, headers: options.headers });
        const body = url === '/api/wayon/json' ? payload : url === '/api/wayon/trips?limit=1000' ? { trips: [trip] } : {};
        return new Response(JSON.stringify(body), { headers: { 'content-type': 'application/json' } });
      };
    }, { payload: combined({ vehicleStatus: snapshot({ data }), trips: [maliciousTrip] }), trip: maliciousTrip });
    await page.addScriptTag({ content: source });
    assert.equal(await page.evaluate(session => window.TraverseWeb.start(session), SESSION), true);
    await page.evaluate(() => {
      loadHistory();
      const [item] = JSON.parse(window.Android.getDrivingHistory());
      renderDriveReportMoments(item.analysis, item.health);
    });
    await page.evaluate(() => window.Android.refreshWayonCloudTrips());
    await page.evaluate(() => loadHistory());
    await page.waitForTimeout(100);
    assert.deepEqual(await page.evaluate(() => ({
      executions: window.__executed, mutations: window.__mutations.length,
      injectedNodes: document.querySelectorAll('#val-mileage img, #val-battery img, #history-container img, #history-container svg, #history-container [onerror], #drive-report-moments img, #drive-report-moments [onerror]').length,
      mileage: document.getElementById('val-mileage').textContent,
    })), { executions: 0, mutations: 0, injectedNodes: 0, mileage: '--' });
    assert.match(await page.locator('#history-container').innerHTML(), /&lt;img/);
    assert.match(await page.locator('#drive-report-moments').innerHTML(), /&lt;img/);
    await page.evaluate(() => window.TraverseWeb.stop());
  } finally { await browser.close(); }
});
