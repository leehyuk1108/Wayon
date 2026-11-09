const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const care = require('./app/src/main/assets/vehicle_care.js');
const html = fs.readFileSync(`${__dirname}/app/src/main/assets/main.html`, 'utf8');

const DAY = 24 * 60 * 60 * 1000;
const NOW = Date.parse('2026-11-20T09:00:00Z');

function fuel(overrides = {}) {
    return { schemaVersion: 'wayon-trip-fuel-v1', source: 'traverseCan', usedL: 3.42, idleL: 0.61, idlePercent: 17.8,
        distanceKm: 25.3, kmPerL: 7.4, lPer100Km: 13.5, levelStartPercent: 78.8, levelEndPercent: 74.1,
        levelStartL: 64.6, levelEndL: 60.8, odometerStartKm: 61346.2, odometerEndKm: 61371.5, oilLifePercent: 25,
        observedS: 1520, partial: false, ...overrides };
}

function trip(daysAgo, fuelBlock) {
    return { time: NOW - daysAgo * DAY, analysis: fuelBlock === undefined ? {} : { schemaVersion: 'x', fuel: fuelBlock } };
}

const options = { timeOf: item => item.time };

test('trip fuel view formats the overview, details and notes', () => {
    const view = care.tripFuelView({ fuel: fuel() });
    assert.deepEqual(view.overview, [['사용 연료', '3.4 L'], ['연비', '7.4 km/L'], ['공회전 연료', '0.6 L · 18%'],
        ['연료량', '79% → 74%']]);
    assert.deepEqual(view.rows.slice(0, 4), [['100 km당', '13.5 L'], ['계기판 기준 거리', '25.3 km'],
        ['남은 연료', '64.6 → 60.8 L'], ['엔진오일 수명', '25%']]);
    assert.equal(view.rows[4][1], '25분');
    assert.equal(view.listText, '7.4 km/L · 3.4 L');
    assert.equal(view.notes.length, 1);
    const partial = care.tripFuelView({ fuel: fuel({ partial: true, kmPerL: undefined }) });
    assert.match(partial.notes[0], /일부 구간/);
    assert.equal(partial.overview[1][1], '--');
    assert.equal(partial.listText, '3.4 L 사용');
});

test('missing, foreign or malformed fuel blocks are ignored', () => {
    for (const analysis of [null, {}, { fuel: null }, { fuel: [] }, { fuel: { ...fuel(), schemaVersion: 'v0' } },
        { fuel: fuel({ usedL: 'x' }) }, { fuel: fuel({ usedL: -1 }) }, { fuel: fuel({ usedL: true }) }]) {
        assert.equal(care.tripFuelView(analysis), null);
    }
    const odd = care.tripFuel({ fuel: fuel({ levelStartPercent: 140, idlePercent: -3 }) });
    assert.equal(odd.levelStartPercent, null);
    assert.equal(odd.idlePercent, null);
});

test('refuel is a gauge jump between consecutive trips and drives the since-refuel figures', () => {
    const items = [ // newest first, like the app's history list
        trip(1, fuel({ usedL: 6, distanceKm: 60, idleL: 1, levelStartPercent: 97, levelEndPercent: 90 })),
        trip(2, fuel({ usedL: 4, distanceKm: 40, idleL: 0, levelStartPercent: 99, levelEndPercent: 97 })),
        trip(3, fuel({ usedL: 5, distanceKm: 50, idleL: 1, levelStartPercent: 12, levelEndPercent: 6 })),
        trip(4, undefined),
    ];
    const trips = care.fuelTrips(items, item => item.time);
    assert.equal(trips.length, 3);
    const refuels = care.detectRefuels(trips);
    assert.equal(refuels.length, 1);
    assert.equal(Math.round(refuels[0].addedL), 76); // 6% -> 99% of 82 L
    const summary = care.careSummary(items, null, NOW, options);
    const rows = Object.fromEntries(summary.rows.map(row => [row.label, row.value]));
    assert.equal(rows['최근 30일 연비'], '10.0 km/L · 10.0 L/100km');
    assert.equal(rows['최근 30일 주행'], '3회 · 150 km · 15.0 L');
    assert.equal(rows['공회전 연료 비율'], '13%');
    assert.match(rows['마지막 주유'], /약 \+76 L \(6% → 99%\)/);
    assert.equal(rows['주유 후'], '100 km · 10.0 L · 10.0 km/L');
    assert.equal(summary.meta, '주행 기록 3회 기준');
});

test('small gauge wobble is not a refuel and old trips leave the 30-day window', () => {
    const items = [trip(1, fuel({ levelStartPercent: 80, levelEndPercent: 78 })),
        trip(2, fuel({ levelStartPercent: 79, levelEndPercent: 75 })), trip(45, fuel())];
    assert.equal(care.detectRefuels(care.fuelTrips(items, item => item.time)).length, 0);
    const rows = care.careSummary(items, null, NOW, options).rows;
    assert.equal(rows.find(row => row.label === '최근 30일 주행').value.startsWith('2회'), true);
});

