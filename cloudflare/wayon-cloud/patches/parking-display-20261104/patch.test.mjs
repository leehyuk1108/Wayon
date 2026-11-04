import test from 'node:test';
import assert from 'node:assert/strict';
import {patch, unpatch, patchModules, sha256, BASELINE_SHA256, OUTPUT_SHA256, RETAINED_MODULE_SHA256} from './patch.mjs';
import {baseline, retained} from './fixture.mjs';

test('exact active bundle patches and reverses byte-for-byte, with both companion modules unchanged', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  const output = patch(baseline);
  assert.equal(sha256(output), OUTPUT_SHA256);
  assert.equal(unpatch(output), baseline);
  const modules = patchModules(baseline, retained);
  for (const [name, hash] of Object.entries(RETAINED_MODULE_SHA256)) {
    assert.equal(modules[name], retained[name]);
    assert.equal(sha256(modules[name]), hash);
  }
  const recognition = '    if (pathname === "/api/parking/recognition") {';
  const auth = '      const identity = await authenticateDeviceKey(request, env);';
  const route = '    if (pathname === "/api/parking/latest") {';
  const publisher = '    if (pathname === "/api/parking/display") {';
  assert.ok(output.indexOf(publisher) < output.indexOf(recognition));
  assert.ok(output.indexOf(publisher) < output.indexOf(auth, output.indexOf(recognition)));
  assert.ok(output.indexOf(route) > output.indexOf(auth, output.indexOf(recognition)));
  const scoped = output.indexOf('      request = scopedDeviceRequest(request, identity.deviceId);', output.indexOf(auth, output.indexOf(recognition)));
  assert.ok(output.indexOf(route) > scoped);
  assert.equal(output.slice(output.indexOf(recognition), output.indexOf(route)),
    baseline.slice(baseline.indexOf(recognition), baseline.indexOf('    if (request.method === "POST" && pathname === "/api/telemetry") {')));
});

test('unknown/repeated/partial inputs and changed/missing/extra modules fail closed', () => {
  for (const input of [baseline + '\n', patch(baseline), baseline.replace('/api/telemetry', '/api/wrong')]) assert.throws(() => patch(input));
  assert.throws(() => unpatch(baseline));
  for (const name of Object.keys(retained)) {
    assert.throws(() => patchModules(baseline, {...retained, [name]: retained[name] + '\n'}));
    const missing = {...retained}; delete missing[name]; assert.throws(() => patchModules(baseline, missing));
  }
  assert.throws(() => patchModules(baseline, {...retained, 'unrelated.js': ''}));
});
