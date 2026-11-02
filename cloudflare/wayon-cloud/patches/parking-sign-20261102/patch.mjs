import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

export {sha256, replaceOnce};
export const BASELINE_SHA256 = '74402c332a51ffde4c00fdd99fc53e7a04830764f082d2a91e37b3a4096232cf';
export const OUTPUT_SHA256 = '0c24e5e60b85663712389c33974435742fe4183fe417744ab7ea01a183f87ed5';
const fragment = readFileSync(new URL('./notice.js', import.meta.url), 'utf8');
const edits = [
  ['function visibleFcmNotification(data) {', fragment + '\n' + `function visibleFcmNotification(data) {
  if (data?.type === "wayon_parking_sign") return {
    title: data.notificationTitle, body: data.notificationBody, channelId: "wayon_parking_sign_alerts"
  };`],
  ['notification: { channel_id: visibleNotification.channelId, ...(data.type === "wayon_automatic_shutdown" ? {tag: data.vehicleEventId} : {}) }',
    'notification: { channel_id: visibleNotification.channelId, ...(data.type === "wayon_automatic_shutdown" ? {tag: data.vehicleEventId} : data.type === "wayon_parking_sign" ? {tag: data.parkingEventId} : {}) }'],
  ['    if (pathname.startsWith("/api/ai/")) {', `    if (pathname === "/api/parking/recognition") {
      return handleParkingRecognition(request, env, ctx);
    }
    if (pathname.startsWith("/api/ai/")) {`],
];

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  const output = edits.reduce((text, [before, after]) => replaceOnce(text, before, after), source);
  assert.equal(sha256(output), OUTPUT_SHA256, 'Unexpected candidate bundle');
  return output;
}

export function unpatch(source) {
  assert.equal(sha256(source), OUTPUT_SHA256, 'Refusing unknown candidate bundle');
  const output = [...edits].reverse().reduce((text, [before, after]) => replaceOnce(text, after, before), source);
  assert.equal(sha256(output), BASELINE_SHA256, 'Baseline restoration mismatch');
  return output;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, output] = process.argv.slice(2);
  assert.ok(input && output && resolve(input) !== resolve(output), 'Specify distinct baseline and new candidate paths');
  const result = patch(readFileSync(input, 'utf8'));
  writeFileSync(output, result, {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({baseline: BASELINE_SHA256, candidate: sha256(result)}));
}
