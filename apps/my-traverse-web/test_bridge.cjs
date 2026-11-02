const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, 'client/bridge.js'), 'utf8');
const NOW = Date.parse('2026-11-02T03:00:00Z');
const iso = offset => new Date(NOW + offset).toISOString();
const SUPPORTED_COMMANDS = ['DOOR_LOCK', 'DOOR_UNLOCK', 'DRIVER_DOOR_UNLOCK', 'VEHICLE_START', 'VEHICLE_STOP',
  'WINDOW_OPEN', 'WINDOW_CLOSE', 'TRUNK_OPEN', 'TRUNK_CLOSE', 'MAIN_LIGHT_ON', 'MAIN_LIGHT_OFF',
  'PANIC', 'SUNROOF_OPEN', 'SUNROOF_CLOSE', 'SUNROOF_TILT'];
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
  const context = vm.createContext({ window: root, Date: Clock, AbortController, URL,
    CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options?.detail; } } });
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

function originalControlUi(h) {
  const html = fs.readFileSync(path.join(__dirname, '../my-traverse-next/app/src/main/assets/main.html'), 'utf8');
  const nodes = new Map();
  const node = id => {
    if (!nodes.has(id)) {
      const attributes = new Map(), classes = new Set();
      nodes.set(id, { id, hidden: false, dataset: {}, style: {}, classes,
        classList: { add: (...names) => names.forEach(n => classes.add(n)), remove: (...names) => names.forEach(n => classes.delete(n)),
          contains: name => classes.has(name), toggle: (name, enabled) => enabled ? classes.add(name) : classes.delete(name) },
        getAttribute: name => attributes.get(name) ?? null,
        setAttribute(name, value) { attributes.set(name, value); },
        removeAttribute(name) { attributes.delete(name); if (name === 'data-feedback-label') delete this.dataset.feedbackLabel; },
        querySelector: selector => selector === '.button-text' ? node(id + '-text') : null,
      });
    }
    return nodes.get(id);
  };
  const ids = ['btnEngineStart', 'btnEngineStop', 'btnTrunkOpen', 'btnTrunkClose', 'btnWindowOpen', 'btnWindowClose',
    'btnSunroofOpen', 'btnSunroofClose', 'btnSunroofTilt', 'btnDoorToggle', 'btnQuickHorn', 'btnGmoneDriverUnlock', 'btnGmoneLightToggle'];
  const commands = ['VEHICLE_START', 'VEHICLE_STOP', 'TRUNK_OPEN', 'TRUNK_CLOSE', 'WINDOW_OPEN', 'WINDOW_CLOSE',
    'SUNROOF_OPEN', 'SUNROOF_CLOSE', 'SUNROOF_TILT', 'DOOR_LOCK', 'PANIC', 'DRIVER_DOOR_UNLOCK', 'MAIN_LIGHT_ON'];
  ids.forEach((id, index) => { node(id).dataset[id.startsWith('btnGmone') ? 'gmoneControl' : 'cmd'] = commands[index]; h.context[id] = node(id); });
  h.root.document.getElementById = node;
  h.root.document.querySelector = node;
  h.root.document.querySelectorAll = () => ids.map(node);
  Object.assign(h.context, { document: h.root.document, setTimeout: h.root.setTimeout, vehicleDataState: 'loading',
    vehicleCommandReady: false, gmoneDetailsCurrent: null, wayonLiveStateCurrent: null, controlDrivingActive: false,
    gmoneOptimisticControls: {}, GMONE_ENGINE_STATUS_MAX_AGE_MS: 300000, engineTimerDisplay: node('engine-timer'),
    gmoneNumber: value => value == null ? null : Number(value), gmoneFormatNumber: String,
    gmoneSettings: value => value?.settings || {}, displayedGmoneClosures: value => value?.closures || {},
    syncGmoneRemoteCountdown() {}, gmoneRemoteTimeLabel: () => '', setSmartControlText() {}, renderHomeQuickIcon() {},
    updateRemoteCountdownDisplays() {},
  });
  const names = ['gmoneSourceEpoch', 'gmoneDetailsSourceUpdatedAt', 'gmoneRemoteStartIsActive', 'gmoneEngineStatusContext',
    'resolveGmoneOptimisticState', 'effectiveGmoneEngineSnapshot', 'effectiveGmoneClosures', 'setSmartControlAction',
    'renderBinarySmartControl', 'renderDoorLockState', 'updateGmoneControlPanel', 'updateGmoneExtendedControls',
    'updateGmoneExtendedControlState', 'commandResultButtonId', 'setButtonFeedback'];
  for (const name of names) {
    const match = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
    assert.ok(match, name); vm.runInContext(match[0], h.context);
    h.root[name] = h.context[name];
  }
  for (const name of names) Object.defineProperty(h.context, name, { configurable: true,
    get: () => h.root[name], set: value => { h.root[name] = value; } });
  h.root.updateRemoteCountdownDisplays = h.context.updateRemoteCountdownDisplays;
  const callback = (name, fn) => { h.root[name] = (...args) => { h.outputs.push([name, ...args]); fn(...args); }; };
  callback('updateVehicleCommandReady', ready => { h.context.vehicleCommandReady = ready; h.root.updateGmoneControlPanel(h.context.gmoneDetailsCurrent); });
  callback('setVehicleDataState', state => { h.context.vehicleDataState = state; });
  callback('updateGmoneDetails', raw => {
    h.context.gmoneDetailsCurrent = raw ? JSON.parse(raw) : null;
    h.root.updateGmoneControlPanel(h.context.gmoneDetailsCurrent);
    h.root.updateGmoneExtendedControls(h.context.gmoneDetailsCurrent);
  });
  callback('updateWayonLiveState', raw => { h.context.wayonLiveStateCurrent = JSON.parse(raw); h.root.updateGmoneControlPanel(h.context.gmoneDetailsCurrent); });
  return { node, nodes };
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
  assert.equal(h.events.at(-1), 'traverseweb:sessionlost');
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

test('account login/logout use specified routes and requery authoritative session capabilities', async () => {
  const h = harness();
  await h.start();
  h.reply('/api/account', { loggedIn: true, email: 'test@example.invalid', message: 'Connected' }, 'POST');
  h.reply('/api/session', { ...COMMAND_SESSION, account: { loggedIn: true, email: 'test@example.invalid' } });
  assert.equal(await h.root.Android.loginGmone(' test@example.invalid ', 'fixture-password'), true);
  const login = h.calls.find(call => call.url === '/api/account');
  assert.deepEqual(JSON.parse(login.body), { email: 'test@example.invalid', password: 'fixture-password' });
  assert.equal(login.headers['X-CSRF-Token'], 'test-csrf');
  assert.deepEqual(h.last('updateGmoneAccountState'), [true, 'test@example.invalid', 'Connected', false]);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [true]);
  h.reply('/api/account', { loggedIn: false, email: '', message: 'Logged out' }, 'DELETE');
  h.route('/api/session', () => ({ status: 200, body: { ...SESSION, account: { loggedIn: false, email: '' } } }));
  assert.equal(await h.root.Android.logoutGmone(), true);
  const logout = h.calls.find(call => call.url === '/api/account' && call.method === 'DELETE');
  assert.equal(logout.body, undefined);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
  assert.equal(h.calls.filter(call => call.url === '/api/session').length, 2);
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
  h.reply('/api/session', { ...COMMAND_SESSION, account: { loggedIn: true, email: 'new@example.invalid' } });
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
  h.reply('/api/session', SESSION);
  h.documentListeners.visibilitychange();
  await h.root.Android.refreshWayonCloudData();
  assert.equal(h.calls.length, 3);
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

test('a deliberately restricted server fixture excludes commands without hardcoding client exclusions', async () => {
  const h = harness();
  await h.start(combined(), { ...COMMAND_SESSION, capabilities: { commands: true, supportedCommands: ['DOOR_LOCK'] } });
  for (const name of SUPPORTED_COMMANDS.filter(name => name !== 'DOOR_LOCK').concat('NOT_A_COMMAND')) {
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
    const excluded = command === 'PANIC' ? 'DOOR_LOCK' : 'PANIC';
    supportedCommands.push(excluded);
    assert.equal(await h.root.Android.handleClick(excluded, '', 'find'), false);
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
    toggle: (name, enabled) => enabled ? button.classes.add(name) : button.classes.delete(name),
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

test('HTTP errors preserve account reasons and only matching structured blocked commands are definitive', async () => {
  const login = harness();
  await login.start();
  login.reply('/api/account', { message: 'Registered account mismatch' }, 'POST', 403);
  assert.equal(await login.root.Android.loginGmone('fixture@example.invalid', 'synthetic'), false);
  assert.equal(login.last('showStatus')[0], 'Registered account mismatch');
  assert.deepEqual(login.last('updateVehicleCommandReady'), [false]);
  for (const result of [
    { ok: false, state: 'blocked', command: 'DOOR_LOCK', message: 'Commands disabled' },
    { ok: false, state: 'blocked', command: 'DOOR_UNLOCK', message: 'Mismatched' },
    { ok: false, state: 'unknown', command: 'DOOR_LOCK', message: 'Uncertain' },
    { ok: true, state: 'server_responded', command: 'DOOR_LOCK', message: 'Untrusted success' },
  ]) {
    const h = harness(); await h.start(combined(), COMMAND_SESSION);
    h.reply('/api/command', result, 'POST', 403);
    assert.equal(await h.root.Android.handleClick('DOOR_LOCK', '', 'door'), false);
    const blocked = result.state === 'blocked' && result.command === 'DOOR_LOCK';
    assert.equal(h.last('setButtonFeedback')[1], blocked ? 'danger' : '');
    if (blocked) assert.equal(h.last('showStatus')[0], 'Commands disabled');
    else assert.match(h.last('showStatus')[0], /\uC7AC\uC804\uC1A1\uD558\uC9C0/);
    assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1);
  }
});

test('login cannot override a disabled server command capability', async () => {
  const h = harness(); await h.start();
  h.reply('/api/account', { loggedIn: true, email: 'fixture@example.invalid' }, 'POST');
  h.reply('/api/session', { ...SESSION, account: { loggedIn: true, email: 'fixture@example.invalid' } });
  assert.equal(await h.root.Android.loginGmone('fixture@example.invalid', 'synthetic'), true);
  assert.equal(h.last('updateGmoneAccountState')[0], true);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
});

test('GMOne login_rejected 401 preserves PWA authentication; unauthorized and ambiguous 401 expire it', async () => {
  for (const body of [
    { code: 'login_rejected', state: 'blocked', message: 'Check fixture credentials' },
    { code: 'login_rejected', state: 'blocked' },
    { error: 'unauthorized' },
    { error: 'unauthorized', code: 'login_rejected', state: 'blocked' },
    { code: 'login_rejected' },
    {},
  ]) {
    const h = harness(); await h.start();
    h.root.Android.setWayonLiveActive(true);
    const stops = h.all('stopWayonLiveView').length;
    h.reply('/api/account', body, 'POST', 401);
    assert.equal(await h.root.Android.loginGmone('fixture@example.invalid', 'synthetic'), false);
    const rejected = body.code === 'login_rejected' && body.state === 'blocked' && body.error !== 'unauthorized';
    assert.equal(h.root.TraverseWeb.csrfToken(), rejected ? 'test-csrf' : '');
    assert.equal(h.events.includes('traverseweb:sessionlost'), !rejected);
    assert.equal(h.all('stopWayonLiveView').length, stops + (rejected ? 0 : 1));
    if (rejected) {
      assert.equal(h.last('updateGmoneAccountState')[3], false);
      if (body.message) assert.equal(h.last('showStatus')[0], body.message);
      else assert.match(h.last('showStatus')[0], /login_rejected/);
    }
  }
});

test('login_rejected is not an authentication bypass on any other 401 route', async () => {
  const h = harness(); await h.start(combined(), COMMAND_SESSION);
  h.reply('/api/command', { code: 'login_rejected', state: 'blocked', command: 'DOOR_LOCK' }, 'POST', 401);
  await h.root.Android.handleClick('DOOR_LOCK', '', 'door');
  assert.equal(h.root.TraverseWeb.csrfToken(), '');
  assert.equal(h.events.at(-1), 'traverseweb:sessionlost');
});

test('session rechecks coalesce, preserve live/feed and pending feedback, and accept the original command result', async () => {
  const h = harness();
  const initial = { ...COMMAND_SESSION, account: { loggedIn: true, email: 'fixture@example.invalid' } };
  await h.start(combined(), initial);
  let finishFeed, finishCommand, finishSession;
  h.route('/api/wayon/json', () => new Promise(resolve => { finishFeed = resolve; }));
  const feedRead = h.root.Android.refreshWayonCloudData();
  const feedSignal = h.calls.at(-1).signal;
  h.root.Android.setWayonLiveActive(true);
  h.route('/api/command', () => new Promise(resolve => { finishCommand = resolve; }), 'POST');
  const commandRead = h.root.Android.handleLongPress('DOOR_LOCK', '', 'door');
  const commandSignal = h.calls.at(-1).signal;
  const stops = h.all('stopWayonLiveView').length;
  const feedback = h.all('setButtonFeedback').length;
  h.route('/api/session', () => new Promise(resolve => { finishSession = resolve; }));
  const first = h.root.TraverseWeb.refreshSession();
  const second = h.root.TraverseWeb.refreshSession();
  assert.equal(first, second);
  finishSession({ status: 200, body: { ...SESSION, csrfToken: 'rotated', account: { loggedIn: false, email: initial.account.email } } });
  assert.equal(await first, true);
  assert.equal(h.root.TraverseWeb.csrfToken(), 'rotated');
  assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
  assert.equal(h.all('setButtonFeedback').length, feedback);
  assert.equal(h.all('stopWayonLiveView').length, stops);
  assert.equal(commandSignal.aborted, false); assert.equal(feedSignal.aborted, false);
  finishFeed({ status: 200, body: combined() }); await feedRead;
  finishCommand({ status: 200, body: { ok: true, state: 'server_responded', command: 'DOOR_LOCK' } });
  assert.equal(await commandRead, true);
  assert.deepEqual(h.last('setButtonFeedback'), ['door', '', 'DOOR_LOCK']);
  assert.equal(h.all('applyGmoneCommandOptimistic').length, 0);
  assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1);
});

test('unchanged rechecks do not clear login inputs, restart live, or fetch vehicle data', async () => {
  const h = harness();
  const initial = { ...COMMAND_SESSION, account: { loggedIn: true, email: 'fixture@example.invalid' } };
  await h.start(combined(), initial);
  h.reply('/api/session', initial);
  h.root.Android.setWayonLiveActive(true);
  const accounts = h.all('updateGmoneAccountState').length, stops = h.all('stopWayonLiveView').length;
  await h.root.TraverseWeb.refreshSession();
  await h.advance(60000);
  h.root.document.hidden = false;
  h.documentListeners.visibilitychange();
  await h.root.TraverseWeb.refreshSession();
  assert.equal(h.all('updateGmoneAccountState').length, accounts);
  assert.equal(h.all('stopWayonLiveView').length, stops);
  assert.equal(h.calls.filter(call => call.url === '/api/wayon/json').length, 1);
  assert.equal(h.calls.filter(call => call.url === '/api/session').length, 3);
});

test('expired command invalidates an older pending session grant', async () => {
  const h = harness(); await h.start(combined(), COMMAND_SESSION);
  let resolve;
  h.route('/api/session', () => new Promise(done => { resolve = done; }));
  const recheck = h.root.TraverseWeb.refreshSession();
  h.reply('/api/command', { ok: false, state: 'blocked', command: 'DOOR_LOCK', code: 'session_expired' }, 'POST', 403);
  await h.root.Android.handleClick('DOOR_LOCK', '', 'door');
  resolve({ status: 200, body: COMMAND_SESSION });
  assert.equal(await recheck, false);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
  assert.equal(h.last('updateGmoneAccountState')[0], false);
});

test('session read failure revokes commands without stopping data or live, and later capability updates recover', async () => {
  const h = harness(); await h.start(combined(), COMMAND_SESSION);
  h.root.Android.setWayonLiveActive(true);
  const stops = h.all('stopWayonLiveView').length;
  h.reply('/api/session', {}, 'GET', 503);
  assert.equal(await h.root.TraverseWeb.refreshSession(), false);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
  assert.equal(h.all('stopWayonLiveView').length, stops);
  h.route('/api/session', () => ({ status: 200, body: COMMAND_SESSION }));
  assert.equal(await h.root.TraverseWeb.refreshSession(), true);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [true]);
  assert.equal(h.all('stopWayonLiveView').length, stops);
});

test('401 clears ordinary and extended in-flight feedback; reauthentication does not resurrect sending', async () => {
  for (const extended of [false, true]) {
    const h = harness(); await h.start(combined(), COMMAND_SESSION);
    h.reply('/api/command', {}, 'POST', 401);
    const method = extended ? 'sendGmoneExtendedControl' : 'handleLongPress';
    await h.root.Android[method]('DOOR_LOCK', ...(extended ? ['door'] : ['', 'door']));
    const callback = extended ? 'updateGmoneExtendedControlState' : 'setButtonFeedback';
    assert.deepEqual(h.last(callback), extended ? ['door', false, null] : ['door', '', 'DOOR_LOCK']);
    assert.equal(h.events.at(-1), 'traverseweb:sessionlost');
    await h.root.TraverseWeb.start(COMMAND_SESSION);
    assert.deepEqual(h.last(callback), extended ? ['door', false, null] : ['door', '', 'DOOR_LOCK']);
  }
});

test('authenticated=false session response expires the web session and clears pending feedback', async () => {
  const h = harness(); await h.start(combined(), COMMAND_SESSION);
  let finish;
  h.route('/api/command', () => new Promise(resolve => { finish = resolve; }), 'POST');
  const pending = h.root.Android.handleLongPress('DOOR_LOCK', '', 'door');
  h.reply('/api/session', { authenticated: false });
  assert.equal(await h.root.TraverseWeb.refreshSession(), false);
  assert.deepEqual(h.last('setButtonFeedback'), ['door', '', 'DOOR_LOCK']);
  finish({ status: 200, body: { ok: true, state: 'server_responded', command: 'DOOR_LOCK' } });
  assert.equal(await pending, false);
  assert.equal(h.root.TraverseWeb.csrfToken(), '');
});

test('actual Android controls select observed remote stop without changing cached state or authorizing driving', async () => {
  const h = harness(), ui = originalControlUi(h);
  const details = { vehicleState: { engineRunning: true, lightRaw: 0 },
    remoteStart: { remainingTimeValid: true, remainingTimeRaw: 600, remainingStarts: 1 } };
  const payload = combined({ state: { updated_at: iso(-5000), onroad: 0, ignition: 1 },
    vehicleStatus: snapshot({ data: { ...snapshot().data, gmone_details: details } }) });
  await h.start(payload, COMMAND_SESSION);
  assert.equal(h.context.vehicleDataState, 'cached');
  assert.equal(ui.node('btnEngineStart').hidden, true);
  assert.equal(ui.node('btnEngineStop').hidden, false);
  assert.equal(ui.node('btnEngineStop').getAttribute('aria-disabled'), 'false');
  assert.equal(ui.node('engine-timer').textContent, '9:50');
  await h.advance(2000); h.root.updateRemoteCountdownDisplays();
  assert.equal(ui.node('engine-timer').textContent, '9:48');
  h.root.updateGmoneControlPanel(h.context.gmoneDetailsCurrent);
  assert.equal(ui.node('btnEngineStop').hidden, false);
  h.root.updateWayonLiveState(JSON.stringify({ onroad: true }));
  assert.equal(ui.node('btnEngineStop').getAttribute('aria-disabled'), 'true');
  assert.equal(h.context.vehicleDataState, 'cached');
  assert.equal(h.all('applyGmoneCommandOptimistic').length, 0);
  assert.equal(h.calls.some(call => call.method !== 'GET'), false);
});

test('missing, stale, expired and malformed observed engine values cannot select remote stop', async () => {
  const valid = { vehicleState: { engineRunning: true }, remoteStart: { remainingTimeValid: true, remainingTimeRaw: 600 } };
  for (const variant of [
    { details: {} }, { details: { ...valid, vehicleState: { engineRunning: false } } },
    { details: { ...valid, remoteStart: { remainingTimeValid: true, remainingTimeRaw: '<img>' } } },
    { details: { ...valid, remoteStart: { remainingTimeValid: true, remainingTimeRaw: 1 } } },
    { details: valid, stale: true }, { details: { ...valid, meta: { updatedAt: iso(-301000) } } },
    { details: { ...valid, meta: { updatedAt: iso(61000) } } },
  ]) {
    const h = harness(), ui = originalControlUi(h);
    await h.start(combined({ state: { updated_at: iso(-5000), onroad: 0, ignition: 0 },
      vehicleStatus: snapshot({ stale: variant.stale || false, data: { ...snapshot().data, gmone_details: variant.details } }) }), COMMAND_SESSION);
    assert.equal(ui.node('btnEngineStop').hidden, true);
    assert.equal(ui.node('btnEngineStart').hidden, false);
    assert.equal(h.context.vehicleDataState, 'cached');
  }
});

test('capability masks survive original rerenders and delayed feedback, and restore only native-enabled buttons', async () => {
  const h = harness(), ui = originalControlUi(h);
  const restricted = { ...COMMAND_SESSION, capabilities: { commands: true, supportedCommands: ['DOOR_LOCK'] } };
  await h.start(combined({ state: { updated_at: iso(-5000), onroad: 0, ignition: 0 } }), restricted);
  for (const id of ['btnQuickHorn', 'btnSunroofTilt', 'btnGmoneDriverUnlock', 'btnGmoneLightToggle']) {
    assert.equal(ui.node(id).getAttribute('aria-disabled'), 'true', id);
  }
  h.root.updateGmoneExtendedControlState('btnGmoneDriverUnlock', false, false);
  await h.advance(1800);
  assert.equal(ui.node('btnGmoneDriverUnlock').getAttribute('aria-disabled'), 'true');
  h.reply('/api/session', COMMAND_SESSION);
  await h.root.TraverseWeb.refreshSession();
  assert.equal(ui.node('btnQuickHorn').getAttribute('aria-disabled'), 'false');
  assert.equal(ui.node('btnSunroofTilt').getAttribute('aria-disabled'), 'false');
  assert.notEqual(ui.node('btnGmoneDriverUnlock').getAttribute('aria-disabled'), 'true');
  assert.equal(ui.node('btnGmoneLightToggle').getAttribute('aria-disabled'), 'true', 'unknown light state remains disabled');
  h.root.updateGmoneExtendedControls({ vehicleState: { lightRaw: 1 } });
  assert.equal(ui.node('btnGmoneLightToggle').getAttribute('aria-disabled'), 'false');
  h.route('/api/session', () => ({ status: 200, body: { ...SESSION, account: { loggedIn: false, email: '' } } }));
  await h.root.TraverseWeb.refreshSession();
  h.root.updateGmoneControlPanel(h.context.gmoneDetailsCurrent);
  h.root.updateGmoneExtendedControls({ vehicleState: { lightRaw: 1 } });
  assert.equal(ui.node('btnQuickHorn').getAttribute('aria-disabled'), 'true');
  assert.equal(ui.node('btnGmoneLightToggle').getAttribute('aria-disabled'), 'true');
});

test('actual Android sending class and label are removed on command 401 and stay removed after login', async () => {
  const h = harness(), ui = originalControlUi(h);
  await h.start(combined(), COMMAND_SESSION);
  let resolve;
  h.route('/api/command', () => new Promise(done => { resolve = done; }), 'POST');
  const pending = h.root.Android.handleLongPress('DOOR_LOCK', '', 'btnDoorToggle');
  assert.equal(ui.node('btnDoorToggle').classes.has('sending'), true);
  resolve({ status: 401, body: {} }); await pending;
  assert.equal(ui.node('btnDoorToggle').classes.has('sending'), false);
  assert.equal(ui.node('btnDoorToggle').dataset.feedbackLabel, undefined);
  await h.root.TraverseWeb.start(COMMAND_SESSION);
  assert.equal(ui.node('btnDoorToggle').classes.has('sending'), false);
});

test('unknown blocks all new command UUIDs for 180s despite fresh data, session checks and in-page restart', async () => {
  const h = harness(), ui = originalControlUi(h);
  await h.start(combined(), COMMAND_SESSION);
  h.reply('/api/session', COMMAND_SESSION);
  h.reply('/api/command', { ok: false, state: 'unknown', command: 'DOOR_LOCK', dispatched: true }, 'POST');
  assert.equal(await h.root.Android.handleLongPress('DOOR_LOCK', '', 'btnDoorToggle'), false);
  assert.match(h.last('showStatus')[0], /180/);
  assert.equal(ui.node('btnDoorToggle').getAttribute('aria-disabled'), 'true');
  await h.advance(4000);
  assert.equal(await h.root.Android.handleLongPress('DOOR_LOCK', '', 'btnDoorToggle'), false);
  assert.equal(await h.root.Android.sendGmoneExtendedControl('MAIN_LIGHT_ON', 'btnGmoneLightToggle'), false);
  h.route('/api/wayon/json', () => ({ status: 200, body: combined({ vehicleStatus: snapshot({
    updatedAt: iso(4000), data: { ...snapshot().data, last_update: iso(4000) },
  }) }) }));
  await h.root.Android.refreshWayonCloudData();
  await h.root.TraverseWeb.refreshSession();
  assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
  h.root.TraverseWeb.stop();
  await h.root.TraverseWeb.start(COMMAND_SESSION);
  await h.advance(175999);
  assert.equal(await h.root.Android.handleClick('DOOR_LOCK', '', 'btnDoorToggle'), false);
  assert.equal(ui.node('btnQuickHorn').getAttribute('aria-disabled'), 'true');
  assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1);
  await h.advance(1);
  assert.deepEqual(h.last('updateVehicleCommandReady'), [true]);
  assert.equal(ui.node('btnDoorToggle').getAttribute('aria-disabled'), 'false');
  assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1, 'expiry does not replay');
  h.route('/api/command', () => ({ status: 200, body: { ok: true, state: 'server_responded', command: 'DOOR_LOCK' } }), 'POST');
  assert.equal(await h.root.Android.handleClick('DOOR_LOCK', '', 'btnDoorToggle'), true);
  assert.deepEqual(h.calls.filter(call => call.url === '/api/command').map(call => JSON.parse(call.body).requestId),
    ['test-request-1', 'test-request-2']);
});

