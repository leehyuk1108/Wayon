import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {BASELINE_SHA256, OUTPUT_SHA256, RETAINED_MODULE_SHA256, patch, patchModules, sha256, unpatch} from './patch.mjs';
import {baseline, columns, retained} from './fixture.mjs';

test('pinned input produces pinned output and restores every original byte', () => {
  assert.equal(sha256(baseline), BASELINE_SHA256);
  const candidate = patch(baseline);
  assert.equal(sha256(candidate), OUTPUT_SHA256);
  assert.equal(unpatch(candidate), baseline);
  assert.equal(patch(baseline), candidate);
});

test('unknown input, already applied patch and altered candidate fail closed', () => {
  assert.throws(() => patch(baseline + '\n'), /unknown production bundle/);
  assert.throws(() => patch(patch(baseline)), /unknown production bundle/);
  assert.throws(() => unpatch(patch(baseline) + '\n'), /unknown candidate bundle/);
});

test('both original companion modules are pinned and retained byte-for-byte', () => {
  const modules = patchModules(baseline, retained);
  assert.deepEqual(Object.keys(modules).sort(), ['worker.js', ...Object.keys(retained)].sort());
  for (const [name, hash] of Object.entries(RETAINED_MODULE_SHA256)) {
    assert.equal(sha256(modules[name]), hash);
    assert.equal(modules[name], retained[name]);
    assert.throws(() => patchModules(baseline, {...retained, [name]: retained[name] + '\n'}), /hash mismatch/);
    const missing = {...retained}; delete missing[name];
    assert.throws(() => patchModules(baseline, missing), /exactly the original/);
  }
  assert.throws(() => patchModules(baseline, {...retained, 'extra.mjs': ''}), /exactly the original/);
});

test('only two additive insertions; old FCM, fanout, detail, imports and exports stay exact', () => {
  const fragment = readFileSync(new URL('./trips.js', import.meta.url), 'utf8');
  const route = '    if (pathname === "/api/mobile/web-trips") {\n      return handleWebTrips(request, env);\n    }\n';
  const candidate = patch(baseline);
  assert.equal(candidate.split(fragment + '\n').length, 2);
  assert.equal(candidate.split(route).length, 2);
  assert.equal(candidate.replace(fragment + '\n', '').replace(route, ''), baseline);
  assert.equal(candidate.slice(candidate.lastIndexOf('\nexport {')), baseline.slice(baseline.lastIndexOf('\nexport {')));
  assert.deepEqual(candidate.match(/^import .*$/gm), baseline.match(/^import .*$/gm));
  const gate = candidate.indexOf('const identity = await authenticateDeviceKey(request, env);', candidate.indexOf('var worker_default ='));
  assert.ok(gate > 0 && candidate.indexOf(route) > gate, 'Route must remain behind registered-key auth');
});

test('new handler has exactly the compact read-only SQL projection and owner parameters', () => {
  const fragment = readFileSync(new URL('./trips.js', import.meta.url), 'utf8');
  const sql = fragment.match(/prepare\(`([\s\S]*?)`\)/)[1];
  const projection = sql.match(/SELECT ([\s\S]*?)\s+FROM/)[1].split(',').map(s => s.trim());
  assert.deepEqual(projection, columns);
  assert.match(sql, /FROM trips WHERE device_id = \? ORDER BY ended_at DESC LIMIT \?/);
  assert.match(fragment, /authorize\(request, env, false\)/);
  assert.match(fragment, /authenticatedDeviceId\(request\)/);
  assert.match(fragment, /\.bind\(deviceId, limit\)\.all\(\)/);
  assert.doesNotMatch(fragment, /route_json|report_json|analysis_json|health_json|JSON\.parse|parseTrip|fetch\(|INSERT|UPDATE|DELETE|console\./);
});
