const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const care = require('./app/src/main/assets/vehicle_care.js');
const html = fs.readFileSync(`${__dirname}/app/src/main/assets/main.html`, 'utf8');

function fuel(overrides = {}) {
    return { schemaVersion: 'wayon-trip-fuel-v1', source: 'traverseCan', usedL: 3.42, idleL: 0.61, idlePercent: 17.8,
        distanceKm: 25.3, kmPerL: 7.4, lPer100Km: 13.5, levelStartPercent: 78.8, levelEndPercent: 74.1,
        levelStartL: 64.6, levelEndL: 60.8, odometerStartKm: 61346.2, odometerEndKm: 61371.5, oilLifePercent: 25,
        observedS: 1520, partial: false, longGaps: 0, ...overrides };
}

test('trip fuel view gives the km/L for the drive report and the fuel detail rows', () => {
    const view = care.tripFuelView({ fuel: fuel() });
    assert.equal(view.economyText, '7.4 km/L');
    assert.deepEqual(view.rows.slice(0, 6), [['사용 연료', '3.4 L'], ['공회전 연료', '0.6 L · 18%'], ['100 km당', '13.5 L'],
        ['연료량', '79% → 74%'], ['남은 연료', '64.6 → 60.8 L'], ['연비 계산 거리', '25.3 km']]);
    assert.equal(view.rows[6][1], '25%');
    assert.equal(view.rows[7][1], '25분');
    assert.equal(view.notes.length, 1);
});

test('short trips have no km/L; partial and gap trips explain themselves', () => {
    const view = care.tripFuelView({ fuel: fuel({ kmPerL: undefined, lPer100Km: undefined, partial: true, longGaps: 2 }) });
    assert.equal(view.economyText, '--');
    assert.ok(view.notes.some(note => /일부 구간/.test(note)));
    assert.ok(view.notes.some(note => /끊긴 구간/.test(note)));
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

// main.html renderers against a minimal fake DOM.
const elements = new Map();
function element(id) {
    if (!elements.has(id)) elements.set(id, { textContent: '', innerHTML: '', style: {} });
    return elements.get(id);
}
const context = vm.createContext({
    document: { getElementById: element },
    window: { VehicleCareReport: care },
    reportDuration: () => '--',
});
for (const name of ['escapeHtml', 'detailRows', 'reportNumber', 'reportValue', 'reportConfidenceLabel', 'reportAnalysisConfidence',
    'renderDriveReportEconomy', 'fuelDetailsHtml', 'renderDriveReportDetails']) {
    const match = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
    assert.ok(match, name);
    vm.runInContext(match[0], context);
}

test('drive report shows km/L beside distance, time and speeds, and a fuel group in the details', () => {
    assert.match(html, /<span>최고속도<\/span><strong id="trip-detail-top">--<\/strong><\/div>\s*<div class="drive-report-overview-item"><span>연비<\/span><strong id="trip-detail-economy">/);
    const analysis = { schemaVersion: 'wayon-drive-report-v2', fuel: fuel() };
    context.renderDriveReportEconomy(analysis);
    assert.equal(element('trip-detail-economy').textContent, '7.4 km/L');
    context.renderDriveReportDetails(analysis);
    assert.match(element('drive-report-details').innerHTML, /<summary>연료<\/summary>.*사용 연료.*3\.4 L/s);
    context.renderDriveReportEconomy({ schemaVersion: 'wayon-drive-report-v2' });
    assert.equal(element('trip-detail-economy').textContent, '--');
    context.renderDriveReportDetails({ schemaVersion: 'wayon-drive-report-v2' });
    assert.doesNotMatch(element('drive-report-details').innerHTML, /<summary>연료<\/summary>/);
});

test('trip list card adds 연비 as a fourth stat only when the trip has fuel data', () => {
    assert.match(html, /const economyStat = fuelView[\s\S]*?<span class="grid-label">연비<\/span>/);
    assert.match(html, /<span class="grid-label">최고<\/span>[\s\S]*?<\/div>\s*\$\{economyStat\}\s*<\/div>/);
});