test('transport failures, malformed replies and HTTP unknown responses retain the full cooldown without automatic retries', async () => {
  for (const response of [new Error('synthetic network loss'),
    { status: 409, body: { ok: false, state: 'unknown' } },
    { status: 200, body: { ok: true, state: 'server_responded', command: 'WRONG' } },
  ]) {
    const h = harness(); await h.start(combined(), COMMAND_SESSION);
    h.reply('/api/session', COMMAND_SESSION);
    h.route('/api/command', () => response, 'POST');
    assert.equal(await h.root.Android.handleClick('DOOR_LOCK', '', 'door'), false);
    await h.advance(179999);
    assert.equal(await h.root.Android.handleClick('DOOR_LOCK', '', 'door'), false);
    assert.deepEqual(h.last('updateVehicleCommandReady'), [false]);
    await h.advance(1);
    assert.deepEqual(h.last('updateVehicleCommandReady'), [true]);
    assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1);
    assert.equal(h.calls.some(call => call.method === 'POST' && call.url.endsWith('/gmone/refresh')), false);
  }
});

test('definitive blocked response does not impose an unknown-outcome cooldown', async () => {
  const h = harness(); await h.start(combined(), COMMAND_SESSION);
  h.reply('/api/command', { ok: false, state: 'blocked', command: 'DOOR_LOCK', dispatched: false }, 'POST');
  await h.root.Android.handleClick('DOOR_LOCK', '', 'door');
  await h.advance(3000);
  h.route('/api/command', () => ({ status: 200, body: { ok: true, state: 'server_responded', command: 'DOOR_LOCK' } }), 'POST');
  assert.equal(await h.root.Android.handleClick('DOOR_LOCK', '', 'door'), true);
  assert.equal(h.calls.filter(call => call.url === '/api/command').length, 2);
});

