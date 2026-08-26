import assert from "node:assert/strict";

import { WayonDeviceRelay } from "../src/worker.js";


class FakeSocket {
  constructor(role) {
    this.role = role;
    this.messages = [];
    this.closes = [];
  }

  deserializeAttachment() {
    return { role: this.role };
  }

  send(message) {
    this.messages.push(message);
  }

  close(code, reason) {
    this.closes.push([code, reason]);
  }
}


const device = new FakeSocket("device");
const replacementClient = new FakeSocket("client");
const state = {
  clients: [replacementClient],
  devices: [device],
  getWebSockets(role) {
    return role === "client" ? this.clients : this.devices;
  },
};
const relay = new WayonDeviceRelay(state);

// A delayed callback for the replaced client must not close the local SSH
// socket belonging to the newly accepted client.
relay.webSocketClose(new FakeSocket("client"));
assert.deepEqual(device.messages, []);

// Once the final client is gone, the device should close its local peer.
state.clients = [];
relay.webSocketClose(new FakeSocket("client"));
assert.deepEqual(device.messages, ["wayon-peer-close"]);

// A delayed callback from a replaced device must not close the active client.
state.clients = [replacementClient];
state.devices = [new FakeSocket("device")];
relay.webSocketClose(device);
assert.deepEqual(replacementClient.closes, []);

// Losing the final device relay invalidates every waiting client.
state.devices = [];
relay.webSocketClose(device);
assert.deepEqual(replacementClient.closes, [[1012, "device offline"]]);

// A key authenticated session can send one short-lived public key to the
// connected device, while client text can never forge relay control messages.
const authorizationDevice = new FakeSocket("device");
state.devices = [authorizationDevice];
state.clients = [replacementClient];
const publicKey = `ssh-rsa ${Buffer.alloc(96, 7).toString("base64")} hylink-android`;
const authorization = await relay.fetch(new Request("https://wayon.internal/authorize-ssh-key", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({
    publicKey,
    authorizationId: "0123456789abcdef0123456789abcdef",
    ttlSeconds: 90,
  }),
}));
assert.equal(authorization.status, 204);
assert.match(authorizationDevice.messages[0], /^wayon-ssh-authorize-v1\./);

const messageCount = authorizationDevice.messages.length;
relay.webSocketMessage(replacementClient, "wayon-ssh-authorize-v1.forged");
assert.equal(authorizationDevice.messages.length, messageCount);
const binary = Uint8Array.from([1, 2, 3]).buffer;
relay.webSocketMessage(replacementClient, binary);
assert.equal(authorizationDevice.messages.at(-1), binary);

console.log("device relay lifecycle tests passed");
