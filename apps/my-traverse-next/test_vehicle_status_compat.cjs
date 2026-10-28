const assert = require('node:assert/strict');
const test = require('node:test');
const policy = require('./app/src/main/assets/vehicle_status.js');

const now = Date.parse('2026-10-28T01:00:00Z');
const timestamp = ageSeconds => new Date(now - ageSeconds * 1000).toISOString();
const live = (overrides = {}) => ({ onroad: false, ignition: false, updatedAt: timestamp(0), ...overrides });
const details = (overrides = {}) => ({
    meta: { source: 'gmone-direct-android', updatedAt: timestamp(300), stale: false },
    battery12v: { voltageV: 12.6, temperatureC: 30 },
    closures: Object.fromEntries(['doors', 'hood', 'trunk', 'sunroof', 'windowFrontLeft',
        'windowFrontRight', 'windowRearLeft', 'windowRearRight'].map(key => [key, { active: false }])),
    tires: { frontLeftKpa: 240, frontRightKpa: 240, rearLeftKpa: 240, rearRightKpa: 240 },
    fuel: { levelLiters: 40, capacityLiters: 82.1, rangeKm: 300 },
    maintenance: { oilLifePercent: 80 },
    diagnostics: { alertCount: 0 },
    vehicleState: { engineRunning: false },
    ...overrides,
});
const qualified = overrides => ({ qualified: true, fresh: true, kind: 'vehicleInputEstimate', voltageV: 11.4, ...overrides });
const evaluate = (vehicle, current) => policy.evaluate(vehicle, current, now);

test('complete fresh GMOne data retains healthy status and its existing 24-hour window', () => {
    assert.equal(evaluate(details(), null).title, 'ALL\nGOOD');
    const vehicle = details();
    vehicle.meta.updatedAt = timestamp(24 * 3600);
    assert.equal(evaluate(vehicle, null).title, 'ALL\nGOOD');
    vehicle.meta.updatedAt = timestamp(24 * 3600 + 1);
    assert.equal(evaluate(vehicle, null).title, 'UPDATE\nDELAYED');
});

test('onroad and unknown mode retain the 45-second freshness bound', () => {
    for (const onroad of [true, undefined, null]) {
        assert.equal(evaluate(null, live({ onroad, updatedAt: timestamp(46) })).title, 'UPDATE\nDELAYED');
        assert.equal(evaluate(details(), live({ onroad, updatedAt: timestamp(46) })).title, 'UPDATE\nDELAYED');
    }
    assert.equal(evaluate(details(), live({ onroad: undefined, updatedAt: timestamp(45) })).title, 'ALL\nGOOD');
    assert.equal(evaluate(null, live({ stale: true })).title, 'UPDATE\nDELAYED');
});

test('offroad upload cadence allows 200 seconds and is bounded at 660 seconds', () => {
    for (const age of [200, 660]) {
        assert.equal(evaluate(details(), live({ updatedAt: timestamp(age) })).title, 'ALL\nGOOD');
        assert.equal(evaluate(null, live({ updatedAt: timestamp(age) })).title, 'STATUS\nUNKNOWN',
            'a timely heartbeat alone must not imply healthy');
        const cloud = details({ meta: { source: 'carrot', updatedAt: timestamp(age) } });
        assert.equal(evaluate(cloud, live({ updatedAt: timestamp(age) })).title, 'LIMITED\nDATA');
    }
    assert.equal(evaluate(details(), live({ updatedAt: timestamp(661) })).title, 'UPDATE\nDELAYED');
    assert.equal(evaluate(null, live({ updatedAt: timestamp(661) })).title, 'UPDATE\nDELAYED');
    const cloud = details({ meta: { source: 'carrot', updatedAt: timestamp(661) } });
    assert.equal(evaluate(cloud, live()).title, 'UPDATE\nDELAYED');
    assert.equal(policy.thresholds.offroadLiveStaleAfterSeconds, 660);
    assert.equal(policy.thresholds.liveStaleAfterSeconds, 45);
});

test('offroad timestamps and stale flags still gate warnings and healthy status', () => {
    for (const overrides of [
        { updatedAt: timestamp(661) }, { updatedAt: timestamp(200), stale: true },
        { updatedAt: null }, { updatedAt: 'invalid' },
    ]) {
        const result = evaluate(null, live({ ...overrides, thermalStatus: 'red', vehicleInput: qualified() }));
        assert.ok(['UPDATE\nDELAYED', 'STATUS\nUNKNOWN'].includes(result.title));
        assert.doesNotMatch(result.detail, /overheated|11\.4V|battery/i);
    }
});