function engineFeed(running, offset = -10000) {
  return combined({ state: { updated_at: iso(offset), onroad: 0, ignition: running ? 1 : 0 },
    vehicleStatus: snapshot({ updatedAt: iso(offset), data: { ...snapshot().data, last_update: iso(offset), gmone_details: {
      vehicleState: { engineRunning: running }, remoteStart: { remainingTimeValid: running, remainingTimeRaw: running ? 600 : 0 },
    } } }) });
}

test('accepted engine start/stop requests one collector refresh and changes selection only on a new observation', async () => {
  for (const command of ['VEHICLE_START', 'VEHICLE_STOP']) {
    const h = harness(), ui = originalControlUi(h);
    const wasRunning = command === 'VEHICLE_STOP';
    await h.start(engineFeed(wasRunning), COMMAND_SESSION);
    h.reply('/api/session', COMMAND_SESSION);
    h.reply('/api/command', { ok: true, state: 'server_responded', command }, 'POST');
    h.reply('/api/wayon/gmone/refresh', { requestedAt: iso(250) }, 'POST');
    h.reply('/api/wayon/gmone/refresh', { pending: false, completedAt: iso(0) });
    h.reply('/api/wayon/gmone/refresh', { pending: false, completedAt: iso(5000) });
    assert.equal(await h.root.Android.handleLongPress(command, '', wasRunning ? 'btnEngineStop' : 'btnEngineStart'), true);
    assert.equal(ui.node('btnEngineStop').hidden, !wasRunning, 'protocol response alone is not engine telemetry');
    await h.advance(250);
    assert.equal(h.calls.filter(call => call.url.endsWith('/gmone/refresh') && call.method === 'POST').length, 1);
    await h.advance(2500);
    assert.equal(ui.node('btnEngineStop').hidden, !wasRunning, 'older collector completion must not finish the refresh');
    h.route('/api/wayon/json', () => ({ status: 200, body: engineFeed(!wasRunning, 5000) }));
    await h.advance(2500);
    assert.equal(ui.node('btnEngineStop').hidden, wasRunning);
    assert.equal(h.context.vehicleDataState, 'cached');
    assert.equal(h.last('showStatus')[1], 'info');
    await h.advance(45000);
    assert.equal(h.calls.filter(call => call.url.endsWith('/gmone/refresh') && call.method === 'POST').length, 1);
    assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1);
    assert.equal(h.all('applyGmoneCommandOptimistic').length, 0);
  }
});

