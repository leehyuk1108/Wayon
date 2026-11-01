import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

export const BASELINE_SHA256 = '77553a4cf67d29cebd9a7685dd4fb416322b8d1c3410869fa9cdae0a65a46177';
export const OUTPUT_SHA256 = '74402c332a51ffde4c00fdd99fc53e7a04830764f082d2a91e37b3a4096232cf';
export const MIGRATION_SHA256 = 'c07195a4960d281cb9ee907ee00299b5338f2ff3958d128e2560c150f30ffc1b';
export const sha256 = value => createHash('sha256').update(value).digest('hex');
const fragment = readFileSync(new URL('./parking_batch.js', import.meta.url), 'utf8');
assert.equal(sha256(readFileSync(new URL('./parking_batch.sql', import.meta.url))), MIGRATION_SHA256, 'Migration drift');
const marker = '// WAYON_PARKING_BATCH_V1_BEGIN';

export function replaceOnce(source, before, after) {
  assert.equal(source.split(before).length - 1, 1, 'Patch anchor must occur exactly once');
  return source.replace(before, () => after);
}

function changes() {
  return [
    ['async function handleSnapshot(request, env) {', fragment + '\nasync function handleSnapshot(request, env) {'],
    ['  const capturedAt = payload.capturedAt || nowIso();\n  const saved = [];',
      '  if (Object.prototype.hasOwnProperty.call(payload, "parking")) return handleParkingBatchSnapshot(payload, request, env);\n' +
      '  const capturedAt = payload.capturedAt || nowIso();\n  const saved = [];'],
    ['    snapshots: (result.results || []).map((snapshot) => aiSnapshot(request, snapshot)),',
      '    snapshots: await parkingBatchAiSnapshots(request, env, result.results || []),'],
  ];
}

export function unpatch(source) {
  let output = source;
  for (const [before, after] of changes().reverse()) output = replaceOnce(output, after, before);
  assert.equal(sha256(output), BASELINE_SHA256, 'Patched bundle has drifted');
  return output;
}

export function patch(source) {
  if (source.includes(marker)) {
    unpatch(source);
    assert.equal(sha256(source), OUTPUT_SHA256, 'Patched bundle has drifted');
    return source;
  }
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle (never use src/worker.js)');
  let output = source;
  for (const [before, after] of changes()) output = replaceOnce(output, before, after);
  assert.equal(unpatch(output), source, 'Patch changed unrelated bytes');
  assert.equal(sha256(output), OUTPUT_SHA256, 'Unexpected candidate bytes');
  return output;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, output] = process.argv.slice(2);
  assert.ok(input && output && resolve(input) !== resolve(output), 'Use separate input and new output files');
  const result = patch(readFileSync(input, 'utf8'));
  writeFileSync(output, result, {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({baseline: BASELINE_SHA256, candidate: sha256(result)}));
}
