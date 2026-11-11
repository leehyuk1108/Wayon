import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

// Applied on top of trip-speed-compat-20261111 (which already drops speed_stats in parseTripRoute).
export const BASELINE_SHA256 = '850417f462bc43f0166cdaaffc3f3fd0ce0139da492d7cd274f00c941f625f12';
export const OUTPUT_SHA256 = '23c4a22573ef958fc57a513752553865c40514798009b69d1c57f9d32f399811';

// Maximum and average speed from the vehicle, not GPS points, for trips uploaded from now on.
// GPS points stop in tunnels (2026-11-10 23:11: 146-149 km/h inside two tunnels, route max 112 km/h).
// The comma already sends maxSpeedMps as the carState maximum over every sample, and the drive report
// carries the Traverse odometer distance. New rows get speed_stats (migration.sql adds the column: the
// seconds covered by the stored average, 0 if none yet) and get avg_speed_mps/max_speed_mps, refreshed by later uploads of the same trip; rows from
// before the change keep speed_stats NULL and their NULL speed columns forever. A later upload of a new
// trip can only raise its maximum, and replaces the average only when it covers at least as long.
// Lists, details and the merge with Wayon server copies prefer the stored vehicle values; trips without
// them keep the previous GPS-based numbers.
const helper = 'function storedVehicleSpeeds(payload, analysis) {\n' +
  '  const number = value => value == null || value === "" || typeof value === "boolean" ? NaN : Number(value);\n' +
  '  const quality = analysis?.dataQuality || {};\n' +
  '  const duration = number(payload?.durationS);\n' +
  '  const timeline = (Array.isArray(analysis?.timeline) ? analysis.timeline : [])\n' +
  '    .map(row => [number(row?.offsetS), number(row?.speedKph) / 3.6])\n' +
  '    .filter(([offset, speed]) => Number.isFinite(offset) && Number.isFinite(speed) && speed >= 0)\n' +
  '    .sort((a, b) => a[0] - b[0]);\n' +
  '  // Maximum: the comma sends the carState maximum; the 5 s carState timeline guards a route fallback.\n' +
  '  const candidates = [number(payload?.maxSpeedMps), ...timeline.map(([, speed]) => speed)].filter(Number.isFinite);\n' +
  '  const peak = candidates.length ? Math.max(...candidates) : NaN;\n' +
  '  const max = number(quality.carStateSamples) > 0 && peak >= 0 && peak < 120 ? peak : null;\n' +
  '  // Average: Traverse odometer distance over the trip time, only when the odometer covered the trip.\n' +
  '  // Reference: the carState timeline integral (cluster speed reads a few percent high) when it spans\n' +
  '  // the whole trip, else the GPS distance (short in tunnels). Too short, partial or inconsistent: none.\n' +
  '  const fuel = analysis?.fuel;\n' +
  '  const meters = number(fuel?.odometerDistanceKm) * 1000;\n' +
  '  let reference = NaN, low = 0.9, high = 1.3;\n' +
  '  if (quality.timelineTruncated === false && timeline.length >= 3 && timeline[0][0] <= 15 && timeline.at(-1)[0] >= duration - 15) {\n' +
  '    reference = timeline.reduce((sum, [offset, speed], i) => i ? sum + (speed + timeline[i - 1][1]) / 2 * (offset - timeline[i - 1][0]) : sum, 0)\n' +
  '      + timeline[0][1] * timeline[0][0] + timeline.at(-1)[1] * Math.max(0, duration - timeline.at(-1)[0]);\n' +
  '    low = 0.85; high = 1.1;\n' +
  '  } else {\n' +
  '    reference = number(payload?.distanceM);\n' +
  '  }\n' +
  '  const avg = meters / duration;\n' +
  '  const consistent = fuel?.source === "traverseCan" && fuel.partial === false && duration >= 60 && meters >= 300\n' +
  '    && reference > 0 && meters >= low * reference && meters <= high * reference && (max == null || avg <= max + 0.5);\n' +
  '  return { max, avg: consistent ? avg : null };\n' +
  '}\n' +
  '__name(storedVehicleSpeeds, "storedVehicleSpeeds");\n' +
  'function withStoredVehicleSpeeds(trip) {\n' +
  '  if (!trip) return trip;\n' +
  '  // speed_stats is internal (marks rows stored by this version); the response shape stays as before.\n' +
  '  const { speed_stats: _speedStats, ...rest } = trip;\n' +
  '  return { ...rest, ...(rest.max_speed_mps != null ? { vehicle_max_speed_mps: rest.max_speed_mps } : {}),\n' +
  '    ...(rest.avg_speed_mps != null ? { vehicle_avg_speed_mps: rest.avg_speed_mps } : {}) };\n' +
  '}\n' +
  '__name(withStoredVehicleSpeeds, "withStoredVehicleSpeeds");\n' +
  'function vehicleSpeedOverrides(d1Trip) {\n' +
  '  return { ...(d1Trip?.vehicle_max_speed_mps != null ? { max_speed_mps: d1Trip.vehicle_max_speed_mps, vehicle_max_speed_mps: d1Trip.vehicle_max_speed_mps } : {}),\n' +
  '    ...(d1Trip?.vehicle_avg_speed_mps != null ? { avg_speed_mps: d1Trip.vehicle_avg_speed_mps, vehicle_avg_speed_mps: d1Trip.vehicle_avg_speed_mps } : {}) };\n' +
  '}\n' +
  '__name(vehicleSpeedOverrides, "vehicleSpeedOverrides");\n';

