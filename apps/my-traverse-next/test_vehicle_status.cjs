const assert = require("node:assert/strict");
const policy = require("./app/src/main/assets/vehicle_status.js");

const now = Date.parse("2026-09-04T14:00:00Z");
const freshUnlocked = policy.evaluate({
  meta: { updatedAt: "2026-09-04T13:55:00Z", stale: false },
  closures: { doors: { active: true } },
}, null, now);
assert.equal(freshUnlocked.detail, "Doors unlocked");

const staleUnlocked = policy.evaluate({
  meta: { updatedAt: "2026-09-04T11:05:55Z", stale: false },
  closures: { doors: { active: true } },
}, null, now);
assert.equal(staleUnlocked.title, "UPDATE\nDELAYED");
assert.equal(staleUnlocked.detail, "Lock status is not confirmed");

console.log("vehicle status policy tests passed");
