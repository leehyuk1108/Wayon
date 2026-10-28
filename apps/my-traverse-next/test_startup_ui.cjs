const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync(`${__dirname}/app/src/main/assets/main.html`, 'utf8');
function source(name) {
    const match = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
    assert.ok(match, name);
    return match[0];
}
const elements = new Map();
function element(id) {
    if (!elements.has(id)) {
        const children = new Map();
        const classes = new Set();
        elements.set(id, {
            id, textContent: '', innerHTML: '', hidden: false, dataset: {}, style: {}, attrs: {},
            classList: {
                add(...names) { names.forEach(name => classes.add(name)); },
                remove(...names) { names.forEach(name => classes.delete(name)); },
                contains(name) { return classes.has(name); },
                toggle(name, force) {
                    const enabled = force === undefined ? !classes.has(name) : !!force;
                    if (enabled) classes.add(name); else classes.delete(name);
                },
            },
            setAttribute(name, value) { this.attrs[name] = value; },
            getAttribute(name) { return this.attrs[name]; },
            querySelector(selector) {
                if (!children.has(selector)) children.set(selector, element(id + selector));
                return children.get(selector);
            },
        });
    }
    return elements.get(id);
}
const context = vm.createContext({
    document: { body: { dataset: {} }, getElementById: element, querySelector: element },
    window: {}, vehicleCommandReady: false, vehicleDataState: 'loading', gmoneDetailsCurrent: null,
    vehicleSnapshotTime: '', GMONE_CLOSURE_DISPLAY_MAX_AGE_MS: 24 * 60 * 60 * 1000,
    wayonLiveStateCurrent: null, latestWayonCloudVoltage: '12.8',
    formatHomeVehicleTime: value => value,
    controlDrivingActive: false, gmoneOptimisticControls: { engine: null },
    gmoneNumber: value => value == null ? null : Number(value),
    gmoneFormatNumber: String, gmoneRemoteTimeLabel: () => '10:00',
    gmoneSettings: module => module.settings || {},
    gmoneDetailsSourceUpdatedAt: details => details?.meta?.updatedAt || null,
    effectiveGmoneClosures: closures => closures || {},
    syncGmoneRemoteCountdown() {},
    scheduleDoorLockStateRefresh() {},
    effectiveGmoneEngineSnapshot: details => ({
        engineKnown: details?.vehicleState?.engineRunning != null,
        engineRunning: details?.vehicleState?.engineRunning === true,
        remoteRunning: details?.remoteStart?.remainingTimeValid === true,
        remoteStart: details?.remoteStart || {},
    }),
    renderHomeQuickIcon() {},
    renderVehicleReport() {},
    updateCarStatus(...values) { context.renderedValues = values; },
    updateGmoneDetails(details) { context.gmoneDetailsCurrent = details; },
    btnDoorToggle: element('btnDoorToggle'),
});
for (const name of ['btnEngineStart', 'btnEngineStop', 'btnTrunkOpen', 'btnTrunkClose',
    'btnWindowOpen', 'btnWindowClose', 'btnSunroofOpen', 'btnSunroofClose', 'btnSunroofTilt', 'engineTimerDisplay']) {
    context[name] = element(name);
}
for (const name of ['gmoneSourceEpoch', 'displayedGmoneClosures', 'setSmartControlAction', 'setSmartControlText', 'renderDoorLockState',
    'renderBinarySmartControl', 'updateGmoneControlPanel', 'updateVehicleCommandReady', 'setVehicleDataState']) {
    vm.runInContext(source(name), context);
}
context.setVehicleDataState('loading');
assert.equal(context.latestWayonCloudVoltage, null);
assert.equal(context.renderedValues[4], '--');
assert.equal(element('home-vehicle-updated').textContent, '차량 정보 불러오는 중');
assert.equal(element('btnDoorToggle').attrs['aria-disabled'], 'true');

context.updateVehicleCommandReady(true);
for (const id of ['btnDoorToggle', 'btnEngineStart', 'btnTrunkClose', 'btnWindowClose']) {
    assert.equal(element(id).attrs['aria-disabled'], 'false', id);
    assert.ok(!element(id).hidden, `${id} must be visible`);
    assert.ok(!element(id).dataset.controlChoices, `${id} must not open another menu`);
}
assert.equal(element('btnDoorToggle').dataset.cmd, 'DOOR_LOCK');
assert.equal(element('btnTrunkOpen').hidden, true);
assert.equal(element('btnWindowOpen').hidden, true);
assert.ok(!element('btnEngineStart').dataset.controlChoices, 'start uses its existing explicit command, no second menu');
for (let i = 0; i < 3; i++) {
    context.updateGmoneControlPanel(null);
    for (const id of ['btnTrunkOpen', 'btnSunroofOpen']) {
        assert.equal(element(id).classList.contains('state-secure'), false, `${id} unknown is not closed`);
        assert.equal(element(id).classList.contains('state-attention'), false, `${id} unknown is not open`);
    }
}

