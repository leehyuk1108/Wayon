import assert from "node:assert/strict";

import worker from "./src/worker.js";

const deviceId = "device-test-0001";
const deviceKey = `wayon_${"a".repeat(48)}`;
const request = new Request("https://wayon-cloud.test/api/trips?limit=5000", {
  headers: { authorization: `Bearer ${deviceKey}` },
});

function authenticationQuery(query) {
  assert.match(query, /FROM wayon_devices/);
  return {
    bind(keyHash) {
      assert.match(keyHash, /^[0-9a-f]{64}$/);
      return { async first() { return { device_id: deviceId }; } };
    },
  };
}

const serverEnv = {
  WAYON_VIEW_TOKEN: "view-token",
  WAYON_SERVER_SYNC_TOKEN: "sync-token",
  SNAPSHOTS: {},
  WAYON_SERVER_API: {
    async fetch(url, options) {
      assert.equal(
        url,
        "http://wayon-server/v1/wayon/trips?limit=5000&offset=0&include_route=false",
      );
      assert.equal(options.headers.authorization, "Bearer sync-token");
      assert.equal(options.headers["x-wayon-device-id"], deviceId);
      return Response.json({
        schemaVersion: "wayon-trip-read-v1",
        trips: [{
          id: "server-trip",
          device_id: deviceId,
          distance_m: 1234,
          max_speed_mps: 14.5,
        }, {
          id: "other-device-trip",
          device_id: "device-test-9999",
          distance_m: 9999,
        }],
      });
    },
  },
  DB: {
    prepare(query) {
      if (/FROM wayon_devices/.test(query)) return authenticationQuery(query);
      if (/UPDATE wayon_devices/.test(query)) {
        return { bind() { return { async run() {} }; } };
      }
      throw new Error(`D1 should not be queried when the server is healthy: ${query}`);
    },
  },
};

const serverResponse = await worker.fetch(request, serverEnv, {});
assert.equal(serverResponse.status, 200);
assert.equal(serverResponse.headers.get("x-wayon-history-source"), "server");
assert.deepEqual(await serverResponse.json(), {
  trips: [{
    id: "server-trip",
    device_id: deviceId,
    distance_m: 1234,
    max_speed_mps: 14.5,
  }],
});

const d1Env = {
  WAYON_VIEW_TOKEN: "view-token",
  WAYON_SERVER_SYNC_TOKEN: "sync-token",
  SNAPSHOTS: {},
  WAYON_SERVER_API: {
    async fetch() {
      throw new Error("server offline");
    },
  },
  DB: {
    prepare(query) {
      if (/FROM wayon_devices/.test(query)) return authenticationQuery(query);
      if (/UPDATE wayon_devices/.test(query)) {
        return { bind() { return { async run() {} }; } };
      }
      assert.match(query, /FROM trips WHERE device_id = \? ORDER BY ended_at DESC LIMIT/);
      return {
        bind(boundDeviceId, limit) {
          assert.equal(boundDeviceId, deviceId);
          assert.equal(limit, 1000);
          return {
            async all() {
              return {
                results: [{
                  id: "d1-trip",
                  route_json: JSON.stringify([{ speed: 7.25 }]),
                }],
              };
            },
          };
        },
      };
    },
  },
};

const originalWarn = console.warn;
console.warn = () => {};
try {
  const d1Response = await worker.fetch(request, d1Env, {});
  assert.equal(d1Response.status, 200);
  assert.equal(d1Response.headers.get("x-wayon-history-source"), "d1");
  assert.deepEqual(await d1Response.json(), {
    trips: [{
      id: "d1-trip",
      max_speed_mps: 7.25,
      report: {},
    }],
  });
} finally {
  console.warn = originalWarn;
}

console.log("server-trip-fallback: PASS");
