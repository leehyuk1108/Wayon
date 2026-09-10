// Local preview QA only. Start a dedicated Chrome profile with --remote-debugging-port=9338.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const origin='http://127.0.0.1:4198';
const targets=await(await fetch('http://127.0.0.1:9338/json/list')).json();
const target=targets.find(t=>t.type==='page'&&(t.url==='about:blank'||t.url.startsWith(origin+'/')));
assert.ok(target,'Dedicated local preview tab required');
const ws=new WebSocket(target.webSocketDebuggerUrl),pending=new Map();let sequence=0;
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
ws.onmessage=event=>{const v=JSON.parse(event.data);if(v.id){const p=pending.get(v.id);pending.delete(v.id);if(v.error)p.reject(v.error);else p.resolve(v.result)}};
const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))});
const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const output=new URL('../output/cloud-design/',import.meta.url);await fs.mkdir(output,{recursive:true});
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
await send('Page.navigate',{url:origin+'/design/cloud-overview/index.html'});
for(let i=0;i<60;i++){if(await evaluate('document.documentElement.dataset.mapReady === "true"'))break;await pause(250)}
await pause(1000);
assert.equal(await evaluate('document.documentElement.dataset.mapReady'), 'true','Vector map loaded');
assert.ok(await evaluate('map.queryRenderedFeatures().length')>0,'Vector features rendered');
const shot=async name=>{const result=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});await fs.writeFile(new URL(name+'.png',output),Buffer.from(result.data,'base64'))};
await shot('home-390');
await evaluate('navigate("vehicle")');await shot('vehicle-390');
await evaluate('data=fixture("warning");render();navigate("now")');await shot('warning-390');
await evaluate('data=fixture("parked");render();navigate("now")');
const result=[];
for(const width of [320,390,768]){
  await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:true});
  for(const large of [false,true]){
    await evaluate(`document.body.classList.toggle('large-text',${large});document.documentElement.style.fontSize='${large?32:16}px'`);
    for(const page of ['now','records','vehicle']){
      await evaluate(`navigate('${page}')`);await pause(50);
      const dimensions=await evaluate('({inner:innerWidth,scroll:document.documentElement.scrollWidth})');
      result.push({width,large,page,...dimensions});assert.ok(dimensions.scroll<=dimensions.inner,JSON.stringify(result.at(-1)));
    }
  }
}
await evaluate('document.body.classList.remove("large-text");document.documentElement.style.fontSize="16px";navigate("now")');
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
await evaluate('map.resize(); void 0');await pause(300);await shot('home-390');
const heightChecks=[];
for(const height of [844,1100,1400]){
  await send('Emulation.setDeviceMetricsOverride',{width:390,height,deviceScaleFactor:1,mobile:true});
  await pause(100);
  const geometry=await evaluate("({height:innerHeight,panelBottom:document.querySelector('.home-content').getBoundingClientRect().bottom,tabTop:document.querySelector('.tab-bar').getBoundingClientRect().top,tabBottom:document.querySelector('.tab-bar').getBoundingClientRect().bottom,mapHeight:document.querySelector('.map-section').getBoundingClientRect().height})");
  assert.ok(Math.abs(geometry.panelBottom-geometry.tabTop)<2,'No gap between home panel and tabs');
  assert.ok(Math.abs(geometry.tabBottom-height)<2,'Layout fills viewport');
  heightChecks.push(geometry);
  if(height===1100)await shot('home-tall-390');
}
assert.ok(heightChecks[2].mapHeight>heightChecks[0].mapHeight,'Extra height is used by the map');
await fs.writeFile(new URL('height-checks.json',output),JSON.stringify(heightChecks,null,2));
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});await pause(100);
// Geolocation tests use public synthetic points, never the operator's real location.
await evaluate("Object.defineProperty(navigator,'geolocation',{configurable:true,value:{getCurrentPosition:(ok)=>ok({coords:{longitude:126.981,latitude:37.568,accuracy:10}})}});void 0");
await evaluate("document.getElementById('locate-button').click()");await pause(500);
assert.equal(await evaluate("document.querySelectorAll('#map-dialog .car-pin').length"),1);
assert.equal(await evaluate("document.querySelectorAll('#map-dialog .my-location-marker').length"),1);
assert.equal(await evaluate("map.getBounds().contains(model.point)&&map.getBounds().contains(myPosition.point)"),true);
assert.equal(await evaluate("document.getElementById('map-dialog').getBoundingClientRect().height"),844);
await shot('full-map-390');
await evaluate("document.getElementById('close-map').click()");await pause(100);
assert.equal(await evaluate("document.querySelectorAll('.map-section .my-location-marker').length"),0);
assert.equal(await evaluate("document.querySelectorAll('.map-section .car-pin').length"),1);
await evaluate("Object.defineProperty(navigator,'geolocation',{configurable:true,value:{getCurrentPosition:(_ok,fail)=>fail({code:1})}});document.getElementById('locate-button').click()");await pause(100);
assert.ok((await evaluate("document.getElementById('my-location-status').textContent")).includes('권한'));
assert.equal(await evaluate("document.querySelectorAll('#map-dialog .my-location-marker').length"),0);
await evaluate("document.getElementById('close-map').click()");await pause(100);
await evaluate("Object.defineProperty(navigator,'geolocation',{configurable:true,value:{getCurrentPosition:(ok)=>{window.__testGeoSuccess=ok}}});document.getElementById('locate-button').click()");await pause(100);
await evaluate("document.getElementById('close-map').click()");await pause(100);
await evaluate("window.__testGeoSuccess({coords:{longitude:126.981,latitude:37.568,accuracy:10}})");
assert.equal(await evaluate("document.querySelectorAll('.my-location-marker').length"),0);
console.log('PASS fullscreen, two markers, fit bounds, home-only vehicle, denied location, late callback');
await send('Page.reload'); // Remove the synthetic geolocation override.
await fs.writeFile(new URL('layout-checks.json',output),JSON.stringify(result,null,2));
console.log(JSON.stringify({layoutChecks:result.length,output:output.pathname}));
ws.close();
