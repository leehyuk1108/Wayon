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

const profile = normalizeAmbientCommand({
  mode: "profile",
  profile: {
    enabled: true,
    driving: {
      zone1: { rgb: [255, 245, 230], brightness: 20, automaticBrightness: true },
      zone2: { rgb: [255, 255, 255], brightness: 40 },
    },
    onroadDoor: { enabled: true, zone2: { rgb: [255, 255, 255], brightness: 100 } },
    offroadDoor: {
      enabled: true,
      zone1: { rgb: [255, 255, 255], brightness: 20 },
      zone2: { rgb: [255, 255, 255], brightness: 100 },
    },
    exitCourtesy: { enabled: true, zone2: { rgb: [255, 255, 255], brightness: 100 }, durationSeconds: 120 },
    overspeed: { enabled: true, zone1: { rgb: [255, 0, 0], brightness: 50 }, brightnessCap: 50 },
    reverseOff: { enabled: true },
    dataWatchdog: { enabled: true, timeoutSeconds: 20 },
    timing: { fadeMilliseconds: 1000, doorCloseDelaySeconds: 20, doorMaxOnMinutes: 20, transitionUpdatesPerSecond: 30 },
  },
}, now);
assert.equal(profile.mode, "profile");
assert.equal(profile.profile.driving.zone1.automaticBrightness, true);
assert.equal(profile.profile.timing.transitionUpdatesPerSecond, 30);
assert.throws(() => normalizeAmbientCommand({
  mode: "profile",
  profile: { ...profile.profile, timing: { ...profile.profile.timing, transitionUpdatesPerSecond: 41 } },
}, now), /invalid_transition_updates_per_second/);
console.log("ambient command tests passed");
