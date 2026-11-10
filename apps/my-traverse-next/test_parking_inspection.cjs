const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const {fileURLToPath, pathToFileURL} = require('node:url');
const api = require('./app/src/main/assets/parking-inspection.js');
const assets = path.join(__dirname, 'app/src/main/assets');
const html = fs.readFileSync(path.join(assets, 'main.html'), 'utf8');
const now = Date.parse('2026-11-04T05:00:00Z');
const evidence = [{frameIndex: 0, box: [0.1, 0.2, 0.3, 0.4]}];
const reading = (overrides = {}) => ({kind: 'pillar', text: 'B12', status: 'readable',
    alternatives: [], evidence, confidence: 'corroborated', ...overrides});
function payload(inspection) {
    return {ok: true, observation: {jobId: 'fixture', eventId: 'fixture', parkedAt: '2026-11-02T01:00:00Z', status: 'completed',
        result: {analysis: {readings: [reading({text: 'BASE'})], exactParkingSpotKnown: false},
            frames: [{phase: 'approach', camera: 'wide'}, {phase: 'parked', camera: 'road'}],
            ...(inspection === undefined ? {} : {inspection: {version: 1, status: 'completed',
                readings: [reading()], surroundings: [], exactParkingSpotKnown: false, humanVerified: false, ...inspection}})}}};
}
const model = inspection => api.viewModel(payload(inspection), now);

test('completed inspection is the fused list, never appended to baseline again', () => {
    const value = payload({readings: [reading({text: 'FUSED', confidence: 'baseline'}), reading({text: 'NEW', confidence: 'additional'})]});
    const before = JSON.stringify(value);
    const result = api.viewModel(value, now);
    assert.deepEqual(result.known.map(r => r.value), ['FUSED', 'NEW']);
    assert.equal(JSON.stringify(value), before);
    assert.deepEqual(model({readings: []}).known, [], 'empty completed results must not revive old readings');
});

test('absent, pending, failed, skipped, unsupported or malformed inspection uses original analysis', () => {
    for (const inspection of [undefined, {status: 'pending'}, {status: 'failed'}, {status: 'skipped'}, {version: 2}, {readings: null}]) {
        const result = model(inspection);
        assert.deepEqual(result.known.map(r => r.value), ['BASE']);
        assert.equal(result.known[0].badge, '\uae30\ubcf8 \ud310\ub3c5');
        assert.deepEqual(result.surroundings, []);
    }
    assert.equal(model({status: 'pending'}).status, '\ucd94\uac00 \ud655\uc778 \uc911');
});

test('baseline-only fused case keeps 203 and one environment clue; export time never replaces capture time', () => {
    const value = payload({readings: [reading({text: '203', confidence: 'baseline'})],
        surroundings: [{type: 'vent', color: 'gray', label: '\uc0ac\uc9c4 \uc624\ub978\ucabd \ud68c\uc0c9 \ud658\uae30\uad6c', evidence}]});
    value.exportGeneratedAt = new Date(now).toISOString();
    const result = api.viewModel(value, now);
    assert.deepEqual(result.known.map(r => [r.value, r.confidence]), [['203', 'baseline']]);
    assert.equal(result.known.filter(r => r.confidence === 'additional').length, 0);
    assert.equal(result.surroundings.length, 1);
    assert.match(result.time, /2026.*11.*02.*2\uc77c \uc804/);
    value.observation.result.inspection.status = 'failed';
    value.observation.result.analysis.readings = [reading({text: '203'})];
    const failed = api.viewModel(value, now);
    assert.deepEqual(failed.known.map(r => r.value), ['203']);
    assert.equal(failed.surroundings.length, 0);
});

test('confidence labels separate disagreements and uncertainty from readable signs', () => {
    const result = model({readings: ['baseline', 'corroborated', 'additional', 'conflict', 'uncertain'].map(confidence => reading({confidence}))});
    assert.deepEqual(result.known.map(r => r.badge), ['\uae30\ubcf8 \ud310\ub3c5', '\uc7ac\ud655\uc778', '\ucd94\uac00 \ud310\ub3c5']);
    assert.deepEqual(result.uncertain.map(r => r.badge), ['\ud310\ub3c5 \ubd88\uc77c\uce58', '\ud655\uc778 \ud544\uc694']);
    const ambiguous = model({readings: [reading({text: null, status: 'ambiguous', alternatives: ['B', '8'], confidence: 'uncertain'})]});
    assert.equal(ambiguous.uncertain[0].alternatives, '\ud6c4\ubcf4: B / 8');
    assert.equal(ambiguous.known.length, 0);
    assert.equal(model({readings: [reading({confidence: 'invented'})]}).known.length, 0);
});

