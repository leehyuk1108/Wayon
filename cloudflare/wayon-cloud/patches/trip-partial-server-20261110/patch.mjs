import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

// Active production bundle after parking-place + trip-history (version 4fefd1dc).
export const BASELINE_SHA256 = 'dff1050210c7aff3d038faa8c49f12d2311d42d550559182e91a6c2c6386f788';
export const OUTPUT_SHA256 = 'd522bc550ea05afc72cd40980cf316814995b0a340e952d30b2ac4771ee2d3aa';

// The Wayon server copies of the 2026-11-08 long drives end after about 33 minutes, so their
// summaries overwrote the D1 trip in both the list and the detail: 200.7 km / 2 h 28 min shown as
// 19.5 km / 33 min. When the server copy spans more than a minute less than the D1 trip, the D1
// timing, distance, positions and speeds win; the route keeps its own longer-span rule and
// report/analysis/health keep theirs.
export const helperAnchor = 'function tripRouteCoveringMoreTime(d1Trip, serverTrip) {\n';
export const helperReplacement = 'function tripSpanMs(trip) {\n' +
  '  const start = Date.parse(trip?.started_at || trip?.startedAt || "");\n' +
  '  const end = Date.parse(trip?.ended_at || trip?.endedAt || "");\n' +
  '  return Number.isFinite(start) && Number.isFinite(end) ? end - start : -1;\n' +
  '}\n' +
  '__name(tripSpanMs, "tripSpanMs");\n' +
  'const D1_TRIP_CORE_FIELDS = ["started_at", "ended_at", "duration_s", "distance_m", "start_lat", "start_lon",\n' +
  '  "end_lat", "end_lon", "avg_speed_mps", "max_speed_mps"];\n' +
  'function d1TripWhenServerCopyIsPartial(d1Trip, serverTrip) {\n' +
  '  if (tripSpanMs(d1Trip) <= tripSpanMs(serverTrip) + 60000) return {};\n' +
  '  // The route is chosen separately (tripRouteCoveringMoreTime); missing D1 speeds are derived,\n' +
  '  // never copied as null over the server values.\n' +
  '  const fields = Object.fromEntries(D1_TRIP_CORE_FIELDS.filter(key => d1Trip[key] != null).map(key => [key, d1Trip[key]]));\n' +
  '  const distance = d1Trip.distance_m == null ? NaN : Number(d1Trip.distance_m);\n' +
  '  const duration = d1Trip.duration_s == null ? NaN : Number(d1Trip.duration_s);\n' +
  '  if (fields.avg_speed_mps == null && Number.isFinite(distance) && duration > 0) fields.avg_speed_mps = distance / duration;\n' +
  '  // The maximum comes from the route that is actually shown (same rule as tripRouteCoveringMoreTime).\n' +
  '  const shown = tripRouteSpanMs(d1Trip.route) > tripRouteSpanMs(serverTrip?.route) ? d1Trip.route : serverTrip?.route;\n' +
  '  if (fields.max_speed_mps == null && Array.isArray(shown)) {\n' +
  '    const max = maxRouteSpeedMps(JSON.stringify(shown));\n' +
  '    if (max != null) fields.max_speed_mps = max;\n' +
  '  }\n' +
  '  return fields;\n' +
  '}\n' +
  '__name(d1TripWhenServerCopyIsPartial, "d1TripWhenServerCopyIsPartial");\n' + helperAnchor;
export const mergeAnchor = '      ...tripRouteCoveringMoreTime(d1Trip, serverTrip),\n';
export const mergeReplacement = mergeAnchor + '      ...d1TripWhenServerCopyIsPartial(d1Trip, serverTrip),\n';

const steps = [[helperAnchor, helperReplacement], [mergeAnchor, mergeReplacement]];

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  let output = source;
  for (const [anchor, replacement] of steps) output = replaceOnce(output, anchor, replacement);
  if (OUTPUT_SHA256 !== 'PENDING') assert.equal(sha256(output), OUTPUT_SHA256, 'Unexpected candidate bundle');
  return output;
}

export function unpatch(source) {
  if (OUTPUT_SHA256 !== 'PENDING') assert.equal(sha256(source), OUTPUT_SHA256, 'Refusing unknown candidate bundle');
  let output = source;
  for (const [anchor, replacement] of [...steps].reverse()) output = replaceOnce(output, replacement, anchor);
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
