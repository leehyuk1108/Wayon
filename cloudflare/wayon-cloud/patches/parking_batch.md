# Explicit Parking Snapshot Groups

## Scope and State

Local patch/test artifacts only. No source Worker, parking collector, phone app,
device, cloud database, or deployment has been changed. No commit/push/handoff.
**Do not deploy `src/worker.js`: it is old and independently dirty.**

The patch is pinned to the private production bundle at
`/Users/hyuklee/Documents/my-traverse-carrot-20261028/shutdown-notice-worker.js`.
The local `cloud-shutdown-deployment/verified.json` records all three modules
matching production version `0e75c093-0d1d-47e1-bfc1-2295ee789a33`, with 22
bindings preserved. A fresh read-only `/content/v2` attempt on 2026-11-02 was
HTTP 401 with the existing Wrangler OAuth credential. No credential refresh was
attempted. **The parent must download/recheck the active bundle and settings
before deployment; this subtask cannot certify the current cloud version.**

- Baseline SHA-256: `77553a4cf67d29cebd9a7685dd4fb416322b8d1c3410869fa9cdae0a65a46177`
- Candidate SHA-256: `74402c332a51ffde4c00fdd99fc53e7a04830764f082d2a91e37b3a4096232cf`
- Migration SHA-256: `c07195a4960d281cb9ee907ee00299b5338f2ff3958d128e2560c150f30ffc1b`

## Wire Contract

One existing `POST /api/snapshot` request per wide frame, with optional:

```json
{
  "capturedAt": "2026-11-02T00:00:00Z",
  "wideJpegBase64": "...",
  "parking": {
    "version": 1,
    "eventId": "parking-unique-id",
    "parkedAt": "2026-11-02T00:00:10Z",
    "index": 0,
    "count": 9,
    "phase": "approach"
  }
}
```

- `capturedAt` is required and retained verbatim as the real frame capture time.
- `parkedAt` is the final stopped-burst reference, **not the gear-P time**.
- `eventId`: 1-96 ASCII characters, `[A-Za-z0-9][A-Za-z0-9_.-]*`, matching the
  parking service's existing identifier grammar. No caller device ID is trusted.
- Exactly six metadata fields; version 1; integer count 2-12; integer index
  0 through count-1. Phase is `approach` or `parked`.
- ISO timestamps require a timezone; whole-second `Z` timestamps are supported.
  Optional fractional seconds (1-6 digits) and numeric offsets are accepted.
- Capture time is within `[parkedAt - 120 seconds, parkedAt]`. The last index
  must be `parked` at `parkedAt`. Group age at upload is at most 2 hours, with
  at most 5 seconds future clock skew. Captures strictly increase by index
  (millisecond comparison); approach frames must precede all parked frames.
- `driverJpegBase64` is optional on **only the first parked index**. It is
  saved as an ordinary driver snapshot with no parking metadata, in the same
  completion transaction. It does not count toward the exterior group count.
  The first-parked rule is checked even with out-of-order concurrent uploads.
- JPEG envelope and Base64 validated before storage; 2 MiB per image and
  16 MiB aggregate exterior bytes per group. Full image decoding remains the
  parking service's job, not this Worker's JPEG marker check.

HTTP 200 means the frame was accepted. `parking.complete: false` in the upload
response means staged, not a published group. Once all indices are present,
`parking.complete: true` is returned. Exact retries return the same IDs and
never rewrite the stored images. Conflicting bytes, count, reference, capture
time or phase return 409; malformed metadata/time/images return 400. An absent
`parking` property uses the original handler byte-for-byte. Explicit null is
invalid, not a fallback to the ordinary path.

The owner-authorized `GET /api/ai/snapshots` adds the original six-field parking
object only to completed wide entries. Existing driver/ordinary/impact entries
keep their previous JSON shape, with no `parking` key. Limit/date behavior and
all other APIs are unchanged. A small list limit can still split a complete
group; collectors must require all unique indices/count/reference/device to
match and must never feed an incomplete explicit group into legacy heuristics.

## Storage and Failure Semantics

An additive `parking_snapshot_frames_v1` D1 table stores bounded metadata,
image hashes and staging identities. Its primary key is `(device_id, event_id,
frame_index)`. No existing table or row is migrated or rewritten. The 12-frame
bound, index constraints, consistency checks and D1 batch transaction prevent
partial or conflicting groups entering the ordinary snapshots table. The
existing `latest_state` pointers move only on completed groups and never back
to an older capture. First-parked driver rows have no parking association in
the owner list or KV metadata.

