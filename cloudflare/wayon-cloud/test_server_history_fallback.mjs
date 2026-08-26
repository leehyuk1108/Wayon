import assert from "node:assert/strict";

import worker from "./src/worker.js";

const deviceId = "device-test-0001";
const deviceKey = `wayon_${"b".repeat(48)}`;

function dbForAuthenticationOnly() {
  return {
    prepare(query) {
      if (/FROM wayon_devices/.test(query)) {
        return {
          bind(keyHash) {
            assert.match(keyHash, /^[0-9a-f]{64}$/);
            return { async first() { return { device_id: deviceId }; } };
          },
        };
      }
      if (/UPDATE wayon_devices/.test(query)) {
        return { bind() { return { async run() {} }; } };
      }
      throw new Error(`D1 history query should not run while server is healthy: ${query}`);
    },
  };
}

const env = {
  WAYON_SERVER_SYNC_TOKEN: "sync-token",
  SNAPSHOTS: {},
  DB: dbForAuthenticationOnly(),
  WAYON_SERVER_API: {
    async fetch(url, options) {
      assert.equal(options.headers.authorization, "Bearer sync-token");
      assert.equal(options.headers["x-wayon-device-id"], deviceId);
      if (url.endsWith("/v1/wayon/impacts?limit=10&offset=0")) {
        return Response.json({
          schemaVersion: "wayon-impact-read-v1",
          impacts: [
            { id: "impact-own", device_id: deviceId },
            { id: "impact-other", device_id: "device-test-9999" },
          ],
        });
      }
      if (url.endsWith("/v1/wayon/snapshots?limit=20&offset=0")) {
        return Response.json({
          schemaVersion: "wayon-snapshot-read-v1",
          generatedAt: "2026-08-26T00:00:00.000Z",
          snapshots: [
            { id: "snapshot-own", device_id: deviceId },
            { id: "snapshot-other", device_id: "device-test-9999" },
          ],
          days: [{ date: "2026-08-26", count: 1 }],
          total: 1,
          limit: 20,
        });
      }
      throw new Error(`unexpected server URL: ${url}`);
    },
  },
};

for (const [path, expected] of [
  ["/api/impacts?limit=10", { impacts: [{ id: "impact-own", device_id: deviceId }] }],
  ["/api/snapshots?limit=20", {
    generatedAt: "2026-08-26T00:00:00.000Z",
    snapshots: [{ id: "snapshot-own", device_id: deviceId }],
    days: [{ date: "2026-08-26", count: 1 }],
    total: 1,
    limit: 20,
  }],
]) {
  const response = await worker.fetch(new Request(`https://wayon-cloud.test${path}`, {
    headers: { authorization: `Bearer ${deviceKey}` },
  }), env, {});
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("x-wayon-history-source"), "server");
  assert.deepEqual(await response.json(), expected);
}

console.log("server-history-fallback: PASS");
