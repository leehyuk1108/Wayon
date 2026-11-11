import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {test} from 'node:test';
import {patch, unpatch, BASELINE_SHA256, OUTPUT_SHA256} from './patch.mjs';
import {sha256} from '../fast-vehicle-state-20261028/patch.mjs';

// The response comparison across the migration window lives in trip-vehicle-speed-20261111/runtime.test.mjs.
const root = process.env.WAYON_ACTIVE_MODULE_DIR || '/Users/hyuklee/Documents/my-traverse-web-20261110/trip-sqlmax';
const baseline = readFileSync(join(root, 'stage-baseline-worker.js'), 'utf8');

test('compatibility patch is byte-exact, reversible and touches only parseTripRoute', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  const candidate = patch(baseline);
  assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
  assert.equal(candidate.length - baseline.length, 'speed_stats: _speedStats, '.length);
});
