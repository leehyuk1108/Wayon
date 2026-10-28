import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

export const BASELINE_SHA256 = '67eccbf0151a79e428244b0e68bc9d800e79215c87d11d64e0b75442188633e8';
export const CANDIDATE_SHA256 = '630b8737898c7788187ce22d39c0d0c8ae9230d22f9b0ac6ab3c788e176d9733';
export const sha256 = value => createHash('sha256').update(value).digest('hex');
const fragment = readFileSync(new URL('./status.fragment.js', import.meta.url), 'utf8');

export function replaceOnce(source, before, after) {
  assert.equal(source.split(before).length - 1, 1, 'Patch anchor must occur exactly once');
  return source.replace(before, () => after);
}

export function namedFunction(source, name) {
  const start = source.search(new RegExp(`^(?:async )?function ${name}\\(`, 'm'));
  assert.ok(start >= 0, `Missing function ${name}`);
  const marker = `__name(${name}, "${name}");`;
  const end = source.indexOf(marker, start);
  assert.ok(end > start, `Missing end marker ${name}`);
  return source.slice(start, end + marker.length);
}

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  let output = replaceOnce(source, namedFunction(source, 'handleGmoneStatus'), fragment.trimEnd());
  const originalLatest = namedFunction(source, 'latestGmoneStatus');
  let latest = replaceOnce(originalLatest, '  const ageSeconds = isoAgeSeconds(row.collected_at);',
    '  if (!gmoneStatusObject(payload?.status)) return null;\n  const ageSeconds = isoAgeSeconds(row.collected_at);');
  latest = replaceOnce(latest, '    ok: true,',
    '    ok: true,\n    ...(typeof payload.clientScope === "string" && /^[0-9a-f]{64}$/i.test(payload.clientScope)\n      ? { clientScope: payload.clientScope.toLowerCase() } : {}),');
  output = replaceOnce(output, originalLatest, latest);
  output = replaceOnce(output, `    if (!requireBindings(env)) {
      return json({ error: "missing_cloudflare_bindings" }, 503);
    }
    const url = new URL(request.url);
    const { pathname } = url;`, `    const url = new URL(request.url);
    const { pathname } = url;
    const gmoneStoredRead = request.method === "GET" && pathname === "/api/gmone/status";
    if (gmoneStoredRead ? !env.DB : !requireBindings(env)) {
      return json({ error: "missing_cloudflare_bindings" }, 503);
    }`);
  output = replaceOnce(output, `    if (pathname.startsWith("/api/ai/")) {`, `    if (gmoneStoredRead) {
      return handleStoredGmoneStatus(request, env);
    }
    if (pathname.startsWith("/api/ai/")) {`);
  assert.equal(sha256(output), CANDIDATE_SHA256, 'Unexpected candidate bytes');
  return output;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, output] = process.argv.slice(2);
  assert.ok(input && output, 'Usage: node patch.mjs /private/baseline/worker.js /private/candidate/worker.js');
  assert.notEqual(resolve(input), resolve(output), 'Never overwrite the baseline');
  const patched = patch(readFileSync(input, 'utf8'));
  mkdirSync(dirname(resolve(output)), {recursive: true});
  writeFileSync(output, patched, {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({baseline: BASELINE_SHA256, candidate: sha256(patched)}));
}