test('approach, parked, mixed and missing evidence remain distinct', () => {
    const sample = sources => model({readings: [reading({evidence: sources})]}).known[0].evidence;
    assert.equal(sample(evidence), '\uc811\uadfc \uc911 \uc0ac\uc9c4');
    assert.equal(sample([{...evidence[0], frameIndex: 1}]), '\uc8fc\ucc28 \uc2dc \uc0ac\uc9c4');
    assert.equal(sample([...evidence, {...evidence[0], frameIndex: 1}]), '\uc811\uadfc \uc911\u00b7\uc8fc\ucc28 \uc2dc \uc0ac\uc9c4');
    for (const source of [[], [null], [{frameIndex: -1}], [{frameIndex: 12}], [{...evidence[0], box: [0, 0, Infinity, 1]}]]) {
        assert.equal(sample(source), '\ucd2c\uc601 \uc2dc\uc810 \ud655\uc778 \ud544\uc694');
    }
    const value = payload({}); value.observation.result.frames[0].camera = 'driver';
    assert.equal(api.viewModel(value, now).known[0].evidence, '\ucd2c\uc601 \uc2dc\uc810 \ud655\uc778 \ud544\uc694');
});

test('old observations always name their original KST date and age; no freshness from fetch time', () => {
    assert.match(model({}).time, /2026.*11.*02.*KST.*2\uc77c \uc804/);
    for (const date of [null, '', 'bad', '2026-11-04T05:00:00', '2027-01-01T00:00:00Z']) {
        const value = payload({}); value.observation.parkedAt = date;
        assert.equal(api.viewModel(value, now).time, '\uad00\uce21 \uc2dc\uac01 \ud655\uc778 \ud544\uc694');
    }
});

test('optional generatedAt is separately labeled and never changes observation time', () => {
    const value = payload({});
    const originalTime = api.viewModel(value, now).time;
    for (const generatedAt of ['2026-11-04T04:58:00Z', '2026-11-04T13:58:00+09:00', '2026-11-04T04:58:00.000000Z']) {
        value.generatedAt = generatedAt;
        const before = JSON.stringify(value);
        const result = api.viewModel(value, now);
        assert.equal(result.time, originalTime);
        assert.match(result.updatedTime, /^\uacb0\uacfc \uac31\uc2e0 .*2026.*11.*04.*KST.*2\ubd84 \uc804$/);
        assert.equal(JSON.stringify(value), before);
    }
});

test('missing or invalid generatedAt is omitted without making a valid observation fail', () => {
    for (const generatedAt of [undefined, null, '', 'bad', 0, false, {}, [],
        '2026-11-04T05:00:00', '2027-01-01T00:00:00Z', '2026-02-30T00:00:00Z',
        '2026-13-01T00:00:00Z', '2026-11-04T24:00:00Z', '2026-11-04T05:00:60Z',
        '2026-11-04T05:00:00+24:00', '2026-11-04T05:00:00Z' + 'x'.repeat(40)]) {
        const value = payload({});
        if (generatedAt !== undefined) value.generatedAt = generatedAt;
        const result = api.viewModel(value, now);
        assert.equal(result.phase, 'ready');
        assert.equal(result.updatedTime, '');
        assert.equal(result.time, model({}).time);
        assert.deepEqual(result.known, model({}).known);
    }
});

