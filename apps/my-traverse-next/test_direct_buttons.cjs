const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');
const html = fs.readFileSync(`${__dirname}/app/src/main/assets/main.html`, 'utf8');
const activity = fs.readFileSync(`${__dirname}/app/src/main/java/com/example/carcontroller/MainActivity.kt`, 'utf8');
const source = name => html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`))[0];

test('no secondary vehicle choice dialog remains; icon-only buttons retain accessible command names', () => {
  assert.equal(/showVehicleControlChoices|controlChoices/.test(html + activity), false);
  assert.match(html, /\.home-quick-action \.button-text \{\s+display: none;/);
  for (const kind of ['Trunk', 'Window', 'Sunroof']) {
    for (const action of ['Open', 'Close']) {
      const tag = html.match(new RegExp(`id="btn${kind}${action}"[^>]+>`))[0];
      assert.match(tag, new RegExp(`data-cmd="${kind.toUpperCase()}_${action.toUpperCase()}"`));
      assert.match(tag, new RegExp(`aria-label="[^"]+${action === 'Open' ? '열기' : '닫기'}"`));
    }
  }
});

test('native engine fresh observation, hood/driving policy and cooldown are unchanged', () => {
  const body = activity.match(/        private fun executeGmoneVehicleControl\([^]*?\n        }/)[0];
  assert.match(body, /if \(vehicleControlInFlight \|\| now - lastGmoneExtendedControlTimeMs < 3_000L\)/);
  assert.match(body, /command == "VEHICLE_START" \|\| command == "VEHICLE_STOP"/);
  assert.match(body, /directVehicleObservation.recent/);
  assert.match(body, /GmoneAccountClient.fetchVehicleStatus/);
  assert.match(body, /RemoteEngineCommandPolicy.blockReason/);
  assert.ok(body.indexOf('if (reason != null) throw IOException(reason)') < body.indexOf('GmoneAccountClient.sendExtendedVehicleControl'));
});

function optimistic() {
  const now = 2000000000000;
  const context = {
    Date: {now: () => now}, gmoneDetailsRevision: 10,
    GMONE_STATE_MISMATCH_GRACE_MS: 5000, GMONE_STATE_MISMATCH_CONFIRMATIONS: 4,
    gmoneSourceEpoch: value => value,
    gmoneOptimisticControls: {doors: {expected: true, createdAt: now - 10000,
      expiresAt: now + 10000, lastCheckedRevision: 0, mismatchCount: 4}},
  };
  vm.runInNewContext(source('resolveGmoneOptimisticState'), context);
  return {context, now, run: (states, at) => context.resolveGmoneOptimisticState('doors', states, at)};
}

test('old or undated server snapshots cannot undo an acknowledged command before its deadline', () => {
  for (const offset of [null, -20000, -10000]) {
    const {context, now, run} = optimistic();
    assert.equal(run([false], offset === null ? null : now + offset), true);
    assert.ok(context.gmoneOptimisticControls.doors);
  }
});

test('newer confirmation or confirmed mismatch clears pending display; expiry remains bounded', () => {
  for (const states of [[true], [false]]) {
    const {context, now, run} = optimistic();
    assert.equal(run(states, now - 5000), null);
    assert.equal(context.gmoneOptimisticControls.doors, undefined);
  }
  const {context, now, run} = optimistic();
  context.gmoneOptimisticControls.doors.expiresAt = now;
  assert.equal(run([false], now - 20000), null);
  assert.equal(context.gmoneOptimisticControls.doors, undefined);
});

test('cached home status uses the original badge and retains genuine warnings', () => {
  const nodes = new Map();
  const element = id => {
    if (!nodes.has(id)) nodes.set(id, {textContent: '', hidden: false, innerHTML: '',
      classList: {add() {}, remove() {}}, querySelector: selector => element(selector)});
    return nodes.get(id);
  };
  let report = {tone: '', title: 'ALL\nGOOD', icon: 'check'};
  const context = {document: {getElementById: element}, vehicleDataState: 'cached',
    wayonLiveStateCurrent: null, wayonImpactStateCurrent: null,
    window: {VehicleStatusPolicy: {evaluate: () => report}}};
  vm.runInNewContext(source('renderVehicleReport'), context);
  for (const [tone, badge] of [['', 'CHECK STATUS'], ['critical', 'ATTENTION'],
    ['offline', 'CONNECTION'], ['driving', 'LIVE STATUS']]) {
    report = {...report, tone};
    context.renderVehicleReport(null);
    assert.equal(element('vehicle-report-kicker-text').textContent, badge);
    assert.equal(element('vehicle-report-title').textContent, report.title);
  }
  context.vehicleDataState = 'unavailable';
  context.renderVehicleReport(null);
  assert.equal(element('vehicle-report-title').textContent, 'UNAVAILABLE');
  assert.doesNotMatch(element('vehicle-report-detail').textContent, /눌러/);
});

test('fuel summary keeps the original timestamp format without new labels or controls', () => {
  const nodes = new Map();
  const element = id => {
    if (!nodes.has(id)) nodes.set(id, {textContent: '', style: {}});
    return nodes.get(id);
  };
  const observed = new Date(Date.now() - 3600000).toISOString();
  const context = {document: {getElementById: element}, vehicleDataState: 'cached',
    vehicleSnapshotTime: observed, traverseFuelCapacityLiters: 82.1,
    gmoneFormatNumber: (n, digits) => n.toFixed(digits)};
  for (const name of ['formatHomeVehicleTime', 'validatedFuelLevel', 'renderHomeFuelSummary']) {
    vm.runInNewContext(source(name), context);
  }
  context.renderHomeFuelSummary(433, 67.3, new Date().toISOString());
  assert.equal(element('home-vehicle-updated').textContent, context.formatHomeVehicleTime(observed));
  assert.equal(element('home-fuel-level').textContent, '~67.3 L');
  assert.equal(element('home-range-value').textContent, '433 km');
  const old = new Date(Date.now() - 2 * 86400000).toISOString();
  context.vehicleSnapshotTime = old;
  context.renderHomeFuelSummary(433, 67.3, new Date().toISOString());
  assert.equal(element('home-vehicle-updated').textContent, `마지막 수집 ${context.formatHomeVehicleTime(old)}`);
  assert.doesNotMatch(html, /SAVED STATUS|서버 저장 정보|retryVehicleData/);
});