test('non-GMOne cloud details cannot reuse the GMOne snapshot window or collector timestamp', () => {
    for (const source of ['firebase', 'carrot', 'wayon-cloud', '']) {
        const vehicle = details({ meta: { source, updatedAt: timestamp(46), collectedAt: timestamp(0), stale: false } });
        assert.equal(evaluate(vehicle, null).title, 'UPDATE\nDELAYED', source);
    }
});

test('GMOne collection provenance and KST timestamp parsing are retained', () => {
    const vehicle = details({ meta: {
        source: 'firebase+gmone-direct', updatedAt: timestamp(25 * 3600),
        collectedAt: '2026-10-28 09:59:00', stale: false,
    } });
    assert.equal(evaluate(vehicle, null).title, 'ALL\nGOOD');
    vehicle.meta.collectedAt = timestamp(25 * 3600);
    vehicle.meta.updatedAt = timestamp(0);
    assert.equal(evaluate(vehicle, null).title, 'UPDATE\nDELAYED');
});

test('missing, invalid or implausibly future timestamps do not imply healthy', () => {
    for (const updatedAt of [undefined, null, '', 'invalid', timestamp(-120)]) {
        assert.equal(evaluate(details({ meta: { source: 'gmone-direct', updatedAt } }), null).title, 'STATUS\nUNKNOWN');
        assert.equal(evaluate(details(), live({ updatedAt })).title, 'STATUS\nUNKNOWN');
    }
    assert.equal(evaluate({}, {}).title, 'STATUS\nUNKNOWN');
    assert.equal(evaluate(null, null).title, 'CHECKING');
});

test('partial reported checks are distinguished from absent health data without ALL GOOD', () => {
    for (const key of ['battery12v', 'closures', 'tires', 'fuel', 'maintenance', 'diagnostics', 'vehicleState']) {
        const vehicle = details();
        delete vehicle[key];
        const result = evaluate(vehicle, null);
        assert.equal(result.title, 'LIMITED\nDATA', key);
        assert.equal(result.tone, '');
        assert.match(result.detail, /No issues in reported checks.*unavailable/);
    }
    assert.equal(evaluate({ meta: details().meta }, null).title, 'STATUS\nUNKNOWN');
    assert.equal(evaluate(null, live({ voltageV: 13.8 })).title, 'STATUS\nUNKNOWN');
});

test('missing battery temperature or a tire reading means limited data, not no data or healthy', () => {
    for (const missing of ['temperature', 'tire']) {
        const vehicle = details();
        if (missing === 'temperature') delete vehicle.battery12v.temperatureC;
        else delete vehicle.tires.frontLeftKpa;
        assert.equal(evaluate(vehicle, null).title, 'LIMITED\nDATA');
        vehicle.battery12v.voltageV = 11.4;
        assert.equal(evaluate(vehicle, null).tone, 'critical', 'known issues must still win for partial data');
    }
});

test('stale voltage, temperature and other cached warnings are not current alerts', () => {
    const vehicle = details({
        battery12v: { voltageV: 5, temperatureC: 70 },
        tires: { frontLeftKpa: 180 }, maintenance: { oilLifePercent: 1 },
        diagnostics: { alertCount: 3 }, fuel: { rangeKm: 1 },
        closures: { doors: { active: true } },
    });
    for (const meta of [
        { source: 'gmone-direct', updatedAt: timestamp(0), stale: true },
        { source: 'gmone-direct', updatedAt: timestamp(25 * 3600) },
        { source: 'firebase', updatedAt: timestamp(661) },
    ]) {
        const result = evaluate({ ...vehicle, meta }, live({ updatedAt: timestamp(661), thermalStatus: 'red', voltageV: 5 }));
        assert.equal(result.title, 'UPDATE\nDELAYED');
        assert.doesNotMatch(result.detail, /battery|temperature|overheated|tire|diagnostic|fuel|unlocked/i);
    }
});

test('fresh GMOne battery thresholds and battery temperature alerts remain intact', () => {
    for (const [voltageV, tone] of [[11.5, 'critical'], [11.8, 'warning'], [11.9, 'secure']]) {
        const result = evaluate(details({ battery12v: { voltageV, temperatureC: 30 } }), null);
        assert.equal(result.tone, tone);
        if (tone !== 'secure') assert.match(result.detail, /12V battery/);
    }
    assert.equal(evaluate(details({ battery12v: { voltageV: 12.6, temperatureC: 65 } }), null).title, 'HIGH\nTEMPERATURE');
    assert.equal(evaluate(details({ battery12v: { voltageV: 12.6, temperatureC: 55 } }), null).tone, 'warning');
});

