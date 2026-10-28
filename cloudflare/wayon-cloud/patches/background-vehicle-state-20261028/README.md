# Background Collector Refresh ACK

Apply this patch only to the exact previously deployed fast-state bundle:

- Input SHA-256: `630b8737898c7788187ce22d39c0d0c8ae9230d22f9b0ac6ab3c788e176d9733`
- Output SHA-256: `d1c969de49b9b452521cf2ac493f7211e85d18a08cff7212310feeb470f040d9`
- Cloud version: `75b26a1c-8cf7-4a3f-83a9-c061dc6befa9`

Do not deploy the unrelated dirty `src/worker.js`. The published Worker keeps
all three modules, 22 bindings, existing authentication and settings. There is
no schema migration or new credential. Private deployment receipts and source
bundles are outside Git.

Only a collector-authenticated `gmone-direct` response with a valid
`refreshStartedAt`, observation time and receipt time can complete a refresh.
It may acknowledge a superseded retry, but never a request created after its
query began. Passive official-cache and phone uploads do not complete it.
Existing legacy freshness/merge behavior is byte-for-byte unchanged.

## Tests

Set `WAYON_FAST_STATE_BASELINE` to the original pre-fast-state bundle used by
the adjacent fast-state test harness. It first applies that pinned patch, then
this patch. Run `node --test status.test.mjs` from this directory.

For real local D1 verification, set `MINIFLARE_MODULE` to the installed Miniflare
module directory and run `node runtime.mjs`. No remote service is contacted by
this test. Results: 12 tests, plus 73 workerd/D1 assertions including 40
concurrent writes. Source scope, authorization, ordering and full-field
preservation remain covered by the adjacent fast-state harness.

## Compatibility

Use `tools/gmone_collector/gmone_background.py`, not the legacy task entrypoint.
The legacy main loop lacks the new refresh ACK contract. Stop the collector
on failure; do not automatically re-register the backed-up legacy task XML.
Cloud rollback alone can restore the previous version without restarting that
legacy collector. See `tools/gmone_collector/BACKGROUND.md` for deployment
requirements, timestamp semantics, query budgets and Windows logon limits.
