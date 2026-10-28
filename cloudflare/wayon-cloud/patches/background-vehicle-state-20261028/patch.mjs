import assert from 'node:assert/strict';
import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {sha256, replaceOnce} from '../fast-vehicle-state-20261028/patch.mjs';

export const BASELINE_SHA256 = '630b8737898c7788187ce22d39c0d0c8ae9230d22f9b0ac6ab3c788e176d9733';
export const CANDIDATE_SHA256 = 'd1c969de49b9b452521cf2ac493f7211e85d18a08cff7212310feeb470f040d9';

export function patch(source) {
  assert.equal(sha256(source), BASELINE_SHA256, 'Refusing unknown production bundle');
  const output = replaceOnce(source, `    if (written.meta.changes === 0) {
      return json({ ok: false, stored: false, error: "snapshot_not_newer" }, 409);
    }
    // A phone receipt does not complete the separate collector refresh job.
    if (source !== "gmone-direct-android" &&
        constantTimeEqual(getBearerToken(request), env.WAYON_GMONE_TOKEN || "")) {
      const acknowledged = await env.DB.prepare(\`
        UPDATE gmone_refresh_requests SET completed_at = ?
        WHERE id = ? AND requested_at <= ?
      \`).bind(receivedAt, deviceId, collectedAt).run();
      if (acknowledged?.success === false) return json({ error: "gmone_status_unavailable" }, 503);
    }`, `    // Passive cache receipt is not proof of a requested vehicle refresh.
    const refreshStart = gmoneTimestamp(payload.refreshStartedAt);
    if (source === "gmone-direct" && vehicle !== null && refreshStart !== null &&
        refreshStart <= vehicle && refreshStart <= collected &&
        collected - refreshStart <= 120000 && vehicle - refreshStart <= 120000 &&
        constantTimeEqual(getBearerToken(request), env.WAYON_GMONE_TOKEN || "")) {
      const acknowledged = await env.DB.prepare(\`
        UPDATE gmone_refresh_requests SET completed_at = ?
        WHERE id = ? AND julianday(requested_at) <= julianday(?)
      \`).bind(receivedAt, deviceId, new Date(refreshStart).toISOString()).run();
      if (acknowledged?.success === false) return json({ error: "gmone_status_unavailable" }, 503);
    }
    // A retry can finish the refresh ACK even if a newer snapshot already won.
    if (written.meta.changes === 0) {
      return json({ ok: false, stored: false, error: "snapshot_not_newer" }, 409);
    }`);
  assert.equal(sha256(output), CANDIDATE_SHA256);
  return output;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, output] = process.argv.slice(2);
  assert.ok(input && output && resolve(input) !== resolve(output));
  const data = patch(readFileSync(input, 'utf8'));
  writeFileSync(output, data, {flag: 'wx', mode: 0o600});
  console.log(JSON.stringify({baseline: BASELINE_SHA256, candidate: sha256(data)}));
}
