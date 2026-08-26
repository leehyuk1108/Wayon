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

for (const [resource, timestampColumn, schemaVersion, collection] of [
  ["impacts", "received_at", "wayon-impact-sync-v1", "impacts"],
  ["snapshots", "created_at", "wayon-snapshot-sync-v1", "snapshots"],
]) {
  const syncRequest = new Request(
    `https://wayon-cloud.test/api/server-sync/${resource}?limit=100&cursor=${cursor}`,
    { headers: { authorization: "Bearer sync-token" } },
  );
  const syncEnv = {
    WAYON_SERVER_SYNC_TOKEN: "sync-token",
    SNAPSHOTS: {},
    DB: {
      prepare(query) {
        assert.match(query, new RegExp(`WHERE ${timestampColumn} > \\?`));
        return {
          bind(createdAt, sameCreatedAt, id, queryLimit) {
            assert.equal(createdAt, "2026-07-29T00:00:00.000Z");
            assert.equal(sameCreatedAt, createdAt);
            assert.equal(id, "last-trip");
            assert.equal(queryLimit, 101);
            return { async all() { return { results: [] }; } };
          },
        };
      },
    },
  };
  const syncResponse = await worker.fetch(syncRequest, syncEnv, {});
  assert.equal(syncResponse.status, 200);
  const syncPayload = await syncResponse.json();
  assert.equal(syncPayload.schemaVersion, schemaVersion);
  assert.deepEqual(syncPayload[collection], []);
  assert.equal(syncPayload.nextCursor, cursor);
  assert.equal(syncPayload.hasMore, false);
}

console.log("server-sync-history-cursors: PASS");
