# My Traverse Login and Gallery Read Budget, 2026-11-02

## Confirmed Incident

The real iPhone's login POST returned 200, followed by session GET 400. A fresh
desktop login and an existing session reproduced it. D1 SELECT returned error
7500: the Cloudflare account exceeded its free daily row-read quota. Login INSERT
could still succeed, so successful password submission was not proof of a usable
session. The generic error hid the database outage.

In the sampled roughly ten-hour query-insights window, two queries accounted for
5,012,488 row reads: snapshot date grouping (198 executions / 3,595,870 reads) and
total snapshot count (156 executions / 1,416,618 reads). Caller attribution was
not established. Separate databases share the account quota, so changing only the
PWA session database would not fix this account-wide incident.

## Correction

- The PWA recurring feed requests a fresh 24-photo list without gallery statistics.
- The old gallery D1 fallback reuses device-scoped hourly summary metadata and
  derives total from its one grouped query. Photos and impact associations remain
  fresh. Existing server-first history preference remains unchanged.
- Recognized local D1 daily read/write quota errors return a sanitized 503,
  `database_daily_limit`, `Retry-After`, and next-UTC-midnight `retryAt`.
- The login/restore screen displays that safe explanation, including 09:00 KST
  reset time. Failed restore never authenticates or clears subscriptions/cookies.
- Authentication, live-state freshness, CSRF, account ownership, command guards,
  encrypted credentials and original Android UI remain unchanged.

The classifier applies to the PWA's own D1 exception chain. Upstream unknown
failures remain sanitized upstream errors, not guessed quota diagnoses. A bad
password is not reclassified as a database outage. No paid plan, schema migration,
data deletion, authentication bypass or vehicle command is part of this fix.

## Verification and Limits

Before deployment: PWA 337/337 tests, including Chromium and native workerd/D1;
pinned gallery patch 15/15 tests, including native workerd/D1/KV. Exact retained
module hashes and round-trip removal of patch fragments prove unrelated deployed
code is unchanged. Android Next original HTML SHA-256 remains
`d26971b235a51fa52aaeda6e1c7e92e7dbb61c0758c8189ab4c49aafebf7e6c5`.

Read-only production PRAGMA verified the existing snapshot index on
`(device_id, captured_at)` and impact indexes on `wide_snapshot_id` and
`driver_snapshot_id`. The native fixture uses those column sets. No production
index/schema change was required. PRAGMA succeeds despite SELECT quota failure;
it is not evidence that authenticated application reads have recovered.
With 1,005 synthetic snapshots and 3,000 impacts, the exact new joined-list query
read 70 rows for a 24-photo page. EXPLAIN used all three indexes with no scan,
automatic index or temporary sort. This is an isolated cost measurement, not a
production row-count or full-account daily cost guarantee.

Claude's final-batch review identified an offline-error wording regression, fixed
with Korean transport guidance and a rejection test. Its missing-index concern
was based on the repository schema; actual production PRAGMA disproved that
premise. Its request to measure the actual JOIN, not a simplified SELECT, was
implemented as above. Claude reviews source; Codex runs the actual tests.

Summary metadata can lag by less than one hour. Distributed cold caches may each
aggregate once; this is not a global lock. The unchanged date filter and impact
joins, other queries and other account applications still need real usage
monitoring. No claim that all future quota exhaustion is impossible.

On this incident date, already-consumed quota is not recoverable by redeploying.
The next normal reset is **2026-11-03 09:00 KST (00:00 UTC)**. While exhausted,
production validation can establish the correct 503 and error display but not
successful authenticated feed/photo loading or remote-control operation. Those
claims require a healthy production database after reset.

## Production Result

- Wayon `6ba010db-cb2e-419d-9fab-79369da18d6b` active at 100%; exact candidate
  hash, both companion modules and 24 bindings verified unchanged as applicable.
- PWA `aeea729d-ec1c-4111-981f-4759bbf4fe98` active at 100%; all existing bindings
  retained and actual pwa.js/pwa.css/bridge.js bytes match the build.
- Unauthenticated new photo, legacy gallery and state endpoints all return 401.
- Fresh valid-password login POST 200 followed by session GET **503** with
  `database_daily_limit`, `Retry-After`, and `2026-11-03T00:00:00.000Z`. No cookie
  deletion or raw D1 error details in the response. Successful login NOT restored.
- Actual iPhone Mirroring: after the user locked the phone to resume mirroring,
  the existing My Traverse home-screen app displayed the Korean quota/reset
  explanation after login. This is physical iPhone UI evidence, not a simulator.
  No app deletion, push reset or vehicle command was performed.

The private verifier initially stopped on a local Python helper-name collision
before its login probe; importing CookieJar directly corrected the verifier.
The successful run above completed afterward. This was not a production failure.

Deployment receipts and before/after bundles are private under
`/Users/hyuklee/Documents/my-traverse-web-20261102/`. No settings secrets, session
cookies, identifiers, image bytes or raw account records belong in Git.

## Rollback

Deploy the pinned Wayon route before the PWA client that uses it. If validation
fails after activation, first restore the PWA to the saved prior version
`aadadba3-4a5f-4f22-9c38-da4f254fba61`, then restore Wayon to
`c144778d-55af-4036-ad00-a0c74563be2e`. Verify the current deployment is still this
task's candidate before either operation. Keep all existing bindings and data;
do not deploy the unrelated dirty main source as a rollback. No schema rollback
is needed. Quota outage alone is expected today, not a reason to remove the fix.
