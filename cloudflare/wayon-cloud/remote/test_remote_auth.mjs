import assert from "node:assert/strict";
import { createHash, randomBytes } from "node:crypto";
import worker, {
  issueLiveProtocol,
  issueRemoteSshProtocol,
  verifyLiveProtocol,
  verifyRemoteSshProtocol,
  visibleFcmNotification,
  WayonLiveFrameAssembler,
  websocketBytes,
} from "../src/worker.js";

const secret = randomBytes(32).toString("hex");
const now = 1_800_000_000;
const deviceId = "test-dongle-001";
const protocol = await issueRemoteSshProtocol(secret, deviceId, now);
const tampered = `${protocol.slice(0, -1)}${protocol.endsWith("0") ? "1" : "0"}`;

assert.deepEqual(await verifyRemoteSshProtocol(protocol, secret, now), { protocol, deviceId });
assert.equal(await verifyRemoteSshProtocol(protocol, secret, now + 61), null);
assert.equal(await verifyRemoteSshProtocol(tampered, secret, now), null);
assert.equal(await verifyRemoteSshProtocol("not-wayon", secret, now), null);
const liveProtocol = await issueLiveProtocol(secret, deviceId, now);
assert.deepEqual(await verifyLiveProtocol(liveProtocol, secret, now), {
  protocol: liveProtocol,
  deviceId,
});
assert.equal(await verifyLiveProtocol(liveProtocol, secret, now + 31), null);
assert.equal(await verifyRemoteSshProtocol(liveProtocol, secret, now), null);
assert.deepEqual([...await websocketBytes(new Blob([Uint8Array.from([0, 127, 255])]))], [0, 127, 255]);

const liveFrame = (type, payload) => {
  const frame = new Uint8Array(24 + payload.length);
  frame.set([87, 76, 86, 49, type], 0);
  new DataView(frame.buffer).setUint32(20, payload.length);
  frame.set(payload, 24);
  return frame;
};
const frameAssembler = new WayonLiveFrameAssembler();
const wideFrame = liveFrame(1, Uint8Array.from([1, 2, 3, 4]));
const driverFrame = liveFrame(2, Uint8Array.from([5, 6]));
assert.deepEqual(frameAssembler.push(wideFrame.subarray(0, 7)), []);
assert.deepEqual(frameAssembler.push(wideFrame.subarray(7, 25)), []);
assert.deepEqual(frameAssembler.push(wideFrame.subarray(25)), [wideFrame]);
assert.deepEqual(frameAssembler.push(Uint8Array.from([...driverFrame, ...wideFrame])), [driverFrame, wideFrame]);
assert.throws(
  () => new WayonLiveFrameAssembler().push(Uint8Array.from({ length: 24 }, (_, index) => index)),
  /invalid Wayon Live frame/,
);

assert.deepEqual(visibleFcmNotification({ type: "wayon_door_lock", locked: "true" }), {
  title: "차량 잠금 활성화",
  body: "차량 잠금이 활성화되었습니다.",
  channelId: "wayon_door_lock_alerts",
});
assert.deepEqual(visibleFcmNotification({
  type: "wayon_door_lock", locked: "false", test: "true",
}), {
  title: "차량 잠금 알림 테스트",
  body: "차량 잠금이 해제되었습니다.",
  channelId: "wayon_door_lock_alerts",
});
assert.equal(visibleFcmNotification({ type: "wayon_impact" }), null);

const wayonKey = `wayon_${randomBytes(32).toString("base64url")}`;
const keyHash = createHash("sha256").update(wayonKey).digest("hex");
const env = {
  DB: {
    prepare(sql) {
      return {
        bind(...values) {
          return {
            async first() {
              return sql.includes("FROM wayon_devices") && values[0] === keyHash
                ? { device_id: deviceId }
                : null;
            },
            async run() { return { success: true }; },
          };
        },
      };
    },
  },
  SNAPSHOTS: {},
  WAYON_UPLOAD_TOKEN: "device-upload-token",
  WAYON_TUNNEL_TOKEN: "tunnel-token",
  WAYON_SSH_SESSION_SECRET: secret,
  DEVICE_RELAY: {},
};
const login = (token) => worker.fetch(new Request("https://wayon.test/api/remote/session", {
  method: "POST",
  headers: { authorization: `Bearer ${token}` },
}), env, {});

const denied = await login("wayon_invalid_key_that_is_long_enough_but_unknown_0000");
assert.equal(denied.status, 401);

const accepted = await login(wayonKey);
assert.equal(accepted.status, 200);
const session = await accepted.json();
assert.match(session.protocol, /^wayon-ssh-v1\./);
assert.equal(session.deviceId, deviceId);
assert.equal((await verifyRemoteSshProtocol(session.protocol, secret))?.deviceId, deviceId);

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
const liveAccepted = await liveSession(wayonKey);
assert.equal(liveAccepted.status, 200);
const live = await liveAccepted.json();
assert.match(live.protocol, /^wayon-live-v1\./);
assert.equal(live.websocketUrl, "wss://wayon.test/api/live/stream");
assert.equal(live.deviceId, deviceId);
assert.equal((await verifyLiveProtocol(live.protocol, secret))?.deviceId, deviceId);
console.log("remote auth tests passed");
