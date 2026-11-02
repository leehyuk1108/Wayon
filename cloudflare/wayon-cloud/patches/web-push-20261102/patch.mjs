import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

export {sha256};
export const BASELINE_SHA256 = '0c24e5e60b85663712389c33974435742fe4183fe417744ab7ea01a183f87ed5';
export const OUTPUT_SHA256 = '247511da7b190bbae926b82f9d442293b352ad6b1526b064ad8375b815d0d689';
const fragment = readFileSync(new URL('./fanout.js', import.meta.url), 'utf8');
const anchor = 'async function sendDataNotifications(env, deviceId, data) {\n' +
  '  if (!validDeviceId(deviceId)) throw new Error("invalid_notification_scope");';
const replacement = fragment + '\n' + anchor +
  '\n  const webPush = sendWayonWebPush(env, deviceId, data).catch(() => false);\n  try {';
const end = '  return { sent, failed, invalid, subscriptions: tokens.length };\n}';
const endReplacement = '  return { sent, failed, invalid, subscriptions: tokens.length };\n' +
  '  } finally {\n    await webPush;\n  }\n}';

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  const output = replaceOnce(replaceOnce(source, anchor, replacement), end, endReplacement);
  assert.equal(sha256(output), OUTPUT_SHA256, 'Unexpected candidate bundle');
  return output;
}

export function unpatch(source) {
  assert.equal(sha256(source), OUTPUT_SHA256, 'Refusing unknown candidate bundle');
  const output = replaceOnce(replaceOnce(source, endReplacement, end), replacement, anchor);
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
