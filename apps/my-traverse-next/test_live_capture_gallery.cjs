const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const html = fs.readFileSync(`${__dirname}/app/src/main/assets/main.html`, 'utf8');
function source(name) {
    const match = html.match(new RegExp(`        (?:async )?function ${name}\\([^]*?\\n        }`));
    assert.ok(match, name);
    return match[0];
}
function fixture(captures) {
    const played = [];
    let historyRenders = 0;
    let requests = 0;
    const context = vm.createContext({
        wayonLiveCaptures: [], wayonLiveCapturesLoadedAt: 0, wayonLiveCapturesLoading: null,
        WAYON_CLOUD_LIVE_CAPTURES_URL: '/captures', WAYON_CLOUD_LIVE_CAPTURE_URL: '/capture',
        wayonLiveCaptureSummary: {}, wayonLiveCaptureCount: {},
        snapshotHistoryFilter: 'live', snapshotHistoryOverlay: { classList: { contains: () => true } },
        snapshotDateTimeDisplay: value => value,
        hasWayonCloudKey: () => true, getWayonCloudViewToken: () => 'test-token',
        renderLiveCaptureHistory() { historyRenders++; },
        window: { startWayonSavedClip: request => played.push(request) },
        async fetch(url) {
            assert.equal(url, '/captures?limit=100');
            requests++;
            return { ok: true, json: async () => ({ captures }) };
        },
    });
    for (const name of ['normalizeLiveCaptureItem', 'renderLiveCaptureSummary', 'loadWayonLiveCaptures',
        'liveCaptureUrl', 'openLiveCaptureClip']) vm.runInContext(source(name), context);
    return { context, played, historyRenders: () => historyRenders, requests: () => requests };
}

test('mixed gallery excludes only explicit road_blackbox clips and retains unknown panorama captures', async () => {
    const captures = [
        { id: 'road-json', kind: 'clip', metadata_json: '{"cameraLayout":"road_blackbox"}' },
        { id: 'road-object', kind: 'clip', metadata_json: { cameraLayout: 'road_blackbox' } },
        { id: 'road-top', kind: 'clip', cameraLayout: 'road_blackbox' },
        { id: 'road-snake', kind: 'clip', camera_layout: 'road_blackbox' },
        { id: 'road-conflict', kind: 'clip', cameraLayout: 'dual_h264', metadata_json: { cameraLayout: 'road_blackbox' } },
        { id: 'panorama', kind: 'clip', metadata_json: '{"cameraLayout":"dual_h264"}', duration_s: 10 },
        { id: 'legacy', kind: 'clip' },
        { id: 'unknown-layout', kind: 'clip', metadata_json: { cameraLayout: 'future_panorama' } },
        { id: 'bad-json', kind: 'clip', metadata_json: '{' },
        { id: 'null-json', kind: 'clip', metadata_json: 'null' },
        { id: 'photo', kind: 'photo' },
        { id: 'photo-layout', kind: 'photo', metadata_json: { cameraLayout: 'road_blackbox' } },
        { kind: 'clip' },
    ].map((capture, index) => ({ captured_at: new Date(100000 + index * 1000).toISOString(), ...capture }));
    const original = JSON.stringify(captures);
    const { context, played, historyRenders, requests } = fixture(captures);
    assert.equal(await context.loadWayonLiveCaptures(), true);
    const ids = Array.from(context.wayonLiveCaptures, capture => capture.id);
    assert.deepEqual(ids, ['photo-layout', 'photo', 'null-json', 'bad-json', 'unknown-layout', 'legacy', 'panorama']);
    assert.equal(JSON.stringify(captures), original, 'source/event capture records must not be mutated');
    assert.equal(context.wayonLiveCaptureCount.textContent, '7개');
    assert.equal(context.wayonLiveCaptureSummary.textContent, '사진 2 · 영상 5');
    assert.equal(historyRenders(), 1);
    assert.equal(context.wayonLiveCapturesLoading, null);
    assert.ok(context.wayonLiveCapturesLoadedAt > 0);
    assert.equal(await context.loadWayonLiveCaptures(), true);
    assert.equal(requests(), 1, 'cached gallery behavior is unchanged');
    for (const capture of context.wayonLiveCaptures.filter(item => item.kind === 'clip')) {
        context.openLiveCaptureClip(capture);
    }
    assert.deepEqual(played.map(request => request.capture.id), ['null-json', 'bad-json', 'unknown-layout', 'legacy', 'panorama']);
    assert.equal(played[4].url, '/capture?id=panorama');
    assert.equal(played[4].capture.durationS, 10);
});

test('blackbox-only gallery is empty without deleting records used by the events page', async () => {
    const captures = [{ id: 'event', kind: 'clip', metadata_json: '{"cameraLayout":"road_blackbox"}' }];
    const { context, played } = fixture(captures);
    assert.equal(await context.loadWayonLiveCaptures(), true);
    assert.equal(context.wayonLiveCaptures.length, 0);
    assert.equal(context.wayonLiveCaptureCount.textContent, '');
    assert.equal(context.wayonLiveCaptureSummary.textContent, '저장된 Live 기록 없음');
    assert.equal(captures.length, 1);
    assert.equal(played.length, 0);
});

test('missing, malformed and unfamiliar metadata never hide existing clips', async () => {
    const captures = [undefined, null, '', 'null', '[]', '{}', '{', { cameraLayout: null }]
        .map((metadata_json, index) => ({ id: `legacy-${index}`, kind: 'clip', metadata_json }));
    const { context } = fixture(captures);
    assert.equal(await context.loadWayonLiveCaptures(), true);
    assert.equal(context.wayonLiveCaptures.length, captures.length);
});
