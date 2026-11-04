import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, RETAINED_MODULE_SHA256} from '../gallery-budget-20261102/patch.mjs';
export {sha256, RETAINED_MODULE_SHA256};

export const BASELINE_SHA256 = '04b38059cbc64ad95609c0ba31a8073810d697cf0f6e44aa2cad92cdb66dbc7b';
export const OUTPUT_SHA256 = '5d4724e39018dd23e26ad52ba458da7d1cd469307e96fb99756cb38da9539c20';
const fragment = readFileSync(new URL('./latest.js', import.meta.url), 'utf8');
const handler = 'async function fetchServerApi(env, path, deviceId) {';
const route = '    if (request.method === "POST" && pathname === "/api/telemetry") {';
const publisherRoute = '    if (pathname === "/api/parking/recognition") {';
const insertHandler = fragment + '\n' + handler;
const insertRoute = '    if (pathname === "/api/parking/latest") {\n' +
  '      return handleParkingLatest(request, env);\n    }\n' + route;
const insertPublisherRoute = '    if (pathname === "/api/parking/display") {\n' +
  '      return handleParkingDisplay(request, env);\n    }\n' + publisherRoute;

function replaceOnce(source, before, after) {
  assert.equal(source.split(before).length - 1, 1, 'Patch anchor must occur exactly once');
  return source.replace(before, () => after);
}

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  const output = replaceOnce(replaceOnce(replaceOnce(source, handler, insertHandler), route, insertRoute), publisherRoute, insertPublisherRoute);
  assert.equal(sha256(output), OUTPUT_SHA256, 'Unexpected candidate bundle');
  return output;
}

export function unpatch(source) {
  assert.equal(sha256(source), OUTPUT_SHA256, 'Refusing unknown candidate bundle');
  const output = replaceOnce(replaceOnce(replaceOnce(source, insertPublisherRoute, publisherRoute), insertRoute, route), insertHandler, handler);
  assert.equal(sha256(output), BASELINE_SHA256, 'Baseline restoration mismatch');
  return output;
}

export function patchModules(source, retained) {
  assert.deepEqual(Object.keys(retained).sort(), Object.keys(RETAINED_MODULE_SHA256).sort(),
    'Retain exactly the original companion modules');
  for (const [name, hash] of Object.entries(RETAINED_MODULE_SHA256)) assert.equal(sha256(retained[name]), hash,
    'Retained module hash mismatch: ' + name);
  return {'worker.js': patch(source), ...retained};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, output, moduleDir = input && dirname(resolve(input))] = process.argv.slice(2);
  assert.ok(input && output && resolve(input) !== resolve(output), 'Specify distinct baseline and new output paths');
  const retained = Object.fromEntries(Object.keys(RETAINED_MODULE_SHA256)
    .map(name => [name, readFileSync(join(moduleDir, name), 'utf8')]));
  const candidate = patchModules(readFileSync(input, 'utf8'), retained)['worker.js'];
  writeFileSync(output, candidate, {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({baseline: BASELINE_SHA256, candidate: sha256(candidate), retained: RETAINED_MODULE_SHA256}));
}
