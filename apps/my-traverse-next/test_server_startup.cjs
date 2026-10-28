const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');
const root = `${__dirname}/app/src/main`;
const activity = fs.readFileSync(`${root}/java/com/example/carcontroller/MainActivity.kt`, 'utf8');
const html = fs.readFileSync(`${root}/assets/main.html`, 'utf8');
function body(name) {
  const match = activity.match(new RegExp(`    (?:private )?fun ${name}\\([^]*?\\n    }`));
  assert.ok(match, name);
  return match[0];
}

test('startup only fetches the authenticated server status; no phone snapshot or automatic vehicle query', () => {
  const startup = body('startForegroundVehicleRefresh');
  assert.match(startup, /vehicleStartup.begin\(false, cloud\)/);
  assert.match(startup, /remove\(VehicleSnapshotPolicy.PREF_KEY\)/);
  assert.match(startup, /setVehicleDataState\('loading'\)/);
  assert.match(startup, /refreshServerVehicleStatus\(\)/);
  assert.doesNotMatch(startup, /offerCached|decode|refreshGmoneAccountInternal|requestWayonGmoneRefresh/);
  assert.doesNotMatch(body('renderVehicleSnapshot'), /VehicleSnapshotPolicy.encode|putString/);
  assert.match(body('refreshServerVehicleStatus'), /\/api\/gmone\/status/);
  assert.match(body('refreshServerVehicleStatus'), /scope != vehicleSnapshotScope\(\)/);
  assert.match(body('refreshServerVehicleStatus'), /generation != vehicleStartup.generation/);
});

test('vehicle polling and drive-transition completion do not depend on the large feed', () => {
  assert.match(body('startWayonCloudAutoRefresh'), /refreshServerVehicleStatus\(\)/);
  assert.doesNotMatch(body('applyWayonCloudFeed'), /receiveVehicleSnapshot/);
  assert.doesNotMatch(body('refreshWayonCloudFeed'), /receiveVehicleSnapshot/);
  const transition = body('requestWayonTransitionRefresh');
  assert.match(transition, /refreshServerVehicleStatus\(force = true\)/);
  assert.doesNotMatch(transition, /refreshGmoneAccountInternal/);
  assert.match(body('applyWayonCloudFeed'), /MiniHomeWidgetStore.updateFromFeed/);
});

test('manual refresh selects one owner rather than sending both direct and collector requests', () => {
  const manual = body('triggerRefresh');
  assert.doesNotMatch(manual, /refreshGmoneAccountInternal/);
  assert.match(manual, /requestWayonGmoneRefresh\(key\)/);
  assert.match(manual, /if \(vehicleControlInFlight\)/);
  assert.match(manual, /VehicleRefreshScheduler.recordVehicleRefreshRequest/);
  assert.match(manual, /refreshServerVehicleStatus\(force = true\)/);
});

test('home keeps its original appearance; editable settings still have an explicit fresh reader', () => {
  assert.doesNotMatch(html, /서버 저장 정보|SAVED STATUS|retryVehicleData/);
  assert.match(html, /if \(meta.cached !== true\) renderGmoneSettings/);
  assert.match(html, /if \(targetTabId === 'tab-settings' && userInitiated && vehicleCommandReady && !gmoneSettingsBusy && !Object.keys\(gmoneSettingsCurrent\).length\) \{\s+window.Android\?\.refreshGmoneSettings\(\)/);
  for (const button of ['btnSecretSettings', 'btnGoToSettings']) {
    assert.match(html, new RegExp(`${button}\\.addEventListener\\('click', \\(\\) => \\{\\s+switchTab\\('tab-settings', true\\)`));
  }
});

test('actual switchTab reads settings for the settings button, which is not a bottom nav item', () => {
  const vm = require('node:vm');
  const switchSource = html.match(/        function switchTab\([^]*?\n        }/)[0];
  const targets = [...html.matchAll(/class="nav-item[^"]*" data-target="([^"]+)"/g)].map(m => m[1]);
  assert.ok(!targets.includes('tab-settings'));
  let settingsReads = 0;
  const element = {style: {}, classList: {add() {}, remove() {}}, querySelector() { return null; }};
  const context = {
    navItems: targets.map(target => ({...element, dataset: {target}})),
    document: {activeElement: null, querySelector: () => null,
      getElementById: () => element, querySelectorAll: () => [element]},
    setTimeout() {}, requestAnimationFrame() {}, recenterVehicleAfterMapCollapse() {},
    refreshDoorLockState() {}, syncWayonImpactAutoClear() {},
    vehicleCommandReady: true, gmoneSettingsBusy: false, gmoneSettingsCurrent: {},
    window: { Android: {
      refreshGmoneSettings() { settingsReads++; } } },
  };
  vm.runInNewContext(switchSource, context);
  for (const tab of targets) context.switchTab(tab);
  assert.equal(settingsReads, 0);
  context.switchTab('tab-settings');
  assert.equal(settingsReads, 0);
  context.switchTab('tab-settings', true);
  assert.equal(settingsReads, 1);
  context.gmoneSettingsBusy = true;
  context.switchTab('tab-settings', true);
  assert.equal(settingsReads, 1);
  context.gmoneSettingsBusy = false;
  context.gmoneSettingsCurrent = {actualSetting: 1};
  context.switchTab('tab-settings', true);
  assert.equal(settingsReads, 1);
  context.gmoneSettingsCurrent = {};
  context.vehicleCommandReady = false;
  context.switchTab('tab-settings', true);
  assert.equal(settingsReads, 1);
});
