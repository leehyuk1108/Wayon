import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

export const BASELINE_SHA256 = 'd1c969de49b9b452521cf2ac493f7211e85d18a08cff7212310feeb470f040d9';
export const OUTPUT_SHA256 = '77553a4cf67d29cebd9a7685dd4fb416322b8d1c3410869fa9cdae0a65a46177';

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  let output = replaceOnce(source, 'async function handleVehicleEvent(request, env) {',
    readFileSync(new URL('./notice.js', import.meta.url), 'utf8') + '\nasync function handleVehicleEvent(request, env, ctx) {');
  output = replaceOnce(output,
    '  const eventType = String(payload.eventType || "").slice(0, 64);',
    '  if (payload.eventType === "automatic_shutdown") return handleShutdownNotice(payload, request, env, ctx);\n' +
    '  const eventType = String(payload.eventType || "").slice(0, 64);');
  output = replaceOnce(output, 'return handleVehicleEvent(request, env);', 'return handleVehicleEvent(request, env, ctx);');
  output = replaceOnce(output, 'function visibleFcmNotification(data) {', `function visibleFcmNotification(data) {
  if (data?.type === "wayon_automatic_shutdown") return {
    title: data.notificationTitle, body: data.notificationBody, channelId: "wayon_power_alerts"
  };`);
  output = replaceOnce(output,
    'notification: { channel_id: visibleNotification.channelId }',
    'notification: { channel_id: visibleNotification.channelId, ...(data.type === "wayon_automatic_shutdown" ? {tag: data.vehicleEventId} : {}) }');
  assert.equal(sha256(output), OUTPUT_SHA256, 'Unexpected candidate bundle');
  return output;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, output] = process.argv.slice(2);
  assert.ok(input && output && resolve(input) !== resolve(output));
  const result = patch(readFileSync(input, 'utf8'));
  writeFileSync(output, result, {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({baseline: BASELINE_SHA256, candidate: sha256(result)}));
}
