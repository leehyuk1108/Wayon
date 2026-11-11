import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

// Active production bundle (version 44b04625, trip-partial-server).
export const BASELINE_SHA256 = 'd522bc550ea05afc72cd40980cf316814995b0a340e952d30b2ac4771ee2d3aa';
export const OUTPUT_SHA256 = '850417f462bc43f0166cdaaffc3f3fd0ce0139da492d7cd274f00c941f625f12';

// Compatibility step before trip-vehicle-speed-20261111's migration adds trips.speed_stats: every
// SELECT * response (detail, export, AI trip and summary) goes through parseTripRoute, which now drops
// that internal column. Works with or without the column; also the rollback target after the migration.
export const anchor = 'function unscoped_parseTripRoute(trip, env) {\n' +
  '  const { route_json: routeJson, report_json: reportJson, health_json: healthJson, ...rest } = trip;\n';
export const replacement = 'function unscoped_parseTripRoute(trip, env) {\n' +
  '  const { route_json: routeJson, report_json: reportJson, health_json: healthJson, speed_stats: _speedStats, ...rest } = trip;\n';

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  const output = replaceOnce(source, anchor, replacement);
  if (OUTPUT_SHA256 !== 'PENDING') assert.equal(sha256(output), OUTPUT_SHA256, 'Unexpected candidate bundle');
  return output;
}

export function unpatch(source) {
  if (OUTPUT_SHA256 !== 'PENDING') assert.equal(sha256(source), OUTPUT_SHA256, 'Refusing unknown candidate bundle');
  const output = replaceOnce(source, replacement, anchor);
  assert.equal(sha256(output), BASELINE_SHA256, 'Baseline restoration mismatch');
  return output;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, output] = process.argv.slice(2);
  assert.ok(input && output && resolve(input) !== resolve(output), 'Specify distinct baseline and new output paths');
  const result = patch(readFileSync(input, 'utf8'));
  writeFileSync(output, result, {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({baseline: BASELINE_SHA256, candidate: sha256(result)}));
}