test('environment and coverage do not produce probabilities, coordinates or full-scene assurances', () => {
    const result = model({surroundings: [{type: 'vent', color: 'gray', label: '\uc0ac\uc9c4 \uc624\ub978\ucabd \ud68c\uc0c9 \ud658\uae30\uad6c', evidence}],
        coverage: {overviewViews: 7, overviewExpected: 12, targetsRequested: 8, targetsInspected: 4, completeSceneGuaranteed: true}});
    assert.equal(result.surroundings[0].value, '\uc0ac\uc9c4 \uc624\ub978\ucabd \ud68c\uc0c9 \ud658\uae30\uad6c');
    assert.equal(result.surroundings[0].evidence, '\uc811\uadfc \uc911 \uc0ac\uc9c4');
    assert.equal(result.coverage, '\uc804\uccb4 \uc0ac\uc9c4 \uac80\ud1a0 7/12 \u00b7 \ud45c\uc9c0 \uac80\ud1a0 4/8');
    assert.doesNotMatch(JSON.stringify(result), /%|latitude|longitude|\uc815\ud655\ud55c \uc8fc\ucc28\uba74 \ud655\uc815/);
    assert.match(result.disclaimer, /\uc0ac\ub78c \ud655\uc778 \uc804.*\uc815\ud655\ud55c \uc8fc\ucc28\uba74\uc740 \ud655\uc778\ub418\uc9c0/);
});

test('null observation and unfinished jobs have explicit states, malformed replies are not empty successes', () => {
    assert.equal(api.viewModel({ok: true, observation: null}).phase, 'empty');
    for (const value of [null, {}, {ok: false}, {ok: true}, {ok: true, observation: []}]) assert.throws(() => api.viewModel(value));
    const value = payload({}); value.observation.result = null; value.observation.status = 'running';
    assert.equal(api.viewModel(value, now).status, '\uc0ac\uc9c4 \ud310\ub3c5 \uc911');
    assert.equal(api.viewModel(value, now).known.length, 0);
});

test('bounded strings, arrays and allowlists cannot turn unknown fields into authoritative labels', () => {
    const result = model({readings: Array.from({length: 50}, () => reading({text: '\uac00'.repeat(200)})),
        surroundings: Array.from({length: 20}, () => ({type: 'door', label: 'X'.repeat(400), evidence}))});
    assert.equal(result.known.length, 32);
    assert.equal(Array.from(result.known[0].value).length, 32);
    assert.equal(result.surroundings.length, 3);
    assert.equal(result.surroundings[0].value.length, 96);
    assert.equal(model({readings: [reading({kind: '__proto__'}), reading({status: 'sure'})]}).known.length, 0);
    assert.equal(model({surroundings: [{type: 'constructor', label: 'bad'}]}).surroundings.length, 0);
});

class Element {
    constructor(tag, document) { this.tagName = tag; this.ownerDocument = document; this.children = []; this.value = ''; }
    set textContent(value) { this.value = value; this.children = []; }
    get textContent() { return this.value + this.children.map(c => c.textContent).join(''); }
    set innerHTML(_) { throw new Error('untrusted HTML sink'); }
    appendChild(child) { this.children.push(child); return child; }
    replaceChildren(...children) { this.children = children; this.value = ''; }
}
function dom() {
    const document = {createElement: tag => new Element(tag, document), createDocumentFragment: () => new Element('fragment', document)};
    return new Element('div', document);
}
const descendants = node => [node, ...node.children.flatMap(descendants)];

test('uncertain details retain all 32 rows, alternatives, badges and evidence without opening by default', () => {
    const root = dom();
    const result = model({readings: Array.from({length: 32}, (_, index) => reading({text: null, status: 'ambiguous',
        confidence: index % 2 ? 'uncertain' : 'conflict', alternatives: [`CANDIDATE-${index}`]}))});
    api.render(root, result);
    const details = descendants(root).filter(node => node.tagName === 'details');
    assert.equal(details.length, 1);
    assert.ok(!details[0].open);
    assert.equal(details[0].children[0].tagName, 'summary');
    assert.equal(details[0].children[0].textContent, '\ud655\uc778 \ud544\uc694 32\uac74');
    const rows = descendants(details[0]).filter(node => node.tagName === 'li');
    assert.equal(rows.length, 32);
    result.uncertain.forEach((item, index) => {
        assert.ok(rows[index].textContent.includes(item.alternatives));
        assert.ok(rows[index].textContent.includes(item.badge));
        assert.ok(rows[index].textContent.includes(item.evidence));
    });
});

