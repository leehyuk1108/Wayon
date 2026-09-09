import assert from "node:assert/strict";
import worker from "./src/worker.js";

// Workers accepts streaming request bodies without Node's duplex option.
const NativeRequest = globalThis.Request;
globalThis.Request = class extends NativeRequest {
  constructor(input, init) {
    super(input, init?.body ? { ...init, duplex: "half" } : init);
  }
};

const operations = [];
let stored = null;
let online = true;
const env = {
  SNAPSHOTS: {},
  DB: {
    prepare(sql) {
      return {
        bind(...values) {
          return {
            sql, values,
            async first() {
              operations.push(sql);
              if (sql.includes("FROM wayon_devices")) return { device_id: "test-device" };
              return stored;
            },
            async run() { throw new Error("GET must not write expiry updates"); },
          };
        },
      };
    },
    async batch(queries) {
      operations.push("persist");
      assert.equal(queries.length, 2);
    },
  },
  DEVICE_RELAY: {
    idFromName(name) { assert.equal(name, "test-device:ssh"); return name; },
    get() {
      return { async fetch(request) {
        assert.equal(operations.at(-1), "persist");
        assert.equal(new URL(request.url).pathname, "/notify-ambient");
        operations.push("notify");
        return new Response(null, { status: online ? 204 : 409 });
      } };
    },
  },
};
const request = (path, body) => new Request(`https://wayon.test/api/ambient/${path}`, {
  method: body ? "POST" : "GET",
  headers: { authorization: `Bearer wayon_${"a".repeat(40)}`, "content-type": "application/json" },
  ...(body ? { body: JSON.stringify(body) } : {}),
});

let result = await worker.fetch(request("command", { mode: "auto" }), env, {});
assert.equal(result.status, 200);
assert.equal((await result.json()).notified, true);
online = false;
result = await worker.fetch(request("command", { mode: "auto" }), env, {});
assert.equal(result.status, 200);
assert.equal((await result.json()).notified, false);
result = await worker.fetch(request("command"), env, {});
assert.equal((await result.json()).command, null);

stored = { id: "expired", status: "pending", expires_at: "2000-01-01T00:00:00.000Z", payload_json: "{}" };
result = await worker.fetch(request("status"), env, {});
assert.equal((await result.json()).command.status, "expired");
stored.status = "acknowledged";
result = await worker.fetch(request("status"), env, {});
assert.equal((await result.json()).command.status, "acknowledged");
console.log("ambient persistence, notification, offline recovery and read-only expiry tests passed");
