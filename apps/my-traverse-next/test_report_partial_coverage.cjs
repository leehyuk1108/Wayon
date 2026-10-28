const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const html = fs.readFileSync(`${__dirname}/app/src/main/assets/main.html`, 'utf8');
const elements = new Map();
function element(id) {
    if (!elements.has(id)) elements.set(id, { textContent: '', innerHTML: '', style: {} });
    return elements.get(id);
}
const context = vm.createContext({
    document: { getElementById: element },
    reportDuration: () => '--', driveReportSummaryText: () => 'unchanged summary',
    renderDriveReportHealth() {}, renderDriveReportAutomation() {}, renderDriveReportBlackbox() {}, renderDriveReportMoments() {},
});
for (const name of ['reportNumber', 'normalizeDriveAnalysis', 'reportValue', 'reportConfidenceLabel',
    'reportAnalysisConfidence', 'reportConditionLabel', 'escapeHtml', 'detailRows', 'renderDriveReportDetails', 'renderDriveReport']) {
    const match = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
    assert.ok(match, name);
    vm.runInContext(match[0], context);
}
const analysis = quality => ({ schemaVersion: 'wayon-drive-report-v1', scores: { comfort: 90 },
    comfort: {}, automation: { opUsagePercent: 75 }, dataQuality: quality });
const partial = { confidence: 'high', partial: true, partialReasons: ['resource_limit'], readSegments: 33, unreadSegments: 60 };

test('93-segment partial route shows 33/93 coverage, not high confidence, in header and details', () => {
    const item = { analysis: analysis(partial) };
    const before = JSON.stringify(item);
    context.renderDriveReport(item);
    assert.equal(element('drive-report-confidence').textContent, '부분 분석 · 33/93구간');
    assert.match(element('drive-report-details').innerHTML, /분석 범위.*부분 분석 · 33\/93구간/);
    assert.doesNotMatch(element('drive-report-details').innerHTML, /신뢰도 높음/);
    assert.equal(element('drive-report-score').textContent, 90);
    assert.equal(element('drive-report-score-state').textContent, '주행 안정적');
    assert.equal(element('drive-report-op-usage').textContent, '75%');
    assert.equal(JSON.stringify(item), before, 'coverage presentation must not mutate analysis or scores');
});

test('available high-confidence health data cannot mask partial trip analysis in the report header', () => {
    context.renderDriveReport({ analysis: analysis(partial), health: {
        available: true, confidence: 'high', load: { driverConditionScore0To100: 88 },
    } });
    assert.equal(element('drive-report-confidence').textContent, '부분 분석 · 33/93구간');
    assert.equal(element('drive-report-score').textContent, 88);
});

test('complete three-segment report and legacy reports without partial flags retain confidence labels', () => {
    context.renderDriveReport({ analysis: analysis({ confidence: 'high', partial: false, readSegments: 3, unreadSegments: 0 }) });
    assert.equal(element('drive-report-confidence').textContent, '신뢰도 높음');
    assert.match(element('drive-report-details').innerHTML, /분석 신뢰도.*신뢰도 높음/);
    assert.doesNotMatch(element('drive-report-details').innerHTML, /부분 분석/);
    for (const [confidence, label] of [['high', '신뢰도 높음'], ['medium', '신뢰도 보통'], ['low', '신뢰도 낮음']]) {
        assert.equal(context.reportAnalysisConfidence(analysis({ confidence })), label);
    }
    assert.equal(context.reportAnalysisConfidence({}), '분석 대기');
});

test('coverage accepts bounded integer counts, explicit total, zero read, and numeric strings', () => {
    for (const [quality, label] of [
        [{ readSegments: 33, totalSegments: 93 }, '부분 분석 · 33/93구간'],
        [{ readSegments: '33', unreadSegments: '60' }, '부분 분석 · 33/93구간'],
        [{ readSegments: 0, unreadSegments: 93 }, '부분 분석 · 0/93구간'],
    ]) assert.equal(context.reportAnalysisConfidence(analysis({ partial: true, ...quality })), label);
});

test('missing, negative, fractional, unsafe and inconsistent counts retain partial with unknown coverage', () => {
    for (const quality of [
        {}, { readSegments: 33 }, { readSegments: 94, totalSegments: 93 },
        { readSegments: 0, unreadSegments: 0 }, { readSegments: true, unreadSegments: 60 },
        { readSegments: -1, unreadSegments: 60 }, { readSegments: 1.5, unreadSegments: 60 },
        { readSegments: Infinity, unreadSegments: 60 }, { readSegments: '', unreadSegments: 60 },
        { readSegments: Number.MAX_SAFE_INTEGER, unreadSegments: 1 },
        { readSegments: '<script>', unreadSegments: 60 },
    ]) assert.equal(context.reportAnalysisConfidence(analysis({ confidence: 'high', partial: true, ...quality })), '부분 분석 · 범위 미상');
});

test('outer native partial metadata survives a structured legacy report wrapper without modifying it', () => {
    const nested = analysis({ confidence: 'high' });
    const wrapped = { schemaVersion: 'wayon-drive-report-v1-legacy', legacyReport: nested, dataQuality: partial };
    const before = JSON.stringify(wrapped);
    context.renderDriveReport({ analysis: wrapped });
    assert.equal(element('drive-report-confidence').textContent, '부분 분석 · 33/93구간');
    assert.match(element('drive-report-details').innerHTML, /33\/93구간/);
    assert.equal(JSON.stringify(wrapped), before);
    assert.equal(context.normalizeDriveAnalysis(wrapped).scores, nested.scores);
});
