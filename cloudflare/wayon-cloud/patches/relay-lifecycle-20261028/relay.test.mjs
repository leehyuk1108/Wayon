import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

assert.ok(process.env.WAYON_RELAY_BASELINE && process.env.WAYON_RELAY_CANDIDATE,'Provide both private exports');
const before = readFileSync(process.env.WAYON_RELAY_BASELINE, 'utf8');
const after = readFileSync(process.env.WAYON_RELAY_CANDIDATE, 'utf8');
function block(source) {
  return source.slice(source.indexOf('var WayonDeviceRelay = class {'), source.indexOf('async function handleRemoteSession('));
}
class Socket {
  constructor(role, readyState = 1) { this.role = role; this.readyState = readyState; this.sent = []; this.closed = []; }
  serializeAttachment(value) { this.role = value.role; }
  deserializeAttachment() { return {role:this.role}; }
  send(value) { if (this.readyState !== 1 || this.failSend) throw Error('closed'); this.sent.push(value); }
  close(code, reason) { this.closed.push({code,reason}); this.readyState = 2; }
}
function setup(source = after, sockets = []) {
  const state = {
    sockets,
    getWebSockets(role) { return this.sockets.filter(s => !role || s.role === role); },
    acceptWebSocket(socket, tags) { socket.role = tags[0]; socket.readyState = 1; this.sockets.push(socket); },
  };
  const context = vm.createContext({
    URL, WebSocket:{OPEN:1}, __name(){}, validSshPublicKey:() => true,
    REMOTE_SSH_MAX_AGE_SECONDS:30, REMOTE_SSH_AUTHORIZE_PREFIX:'test-only',
    textToBase64Url:value => Buffer.from(value).toString('base64url'),
    Response:class { constructor(body, options = {}) { this.body = body; Object.assign(this,options); } },
    WebSocketPair:class { constructor() { this[0] = new Socket('external'); this[1] = new Socket('unassigned'); } },
  });
  vm.runInContext(block(source), context);
  return {state, relay:new context.WayonDeviceRelay(state)};
}
const upgrade = role => new Request('https://test.invalid/relay', {headers:{upgrade:'websocket','x-wayon-relay-role':role,'x-wayon-relay-protocol':'preserved'}});

