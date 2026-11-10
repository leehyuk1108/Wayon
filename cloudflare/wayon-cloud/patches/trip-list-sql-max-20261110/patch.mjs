import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

// Active production bundle after trip-partial-server (version 44b04625).
export const BASELINE_SHA256 = 'd522bc550ea05afc72cd40980cf316814995b0a340e952d30b2ac4771ee2d3aa';
export const OUTPUT_SHA256 = 'f7ca6716601d31b0f0cf702ede2fb9236f96e52922735f39b847e8a2d822767e';

// Reading all 866 routes (38.7 MB) in 90-route batches took 25-27 s per list request and repeated
// requests returned 503, so the Android app again fell back to 600 trips. SQLite now takes each
// maximum for routes whose points are plain (every object point has a numeric speedMps, or no
// speed key at all), where maxRouteSpeedMps gives the same number; only routes with any other
// point shape, invalid JSON or a non-array top level are still read and parsed in the Worker.
// json_each's type column is checked before any json_type/json_extract on a point, and CASE is
// evaluated lazily, so a string point is never parsed as JSON. No abs(): it overflows on the
// smallest 64-bit integer; only real values are range-checked for infinity.
export const anchor = '  const rows = trips.results || [];\n' +
  '  const maxSpeedById = new Map();\n' +
  '  for (let index = 0; index < rows.length; index += 90) {\n' +
  '    const ids = rows.slice(index, index + 90).map(row => row.id);\n';
export const replacement = '  const rows = trips.results || [];\n' +
  '  const maxSpeedById = new Map();\n' +
  '  const plain = await env.DB.prepare(`\n' +
  '    SELECT id,\n' +
  '      CASE WHEN json_valid(route_json) THEN (CASE WHEN json_type(route_json) = \'array\' THEN (\n' +
  '        SELECT COALESCE(SUM(CASE WHEN p.type = \'object\' THEN (CASE\n' +
  '            WHEN json_type(p.value, \'$.speedMps\') = \'integer\' THEN 0\n' +
  '            WHEN json_type(p.value, \'$.speedMps\') = \'real\'\n' +
  '              THEN (CASE WHEN json_extract(p.value, \'$.speedMps\') BETWEEN -1e308 AND 1e308 THEN 0 ELSE 1 END)\n' +
  '            WHEN json_type(p.value, \'$.speedMps\') IS NULL OR json_type(p.value, \'$.speedMps\') = \'null\'\n' +
  '              THEN (CASE WHEN json_type(p.value, \'$.speed_mps\') IS NULL AND json_type(p.value, \'$.speed\') IS NULL THEN 0 ELSE 1 END)\n' +
  '            ELSE 1 END) ELSE 0 END), 0)\n' +
  '        FROM json_each(route_json) AS p) ELSE 1 END) ELSE 1 END AS odd_points,\n' +
  '      CASE WHEN json_valid(route_json) THEN (CASE WHEN json_type(route_json) = \'array\' THEN (\n' +
  '        SELECT MAX(CASE WHEN p.type = \'object\' THEN (CASE\n' +
  '            WHEN json_type(p.value, \'$.speedMps\') IN (\'integer\', \'real\') THEN json_extract(p.value, \'$.speedMps\') END) END)\n' +
  '        FROM json_each(route_json) AS p) END) END AS plain_max_speed_mps\n' +
  '    FROM trips WHERE device_id = ? ORDER BY ended_at DESC LIMIT ?\n' +
  '  `).bind(deviceId, Math.min(limit, 1e3)).all();\n' +
  '  const oddIds = new Set();\n' +
  '  for (const row of plain.results || []) {\n' +
  '    if (row.odd_points === 0) maxSpeedById.set(row.id, row.plain_max_speed_mps ?? null);\n' +
  '    else oddIds.add(row.id);\n' +
  '  }\n' +
  '  const oddRows = rows.filter(row => oddIds.has(row.id) || !maxSpeedById.has(row.id));\n' +
  '  for (let index = 0; index < oddRows.length; index += 90) {\n' +
  '    const ids = oddRows.slice(index, index + 90).map(row => row.id);\n';

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