test('known signs and environment candidates stay outside details, with the human-review disclaimer', () => {
    const root = dom();
    const result = model({readings: [reading(), reading({status: 'ambiguous', text: null, alternatives: ['B13']})],
        surroundings: [{type: 'vent', label: 'ENVIRONMENT-CANDIDATE', evidence}]});
    api.render(root, result);
    const content = root.children[0];
    assert.deepEqual(content.children.filter(node => node.tagName === 'h6').map(node => node.textContent),
        ['\uc77d\uc740 \ud45c\uc9c0', '\uc8fc\ubcc0 \ud658\uacbd \ud6c4\ubcf4']);
    assert.equal(content.children.filter(node => node.tagName === 'ul').length, 2);
    assert.ok(content.children.find(node => node.tagName === 'details'));
    assert.match(root.textContent, /AI.*\uc0ac\ub78c \ud655\uc778 \uc804/);
    api.render(root, model({readings: [reading()]}));
    assert.equal(descendants(root).filter(node => node.tagName === 'details').length, 0);
});

test('renderer orders observation before result update and skips absent update metadata', () => {
    const root = dom();
    const value = payload({});
    value.generatedAt = '2026-11-04T04:58:00Z';
    const result = api.viewModel(value, now);
    api.render(root, result);
    assert.equal(root.children[0].children[0].textContent, result.time);
    assert.equal(root.children[0].children[1].textContent, result.updatedTime);
    value.generatedAt = 'invalid';
    api.render(root, api.viewModel(value, now));
    assert.doesNotMatch(root.textContent, /\uacb0\uacfc \uac31\uc2e0/);
});

test('real renderer uses text nodes for signs, alternatives and environment; reset removes all details', () => {
    const root = dom();
    const attack = '<img src=x onerror=alert(1)>';
    const result = model({readings: [reading({text: attack}), reading({status: 'ambiguous', text: null, alternatives: [attack]})],
        surroundings: [{type: 'door', label: attack, evidence}]});
    api.render(root, result);
    assert.match(root.textContent, /<img src=x onerror=alert\(1\)>/);
    const tags = node => [node.tagName, ...node.children.flatMap(tags)];
    assert.ok(!tags(root).some(tag => ['img', 'script', 'iframe'].includes(tag)));
    api.render(root, {phase: 'idle', message: 'cleared'});
    assert.equal(root.textContent, 'cleared');
});

function controller(request = async () => ({ok: true, json: async () => payload({})})) {
    let token = 'fixture-token';
    const calls = [], states = [], timers = new Map();
    let timerId = 0;
    const view = api.createController({endpoint: '/api/parking/latest', getToken: () => token, now: () => now,
        request: (...args) => { calls.push(args); return request(...args); }, onChange: state => states.push(state),
        setTimeout: callback => { timers.set(++timerId, callback); return timerId; }, clearTimeout: id => timers.delete(id)});
    return {view, calls, states, timers, setToken(value) { token = value; view.setToken(value); },
        setRawToken(value) { token = value; }, last: () => states.at(-1)};
}
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return {promise, resolve}; };
const response = value => ({ok: true, json: async () => value});

test('only first gallery open and explicit refresh fetch; one inflight GET with existing Bearer and no-store', async () => {
    const wait = deferred(), f = controller(() => wait.promise);
    assert.equal(f.calls.length, 0);
    const first = f.view.open();
    assert.equal(f.view.open(), first);
    assert.equal(f.view.refresh(), first);
    assert.equal(f.calls.length, 1);
    assert.equal(f.calls[0][0], '/api/parking/latest');
    assert.equal(f.calls[0][1].method, 'GET');
    assert.equal(f.calls[0][1].headers.Authorization, 'Bearer fixture-token');
    assert.equal(f.calls[0][1].cache, 'no-store');
    wait.resolve(response(payload({})));
    assert.equal(await first, true);
    for (let i = 0; i < 5; i++) await f.view.open();
    assert.equal(f.calls.length, 1);
    assert.equal(f.timers.size, 0, 'no polling/retry timer survives');
    await f.view.refresh();
    assert.equal(f.calls.length, 2);
});

test('unchanged credentials/account callbacks do not clear a result or re-fetch it', async () => {
    const f = controller(); f.view.setAccount(true, 'fixture@example.invalid');
    await f.view.open();
    const before = f.states.length;
    f.setToken('fixture-token'); f.view.setAccount(true, 'fixture@example.invalid');
    assert.equal(f.states.length, before);
    await f.view.open(); assert.equal(f.calls.length, 1);
});

