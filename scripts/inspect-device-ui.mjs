// Read-only by default. Expression and screenshot are explicit local debugging actions.
// Never print credentials, raw feed, or location coordinates. Captures stay outside Git.
import fs from 'node:fs/promises';
const targets=await(await fetch('http://127.0.0.1:9339/json/list')).json();
const target=targets.find(t=>t.url==='file:///android_asset/main.html');
if(!target)throw Error('Hylink WebView not found');
const ws=new WebSocket(target.webSocketDebuggerUrl),pending=new Map();let seq=0;
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
ws.onmessage=e=>{const v=JSON.parse(e.data);if(v.id){const p=pending.get(v.id);pending.delete(v.id);v.error?p.reject(v.error):p.resolve(v.result)}};
const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}))});
try{
const expression=process.argv[2]||`({ready:typeof render==='function',hasKey:!!window.hylink?.token,hasFeed:!!window.hylink?.data?.feed?.state,errors:window.hylink?.data?.errors?.map(e=>e.name),mapReady:document.documentElement.dataset.mapReady,features:typeof map!=='undefined'&&map?.loaded()?map.queryRenderedFeatures().length:0,width:innerWidth,height:innerHeight,scroll:document.documentElement.scrollWidth,state:document.querySelector('#vehicle-state')?.textContent,tripCount:window.hylink?.data?.trips?.trips?.length,photoCount:window.hylink?.data?.snapshots?.snapshots?.length,captureCount:window.hylink?.data?.liveCaptures?.captures?.length})`;
const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));
console.log(JSON.stringify(result.result.value));
if(process.argv[3]){const shot=await send('Page.captureScreenshot',{format:'png'});await fs.writeFile(process.argv[3],Buffer.from(shot.data,'base64'))}
}finally{ws.close()}
