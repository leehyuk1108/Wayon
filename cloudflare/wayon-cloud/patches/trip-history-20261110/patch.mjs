import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

// Applied on top of parking-place-20261110 (its candidate bundle).
export const BASELINE_SHA256 = 'c6060f9c392bc8ef14515f88ecdb1b3df5af3a472ea10d45c920b920c19cc12a';
export const OUTPUT_SHA256 = 'dff1050210c7aff3d038faa8c49f12d2311d42d550559182e91a6c2c6386f788';

// 1. Trip detail: the Wayon server copy of a long drive can hold only its first ~30 minutes
//    (2026-11-08 200 km drive: server 07:24-07:57, D1 07:24-09:52), and it overwrote the D1 route.
export const mergeAnchor = '    mergedById.set(id, d1Trip ? {\n' +
  '      ...d1Trip,\n' +
  '      ...serverTrip,\n' +
  '      id,\n';
export const mergeReplacement = mergeAnchor +
  '      ...tripRouteCoveringMoreTime(d1Trip, serverTrip),\n';
export const helperAnchor = 'function mergeServerTripsWithD1(serverTrips, d1Trips, deviceId, limit) {\n';
export const helperReplacement = 'function tripRouteSpanMs(route) {\n' +
  '  if (!Array.isArray(route) || route.length < 2) return -1;\n' +
  '  const first = Date.parse(route[0]?.time || "");\n' +
  '  const last = Date.parse(route[route.length - 1]?.time || "");\n' +
  '  return Number.isFinite(first) && Number.isFinite(last) ? last - first : -1;\n' +
  '}\n' +
  '__name(tripRouteSpanMs, "tripRouteSpanMs");\n' +
  'function tripRouteCoveringMoreTime(d1Trip, serverTrip) {\n' +
  '  // Keep whichever route spans more of the drive; ties keep the server copy as before.\n' +
  '  if (!Array.isArray(d1Trip?.route) || tripRouteSpanMs(d1Trip.route) <= tripRouteSpanMs(serverTrip?.route)) return {};\n' +
  '  return { route: d1Trip.route, route_point_count: d1Trip.route.length };\n' +
  '}\n' +
  '__name(tripRouteCoveringMoreTime, "tripRouteCoveringMoreTime");\n' + helperAnchor;

// 2. Trip list: summaries read every route_json (145 KB for a long drive) in one D1 result only to take
//    a maximum speed; limit=1000 failed with error 1101 while 500 worked, and the Android app fell back
//    to 300-600 of 892 trips. Holding all routes at once is the likely cause (not proven). The summary
//    rows are now read without routes, and each maximum still comes from the same maxRouteSpeedMps,
//    over routes read 90 at a time (91 bound parameters, under D1's 100).
export const listAnchor = '           route_json, report_json, health_json, health_updated_at\n' +
  '    FROM trips WHERE device_id = ? ORDER BY ended_at DESC LIMIT ?\n' +
  '  `).bind(deviceId, Math.min(limit, 1e3)).all();\n' +
  '  return (trips.results || []).map(trip => parseTripSummary(trip, env));\n}';
export const listReplacement = '           report_json, health_json, health_updated_at\n' +
  '    FROM trips WHERE device_id = ? ORDER BY ended_at DESC LIMIT ?\n' +
  '  `).bind(deviceId, Math.min(limit, 1e3)).all();\n' +
  '  const rows = trips.results || [];\n' +
  '  const maxSpeedById = new Map();\n' +
  '  for (let index = 0; index < rows.length; index += 90) {\n' +
  '    const ids = rows.slice(index, index + 90).map(row => row.id);\n' +
  '    const routes = await env.DB.prepare(\n' +
  '      `SELECT id, route_json FROM trips WHERE device_id = ? AND id IN (${ids.map(() => "?").join(",")})`\n' +
  '    ).bind(deviceId, ...ids).all();\n' +
  '    for (const route of routes.results || []) maxSpeedById.set(route.id, maxRouteSpeedMps(route.route_json));\n' +
  '  }\n' +
  '  return rows.map(trip => parseTripSummary({ ...trip, route_max_speed_mps: maxSpeedById.get(trip.id) ?? null }, env));\n}';
export const summaryAnchor = '  const { route_json: routeJson, report_json: reportJson, health_json: healthJson, ...rest } = trip;\n' +
  '  const parsed = tripWithAnalysis({\n' +
  '    ...rest,\n' +
  '    max_speed_mps: maxRouteSpeedMps(routeJson)\n';
export const summaryReplacement = '  const { route_json: routeJson, report_json: reportJson, health_json: healthJson,\n' +
  '    route_max_speed_mps: routeMaxSpeedMps, ...rest } = trip;\n' +
  '  const parsed = tripWithAnalysis({\n' +
  '    ...rest,\n' +
  '    max_speed_mps: routeJson !== undefined ? maxRouteSpeedMps(routeJson) : (routeMaxSpeedMps ?? null)\n';

const steps = [[helperAnchor, helperReplacement], [mergeAnchor, mergeReplacement],
  [listAnchor, listReplacement], [summaryAnchor, summaryReplacement]];

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
