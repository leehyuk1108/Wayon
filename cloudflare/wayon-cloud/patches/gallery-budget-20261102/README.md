# Gallery Read Budget Patch

This patch is deliberately applied to the deployed bundle, not the unrelated
dirty `src/worker.js`. Unknown input or companion modules fail closed.

- Baseline deployment: `c144778d-55af-4036-ad00-a0c74563be2e`
- Baseline main SHA-256: `e37c4b20f633f9a307b97738571e71931fca22b9f45900a26d6f944dfa793ab7`
- Candidate main SHA-256: `04b38059cbc64ad95609c0ba31a8073810d697cf0f6e44aa2cad92cdb66dbc7b`
- Companion modules, assets, all 24 bindings, auth and command policy are retained.

## Changes

`GET /api/mobile/web-snapshots?limit=24` returns only the authenticated device's
current photo list and existing impact fields. It performs no total/day aggregate,
server-history request or metadata-cache access. The default is 24, maximum 1000.
The PWA recurring composed feed uses this endpoint. `/api/state` still has its
original 12-photo preview; it was not repurposed as a 24-photo response.

The existing `/api/snapshots` keeps its server-first path. Only its D1 fallback
caches display-only `days` and `total` by device hash and UTC-hour bucket in the
existing SNAPSHOTS KV, under `meta/snapshot-stats/v1/`. Total is calculated from
the grouped rows, including the NULL date group, eliminating the separate COUNT.
Fresh photo rows and impact metadata are queried for every request.

Summary counts/dates may lag by less than one hour; this is not a photo cache.
`statsComputedAt` and `statsExpiresAt` make this explicit. New photos appear in
the returned list even before summary expiration. UTC hour rollover (also a KST
hour rollover) invalidates old metadata regardless of physical KV TTL. KV TTL is
7200 seconds to avoid Cloudflare's minimum-TTL issue near a bucket boundary.

Memory retains at most 32 entries per isolate and coalesces in-flight aggregation.
KV read failure does NOT cause an expensive fallback scan. A successful aggregate
is retained locally if KV write fails. A distributed cold miss or multiple regions
can still repeat aggregation; this is not a global exactly-once promise. Requests
use `no-store`; session, live vehicle state, command validation and snapshot bytes
are never cached by this patch.

## Verification

```sh
node --test cloudflare/wayon-cloud/patches/gallery-budget-20261102/*.test.mjs
node cloudflare/wayon-cloud/patches/gallery-budget-20261102/patch.mjs \
  /private/deployed/worker.js /private/candidate.worker.js /private/deployed
```

Tests need the exact private production baseline plus the two retained modules.
Override `WAYON_GALLERY_BASELINE`, `WAYON_GALLERY_MODULE_DIR` and
`MINIFLARE_MODULE` for another environment. Credentials and private images are not
fixtures. Native workerd/D1/KV tests verify registered-key auth, owner isolation,
method restrictions, read-only behavior, impacts, limits, fresh-list/cached-summary
semantics, and sanitized failure. VM tests cover clock boundaries, corruption,
NULL dates, KV failures, bounded memory and concurrent requests. The patch test
reverses both replacements and compares every other byte with baseline.

The SQL date filter and impact joins remain unchanged. The indexed fixture proves
bounded recent-page reads, not every production query's cost. Other apps in the
same Cloudflare account consume the same daily budget. This patch cannot restore
already-consumed D1 quota; login recovery requires the daily reset or a separately
authorized plan change. Do not bypass authentication or clear notification data.