test('legacy voltage and deviceInput diagnostics never supply battery alerts', () => {
    for (const voltageV of [5, 11.4, 13.8, null]) {
        const result = evaluate(null, live({ voltageV, deviceInput: { voltageV: 5, fresh: true } }));
        assert.equal(result.title, 'STATUS\nUNKNOWN');
        assert.doesNotMatch(result.detail, /battery|5\.0V/);
    }
    const result = evaluate(details({ meta: { source: 'carrot', updatedAt: timestamp(0) }, battery12v: { voltageV: 5, temperatureC: 70 } }), null);
    assert.equal(result.title, 'LIMITED\nDATA');
    assert.doesNotMatch(result.detail, /battery|70/);
});

test('only fresh, qualified input estimates are used and are never called battery terminal voltage', () => {
    const result = evaluate(null, live({ voltageV: null, vehicleInput: qualified() }));
    assert.equal(result.tone, 'critical');
    assert.equal(result.detail, 'Vehicle input estimate 11.4V');
    for (const overrides of [{ qualified: false }, { qualified: 'true' }, { fresh: false }, { fresh: null },
        { kind: 'deviceInput' }, { kind: undefined }, { voltageV: null }]) {
        assert.equal(evaluate(null, live({ vehicleInput: qualified(overrides) })).title, 'STATUS\nUNKNOWN');
    }
    assert.equal(evaluate(null, live({ vehicleInput: qualified(), updatedAt: timestamp(661) })).title, 'UPDATE\nDELAYED');
    assert.equal(evaluate(null, live({ vehicleInput: qualified(), unavailable: true })).title, 'VEHICLE\nOFFLINE');
    assert.equal(evaluate(null, live({ vehicleInput: qualified({ voltageV: 13.8 }) })).detail,
        'Vehicle input estimate 13.8V · Vehicle health is not confirmed');
});

test('fresh GMOne battery provenance takes priority over input estimates', () => {
    assert.equal(evaluate(details(), live({ voltageV: 5, vehicleInput: qualified() })).title, 'ALL\nGOOD');
});

test('fresh warnings, driving, remote start, offline and impact priority are retained', () => {
    assert.equal(evaluate(details({ closures: { doors: { active: true } } }), null).detail, 'Doors unlocked');
    assert.equal(evaluate(details({ tires: { frontLeftKpa: 180 } }), null).title, 'TIRE\nPRESSURE');
    assert.equal(evaluate(details({ maintenance: { oilLifePercent: 5 } }), null).title, 'SERVICE\nDUE');
    assert.equal(evaluate(details({ diagnostics: { alertCount: 2 } }), null).detail, '2 diagnostic alerts');
    assert.equal(evaluate(details({ fuel: { rangeKm: 20 } }), null).tone, 'warning');
    assert.equal(evaluate(details({ remoteStart: { remainingStarts: 0 } }), null).title, 'START\nUNAVAILABLE');
    assert.equal(evaluate(details({ module: { settings: { all_function_stop: 0 } } }), null).title, 'REMOTE\nUNAVAILABLE');
    assert.equal(evaluate(details({ vehicleState: { engineRunning: true },
        remoteStart: { remainingTimeValid: true, remainingTimeRaw: 60 } }), null).title, 'REMOTE\nSTART');
    const driving = evaluate(null, live({ onroad: true, latitude: 37, longitude: 127, gpsFresh: true, openpilotActive: true, speedKph: 50 }));
    assert.equal(driving.title, 'DRIVING');
    assert.equal(driving.detail, '50 km/h · Openpilot engaged');
    assert.equal(evaluate(null, live({ onroad: true, gpsFresh: false })).title, 'LOCATION\nUNKNOWN');
    assert.equal(evaluate(null, live({ thermalStatus: 'red' })).tone, 'critical');
    assert.equal(evaluate(null, live({ ignition: true })).title, 'ENGINE\nON');
    assert.equal(evaluate(details(), live({ unavailable: true })).title, 'VEHICLE\nOFFLINE');
    assert.equal(policy.evaluate(null, live({ updatedAt: timestamp(60) }), now, { receivedAtMs: now }).title, 'IMPACT\nDETECTED');
});