D1 was chosen over a shared KV manifest because
[KV concurrent writes are last-writer-wins](https://developers.cloudflare.com/kv/api/write-key-value-pairs/),
whereas [D1 batches run in one transaction](https://developers.cloudflare.com/d1/observability/find-expensive-queries/).
KV metadata still includes a copy on wide images; it is not the authority for
completion. No additional Worker binding or service credential is needed.

At most eight incomplete groups per device are admitted. New uploads clean
expired partial metadata/images after the 2-hour window plus 5 minutes of grace;
completed metadata lives alongside its immutable snapshots. Cleanup only claims
unpublished keys belonging to the authenticated device. No shared or historical
image is deleted. If KV cleanup fails, an unreferenced image may remain. KV and
D1 do not share a transaction: a crash/uncertain D1 response after KV writes may
also leave an orphan object. Such keys are deliberately not deleted when a
commit might have succeeded. They never expose a partial group as complete.
Remote KV propagation/availability and actual device upload latency are not
proved by local workerd tests.

## Existing Deployment Workflow

Private helpers found locally (read, not run):

- `/Users/hyuklee/Documents/my-traverse-carrot-20261028/deploy_shutdown_notice.py`
  sets the last candidate/version and delegates to `deploy_fast_state.py`.
- `/Users/hyuklee/Documents/my-traverse-carrot-20261028/deploy_fast_state.py`
  performs stage/activate/verify/rollback, inheriting bindings strictly,
  preserving assets/settings, and verifying the multipart `/content/v2` bytes.
- `/Users/hyuklee/Desktop/Coding/프로젝트/trailblazer_acc/release/hylink-reissue-20260930/deploy.py`
  contains the underlying private authenticated API helpers. Importing it has
  directory/permission side effects; do not import merely to inspect it.
- Original extra modules are in the private `cloud-baseline` directory:
  `key_diagnostics.mjs` and `device_reissue.mjs`. Preserve both exactly.

Parent-only deployment sequence:

1. Download active content/settings/deployments/most recent uploaded version
   into a new private directory. Require one active version at 100%, the same
   version as latest uploaded, and the exact baseline SHA above. Stop on drift.
   Compare all module hashes, settings/bindings and assets, not just worker.js.
2. Run this patcher against that downloaded module into a **new** private file.
   Input/output/migration hashes and every replacement anchor are guarded.
   Reapplying to its exact output is a no-op; partial/drifted patches fail.
3. Run the tests below using that private baseline and its two sibling modules.
4. Adapt the existing private deployment helper with the freshly verified active
   version as rollback target, the new candidate hash and a new receipt folder.
   Do not run the old helper unchanged: its hardcoded previous version and
   candidate would deploy the earlier notification release.
5. Stage while preserving all current modules, bindings, secrets, settings and
   assets. Apply only `parking_batch.sql` to the existing D1 database before
   activation; verify table/index schema and unchanged existing row counts.
6. Activate only after preflight still matches. Redownload and compare all
   module bytes/settings. Verify unauthorized snapshot writes and AI reads are
   still 401; then parent can verify authorized device uploads/readback.
7. Rollback switches to the exact prior Worker version, leaving the additive
   table and immutable images intact. Disable new capture uploads before rollback:
   the old Worker ignores `parking` and would publish each frame as ordinary.

## Reproduction and Results

```sh
NODE=/Users/hyuklee/.local/share/rea/node-v24.21.0-darwin-arm64/bin/node
export WAYON_PARKING_BASELINE=/private/download/worker.js
export WAYON_PARKING_MODULE_DIR=/private/download
export MINIFLARE_MODULE=/Users/hyuklee/.npm/_npx/32026684e21afda6/node_modules/miniflare
"$NODE" --test parking_batch.test.mjs
"$NODE" parking_batch.mjs "$WAYON_PARKING_BASELINE" /private/new-candidate/worker.js
```

20 tests passed using real local workerd, D1 and KV with the three private
production modules. Includes a whole-second 6-approach + 3-parked group plus
ordinary first-parked driver, concurrent retries/conflicts, auth/revocation,
forged device scope, fresh/stale boundaries, all bounds, 100-row list, 2 MiB
input, incomplete capacity/expiry, old snapshot/byte preservation and an
injected D1 transaction failure. Test Worker outbound requests are forbidden;
Miniflare's automatic `cf.json` download is disabled. No remote/runtime/device
deployment or end-to-end collector behavior is claimed.