const steps = [
  // helpers next to the other trip merge helpers
  ['function tripRouteSpanMs(route) {\n', helper + 'function tripRouteSpanMs(route) {\n'],
  // insert-only columns (ON CONFLICT leaves them as they are)
  ['  const analysis = normalizeTripAnalysis(payload);\n\n  const written = await env.DB.prepare(`\n',
   '  const analysis = normalizeTripAnalysis(payload);\n  const vehicleSpeeds = storedVehicleSpeeds(payload, analysis);\n\n  const written = await env.DB.prepare(`\n'],
  ['      start_lon, end_lat, end_lon, route_point_count, route_json, report_json, created_at\n    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n',
   '      start_lon, end_lat, end_lon, route_point_count, route_json, report_json, created_at,\n      avg_speed_mps, max_speed_mps, speed_stats\n    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n'],
  // Only rows inserted by this version (speed_stats NOT NULL: seconds covered by the stored average,
  // 0 if none yet) take later vehicle values; rows from before it (speed_stats NULL) never change.
  // The maximum only rises; the average changes only for an upload covering at least as many seconds.
  ['      report_json = excluded.report_json, created_at = excluded.created_at\n',
   '      report_json = excluded.report_json, created_at = excluded.created_at,\n' +
   '      avg_speed_mps = CASE WHEN trips.speed_stats IS NOT NULL AND excluded.avg_speed_mps IS NOT NULL\n' +
   '        AND excluded.speed_stats >= trips.speed_stats THEN excluded.avg_speed_mps ELSE trips.avg_speed_mps END,\n' +
   '      speed_stats = CASE WHEN trips.speed_stats IS NOT NULL AND excluded.avg_speed_mps IS NOT NULL\n' +
   '        AND excluded.speed_stats >= trips.speed_stats THEN excluded.speed_stats ELSE trips.speed_stats END,\n' +
   '      max_speed_mps = CASE WHEN trips.speed_stats IS NOT NULL THEN max(COALESCE(excluded.max_speed_mps, trips.max_speed_mps),\n' +
   '        COALESCE(trips.max_speed_mps, excluded.max_speed_mps)) ELSE trips.max_speed_mps END\n'],
  ['    JSON.stringify(route),\n    JSON.stringify(analysis),\n    nowIso(),\n  ).run();\n',
   '    JSON.stringify(route),\n    JSON.stringify(analysis),\n    nowIso(),\n    vehicleSpeeds.avg,\n    vehicleSpeeds.max,\n    vehicleSpeeds.avg == null ? 0 : Math.max(1, Math.round(Number(payload.durationS))),\n  ).run();\n'],
  // list: stored vehicle values first; routes are read only for trips without a stored maximum
  ['           CASE\n             WHEN duration_s > 0 AND distance_m IS NOT NULL THEN distance_m / duration_s\n             ELSE NULL\n           END AS avg_speed_mps,\n           report_json, health_json, health_updated_at\n',
   '           CASE\n             WHEN avg_speed_mps IS NOT NULL THEN avg_speed_mps\n             WHEN duration_s > 0 AND distance_m IS NOT NULL THEN distance_m / duration_s\n             ELSE NULL\n           END AS avg_speed_mps,\n           avg_speed_mps AS vehicle_avg_speed_mps, max_speed_mps AS vehicle_max_speed_mps,\n           report_json, health_json, health_updated_at\n'],
  ['  for (let index = 0; index < rows.length; index += 90) {\n    const ids = rows.slice(index, index + 90).map(row => row.id);\n',
   '  const routeRows = rows.filter(row => row.vehicle_max_speed_mps == null);\n  for (let index = 0; index < routeRows.length; index += 90) {\n    const ids = routeRows.slice(index, index + 90).map(row => row.id);\n'],
  ['  return rows.map(trip => parseTripSummary({ ...trip, route_max_speed_mps: maxSpeedById.get(trip.id) ?? null }, env));\n',
   '  return rows.map(({ vehicle_avg_speed_mps: vehicleAvg, vehicle_max_speed_mps: vehicleMax, ...trip }) => parseTripSummary({\n' +
   '    ...trip, route_max_speed_mps: vehicleMax ?? maxSpeedById.get(trip.id) ?? null,\n' +
   '    ...(vehicleMax != null ? { vehicle_max_speed_mps: vehicleMax } : {}),\n' +
   '    ...(vehicleAvg != null ? { vehicle_avg_speed_mps: vehicleAvg } : {}),\n  }, env));\n'],
  // detail: the raw columns are the stored vehicle values
  ['      const d1TripWithHealth = d1Trip ? await tripWithHealth(env, d1Trip) : null;\n',
   '      const d1TripWithHealth = d1Trip ? withStoredVehicleSpeeds(await tripWithHealth(env, d1Trip)) : null;\n'],
  ['    return historyJson(await tripWithHealth(env, d1Trip), "d1");\n',
   '    return historyJson(withStoredVehicleSpeeds(await tripWithHealth(env, d1Trip)), "d1");\n'],
  // merge: stored vehicle values win over a Wayon server copy
  ['      ...d1TripWhenServerCopyIsPartial(d1Trip, serverTrip),\n',
   '      ...d1TripWhenServerCopyIsPartial(d1Trip, serverTrip),\n      ...vehicleSpeedOverrides(d1Trip),\n'],
];

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
