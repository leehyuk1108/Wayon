const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');
const html = fs.readFileSync(`${__dirname}/app/src/main/assets/main.html`, 'utf8');
const activity = fs.readFileSync(`${__dirname}/app/src/main/java/com/example/carcontroller/MainActivity.kt`, 'utf8');
const source = name => html.match(new RegExp(`        function ${name}\\([^]*?\\n        }`))[0];

test('no secondary vehicle choice dialog remains; visible buttons name their commands', () => {
  assert.equal(/showVehicleControlChoices|controlChoices/.test(html + activity), false);
  assert.match(html, /\.home-quick-action \.button-text \{\s+display: block;/);
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
