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

// Losing the device relay invalidates every waiting client.
state.clients = [replacementClient];
relay.webSocketClose(device);
assert.deepEqual(replacementClient.closes, [[1012, "device offline"]]);

console.log("device relay lifecycle tests passed");
