import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';

const require = createRequire(import.meta.url);
const {Miniflare,convertV4MiniflareOptions} = require(process.env.MINIFLARE_MODULE || 'miniflare');
const WebSocketClient = require(process.env.WS_MODULE || 'ws');
assert.ok(process.env.WAYON_RELAY_CANDIDATE,'Provide the private candidate export');
const source = readFileSync(process.env.WAYON_RELAY_CANDIDATE,'utf8');
assert.equal(createHash('sha256').update(source).digest('hex'),'67eccbf0151a79e428244b0e68bc9d800e79215c87d11d64e0b75442188633e8');
const block = source.slice(source.indexOf('var WayonDeviceRelay = class {'),source.indexOf('async function handleRemoteSession('));
const script = `const __name = () => {};
${block}
class RelayProbe extends WayonDeviceRelay {
  async fetch(request) {
    if (new URL(request.url).pathname === '/probe') return Response.json({
      events:this.events || [], sockets:this.state.getWebSockets().map(s => ({role:s.deserializeAttachment()?.role,state:s.readyState}))
    });
    return super.fetch(request);
  }
  webSocketClose(socket,...args) {
    this.events ||= [];
    this.events.push({role:socket.deserializeAttachment()?.role,before:socket.readyState,
      peers:this.state.getWebSockets().map(s=>({role:s.deserializeAttachment()?.role,state:s.readyState}))});
    super.webSocketClose(socket,...args);
  }
}
export { RelayProbe };
export default { async fetch(request, env) {
  if (new URL(request.url).pathname === '/constant') return Response.json({open:WebSocket.OPEN});
  return env.RELAY.get(env.RELAY.idFromName('isolated-test')).fetch(request);
}};`;
const options = {modules:true,script,compatibilityDate:'2026-05-14',durableObjects:{RELAY:'RelayProbe'}};
const mf = new Miniflare(convertV4MiniflareOptions ? convertV4MiniflareOptions(options) : options);
const sockets = [];
const observations = [];
const delay = ms => new Promise(resolve => setTimeout(resolve,ms));
async function until(predicate) {
  for (let i=0;i<400;i++) { if(await predicate()) return; await delay(25); }
  assert.ok(await predicate(),'runtime websocket event timed out');
}
const probe = async () => (await mf.dispatchFetch('http://relay.local/probe')).json();
async function connect(role) {
  const url = new URL('/connect',await mf.ready);
  url.protocol = 'ws:';
  const socket = new WebSocketClient(url,{headers:{'x-wayon-relay-role':role}});
  const messages = [], closes = [], errors = [];
  socket.on('message',(data,binary) => messages.push(binary ? data : data.toString()));
  socket.on('close',code => closes.push(code));
  socket.on('error',error => errors.push(String(error)));
  sockets.push(socket);
  observations.push({role,messages,closes,errors});
  await new Promise((resolve,reject) => {socket.once('open',resolve);socket.once('error',reject);});
  return {socket,messages,closes};
}
try {
  assert.deepEqual(await (await mf.dispatchFetch('http://relay.local/constant')).json(),{open:1});
  const device = await connect('device');
  const first = await connect('client');
  await until(() => device.messages.includes('wayon-peer-open'));
  const heartbeat = new Uint8Array([87,76,80,49]);
  first.socket.send(heartbeat);
  await until(() => device.messages.some(message => typeof message !== 'string'));
  assert.deepEqual(new Uint8Array(device.messages.find(message => typeof message !== 'string')),heartbeat);
  const capture = new Uint8Array(1100000).fill(42);
  capture.set([87,76,67,49]);
  first.socket.send(capture);
  await until(() => device.messages.some(message => message.byteLength === capture.byteLength));
  assert.deepEqual(new Uint8Array(device.messages.find(message => message.byteLength === capture.byteLength)),capture);
  const second = await connect('client');
  await until(() => first.closes.length > 0);
  await until(async () => (await probe()).events.some(event => event.role === 'client'));
  assert.equal(first.closes[0],1000);
  device.socket.send('replacement-viewer-frame');
  await until(() => second.messages.includes('replacement-viewer-frame'));
  assert.equal(device.messages.filter(message => message === 'wayon-peer-close').length,0);
  const replacement = await connect('device');
  await until(() => device.closes.length > 0 && replacement.messages.includes('wayon-peer-open'));
  await until(async () => (await probe()).events.some(event => event.role === 'device'));
  assert.equal(device.closes[0],1000);
  assert.deepEqual(second.closes,[]);
  replacement.socket.send('replacement-device-frame');
  await until(() => second.messages.includes('replacement-device-frame'));
  assert.equal((await mf.dispatchFetch('http://relay.local/notify-ambient',{method:'POST'})).status,204);
  await until(() => replacement.messages.includes('wayon-ambient-command-v1'));
  second.socket.close(1000,'done');
  await until(() => replacement.messages.includes('wayon-peer-close'));
  const third = await connect('client');
  await until(() => replacement.messages.filter(message => message === 'wayon-peer-open').length === 2);
  replacement.socket.close(1000,'device disconnected');
  await until(() => third.closes.includes(1012));
  console.log(JSON.stringify({workerd:true,compatibilityDate:'2026-05-14',openConstant:1,
    binaryHeartbeat:true,captureBytes:capture.byteLength,viewerReplacement:true,deviceReplacement:true,
    serverCloseCallbacksObserved:true,ambientNotify:true,closeAndReopen:true,deviceLoss:true,
    closingStateObserved:(await probe()).events.some(event => event.before === 2)}));
} catch (error) {
  console.error(JSON.stringify(observations.map(({role,messages,closes,errors}) => ({role,messageCount:messages.length,closes,errors}))));
  console.error(await (await mf.dispatchFetch('http://relay.local/probe')).text());
  throw error;
} finally {
  for(const socket of sockets) { try { socket.close(); } catch {} }
  await mf.dispose();
}