test('logout clears immediately and even an abort-ignoring old reply cannot repopulate', async () => {
    const wait = deferred(), f = controller(() => wait.promise);
    const pending = f.view.open();
    f.view.clear();
    assert.equal(f.last().phase, 'idle');
    assert.equal(f.calls[0][1].signal.aborted, true);
    assert.equal(await pending, false);
    wait.resolve(response(payload({})));
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(f.last().phase, 'idle');
    assert.equal(f.timers.size, 0);
});

test('account change cancels pending JSON parsing and isolates the replacement job', async () => {
    const body = deferred(); let calls = 0;
    const f = controller(async () => ++calls === 1 ? {ok: true, json: () => body.promise} : response(payload({readings: [reading({text: 'NEW'})]})));
    f.view.setAccount(true, 'first@example.invalid');
    const old = f.view.open(); await Promise.resolve();
    f.view.setAccount(true, 'second@example.invalid');
    assert.equal(f.last().phase, 'idle');
    await f.view.open();
    body.resolve(payload({readings: [reading({text: 'OLD'})]}));
    await old; await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(f.last().known.map(r => r.value), ['NEW']);
});

test('removed/replaced cloud token clears data; missing auth never sends a request', async () => {
    const f = controller(); await f.view.open();
    f.setToken(''); assert.equal(f.last().phase, 'idle');
    await f.view.open(); await f.view.refresh(); assert.equal(f.calls.length, 1);
    f.setToken('replacement-fixture'); await f.view.open();
    assert.equal(f.calls[1][1].headers.Authorization, 'Bearer replacement-fixture');
});

test('credential input changing before its callback cannot leave old data or a stuck loading state', async () => {
    for (const ok of [true, false]) {
        const wait = deferred(), f = controller(() => wait.promise);
        const pending = f.view.open();
        f.setRawToken('replacement');
        wait.resolve(ok ? response(payload({})) : {ok: false});
        assert.equal(await pending, false);
        assert.equal(f.last().phase, 'idle');
        assert.equal(f.timers.size, 0);
    }
});

test('network, HTTP and invalid JSON failures stop without retry, explicit refresh recovers', async () => {
    for (const reply of [() => Promise.reject(new Error('network')), async () => ({ok: false}),
        async () => ({ok: true, json: async () => { throw new Error('json'); }}), async () => response({ok: false})]) {
        let calls = 0;
        const f = controller((...args) => ++calls === 1 ? reply(...args) : Promise.resolve(response(payload({}))));
        assert.equal(await f.view.open(), false); assert.equal(f.last().phase, 'error');
        await f.view.open(); assert.equal(f.calls.length, 1); assert.equal(f.timers.size, 0);
        assert.equal(await f.view.refresh(), true); assert.equal(f.last().phase, 'ready');
    }
});

test('deadline covers a stuck fetch or body parser without retries or stale completion', async () => {
    for (const phase of ['fetch', 'body']) {
        const wait = deferred();
        const f = controller(() => phase === 'fetch' ? wait.promise : Promise.resolve({ok: true, json: () => wait.promise}));
        const pending = f.view.open(); await Promise.resolve();
        [...f.timers.values()][0]();
        assert.equal(await pending, false); assert.equal(f.last().phase, 'error');
        assert.equal(f.calls[0][1].signal.aborted, true);
        wait.resolve(phase === 'fetch' ? response(payload({})) : payload({}));
        await new Promise(resolve => setImmediate(resolve));
        assert.equal(f.last().phase, 'error'); assert.equal(f.timers.size, 0);
    }
});

