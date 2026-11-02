import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

export const sha256 = value => createHash('sha256').update(value).digest('hex');
export const BASELINE_SHA256 = '247511da7b190bbae926b82f9d442293b352ad6b1526b064ad8375b815d0d689';
export const OUTPUT_SHA256 = 'e37c4b20f633f9a307b97738571e71931fca22b9f45900a26d6f944dfa793ab7';
export const RETAINED_MODULE_SHA256 = Object.freeze({
  'key_diagnostics.mjs': '1432f3bf0df3e7b73b3fd87c27062db9116230e4526359a6ccfcb85b0e5fbed5',
  'device_reissue.mjs': 'e44ea8791f7b63bcff47cc576f9762a7b3910e670f3932f1e5ee0f0f86cf9f84',
});
const fragment = readFileSync(new URL('./trips.js', import.meta.url), 'utf8');
const handlerAnchor = 'async function handleState(request, env) {';
const handlerReplacement = fragment + '\n' + handlerAnchor;
const routeAnchor = '    if (request.method === "GET" && pathname === "/api/state") {';
const routeReplacement = '    if (pathname === "/api/mobile/web-trips") {\n' +
  '      return handleWebTrips(request, env);\n    }\n' + routeAnchor;

function replaceOnce(source, before, after) {
  assert.equal(source.split(before).length - 1, 1, 'Patch anchor must occur exactly once');
  return source.replace(before, () => after);
}

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  const output = replaceOnce(replaceOnce(source, handlerAnchor, handlerReplacement), routeAnchor, routeReplacement);
  assert.equal(sha256(output), OUTPUT_SHA256, 'Unexpected candidate bundle');
  return output;
}

export function unpatch(source) {
  assert.equal(sha256(source), OUTPUT_SHA256, 'Refusing unknown candidate bundle');
  const output = replaceOnce(replaceOnce(source, routeReplacement, routeAnchor), handlerReplacement, handlerAnchor);
  assert.equal(sha256(output), BASELINE_SHA256, 'Baseline restoration mismatch');
  return output;
}

export function patchModules(source, retained) {
  assert.deepEqual(Object.keys(retained).sort(), Object.keys(RETAINED_MODULE_SHA256).sort(),
    'Retain exactly the original companion modules');
  for (const [name, hash] of Object.entries(RETAINED_MODULE_SHA256)) {
    assert.equal(sha256(retained[name]), hash, 'Retained module hash mismatch: ' + name);
  }
  return {'worker.js': patch(source), ...retained};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, output, moduleDir = input ? join(dirname(resolve(input)), 'baseline') : ''] = process.argv.slice(2);
  assert.ok(input && output && resolve(input) !== resolve(output), 'Specify distinct baseline and new output paths');
  const retained = Object.fromEntries(Object.keys(RETAINED_MODULE_SHA256)
    .map(name => [name, readFileSync(join(moduleDir, name), 'utf8')]));
  const result = patchModules(readFileSync(input, 'utf8'), retained)['worker.js'];
  writeFileSync(output, result, {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({baseline: BASELINE_SHA256, candidate: sha256(result), retained: RETAINED_MODULE_SHA256}));
}
