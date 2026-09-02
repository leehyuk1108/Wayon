import assert from "node:assert/strict";
import { normalizeAmbientCommand } from "./src/worker.js";

const now = new Date("2026-08-28T00:00:00.000Z");
const command = normalizeAmbientCommand({
  mode: "manual",
  zone1: { enabled: true, rgb: [255, 120, 0], brightness: 20 },
  zone2: { enabled: true, rgb: [10, 20, 30], brightness: 40 },
  durationSeconds: 900,
}, now);
assert.deepEqual(command.zone2.rgb, [10, 20, 30]);
assert.equal(command.durationSeconds, 900);
assert.throws(() => normalizeAmbientCommand({
  mode: "manual",
  zone1: { rgb: [256, 0, 0], brightness: 20 },
  zone2: { rgb: [0, 0, 0], brightness: 40 },
  durationSeconds: 900,
}, now), /invalid_zone1_rgb_0/);
console.log("ambient command tests passed");