test('engine collector failures/timeouts and unchanged snapshots never invent a running engine or retry POST', async () => {
  for (const outcome of ['post-failed', 'timeout', 'old-snapshot']) {
    const h = harness(), ui = originalControlUi(h);
    await h.start(engineFeed(false), COMMAND_SESSION);
    h.reply('/api/session', COMMAND_SESSION);
    h.reply('/api/command', { ok: true, state: 'server_responded', command: 'VEHICLE_START' }, 'POST');
    h.reply('/api/wayon/gmone/refresh', outcome === 'post-failed' ? {} : { requestedAt: iso(250) }, 'POST', outcome === 'post-failed' ? 503 : 200);
    h.reply('/api/wayon/gmone/refresh', { pending: outcome !== 'old-snapshot', completedAt: iso(1000) });
    await h.root.Android.handleLongPress('VEHICLE_START', '', 'btnEngineStart');
    await h.advance(120000);
    assert.equal(ui.node('btnEngineStop').hidden, true);
    assert.equal(h.context.vehicleDataState, 'cached');
    assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1);
    assert.equal(h.calls.filter(call => call.url.endsWith('/gmone/refresh') && call.method === 'POST').length, 1);
    const polls = h.calls.filter(call => call.url.endsWith('/gmone/refresh') && call.method === 'GET').length;
    assert.ok(polls <= 36);
    await h.advance(30000);
    assert.equal(h.calls.filter(call => call.url.endsWith('/gmone/refresh') && call.method === 'GET').length, polls);
    assert.equal(h.all('applyGmoneCommandOptimistic').length, 0);
  }
});

