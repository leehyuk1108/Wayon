import assert from "node:assert/strict";
import test from "node:test";

import {
  authorizeGmoneRefreshPoll,
  mergeVehicleStatus,
  sanitizeGmonePayload,
} from "./src/worker.js";

test("fresh GMOne status overrides matching Firebase fields", () => {
  const firebase = {
    ok: true,
    source: "firebase",
    updatedAt: "2026-08-18T00:00:00.000Z",
    data: { fuel: "30", range: "250", firebaseOnly: "kept" },
  };
  const gmone = {
    ok: true,
    source: "gmone-direct",
    updatedAt: "2026-08-18T01:00:00.000Z",
    collectedAt: "2026-08-18T01:00:00.000Z",
    stale: false,
    data: { fuel: "63", range: "582" },
  };

  const merged = mergeVehicleStatus(firebase, gmone);
  assert.equal(merged.source, "firebase+gmone-direct");
  assert.deepEqual(merged.data, { fuel: "63", range: "582", firebaseOnly: "kept" });
  assert.equal(merged.updatedAt, gmone.updatedAt);
});

test("stale GMOne status does not replace an available Firebase status", () => {
  const merged = mergeVehicleStatus(
    { ok: true, updatedAt: "2026-08-18T01:00:00.000Z", data: { fuel: "30" } },
    { ok: true, source: "gmone-direct", stale: true, data: { fuel: "63" } },
  );
  assert.equal(merged.data.fuel, "30");
  assert.equal(merged.source, "firebase");
});

test("GMOne payload sanitization removes account and vehicle identifiers", () => {
  const sanitized = sanitizeGmonePayload({
    email: "owner@example.com",
    token_key: "secret",
    vin: "1ABCDEFGH23456789",
    status: { fuel: "63" },
    nested: { ticket_uuid: "ticket", safe: true },
  });

  assert.deepEqual(sanitized, {
    status: { fuel: "63" },
    nested: { safe: true },
  });
});

test("GMOne refresh completion can be polled with view or collector credentials", () => {
  const env = {
    WAYON_VIEW_TOKEN: "view-token",
    WAYON_UPLOAD_TOKEN: "upload-token",
    WAYON_GMONE_TOKEN: "collector-token",
  };
  const request = (token) => new Request("https://wayon.example/api/gmone/refresh", {
    headers: { authorization: `Bearer ${token}` },
  });

  assert.equal(authorizeGmoneRefreshPoll(request("view-token"), env), true);
  assert.equal(authorizeGmoneRefreshPoll(request("upload-token"), env), true);
  assert.equal(authorizeGmoneRefreshPoll(request("collector-token"), env), true);
  assert.equal(authorizeGmoneRefreshPoll(request("wrong-token"), env), false);
});
