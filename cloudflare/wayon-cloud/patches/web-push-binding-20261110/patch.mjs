import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

// Active production bundle (parking-display-20261104 candidate, version 3c8dd130).
export const BASELINE_SHA256 = '5d4724e39018dd23e26ad52ba458da7d1cd469307e96fb99756cb38da9539c20';
export const OUTPUT_SHA256 = '050963dbfa69677fa15ac62f1aa5c06315b8cc616c0967609457fe6bb341e65a';
export const anchor = '    const response = await Promise.race([fetch(WAYON_WEB_PUSH_URL, {';
// Same-account workers.dev subrequests do not reach another Worker; a service binding does.
// Without the binding the original public fetch is used unchanged.
export const replacement = '    const transport = env.MY_TRAVERSE_WEB && typeof env.MY_TRAVERSE_WEB.fetch === "function"\n' +
  '      ? env.MY_TRAVERSE_WEB.fetch.bind(env.MY_TRAVERSE_WEB) : fetch;\n' +
  '    const response = await Promise.race([transport(WAYON_WEB_PUSH_URL, {';

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
