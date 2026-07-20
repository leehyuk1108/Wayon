import assert from "node:assert/strict";
import { randomBytes } from "node:crypto";
import worker, {
  issueLiveProtocol,
  issueRemoteSshProtocol,
  verifyLiveProtocol,
  verifyRemoteSshProtocol,
  websocketBytes,
} from "../src/worker.js";

const secret = randomBytes(32).toString("hex");
const now = 1_800_000_000;
const protocol = await issueRemoteSshProtocol(secret, now);
const tampered = `${protocol.slice(0, -1)}${protocol.endsWith("0") ? "1" : "0"}`;

assert.equal(await verifyRemoteSshProtocol(protocol, secret, now), protocol);
assert.equal(await verifyRemoteSshProtocol(protocol, secret, now + 61), "");
assert.equal(await verifyRemoteSshProtocol(tampered, secret, now), "");
assert.equal(await verifyRemoteSshProtocol("not-wayon", secret, now), "");
const liveProtocol = await issueLiveProtocol(secret, now);
assert.equal(await verifyLiveProtocol(liveProtocol, secret, now), liveProtocol);
assert.equal(await verifyLiveProtocol(liveProtocol, secret, now + 31), "");
assert.equal(await verifyRemoteSshProtocol(liveProtocol, secret, now), "");
assert.deepEqual([...await websocketBytes(new Blob([Uint8Array.from([0, 127, 255])]))], [0, 127, 255]);

const env = {
  DB: {},
  SNAPSHOTS: {},
  WAYON_UPLOAD_TOKEN: "device-upload-token",
  WAYON_TUNNEL_TOKEN: "tunnel-token",
  WAYON_SSH_USERNAME: "comma",
  WAYON_SSH_PASSWORD: "test-password",
  WAYON_SSH_SESSION_SECRET: secret,
  WAYON_PUSH_REGISTRATION_TOKEN: "mobile-token",
  COMMA_NETWORK: {},
};
const login = (password) => worker.fetch(new Request("https://wayon.test/api/remote/session", {
  method: "POST",
  headers: {
    authorization: `Basic ${Buffer.from(`comma:${password}`, "utf8").toString("base64")}`,
  },
}), env, {});

const denied = await login("wrong-password");
assert.equal(denied.status, 401);

const accepted = await login("test-password");
assert.equal(accepted.status, 200);
const session = await accepted.json();
assert.match(session.protocol, /^wayon-ssh-v1\./);
assert.equal(await verifyRemoteSshProtocol(session.protocol, secret), session.protocol);

const bootstrap = (token) => worker.fetch(new Request("https://wayon.test/api/remote/bootstrap", {
  headers: { authorization: `Bearer ${token}` },
}), env, {});
assert.equal((await bootstrap("wrong-token")).status, 401);
const bootstrapAccepted = await bootstrap("device-upload-token");
assert.equal(bootstrapAccepted.status, 200);
assert.deepEqual(await bootstrapAccepted.json(), { tunnelToken: "tunnel-token" });

const liveSession = (token) => worker.fetch(new Request("https://wayon.test/api/live/session", {
  method: "POST",
  headers: { authorization: `Bearer ${token}` },
}), env, {});
assert.equal((await liveSession("wrong-token")).status, 401);
const liveAccepted = await liveSession("mobile-token");
assert.equal(liveAccepted.status, 200);
const live = await liveAccepted.json();
assert.match(live.protocol, /^wayon-live-v1\./);
assert.equal(live.websocketUrl, "wss://wayon.test/api/live/stream");
assert.equal(await verifyLiveProtocol(live.protocol, secret), live.protocol);
console.log("remote auth tests passed");