test('only relay class changes from pinned deployed worker; identity and auth remain identical', () => {
  assert.equal(createHash('sha256').update(before).digest('hex'),'d13f92bb417f302bc29bfd4fe544061a3b2ca2723ead13a608ae8a64340db25d');
  assert.equal(createHash('sha256').update(after).digest('hex'),'67eccbf0151a79e428244b0e68bc9d800e79215c87d11d64e0b75442188633e8');
  assert.equal(after.replace(block(after),block(before)),before);
});
test('retained CLOSING device before OPEN device reproduces original throw; new client selects open device', async () => {
  const old = setup(before,[new Socket('device',2),new Socket('device')]);
  await assert.rejects(old.relay.fetch(upgrade('client')),/closed/);
  const closing = new Socket('device',2), device = new Socket('device');
  const {relay} = setup(after,[closing,device]);
  const response = await relay.fetch(upgrade('client'));
  assert.equal(response.status,101);
  assert.equal(response.headers['Sec-WebSocket-Protocol'],'preserved');
  assert.deepEqual(closing.sent,[]);
  assert.deepEqual(device.sent,['wayon-peer-open']);
});
test('only closing devices gives controlled viewer close, not a failed upgrade', async () => {
  const {relay,state} = setup(after,[new Socket('device',2)]);
  assert.equal((await relay.fetch(upgrade('client'))).status,101);
  assert.equal(state.sockets.at(-1).closed[0].code,1013);
});
test('send failure during handshake closes new viewer without throwing', async () => {
  const device = new Socket('device'); device.failSend = true;
  const {relay,state} = setup(after,[device]);
  assert.equal((await relay.fetch(upgrade('client'))).status,101);
  assert.equal(state.sockets.at(-1).closed[0].code,1013);
});
test('replacement and late close cannot close the new active session', async () => {
  const device = new Socket('device'), oldClient = new Socket('client');
  const {relay,state} = setup(after,[device,oldClient]);
  await relay.fetch(upgrade('client'));
  assert.equal(oldClient.readyState,2);
  relay.webSocketClose(oldClient);
  assert.deepEqual(device.sent,['wayon-peer-open']);
  relay.webSocketClose(state.sockets.at(-1));
  assert.deepEqual(device.sent,['wayon-peer-open','wayon-peer-close']);
});
test('new device never opens camera for closing clients', async () => {
  const {relay,state} = setup(after,[new Socket('client',2)]);
  await relay.fetch(upgrade('device'));
  assert.deepEqual(state.sockets.at(-1).sent,[]);
});
test('current device loss closes open viewers; late old-device loss preserves replacement', () => {
  const client = new Socket('client'), old = new Socket('device',2), current = new Socket('device');
  const {relay} = setup(after,[client,old,current]);
  relay.webSocketClose(old);
  assert.deepEqual(client.closed,[]);
  relay.webSocketClose(current);
  assert.equal(client.closed[0].code,1012);
});
test('binary heartbeat/video preserved, client text and stale-source data rejected', () => {
  const client = new Socket('client'), device = new Socket('device'), stale = new Socket('device',2), closed = new Socket('client',3);
  const {relay} = setup(after,[client,device,stale,closed]);
  const heartbeat = new Uint8Array([87,76,80,49]).buffer;
  relay.webSocketMessage(client,heartbeat);
  assert.equal(device.sent[0],heartbeat);
  relay.webSocketMessage(client,'ignored');
  assert.equal(device.sent.length,1);
  relay.webSocketMessage(stale,'stale');
  assert.equal(client.sent.length,0);
  relay.webSocketMessage(device,heartbeat);
  assert.equal(client.sent[0],heartbeat);
  assert.equal(closed.sent.length,0);
  relay.webSocketMessage(new Socket('unknown'),heartbeat);
  assert.equal(device.sent.length,1);
});
test('ambient notify uses open device, and handles an unavailable or failing device', async () => {
  const device = new Socket('device');
  const {relay} = setup(after,[new Socket('device',2),device]);
  const request = () => new Request('https://test.invalid/notify-ambient',{method:'POST'});
  assert.equal((await relay.fetch(request())).status,204);
  assert.deepEqual(device.sent,['wayon-ambient-command-v1']);
  device.failSend = true;
  assert.equal((await relay.fetch(request())).status,503);
  assert.equal((await relay.fetch(request())).status,409);
});
test('error releases a retained socket and notifies the other side', () => {
  const device = new Socket('device'), client = new Socket('client');
  const {relay} = setup(after,[device,client]);
  relay.webSocketError(client);
  assert.equal(client.closed[0].code,1011);
  assert.deepEqual(device.sent,['wayon-peer-close']);
});
test('revoke still closes every connection, including retained closing ones', async () => {
  const sockets = [new Socket('device'),new Socket('client'),new Socket('client',2)];
  const {relay} = setup(after,sockets);
  assert.equal((await relay.fetch(new Request('https://test.invalid/revoke-key',{method:'POST'}))).status,204);
  assert.ok(sockets.every(s => s.closed[0].reason === 'key replaced'));
});

test('device replacement opens the existing viewer and rejects the old sender', async () => {
  const old = new Socket('device'), client = new Socket('client');
  const {relay,state} = setup(after,[old,client]);
  assert.equal((await relay.fetch(upgrade('device'))).status,101);
  const replacement = state.sockets.at(-1);
  assert.deepEqual(replacement.sent,['wayon-peer-open']);
  relay.webSocketClose(old);
  relay.webSocketMessage(old,'old frame');
  relay.webSocketMessage(replacement,'new frame');
  assert.deepEqual(client.closed,[]);
  assert.deepEqual(client.sent,['new frame']);
});
test('close that throws still notifies the peer', () => {
  const client = new Socket('client'), device = new Socket('device');
  client.close = () => { throw Error('already closed'); };
  const {relay} = setup(after,[client,device]);
  relay.webSocketClose(client);
  assert.deepEqual(device.sent,['wayon-peer-close']);
});
test('SSH notify selects an open device and returns controlled failure', async () => {
  const device = new Socket('device');
  const {relay} = setup(after,[new Socket('device',2),device]);
  const request = (ttlSeconds = 60) => new Request('https://test.invalid/authorize-ssh-key',{
    method:'POST',body:JSON.stringify({publicKey:'fixture-only',authorizationId:'a'.repeat(32),ttlSeconds}),
  });
  assert.equal((await relay.fetch(request(5))).status,400);
  assert.equal(device.sent.length,0);
  assert.equal((await relay.fetch(request())).status,204);
  assert.equal(device.sent.length,1);
  device.failSend = true;
  assert.equal((await relay.fetch(request())).status,503);
  device.readyState = 2;
  assert.equal((await relay.fetch(request())).status,409);
});
