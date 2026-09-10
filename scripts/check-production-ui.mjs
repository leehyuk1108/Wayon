// Synthetic browser regression tests. Never imported into the APK.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const targets=await(await fetch('http://127.0.0.1:9338/json/list')).json();
const target=targets.find(t=>t.type==='page');
const ws=new WebSocket(target.webSocketDebuggerUrl),pending=new Map();let sequence=0;
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
ws.onmessage=e=>{const v=JSON.parse(e.data);if(v.id){const p=pending.get(v.id);pending.delete(v.id);v.error?p.reject(v.error):p.resolve(v.result)}};
const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))});
const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
try {
await send('Page.enable');await send('Runtime.enable');
const errors=[];ws.addEventListener('message',e=>{const v=JSON.parse(e.data);if(v.method==='Runtime.exceptionThrown')errors.push(v.params.exceptionDetails.text)});
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
await send('Page.navigate',{url:'http://127.0.0.1:4198/app/src/main/assets/main.html'});await pause(1200);
assert.equal(await evaluate("document.querySelector('#vehicle-state').textContent"),'차량을 연결해 주세요');
assert.equal(await evaluate("document.querySelectorAll('.car-pin').length"),0,'No fabricated vehicle location');
await evaluate(`window.Android={refreshWayonData(){},requestTripDetail(id){window.__tripId=id},connectWayonTerminal(){throw Error('No real terminal allowed in test')},disconnectWayonTerminal(){},requestCurrentLocation(id){window.__locationId=id},cancelCurrentLocation(){}};window.onHylinkNativeReady('synthetic-test-key','https://invalid.example');window.onHylinkData({feed:{state:{updated_at:new Date().toISOString(),onroad:0,ignition:0,latitude:37.5665,longitude:126.978,voltage_v:12.4,raw_json:{gps:{fresh:true,accuracyM:6},device:{type:'comma 3X'},vehicle:{available:false}}}},trips:{trips:[{id:'test-trip',started_at:'2026-09-10T05:00:00Z',ended_at:'2026-09-10T05:22:00Z',distance_m:12700,duration_s:1320,avg_speed_mps:9.6}]},snapshots:{snapshots:[]},liveCaptures:{captures:[]},impacts:{impacts:[]}})`);
for(let i=0;i<80;i++){if(await evaluate('!!map?.loaded()'))break;await pause(250)}
assert.equal(await evaluate("document.querySelector('#trip-distance').textContent"),'12.7');
assert.ok(await evaluate('map.queryRenderedFeatures().length')>0,'Vendored vector renderer loads');
await evaluate("data.liveCaptures={captures:[{id:'test-clip',kind:'clip',duration_s:10}]};window.startWayonSavedClip=request=>{window.__testClipRequested=request.capture.durationS};document.querySelector('[data-filter=captures]').click();navigate('records')");
assert.ok((await evaluate("document.getElementById('record-content').textContent")).includes('10초 영상'),'Cloud kind=clip is video, not a photo');
assert.equal(await evaluate("document.querySelectorAll('[data-thumbnail]').length"),0,'Clip is not fetched as an image');
await evaluate("document.querySelector('[data-record]').click()");assert.equal(await evaluate('window.__testClipRequested'),10);
await evaluate("navigate('now')");
await evaluate("document.getElementById('locate-button').click()");await pause(100);
await evaluate("onHylinkLocation(window.__locationId,{latitude:37.568,longitude:126.981,accuracy:10})");
assert.equal(await evaluate("document.querySelectorAll('#map-dialog .my-location-marker').length"),1);
await evaluate("document.getElementById('close-map').click()");await pause(100);
assert.equal(await evaluate("document.querySelectorAll('.map-section .my-location-marker').length"),0);
await evaluate("document.getElementById('locate-button').click()");await pause(100);
await evaluate("onHylinkLocation(window.__locationId,{error:true,code:1})");
assert.ok((await evaluate("document.getElementById('my-location-status').textContent")).includes('권한'));
await evaluate("document.getElementById('close-map').click()");await pause(100);
await evaluate("document.getElementById('recent-trip').click()");
assert.equal(await evaluate('window.__tripId'),'test-trip');
await evaluate("onHylinkTripDetail({distance_m:12700,duration_s:1320,route:[]})");
assert.ok((await evaluate("document.getElementById('sheet-content').textContent")).includes('12.7 km'));
await evaluate("document.getElementById('close-sheet').click()");
let layouts=0;
for(const width of [320,390,768,1100])for(const scale of [1,2]){
await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:true});
await evaluate('onHylinkFontScale('+scale+')');
for(const page of ['now','records','vehicle']){
await evaluate('navigate('+JSON.stringify(page)+')');await pause(50);
assert.ok(await evaluate('document.documentElement.scrollWidth<=innerWidth'),'No horizontal overflow: '+[width,scale,page]);layouts++;
}}
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
await evaluate("onHylinkFontScale(1);navigate('now')");await pause(100);
const output=new URL('../output/production-ui/',import.meta.url);await fs.mkdir(output,{recursive:true});
const shot=await send('Page.captureScreenshot',{format:'png'});await fs.writeFile(new URL('home.png',output),Buffer.from(shot.data,'base64'));
await evaluate("onHylinkData({feed:{state:{updated_at:new Date().toISOString(),onroad:0,ignition:0}},errors:[{name:'snapshots',message:'unavailable'}]});document.querySelector('[data-filter=photos]').click();navigate('records')");
assert.ok((await evaluate("document.getElementById('record-content').textContent")).includes('갱신하지 못했어요'));
await evaluate("onHylinkKeyCleared()");await pause(100);
assert.equal(await evaluate("document.querySelectorAll('.car-pin,.my-location-marker').length"),0);
assert.equal(await evaluate('mediaCache.size'),0);
assert.deepEqual(errors,[],'No JS exceptions');
console.log('PASS production callbacks, missing data, map renderer, phone permission states, trip detail, key clearing and '+layouts+' layouts');
}finally{await send('Page.navigate',{url:'about:blank'});ws.close()}