context.setVehicleDataState('unavailable');
assert.equal(element('retryVehicleData').hidden, false);
assert.equal(element('btnDoorToggle').attrs['aria-disabled'], 'false');
context.setVehicleDataState('ready');
assert.equal(element('retryVehicleData').hidden, true);

const parked = {
    meta: {updatedAt: new Date().toISOString()},
    vehicleState: { engineRunning: false }, remoteStart: { remainingStarts: 2 },
    module: { settings: { all_function_stop: 1 } },
    closures: { doors: { active: false }, hood: { active: false } },
};
context.gmoneDetailsCurrent = parked;
context.renderedValues = ['preserved'];
context.setVehicleDataState('cached', '2026-10-28 19:30:00', true);
assert.equal(context.renderedValues[0], 'preserved', 'cached values must remain visible');
assert.ok(element('home-vehicle-updated').textContent.includes('서버 저장 정보'));
assert.ok(element('home-vehicle-updated').textContent.includes('갱신 중'));
assert.equal(element('retryVehicleData').hidden, true);
assert.equal(element('btnDoorToggle').dataset.cmd, 'DOOR_UNLOCK', 'received server lock selects the labeled action');
assert.ok(!element('btnDoorToggle').dataset.controlChoices);
assert.equal(element('btnDoorToggle').querySelector('.button-text').textContent, '잠금 해제');
assert.equal(element('engine-control-state').textContent, '요청 시 상태 확인');
context.setVehicleDataState('cached', '2026-10-28 19:30:00', false);
assert.equal(element('retryVehicleData').hidden, false);
assert.equal(context.renderedValues[0], 'preserved', 'refresh failure must retain snapshot');
const freshTime = new Date().toISOString();
context.setVehicleDataState('ready', freshTime);
assert.equal(element('home-vehicle-updated').textContent, freshTime,
    'a direct response must clear the saved/refreshing label after details render');
const oldTime = new Date(Date.now() - 2 * 86400000).toISOString();
context.setVehicleDataState('ready', oldTime);
assert.equal(element('home-vehicle-updated').textContent, `마지막 수집 ${oldTime}`,
    'an old direct response must retain the age warning');
context.setVehicleDataState('ready', freshTime);
context.updateGmoneControlPanel(parked);
assert.equal(element('btnDoorToggle').dataset.cmd, 'DOOR_UNLOCK');
assert.ok(!element('btnDoorToggle').dataset.controlChoices);
assert.equal(element('btnEngineStart').attrs['aria-disabled'], 'false');
context.updateGmoneControlPanel({ ...parked, closures: { hood: { active: true } } });
assert.equal(element('btnEngineStart').attrs['aria-disabled'], 'true');
context.controlDrivingActive = true;
context.updateGmoneControlPanel(parked);
assert.equal(element('btnEngineStart').attrs['aria-disabled'], 'true');
assert.equal(element('btnDoorToggle').attrs['aria-disabled'], 'false');
context.updateVehicleCommandReady(false);
assert.equal(element('btnDoorToggle').attrs['aria-disabled'], 'true');

// Server snapshots select explicit closure actions, never engine authorization.
context.controlDrivingActive = false;
context.updateVehicleCommandReady(true);
const closed = Object.fromEntries(['doors', 'trunk', 'sunroof', 'windowFrontLeft',
    'windowFrontRight', 'windowRearLeft', 'windowRearRight'].map(key => [key, {active: false}]));
