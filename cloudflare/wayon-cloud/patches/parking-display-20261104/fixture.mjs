import {readFileSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {RETAINED_MODULE_SHA256} from './patch.mjs';

export const baselinePath = process.env.WAYON_PARKING_DISPLAY_BASELINE ||
  '/Users/hyuklee/Documents/parking-scene-benchmark-20261104/display-cloud-baseline/worker.js';
export const baseline = readFileSync(baselinePath, 'utf8');
const moduleDir = process.env.WAYON_PARKING_DISPLAY_MODULE_DIR || dirname(baselinePath);
export const retained = Object.fromEntries(Object.keys(RETAINED_MODULE_SHA256)
  .map(name => [name, readFileSync(join(moduleDir, name), 'utf8')]));

export const OWNER = 'fixture-owner';
export const MAX = 196608;
export function payload(deviceId = OWNER) {
  const evidence = [0, 1].map(frameIndex => ({frameIndex, box: [0.1, 0.2, 0.3, 0.4]}));
  const reading = {kind: 'pillar', text: '203', status: 'readable', alternatives: [], evidence};
  return {schemaVersion: 'wayon-parking-read-v1', deviceId, generatedAt: '2026-11-04T01:00:00.123456+00:00',
    observation: {jobId: 'a'.repeat(32), eventId: 'parking-fixture', parkedAt: '2026-10-01T01:00:00Z', status: 'completed', result: {
      analysis: {readings: [structuredClone(reading)], exactParkingSpotKnown: false},
      frames: [0, 1].map(i => ({capturedAt: `2026-10-01T01:00:0${i}Z`, phase: i ? 'parked' : 'approach', camera: 'road'})),
      inspection: {version: 1, status: 'completed', readings: [{...reading, confidence: 'baseline'}],
        surroundings: [{type: 'door', color: 'gray', label: 'door', evidence: structuredClone(evidence)}],
        coverage: {overviewViews: 12, overviewExpected: 12, targetsRequested: 4, targetsInspected: 4, completeSceneGuaranteed: false},
        humanVerified: false, exactParkingSpotKnown: false},
    }}};
}
