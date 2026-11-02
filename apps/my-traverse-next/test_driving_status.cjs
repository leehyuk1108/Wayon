const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');
const vm = require('node:vm');
const policy = require('./app/src/main/assets/vehicle_status.js');

const now = Date.parse('2026-11-02T00:00:00Z');
const timestamp = age => new Date(now - age * 1000).toISOString();
const live = overrides => ({
    updatedAt: timestamp(0), onroad: true, ignition: true, speedKph: 50,
    latitude: 37, longitude: 127, gpsFresh: true, ...overrides,
});
const details = overrides => ({
    meta: { source: 'gmone-direct-android', updatedAt: timestamp(10) },
    vehicleState: { engineRunning: false }, ...overrides,
});

test('GPS availability and openpilot engagement do not control the driving headline', () => {
    for (const active of [true, false]) {
        for (const gps of [
            { gpsFresh: false }, { latitude: null }, { longitude: null }, { gpsFresh: true },
        ]) {
            const result = policy.evaluate(null, live({ ...gps, openpilotActive: active }), now);
            assert.equal(result.title, 'DRIVING');
            assert.equal(result.operatingState, 'driving');
            assert.match(result.detail, active ? /Openpilot engaged/ : /Openpilot disengaged/);
            if (gps.gpsFresh === false || gps.latitude === null || gps.longitude === null) {
                assert.equal(result.tone, 'warning');
                assert.match(result.detail, /GPS unavailable/);
            }
        }
    }
});

test('vehicle warnings remain visible without replacing fresh driving or ignition state', () => {
    const cases = [
        [details({ closures: { doors: { active: true } } }), /Doors unlocked/],
        [details({ tires: { frontLeftKpa: 180 } }), /Check tire/],
        [details({ maintenance: { oilLifePercent: 5 } }), /oil service/],
        [details({ remoteStart: { remainingStarts: 0 } }), /No remote starts/],
        [details({ module: { settings: { all_function_stop: 0 } } }), /disabled/],
        [details({ meta: { source: 'gmone', updatedAt: timestamp(90000) } }), /not confirmed/],
        [details({ meta: {} }), /freshness is not confirmed/],
    ];
    for (const onroad of [true, false]) {
        for (const [vehicle, warning] of cases) {
            const result = policy.evaluate(vehicle, live({ onroad }), now);
            assert.equal(result.title, onroad ? 'DRIVING' : 'ENGINE\nON');
            assert.equal(result.tone, 'warning');
            assert.match(result.detail, warning);
            assert.match(result.healthDetail, warning);
        }
    }
});

test('missing, stale, unavailable and invalid live timestamps never gain a confirmed operating state', () => {
    for (const onroad of [true, false]) {
        for (const invalid of [
            { updatedAt: timestamp(onroad ? 46 : 661) }, { updatedAt: timestamp(-120) }, { updatedAt: 'invalid' },
            { updatedAt: null }, { stale: true }, { unavailable: true },
        ]) {
            const result = policy.evaluate(null, live({ onroad, ...invalid }), now);
            assert.equal(result.operatingState, undefined);
            assert.ok(!['DRIVING', 'ENGINE\nON'].includes(result.title));
        }
        assert.equal(policy.evaluate(null, live({ onroad, updatedAt: timestamp(onroad ? 45 : 660) }), now).tone, 'driving');
    }
    assert.equal(policy.evaluate(null, live({ onroad: false, ignition: false, updatedAt: timestamp(660) }), now).title,
        'STATUS\nUNKNOWN', 'parked heartbeat freshness must not be shortened');
});

test('urgent alerts retain their headline, severity and detail alongside operating state', () => {
    for (const onroad of [true, false]) {
        const result = policy.evaluate(details({ battery12v: { voltageV: 11.4 } }), live({ onroad }), now);
        assert.equal(result.tone, 'critical');
        assert.equal(result.title, 'ATTENTION');
        assert.match(result.detail, onroad ? /^Driving/ : /^Engine on/);
        assert.match(result.detail, /12V battery 11.4V/);
        const impact = policy.evaluate(null, live({ onroad }), now, { receivedAtMs: now });
        assert.equal(impact.title, 'IMPACT\nDETECTED');
        assert.equal(impact.operatingState, onroad ? 'driving' : 'engineOn');
        assert.match(impact.detail, /Parking security event/);
    }
});