const server = {...parked, closures: closed};
context.setVehicleDataState('cached');
context.updateGmoneControlPanel(server);
for (const id of ['btnTrunkOpen', 'btnWindowOpen', 'btnSunroofOpen']) {
    assert.equal(element(id).hidden, false, `${id} is the closed-state action`);
    assert.equal(element(id).querySelector('.button-text').textContent, '열기');
}
assert.equal(element('engine-control-state').textContent, '요청 시 상태 확인');
const opened = Object.fromEntries(Object.keys(closed).map(key => [key, {active: true}]));
context.updateGmoneControlPanel({...server, closures: opened});
assert.equal(element('btnDoorToggle').dataset.cmd, 'DOOR_LOCK');
for (const id of ['btnTrunkClose', 'btnWindowClose', 'btnSunroofClose']) {
    assert.equal(element(id).hidden, false);
    assert.equal(element(id).querySelector('.button-text').textContent, '닫기');
}
for (const updatedAt of ['invalid', new Date(Date.now() - 25 * 3600000).toISOString(),
    new Date(Date.now() + 120000).toISOString()]) {
    context.updateGmoneControlPanel({...server, meta: {updatedAt}});
    assert.equal(element('btnDoorToggle').dataset.cmd, 'DOOR_LOCK');
    assert.equal(element('btnDoorToggle').querySelector('.button-text').textContent, '잠그기');
    for (const id of ['btnTrunkClose', 'btnWindowClose', 'btnSunroofClose']) {
        assert.equal(element(id).hidden, false);
        assert.equal(element(id).attrs['aria-disabled'], 'false');
        assert.equal(element(id).classList.contains('state-secure'), false);
    }
}
context.updateGmoneControlPanel({...server, closures: {windowFrontLeft: {active: false}}});
assert.equal(element('btnWindowOpen').hidden, true, 'partial window data must not imply all closed');
assert.equal(element('btnWindowClose').hidden, false);
context.updateVehicleCommandReady(false);
assert.equal(element('btnWindowClose').attrs['aria-disabled'], 'true');

// Exercise the actual long-press bridge, not just the enabled appearance.
const dispatched = [];
let fireLongPress = null;
context.activeLongPress = null;
context.longPressTimer = null;
context.longPressDuration = 600;
context.setTimeout = callback => { fireLongPress = callback; return 1; };
context.clearTimeout = () => { fireLongPress = null; };
context.window.Android = {
    showVehicleControlChoices: (...args) => dispatched.push(['choices', ...args]),
    handleLongPress: (...args) => dispatched.push(['command', ...args]),
};
context.controlDrivingActive = false;
context.setVehicleDataState('loading');
context.updateVehicleCommandReady(true);
for (const name of ['cancelLongPress', 'handleTouchStart', 'handleTouchEnd']) {
    vm.runInContext(source(name), context);
}
const touch = button => ({
    preventDefault() {}, currentTarget: button,
    touches: [{ identifier: 1 }], changedTouches: [{ identifier: 1 }],
});
context.handleTouchStart(touch(element('btnDoorToggle')));
context.setVehicleDataState('cached');
context.updateGmoneControlPanel(parked);
fireLongPress();
assert.deepEqual(dispatched, [], 'a direction change while holding must cancel, not send the opposite action');
context.handleTouchStart(touch(element('btnDoorToggle')));
fireLongPress();
assert.deepEqual(dispatched, [['command', 'DOOR_UNLOCK', '문 잠금해제', 'btnDoorToggle']],
    'the next hold sends the labeled server-state action without another choice');
context.setVehicleDataState('loading');
element('btnEngineStart').dataset.cmd = 'VEHICLE_START';
element('btnEngineStart').dataset.name = 'start';
context.handleTouchStart(touch(element('btnEngineStart')));
fireLongPress();
assert.deepEqual(dispatched[1], ['command', 'VEHICLE_START', 'start', 'btnEngineStart'],
    'engine requests must reach the native safety checks before dashboard data is ready');
context.handleTouchStart(touch(element('btnEngineStart')));
context.handleTouchEnd(touch(element('btnEngineStart')));
assert.equal(fireLongPress, null, 'releasing early must not send a command');
assert.equal(dispatched.length, 2);
context.window.Android.sendGmoneExtendedControl = (...args) => dispatched.push(['extended', ...args]);
const light = element('light');
light.dataset.gmoneControl = 'MAIN_LIGHT_ON';
context.handleTouchStart(touch(light));
light.dataset.gmoneControl = 'MAIN_LIGHT_OFF';
fireLongPress();
assert.equal(dispatched.length, 2, 'a changed light action must also cancel');
context.handleTouchStart(touch(light));
fireLongPress();
assert.deepEqual(dispatched[2], ['extended', 'MAIN_LIGHT_OFF', 'light']);
context.handleTouchStart(touch(light));
light.hidden = true;
fireLongPress();
assert.equal(dispatched.length, 3, 'a hidden action cannot dispatch');
console.log('startup UI: loading, failure, immediate controls, long-press dispatch and engine guards passed');
