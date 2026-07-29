import assert from "node:assert/strict";

import worker from "./src/worker.js";

const cursor = Buffer.from(JSON.stringify({
  createdAt: "2026-07-29T00:00:00.000Z",
  id: "last-trip",
})).toString("base64url");

const request = new Request(
  `https://wayon-cloud.test/api/server-sync/trips?limit=100&cursor=${cursor}`,
  { headers: { authorization: "Bearer sync-token" } },
);

const env = {
  WAYON_SERVER_SYNC_TOKEN: "sync-token",
  SNAPSHOTS: {},
  DB: {
    prepare(query) {
      assert.match(query, /WHERE created_at > \?/);
      return {
        bind(createdAt, sameCreatedAt, id, queryLimit) {
          assert.equal(createdAt, "2026-07-29T00:00:00.000Z");
          assert.equal(sameCreatedAt, createdAt);
          assert.equal(id, "last-trip");
          assert.equal(queryLimit, 101);
          return {
            async all() {
              return { results: [] };
            },
          };
        },
      };
    },
  },
};

const response = await worker.fetch(request, env, {});
assert.equal(response.status, 200);
const payload = await response.json();
assert.match(payload.generatedAt, /^\d{4}-\d{2}-\d{2}T/);
delete payload.generatedAt;
assert.deepEqual(payload, {
  schemaVersion: "wayon-trip-sync-v1",
  trips: [],
  nextCursor: cursor,
  hasMore: false,
});

console.log("server-sync-cursor: PASS");
