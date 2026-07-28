import assert from "node:assert/strict";
import {
  attachPandaCounterHealth,
  buildAiPandaInterface,
} from "./src/panda_counter_health.mjs";

function payload(overrides = {}) {
  return {
    panda: {
      uptimeS: 1000,
      faultStatus: "none",
      faults: [],
      heartbeatLost: false,
      safetyRxChecksInvalid: false,
      rxBufferOverflow: 24454,
      txBufferOverflow: 0,
      spiErrorCount: 55975,
      ...overrides,
    },
  };
}

const stable = payload({ uptimeS: 1015, spiErrorCount: 55980 });
attachPandaCounterHealth(
  stable,
  payload(),
  "2026-07-28T04:00:00Z",
  "2026-07-28T04:00:15Z",
);
assert.equal(stable.panda.counterHealth.assessment, "okNoNewCanOverflow");
assert.equal(stable.panda.counterHealth.shouldAlert, false);
assert.equal(stable.panda.counterHealth.deltaSincePreviousSample.rxBufferOverflow, 0);
assert.equal(stable.panda.counterHealth.deltaSincePreviousSample.spiErrorCount, 5);

const increased = payload({ uptimeS: 1015, rxBufferOverflow: 24456 });
attachPandaCounterHealth(
  increased,
  payload(),
  "2026-07-28T04:00:00Z",
  "2026-07-28T04:00:15Z",
);
assert.equal(increased.panda.counterHealth.assessment, "newCanOverflowCounterIncrease");
assert.equal(increased.panda.counterHealth.shouldAlert, true);
assert.equal(increased.panda.counterHealth.deltaSincePreviousSample.rxBufferOverflow, 2);

const rebooted = payload({
  uptimeS: 3,
  rxBufferOverflow: 0,
  spiErrorCount: 0,
});
attachPandaCounterHealth(
  rebooted,
  payload(),
  "2026-07-28T04:00:00Z",
  "2026-07-28T04:00:15Z",
);
assert.equal(rebooted.panda.counterHealth.assessment, "baselineEstablished");
assert.equal(rebooted.panda.counterHealth.samePandaBoot, false);
assert.equal(rebooted.panda.counterHealth.shouldAlert, false);

const aiPanda = buildAiPandaInterface(stable.panda);
assert.equal("rxBufferOverflow" in aiPanda, false);
assert.equal(aiPanda.diagnosticCounters.rxBufferOverflowTotal, 24454);
assert.equal(aiPanda.counterHealth.shouldAlert, false);

console.log("panda counter health tests passed");