function htmlFunction(name) {
    const match = html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`));
    assert.ok(match, name); return match[0];
}

test('actual HTML requests on gallery entry/manual refresh, never automatic feed/visibility/timer callbacks', () => {
    assert.match(htmlFunction('switchTab'), /targetTabId === 'tab-extras'\) window\.parkingInspectionView\?\.open\(\)/);
    assert.doesNotMatch(htmlFunction('onWayonCloudDataUpdated'), /parkingInspection/);
    assert.doesNotMatch(htmlFunction('updateWayonCloudSnapshots'), /parkingInspection/);
    assert.equal((html.match(/parkingInspectionView\?\.open\(/g) || []).length, 1);
    assert.equal((html.match(/parkingInspectionView\?\.refresh\(/g) || []).length, 2);
    let visible = true, refreshed = 0;
    const context = {window: {parkingInspectionView: {refresh() { refreshed++; }}}, console: {log() {}},
        document: {getElementById: () => ({classList: {contains: () => visible}})}, refreshDoorLockState() {}, showStatus() {}};
    vm.runInNewContext(htmlFunction('requestAppRefresh'), context);
    context.requestAppRefresh('pull'); assert.equal(refreshed, 1);
    visible = false; context.requestAppRefresh(); assert.equal(refreshed, 1);
});

test('HTML auth transitions clear synchronously, independent of native/PWA login completion', () => {
    assert.match(htmlFunction('updateWayonCloudKeyInput'), /parkingInspectionView\?\.setToken\(value\)/);
    assert.match(htmlFunction('updateGmoneAccountState'), /parkingInspectionView\?\.setAccount\(loggedIn, email\)/);
    for (const command of ['loginGmone', 'logoutGmone']) assert.match(html,
        new RegExp(`parkingInspectionView\\?\\.clear\\(\\);\\s+window\\.Android\\?\\.${command}`));
    assert.match(html, /event\.target\.closest\?\.\('#pwa-logout'\)\) window\.parkingInspectionView\?\.clear\(\);\s+}, true\)/);
    assert.match(html, /addEventListener\('traverseweb:sessionlost', \(\) => window\.parkingInspectionView\?\.clear\(\)\)/);
});

test('module and every inline script parse; text wrapping and accessible refresh are present', () => {
    new vm.Script(fs.readFileSync(path.join(assets, 'parking-inspection.js'), 'utf8'));
    for (const script of html.matchAll(/<script(?:\s[^>]*)?>([^]*?)<\/script>/g)) new vm.Script(script[1]);
    assert.match(html, /<script src="parking-inspection\.js"><\/script>/);
    assert.match(html, /id="parking-inspection-refresh"\s+title="[^"]+" aria-label="[^"]+"/);
    assert.match(html, /\.parking-inspection-line\s*\{[^}]*flex-wrap: wrap/);
    assert.match(html, /\.parking-inspection-badge\s*\{[^}]*white-space: normal;[^}]*overflow-wrap: anywhere/);
});

test('actual PWA build copies the new module and rewrites its HTML endpoint without any filesystem writes', async () => {
    const buildPath = path.resolve(__dirname, '../my-traverse-web/scripts/build.mjs');
    const build = fs.readFileSync(buildPath, 'utf8');
    const writes = new Map(), copies = [];
    const sharp = () => ({resize() { return this; }, flatten() { return this; }, png() { return this; }, async toFile() {}});
    const context = {
        cp: async (from, to, options) => {
            copies.push([from, to, options]);
            if (options?.recursive) writes.set(path.join(to, 'parking-inspection.js'), fs.readFileSync(path.join(from, 'parking-inspection.js'), 'utf8'));
        }, mkdir: async () => {}, unlink: async () => {}, readFile: fs.promises.readFile,
        writeFile: async (file, text) => writes.set(file, text), fileURLToPath, URL,
        createHash: require('node:crypto').createHash, sharp, console: {log() {}},
    };
    const source = build.replace(/^import .*;\r?\n/gm, '').replaceAll('import.meta.url', JSON.stringify(pathToFileURL(buildPath).href));
    await vm.runInNewContext(`(async () => {${source}\n})()`, context);
    const web = path.resolve(__dirname, '../my-traverse-web/public');
    assert.ok(copies.some(([from, to, options]) => path.resolve(from) === assets && path.resolve(to) === web && options.recursive));
    assert.equal(writes.get(path.join(web, 'parking-inspection.js')), fs.readFileSync(path.join(assets, 'parking-inspection.js'), 'utf8'));
    const built = writes.get(path.join(web, 'index.html'));
    assert.match(built, /src="parking-inspection\.js"/);
    assert.match(built, /WAYON_CLOUD_PARKING_URL = "\/api\/wayon\/parking\/latest"/);
    assert.ok(built.indexOf('src="parking-inspection.js"') < built.indexOf('window.parkingInspectionView ='));
});

test('focus picks the latest parked exterior frame of the first readable sign, with its box', () => {
    const frames = [
        {phase: 'approach', camera: 'wide', capturedAt: '2026-11-02T00:59:00Z'},
        {phase: 'parked', camera: 'wide', capturedAt: '2026-11-02T01:00:10Z'},
        {phase: 'parked', camera: 'wide', capturedAt: '2026-11-02T01:00:20Z'},
    ];
    const value = payload({readings: [reading({text: '201', evidence: [
        {frameIndex: 0, box: [0.1, 0.1, 0.2, 0.2]},
        {frameIndex: 2, box: [0.4, 0.3, 0.5, 0.45]},
        {frameIndex: 1, box: [0.41, 0.31, 0.51, 0.46]},
    ]})]});
    value.observation.result.frames = frames;
    const before = JSON.stringify(value);
    const focus = api.viewModel(value, now).focus;
    assert.deepEqual(focus, {label: '기둥 201', capturedAt: '2026-11-02T01:00:20.000Z', camera: 'wide', phase: 'parked', box: [0.4, 0.3, 0.5, 0.45]});
    assert.equal(JSON.stringify(value), before, 'the payload is not changed');
});

test('focus is null without a valid exterior frame time and box', () => {
    const base = [{phase: 'parked', camera: 'wide', capturedAt: '2026-11-02T01:00:10Z'}];
    const cases = [
        [{frameIndex: 0, box: [0.5, 0.3, 0.4, 0.45]}],
        [{frameIndex: 0, box: [0.4, 0.3, 1.5, 0.45]}],
        [{frameIndex: 0, box: [0.4, 0.3, 0.5]}],
        [{frameIndex: 3, box: [0.4, 0.3, 0.5, 0.45]}],
    ];
    for (const evidence of cases) {
        const value = payload({readings: [reading({evidence})]});
        value.observation.result.frames = base;
        assert.equal(api.viewModel(value, now).focus, null, JSON.stringify(evidence));
    }
    for (const frame of [{phase: 'parked', camera: 'driver', capturedAt: '2026-11-02T01:00:10Z'}, {phase: 'parked', camera: 'wide'}]) {
        const value = payload({readings: [reading({evidence: [{frameIndex: 0, box: [0.4, 0.3, 0.5, 0.45]}]})]});
        value.observation.result.frames = [frame];
        assert.equal(api.viewModel(value, now).focus, null, JSON.stringify(frame));
    }
    assert.equal(model({readings: [reading({status: 'ambiguous', text: null, confidence: 'uncertain'})]}).focus, null, 'unreadable signs give no focus');
});

test('unread signs with neither text nor a candidate are left out; candidates and low-confidence text stay', () => {
    // The 2026-11-10 street case: one readable sign, seven unread shop signs of which only one had a candidate.
    const unread = Array.from({length: 6}, () => reading({kind: 'unknown', status: 'ambiguous', text: null, confidence: 'uncertain'}));
    const result = model({readings: [reading({kind: 'unknown', text: 'READ', confidence: 'additional'}), ...unread,
        reading({kind: 'unknown', status: 'ambiguous', text: null, confidence: 'uncertain', alternatives: ["AMBER'S ENGLISH"]}),
        reading({kind: 'pillar', status: 'readable', text: 'B7', confidence: 'conflict'}),
        reading({kind: 'zone', status: 'ambiguous', text: null, confidence: 'uncertain', alternatives: ['   ']})]});
    assert.deepEqual(result.known.map(r => r.value), ['READ']);
    assert.deepEqual(result.uncertain.map(r => [r.value, r.alternatives]),
        [['판독 불명', "후보: AMBER'S ENGLISH"], ['B7', '']]);
    const root = dom();
    api.render(root, result);
    assert.equal(descendants(root).find(node => node.tagName === 'summary').textContent, '확인 필요 2건');
    api.render(root, model({readings: unread}));
    assert.equal(descendants(root).filter(node => node.tagName === 'details').length, 0, 'nothing to check, no fold');
    assert.match(root.textContent, /확인된 사진 단서가 없습니다/);
});
