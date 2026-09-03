import assert from "node:assert/strict";

import { vehicleEventNotificationEligible } from "./src/worker.js";

const now = Date.parse("2026-09-04T00:10:00.000Z");

assert.equal(vehicleEventNotificationEligible("2026-09-04T00:09:30.000Z", now), true);
assert.equal(vehicleEventNotificationEligible("2026-09-04T00:00:00.000Z", now), true);
assert.equal(vehicleEventNotificationEligible("2026-09-03T23:59:59.000Z", now), false);
assert.equal(vehicleEventNotificationEligible("2026-09-04T00:12:01.000Z", now), false);
assert.equal(vehicleEventNotificationEligible("not-a-time", now), false);

console.log("vehicle event age tests passed");