test('live readings: fresh shows charging voltage, last-known hides it, oil warning at 15%', () => {
    const live = { vehicleCare: { fresh: true, observedAt: '2026-11-20T08:59:00Z', source: 'traverseCan',
        fuelLevelPercent: 78.8, fuelLiters: 64.6, oilLifePercent: 14, odometerKm: 61466.2, batteryVoltage: 14.12,
        batteryCurrentA: 24.3, batterySocPercent: 82 } };
    const fresh = care.careSummary([], live, NOW, options);
    const rows = Object.fromEntries(fresh.rows.map(row => [row.label, row.value]));
    assert.equal(rows['연료량'], '79% · 약 65 L');
    assert.equal(rows['엔진오일 수명'], '14% · 교환 시기');
    assert.equal(rows['12V 배터리 충전'], '82%');
    assert.equal(rows['배터리 전압'], '14.1 V · 충전 24 A');
    assert.equal(rows['주행거리계'], '61,466 km');
    assert.equal(fresh.meta, '주행 중 실시간');
    assert.equal(fresh.oilWarning, true);
    const parked = care.careSummary([], { vehicleCare: { ...live.vehicleCare, fresh: false, oilLifePercent: 60 } }, NOW, options);
    assert.equal(parked.rows.some(row => row.label === '배터리 전압'), false);
    assert.match(parked.meta, /^마지막 수신 11\/20 /);
    assert.equal(parked.oilWarning, false);
});

test('bad live values are dropped and nothing known gives the empty text', () => {
    assert.equal(care.liveCare({ vehicleCare: { observedAt: 'nope', fuelLevelPercent: 50 } }), null);
    const bad = care.liveCare({ vehicleCare: { observedAt: '2026-11-20T08:00:00Z', fuelLevelPercent: 150,
        batteryVoltage: 40, oilLifePercent: '25', odometerKm: true } });
    assert.equal(bad.fuelLevelPercent, null);
    assert.equal(bad.batteryVoltage, null);
    assert.equal(bad.oilLifePercent, 25);
    assert.equal(bad.odometerKm, null);
    const empty = care.careSummary([], null, NOW, options);
    assert.equal(empty.empty, true);
    assert.match(empty.emptyText, /다음 주행부터/);
});

// main.html renderers, run against a minimal fake DOM.
const elements = new Map();
function element(id) {
    if (!elements.has(id)) {
        elements.set(id, { textContent: '', innerHTML: '', style: {}, children: [], classes: new Set(),
            classList: { toggle(name, on) { on ? this.owner.classes.add(name) : this.owner.classes.delete(name); } },
            replaceChildren(...nodes) { this.children = nodes; } });
        elements.get(id).classList.owner = elements.get(id);
    }
    return elements.get(id);
}
const rendered = [];
const context = vm.createContext({
    document: { getElementById: element, createElement: () => ({ className: '', textContent: '' }) },
    window: { VehicleCareReport: care },
    currentHistoryItems: [],
    wayonLiveStateCurrent: null,
    normalizeHistoryItems: items => items,
    tripTimestamp: item => item.time,
    renderGmoneRows: (id, rows) => rendered.push([id, rows]),
    console,
});
for (const name of ['escapeHtml', 'detailRows', 'normalizeDriveAnalysis', 'renderDriveReportFuel', 'canCareHistory', 'renderCanCare']) {
    const match = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
    assert.ok(match, name);
    vm.runInContext(match[0], context);
}
vm.runInContext('var canCareHistoryCache = null;', context);

test('trip detail fuel section renders the overview and an empty text for old trips', () => {
    context.renderDriveReportFuel({ fuel: fuel() });
    const markup = element('drive-report-fuel-content').innerHTML;
    assert.match(markup, /drive-report-fuel-overview/);
    assert.match(markup, /<span>연비<\/span><strong>7\.4 km\/L<\/strong>/);
    assert.match(markup, /<summary>연료 상세<\/summary>/);
    assert.match(markup, /drive-report-fuel-note/);
    context.renderDriveReportFuel({ schemaVersion: 'wayon-drive-report-v2' });
    assert.match(element('drive-report-fuel-content').innerHTML, /업데이트 이후 주행부터/);
});

test('info tab section uses history from the bridge once and renders rows or the empty text', () => {
    element('can-care-section');
    let reads = 0;
    context.window.Android = { getDrivingHistory: () => { reads += 1; return JSON.stringify([trip(1, fuel())]); } };
    context.renderCanCare(true);
    assert.equal(reads, 1);
    assert.equal(rendered.at(-1)[0], 'can-care-list');
    assert.equal(rendered.at(-1)[1][0].label, '최근 30일 연비');
    assert.equal(element('can-care-meta').textContent, '주행 기록 1회 기준');
    context.renderCanCare();
    assert.equal(reads, 1, 'cached between live updates');
    context.window.Android = { getDrivingHistory: () => '[]' };
    context.renderCanCare(true);
    assert.match(element('can-care-list').children[0].textContent, /다음 주행부터/);
});
