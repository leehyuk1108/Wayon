import assert from "node:assert/strict";

import worker from "./src/worker.js";

const request = new Request("https://wayon-cloud.test/api/trips?limit=5000", {
  headers: { authorization: "Bearer view-token" },
});

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
      return Response.json({
        schemaVersion: "wayon-trip-read-v1",
        trips: [{
          id: "server-trip",
          distance_m: 1234,
          max_speed_mps: 14.5,
        }],
      });
    },
  },
  DB: {
    prepare() {
      throw new Error("D1 should not be queried when the server is healthy");
    },
  },
};

const serverResponse = await worker.fetch(request, serverEnv, {});
assert.equal(serverResponse.status, 200);
assert.equal(serverResponse.headers.get("x-wayon-history-source"), "server");
assert.deepEqual(await serverResponse.json(), {
  trips: [{
    id: "server-trip",
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
      assert.match(query, /FROM trips ORDER BY ended_at DESC LIMIT/);
      return {
        bind(limit) {
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
    }],
  });
} finally {
  console.warn = originalWarn;
}

console.log("server-trip-fallback: PASS");
