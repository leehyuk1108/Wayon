# Parking place in the parking display (2026-11-10)

The parking server now adds `inspection.place` ({setting, level, area}, each an enum
with `unknown`) when its two blind full-frame classifications agree. The active
wayon-cloud bundle rebuilt each inspection from allowlisted fields and dropped it.

- Baseline: active `worker.js` `050963db…` (web-push-binding-20261110, version 51eba5be).
- Candidate: `c6060f9c…`. One insertion in `parkingDisplayInspection`: a present `place`
  must be an object whose three fields are known enum values, copied field by field;
  anything else rejects that display POST (the stored display stays). Without `place`
  the output is unchanged. GET, auth, KV keys, TTL and other routes are untouched.
- `node patch.mjs <baseline> <new-output>` writes the candidate; `unpatch` restores the
  baseline byte for byte.
- `runtime.test.mjs` (Miniflare, private copies of the active modules): byte-exact
  round trip, valid place kept, four invalid shapes rejected without replacing the
  stored display, results without place unchanged, and the unpatched bundle dropping it.
- Deployment: stage a version inheriting all 25 bindings (compared field by field),
  then activate; other modules must stay byte-identical. Rollback only when this
  candidate is the active 100% version.
