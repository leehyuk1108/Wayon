import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, RETAINED_MODULE_SHA256} from '../web-controls-20261102/patch.mjs';
export {sha256, RETAINED_MODULE_SHA256};

export const BASELINE_SHA256 = 'e37c4b20f633f9a307b97738571e71931fca22b9f45900a26d6f944dfa793ab7';
export const OUTPUT_SHA256 = '04b38059cbc64ad95609c0ba31a8073810d697cf0f6e44aa2cad92cdb66dbc7b';
const fragment = readFileSync(new URL('./snapshots.js', import.meta.url), 'utf8');
const start = 'async function handleSnapshotsList(request, env) {';
const end = '__name(handleSnapshotsList, "handleSnapshotsList");';
const route = '    if (request.method === "GET" && pathname === "/api/state") {';
const newRoute = '    if (pathname === "/api/mobile/web-snapshots") {\n' +
  '      return handleWebSnapshots(request, env);\n    }\n' + route;

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  for (const anchor of [start, end, route]) assert.equal(source.split(anchor).length - 1, 1);
  const output = (source.slice(0, source.indexOf(start)) + fragment + end +
    source.slice(source.indexOf(end) + end.length)).replace(route, () => newRoute);
  assert.equal(sha256(output), OUTPUT_SHA256, 'Unexpected candidate');
  return output;
}

export function patchModules(source, retained) {
  assert.deepEqual(Object.keys(retained).sort(), Object.keys(RETAINED_MODULE_SHA256).sort());
  for (const [name, hash] of Object.entries(RETAINED_MODULE_SHA256)) assert.equal(sha256(retained[name]), hash);
  return {'worker.js': patch(source), ...retained};
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, output, moduleDir = input && dirname(resolve(input))] = process.argv.slice(2);
  assert.ok(input && output && resolve(input) !== resolve(output));
  const retained = Object.fromEntries(Object.keys(RETAINED_MODULE_SHA256).map(name => [name, readFileSync(join(moduleDir, name), 'utf8')]));
  const result = patchModules(readFileSync(input, 'utf8'), retained)['worker.js'];
  writeFileSync(output, result, {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({baseline: BASELINE_SHA256, candidate: sha256(result)}));
}