test('remote start is retained while parked, but does not hide confirmed onroad state', () => {
    const vehicle = details({ vehicleState: { engineRunning: true },
        remoteStart: { remainingTimeValid: true, remainingTimeRaw: 60 } });
    assert.equal(policy.evaluate(vehicle, live({ onroad: false }), now).title, 'REMOTE\nSTART');
    assert.equal(policy.evaluate(vehicle, live(), now).title, 'DRIVING');
});

test('state transitions clear driving and do not mutate inputs or latch previous data', () => {
    const current = live();
    const vehicle = details();
    const original = JSON.stringify([vehicle, current]);
    assert.equal(policy.evaluate(vehicle, current, now).title, 'DRIVING');
    assert.equal(JSON.stringify([vehicle, current]), original);
    assert.equal(policy.evaluate(vehicle, live({ onroad: false, ignition: false }), now).operatingState, undefined);
    assert.equal(policy.evaluate(vehicle, null, now).operatingState, undefined);
    assert.equal(policy.evaluate(vehicle, current, now + 46000).operatingState, undefined);
});

const html = fs.readFileSync(`${__dirname}/app/src/main/assets/main.html`, 'utf8');
function renderer() {
    const elements = new Map();
    const get = id => {
        if (!elements.has(id)) elements.set(id, {
            textContent: '', hidden: true, innerHTML: '',
            classList: { add() {}, remove() {} }, querySelector: name => get(id + name),
        });
        return elements.get(id);
    };
    class FixedDate extends Date { static now() { return now; } }
    const context = vm.createContext({
        document: { getElementById: get }, Date: FixedDate,
        window: { VehicleStatusPolicy: policy },
        vehicleDataState: 'loading', wayonLiveStateCurrent: null, wayonImpactStateCurrent: null,
        vehicleCommandReady: false, controlDrivingActive: false,
        effectiveGmoneEngineSnapshot: d => ({ vehicleState: d.vehicleState, remoteStart: d.remoteStart }),
        effectiveGmoneClosures: d => d, gmoneDetailsSourceUpdatedAt: d => d?.meta?.updatedAt,
        gmoneRemoteTimeLabel: () => '1:00',
    });
    const source = html.match(/        function renderVehicleReport\([^]*?\n        }/);
    assert.ok(source);
    vm.runInContext(source[0], context);
    return { context, get };
}

test('the actual home renderer shows live operating state while separate vehicle details load or fail', () => {
    const { context, get } = renderer();
    for (const state of ['loading', 'unavailable', 'cached', 'ready']) {
        context.vehicleDataState = state;
        for (const onroad of [true, false]) {
            context.wayonLiveStateCurrent = live({ onroad, gpsFresh: false });
            context.renderVehicleReport(null);
            assert.equal(get('vehicle-report-title').textContent, onroad ? 'DRIVING' : 'ENGINE\nON');
            assert.equal(context.vehicleCommandReady, false, 'presentation must not authorize commands');
            assert.equal(context.controlDrivingActive, false, 'presentation must not change command policy');
        }
    }
});

test('the actual home renderer retains loading/unavailable gates without fresh operating evidence', () => {
    const { context, get } = renderer();
    for (const state of ['loading', 'unavailable']) {
        context.vehicleDataState = state;
        for (const current of [null, live({ updatedAt: timestamp(46) }), live({ unavailable: true }),
            live({ onroad: false, ignition: false })]) {
            context.wayonLiveStateCurrent = current;
            context.renderVehicleReport(null);
            assert.equal(get('vehicle-report-title').textContent, state === 'loading' ? 'LOADING' : 'UNAVAILABLE');
        }
    }
});
