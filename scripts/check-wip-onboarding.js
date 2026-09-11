async (page) => {
  const check = (value, message) => { if (!value) throw new Error(message); };
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:4198/app/src/main/assets/main.html');
  await page.setViewportSize({width:390,height:844});
  await page.locator('#connect-home').click();
  await page.locator('#connection-key').fill('wayon_short');
  await page.locator('#save-key').click();
  check((await page.locator('#key-feedback').innerText()).includes('전체 키'), 'Invalid key feedback');
  await page.evaluate(() => {
    window.Android = {
      saveWayonCloudKey() { window.onHylinkKeyPending(); }, refreshWayonData() {},
      disconnectWayonTerminal() {}, cancelCurrentLocation() {},
      requestWayonLiveSession() { throw new Error('Real live forbidden'); },
      connectWayonTerminal() { throw new Error('Real SSH forbidden'); },
    };
  });
  await page.locator('#connection-key').fill('wayon_'+'synthetic'.repeat(6));
  await page.locator('#save-key').click();
  check(await page.locator('#save-key').isDisabled(), 'Pending authentication disables duplicate submissions');
  await page.evaluate(() => onHylinkKeyError('연결 실패 테스트 · 기존 키는 유지됩니다.'));
  check(await page.locator('#save-key').isEnabled(), 'Failed auth can retry');
  await page.evaluate(() => {
    onHylinkNativeReady('wayon_'+'synthetic'.repeat(6),'https://invalid.example');
    onHylinkKeySaved('wayon_'+'synthetic'.repeat(6));
    window.__feed = (onroad, ignition, features) => onHylinkData({
      feed: {state: {updated_at:new Date().toISOString(), onroad, ignition, raw_json:{
        hylink:features, vehicle:{available:onroad, speedKph:42, steeringFault:{temporary:false, permanent:false},can:{valid:true,timeout:false}},
        device:{type:'Synthetic comma', usage:{freeSpacePercent:70},thermal:{temperaturesC:{max:45}}}
      }}}, trips:{trips:[]},snapshots:{snapshots:[]},impacts:{impacts:[]},liveCaptures:{captures:[]}
    });
    __feed(true,true,{mediaEnabled:true,impactEnabled:true,remoteEnabled:true,liveReady:false,impactReady:false,remoteReady:false});
  });
  check(await page.locator('#btnWayonLive').isDisabled(), 'Onroad live blocked');
  check(await page.locator('[data-open-terminal]').isDisabled(), 'Onroad SSH blocked');
  check((await page.locator('#vehicle-state').innerText()).includes('주행 중'), 'Driving data still shown');
  await page.locator('[data-navigate=vehicle]').click();
  check((await page.locator('#vehicle-content').innerText()).includes('42 km/h'), 'Onroad speed retained');
  await page.evaluate(() => __feed(false,false,{mediaEnabled:false,remoteEnabled:false}));
  check(await page.locator('#btnWayonLive').isDisabled(), 'Consent disabled blocks live');
  check((await page.locator('#terminal-availability').innerText()).includes('IP:1108'), 'Actionable setting guidance');
  await page.evaluate(() => __feed(false,false,{mediaEnabled:true,impactEnabled:true,remoteEnabled:true,liveReady:true,impactReady:true,remoteReady:true}));
  check(await page.locator('#btnWayonLive').isEnabled(), 'Offroad live available');
  check(await page.locator('[data-open-terminal]').isEnabled(), 'Offroad SSH available');
  let layouts = 0;
  for (const width of [320,390,768,1100]) for (const scale of [1,2]) {
    await page.setViewportSize({width,height:844});
    await page.evaluate(s => onHylinkFontScale(s),scale);
    for (const tab of ['now','records','vehicle']) {
      await page.evaluate(t => navigate(t),tab);
      check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'No overflow: '+[width,scale,tab]);
      layouts++;
    }
    await page.locator('#connection-button').click();
    check(await page.evaluate(() => document.getElementById('sheet').scrollWidth <= document.getElementById('sheet').clientWidth+1), 'Key sheet reflows');
    await page.locator('#close-sheet').click();
  }
  await page.setViewportSize({width:390,height:844});
  await page.evaluate(() => {onHylinkFontScale(1);navigate('vehicle');});
  await page.locator('#connection-button').click();
  await page.screenshot({path:'output/playwright/wip-key-entry.png'});
  await page.locator('#close-sheet').click();
  await page.evaluate(() => onHylinkKeyCleared());
  check(await page.locator('#connect-home').isVisible(), 'Logged out onboarding restored');
  check(await page.locator('#btnWayonLive').isDisabled(), 'Logged out camera blocked');
  check(errors.length === 0, 'No JS exceptions: '+errors.join(', '));
  return 'PASS key entry/validation/retry, onroad telemetry, feature consent gates, logout and '+layouts+' layouts';
}
