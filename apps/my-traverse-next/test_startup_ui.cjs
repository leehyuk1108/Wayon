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
    wayonLiveStateCurrent: null, latestWayonCloudVoltage: '12.8',
    formatHomeVehicleTime: value => value,
    controlDrivingActive: false, gmoneOptimisticControls: { engine: null },
    gmoneNumber: value => value == null ? null : Number(value),
    gmoneFormatNumber: String, gmoneRemoteTimeLabel: () => '10:00',
    gmoneSettings: module => module.settings || {},
    gmoneDetailsSourceUpdatedAt: () => 0,
    effectiveGmoneClosures: closures => closures || {},
    syncGmoneRemoteCountdown() {},
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
for (const name of ['setSmartControlAction', 'setSmartControlText', 'renderDoorLockState',
    'renderBinarySmartControl', 'updateGmoneControlPanel', 'updateVehicleCommandReady', 'setVehicleDataState']) {
    vm.runInContext(source(name), context);
}
context.setVehicleDataState('loading');
assert.equal(context.latestWayonCloudVoltage, null);
assert.equal(context.renderedValues[4], '--');
assert.equal(element('home-vehicle-updated').textContent, '차량 정보 불러오는 중');
assert.equal(element('btnDoorToggle').attrs['aria-disabled'], 'true');

context.updateVehicleCommandReady(true);
for (const id of ['btnDoorToggle', 'btnEngineStart', 'btnTrunkOpen', 'btnWindowOpen']) {
    assert.equal(element(id).attrs['aria-disabled'], 'false', id);
    if (id !== 'btnEngineStart') assert.ok(element(id).dataset.controlChoices, `${id} must not guess current state`);
}
assert.equal(element('btnEngineStart').dataset.controlChoices, '', 'start uses its existing explicit command, no second menu');
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
    vehicleState: { engineRunning: false }, remoteStart: { remainingStarts: 2 },
    module: { settings: { all_function_stop: 1 } },
    closures: { doors: { active: false }, hood: { active: false } },
};
context.gmoneDetailsCurrent = parked;
context.renderedValues = ['preserved'];
context.setVehicleDataState('cached', '2026-10-28 19:30:00', true);
assert.equal(context.renderedValues[0], 'preserved', 'cached values must remain visible');
assert.ok(element('home-vehicle-updated').textContent.includes('저장된 정보'));
assert.ok(element('home-vehicle-updated').textContent.includes('갱신 중'));
assert.equal(element('retryVehicleData').hidden, true);
assert.equal(element('btnDoorToggle').dataset.controlChoices, 'doors', 'cached lock must not choose an action');
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
assert.equal(element('btnDoorToggle').dataset.controlChoices, '');
assert.equal(element('btnEngineStart').attrs['aria-disabled'], 'false');
context.updateGmoneControlPanel({ ...parked, closures: { hood: { active: true } } });
assert.equal(element('btnEngineStart').attrs['aria-disabled'], 'true');
context.controlDrivingActive = true;
context.updateGmoneControlPanel(parked);
assert.equal(element('btnEngineStart').attrs['aria-disabled'], 'true');
assert.equal(element('btnDoorToggle').attrs['aria-disabled'], 'false');
context.updateVehicleCommandReady(false);
assert.equal(element('btnDoorToggle').attrs['aria-disabled'], 'true');

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
context.updateGmoneControlPanel(parked);
fireLongPress();
assert.deepEqual(dispatched, [['choices', 'doors', 'btnDoorToggle']],
    'an unknown door state becoming known while holding must not change the requested action');
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
console.log('startup UI: loading, failure, immediate controls, long-press dispatch and engine guards passed');