test('engine followup waits for a preexisting refresh then makes only one new collector request', async () => {
  const h = harness(); await h.start(engineFeed(false), COMMAND_SESSION);
  h.reply('/api/wayon/gmone/refresh', { requestedAt: iso(0) }, 'POST');
  h.reply('/api/wayon/gmone/refresh', { requestedAt: iso(2750) }, 'POST');
  h.reply('/api/wayon/gmone/refresh', { pending: false, completedAt: iso(1000) });
  h.reply('/api/wayon/gmone/refresh', { pending: false, completedAt: iso(5000) });
  await h.root.Android.refreshCarData();
  h.reply('/api/command', { ok: true, state: 'server_responded', command: 'VEHICLE_START' }, 'POST');
  await h.root.Android.handleLongPress('VEHICLE_START', '', 'engine');
  await h.advance(10000);
  assert.equal(h.calls.filter(call => call.url.endsWith('/gmone/refresh') && call.method === 'POST').length, 2);
  assert.equal(h.calls.filter(call => call.url === '/api/command').length, 1);
});

test('post-collector feed read cannot be satisfied by a pre-collector in-flight cache response', async () => {
  const h = harness(), ui = originalControlUi(h);
  await h.start(engineFeed(false), COMMAND_SESSION);
  h.reply('/api/command', { ok: true, state: 'server_responded', command: 'VEHICLE_START' }, 'POST');
  h.reply('/api/wayon/gmone/refresh', { requestedAt: iso(250) }, 'POST');
  h.reply('/api/wayon/gmone/refresh', { pending: false, completedAt: iso(2000) });
  await h.root.Android.handleLongPress('VEHICLE_START', '', 'btnEngineStart');
  await h.advance(250);
  let finishOld;
  h.route('/api/wayon/json', () => new Promise(resolve => { finishOld = resolve; }));
  const oldRead = h.root.Android.refreshWayonCloudData();
  const poll = h.advance(2500);
  for (let i = 0; i < 10; i++) await Promise.resolve();
  assert.equal(ui.node('btnEngineStop').hidden, true);
  h.route('/api/wayon/json', () => ({ status: 200, body: engineFeed(true, 2000) }));
  finishOld({ status: 200, body: engineFeed(false) });
  await oldRead; await poll;
  assert.equal(h.calls.filter(call => call.url === '/api/wayon/json').length, 3);
  assert.equal(ui.node('btnEngineStop').hidden, false);
  assert.equal(h.context.vehicleDataState, 'cached');
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

test('compact trip NULL maxima remain unknown without route fetches; measured zero and numeric maxima survive', async () => {
  const h = harness();
  const maxima = [null, undefined, '', false, 0, '0', 12.5, '12.5'];
  const rows = maxima.map((max_speed_mps, index) => ({ id: `compact-${index}`, started_at: iso(-10000 - index * 1000),
    distance_m: 1000, duration_s: 100, avg_speed_mps: null, max_speed_mps, ...(index % 2 ? { route: [] } : {}) }));
  await h.start(combined({ trips: rows }));
  const history = JSON.parse(h.root.Android.getDrivingHistory());
  assert.deepEqual(history.map(item => item.topSpeed), ['-- km/h', '-- km/h', '-- km/h', '-- km/h', '0 km/h', '0 km/h', '45 km/h', '45 km/h']);
  assert.ok(history.every(item => item.avgSpeed === '36 km/h'), 'keep the existing distance/time average, not an invented maximum');
  assert.ok(history.every(item => item.route.length === 0));
  assert.deepEqual(h.calls.map(call => call.url), ['/api/wayon/json']);
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

test('real Chromium: 819 compact NULL maxima render unknown in the original history list and aggregate', {
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
    const functions = ['escapeHtml', 'tripTimestamp', 'normalizeHistoryItems', 'simplifyTripAddress',
      'parseDistanceKm', 'parseDurationSec', 'parseSpeedKmh', 'formatTripTimeRange', 'loadHistory'].map(name => {
      const match = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
      assert.ok(match, name); return match[0];
    }).join('\n');
    const historyId = html.match(/const historyContainer = document\.getElementById\('([^']+)'\)/)?.[1];
    assert.equal(historyId, 'history-list-container', 'use the actual Android DOM target');
    const ids = [historyId, 'today-date-display', 'total-dist-val', 'total-top-speed', 'total-max-dist',
      'total-time', 'total-max-time', 'today-dist', 'today-time', 'today-avg'];
    await page.setContent(ids.map(id => `<div id="${id}"></div>`).join(''));
    await page.addScriptTag({ content: `let currentHistoryItems = [];
      const historyContainer = document.getElementById(${JSON.stringify(historyId)});\n${functions}` });
    await page.evaluate(() => {
      window.Android = { getDrivingHistory: () => JSON.stringify([{ id: 'positive-control', date: '2026-11-02',
        time: '12:00', distance: '1 km', duration: '00:01:40', avgSpeed: '36 km/h', topSpeed: '-- km/h' }]) };
      loadHistory();
    });
    const maxima = `#${historyId} .trip-history-item .list-stats-box .grid-item:last-child .grid-value`;
    assert.deepEqual(await page.locator(maxima).allTextContents(), ['0 km/h'], 'positive control: original missing-speed coercion');
    assert.equal(await page.locator('#total-top-speed').textContent(), '0 km / h');
    const rows = Array.from({ length: 819 }, (_, index) => ({ id: `compact-${index}`, started_at: iso(-index * 60000),
      distance_m: 1000, duration_s: 100, avg_speed_mps: null, max_speed_mps: null }));
    await page.evaluate(({ rows, callbacks }) => {
      for (const name of callbacks) window[name] = () => {};
      window.__compactRows = rows; window.__requests = [];
      window.fetch = async (url, options) => {
        window.__requests.push({ url, method: options.method });
        if (url !== '/api/wayon/json') throw Error('Unexpected request');
        return new Response(JSON.stringify({ trips: window.__compactRows }), { headers: { 'content-type': 'application/json' } });
      };
    }, { rows, callbacks: CALLBACKS });
    await page.addScriptTag({ content: source });
    await page.evaluate(session => window.TraverseWeb.start(session), SESSION);
    await page.evaluate(() => loadHistory());
    assert.equal(await page.locator(maxima).count(), 819);
    assert.ok((await page.locator(maxima).allTextContents()).every(value => value === '-- km/h'));
    assert.equal(await page.locator('#total-top-speed').textContent(), '-- km / h');
    await page.evaluate(async () => {
      window.__compactRows = window.__compactRows.slice(0, 3);
      window.__compactRows[1].max_speed_mps = 0;
      window.__compactRows[2].max_speed_mps = 12.5;
      await window.Android.refreshWayonCloudData(); loadHistory();
    });
    assert.deepEqual(await page.locator(maxima).allTextContents(), ['-- km/h', '0 km/h', '45 km/h']);
    assert.equal(await page.locator('#total-top-speed').textContent(), '45 km / h');
    await page.evaluate(async () => {
      window.__compactRows = [window.__compactRows[1]];
      await window.Android.refreshWayonCloudData(); loadHistory();
    });
    assert.deepEqual(await page.locator(maxima).allTextContents(), ['0 km/h']);
    assert.equal(await page.locator('#total-top-speed').textContent(), '0 km / h');
    assert.deepEqual(await page.evaluate(() => window.__requests), Array(3).fill({ url: '/api/wayon/json', method: 'GET' }));
    await page.evaluate(() => window.TraverseWeb.stop());
  } finally { await browser.close(); }
});

test('real Chromium: unchanged Android HTML keeps cached state, selects stop, gates commands and clears 401 feedback', {
  skip: !process.env.TRAVERSE_PLAYWRIGHT_MODULE,
}, async () => {
  const { chromium } = require(process.env.TRAVERSE_PLAYWRIGHT_MODULE);
  const browser = await chromium.launch({ headless: true,
    ...(process.env.TRAVERSE_BROWSER_EXECUTABLE ? { executablePath: process.env.TRAVERSE_BROWSER_EXECUTABLE } : {}),
    args: ['--disable-background-networking'],
  });
  try {
    const assets = path.resolve(__dirname, '../my-traverse-next/app/src/main/assets');
    const html = fs.readFileSync(path.join(assets, 'main.html'), 'utf8')
      .replace('<head>', '<head><script src="/bridge.js"></script>')
      .replaceAll('https://wayon-cloud.hyuklee.workers.dev/api/', '/api/wayon/');
    const payload = combined({ state: { updated_at: iso(-5000), onroad: 0, ignition: 1 },
      vehicleStatus: snapshot({ data: { ...snapshot().data, gmone_details: {
        vehicleState: { engineRunning: true }, remoteStart: { remainingTimeValid: true, remainingTimeRaw: 600 },
      } } }) });
    let session = { ...COMMAND_SESSION, capabilities: { commands: true, supportedCommands: ['DOOR_LOCK', 'VEHICLE_STOP'] } };
    const mutations = [], errors = [];
    const context = await browser.newContext({ offline: true, serviceWorkers: 'block', viewport: { width: 390, height: 844 } });
    await context.addInitScript(now => { Date.now = () => now; }, NOW);
    await context.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.origin !== 'https://fixture.invalid') return route.abort();
      if (url.pathname === '/') return route.fulfill({ contentType: 'text/html', body: html });
      if (url.pathname === '/bridge.js') return route.fulfill({ contentType: 'application/javascript', body: source });
      if (url.pathname.startsWith('/api/')) {
        if (route.request().method() !== 'GET') mutations.push(url.pathname);
        const body = url.pathname === '/api/session' ? session : url.pathname === '/api/wayon/json' ? payload : {};
        return route.fulfill({ status: url.pathname === '/api/command' ? 401 : 200,
          contentType: 'application/json', body: JSON.stringify(body) });
      }
      const file = path.resolve(assets, '.' + decodeURIComponent(url.pathname));
      if (!file.startsWith(assets + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) return route.abort();
      const contentType = { '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png', '.webp': 'image/webp',
        '.svg': 'image/svg+xml', '.woff2': 'font/woff2' }[path.extname(file)] || 'application/octet-stream';
      return route.fulfill({ contentType, body: fs.readFileSync(file) });
    });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('https://fixture.invalid/', { waitUntil: 'domcontentloaded' });
    assert.equal(await page.evaluate(session => window.TraverseWeb.start(session), session), true);
    for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
      await page.setViewportSize(viewport);
      assert.deepEqual(await page.evaluate(() => ({ state: document.body.dataset.vehicleState,
        startHidden: document.getElementById('btnEngineStart').hidden, stopHidden: document.getElementById('btnEngineStop').hidden,
        panicDisabled: document.getElementById('btnQuickHorn').getAttribute('aria-disabled'),
      })), { state: 'cached', startHidden: true, stopHidden: false, panicDisabled: 'true' });
      const bounds = await page.locator('#btnEngineStop').boundingBox();
      assert.ok(bounds && bounds.width > 0 && bounds.height > 0 && bounds.x >= 0 && bounds.x + bounds.width <= viewport.width);
    }
    session = COMMAND_SESSION;
    await page.evaluate(() => window.TraverseWeb.refreshSession());
    assert.equal(await page.locator('#btnQuickHorn').getAttribute('aria-disabled'), 'false');
    assert.equal(await page.evaluate(() => window.Android.handleLongPress('DOOR_LOCK', '', 'btnDoorToggle')), false);
    assert.equal(await page.locator('#btnDoorToggle').getAttribute('data-feedback-label'), null);
    assert.equal(await page.locator('#btnDoorToggle').evaluate(button => button.classList.contains('sending')), false);
    assert.deepEqual(mutations, ['/api/command']);
    assert.deepEqual(errors, []);
    await page.evaluate(() => window.TraverseWeb.stop());
  } finally { await browser.close(); }
});
