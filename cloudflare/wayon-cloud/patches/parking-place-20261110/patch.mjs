import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

// Active production bundle (web-push-binding-20261110 candidate, version 51eba5be).
export const BASELINE_SHA256 = '050963dbfa69677fa15ac62f1aa5c06315b8cc616c0967609457fe6bb341e65a';
export const OUTPUT_SHA256 = 'c6060f9c392bc8ef14515f88ecdb1b3df5af3a472ea10d45c920b920c19cc12a';
export const anchor = '  return {...result, exactParkingSpotKnown: false, humanVerified: false};\n}';
// The parking server now sends a coarse place judgement (two blind classifications agreeing
// field by field). Only the three known enum fields pass; anything else rejects the display.
export const replacement = '  if (Object.hasOwn(item, "place")) {\n' +
  '    parkingDisplayCheck(parkingDisplayObject(item.place));\n' +
  '    const place = {};\n' +
  '    for (const [key, values] of [["setting", ["unknown", "indoor", "outdoor"]],\n' +
  '      ["level", ["unknown", "underground", "ground", "upper"]],\n' +
  '      ["area", ["unknown", "parking_structure", "parking_lot", "street"]]]) {\n' +
  '      parkingDisplayCheck(values.includes(item.place[key]));\n' +
  '      place[key] = item.place[key];\n' +
  '    }\n' +
  '    result.place = place;\n' +
  '  }\n' + anchor;

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
