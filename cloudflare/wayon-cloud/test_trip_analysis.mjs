import assert from "node:assert/strict";
import { normalizeTripAnalysis } from "./src/worker.js";

const modern = { schemaVersion: "wayon-drive-report-v1", scores: { comfort: 91 } };
assert.deepEqual(normalizeTripAnalysis({ analysis: modern }), modern);

const legacy = normalizeTripAnalysis({
  durationS: 120,
  report: {
    schemaVersion: "wayon-trip-report-v1",
    openpilot: { activeDurationS: 30, activePercent: 25 },
    stopQuality: {
      count: 2,
      score: 72,
      harshCount: 1,
      events: [{ peak_jerk_mps3: 4.5 }, { peak_jerk_mps3: 7.2 }],
    },
    cutInRisk: { eventCount: 3, maxLevel: 2 },
  },
});

assert.equal(legacy.schemaVersion, "wayon-drive-report-v1-legacy");
assert.equal(legacy.dataQuality.confidence, "medium");
assert.equal(legacy.scores.comfort, 72);
assert.equal(legacy.automation.opUsagePercent, 25);
assert.equal(legacy.automation.manualS, 90);
assert.equal(legacy.comfort.peakJerkMps3, 7.2);
assert.equal(legacy.longitudinal.cutInEventCount, 3);
assert.deepEqual(normalizeTripAnalysis({ report: {} }), {});

console.log("trip analysis compatibility tests passed");
