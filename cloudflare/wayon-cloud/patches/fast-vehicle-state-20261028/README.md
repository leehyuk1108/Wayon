# Fast Vehicle State Patch

Local sidecar only. No cloud API calls, credentials, deployment, phone commands,
dependency installation, or handoff-log writes were performed by this task.
The dirty `cloudflare/wayon-cloud/src/worker.js` and other patches are untouched.

## Pinned Artifact

- Input SHA256: `67eccbf0151a79e428244b0e68bc9d800e79215c87d11d64e0b75442188633e8`
- Output SHA256: `630b8737898c7788187ce22d39c0d0c8ae9230d22f9b0ac6ab3c788e176d9733`
- Private input: `/Users/hyuklee/Documents/my-traverse-carrot-20261028/cloud-relay-candidate/worker.js`
- Private output: `/Users/hyuklee/Documents/my-traverse-carrot-20261028/cloud-fast-state-candidate/worker.js`

`patch.mjs` checks the entire input hash and exact single-occurrence anchors. It
replaces only `handleGmoneStatus`, inserts its narrowly scoped helpers, adds
`clientScope`/malformed-row handling to `latestGmoneStatus`, and inserts the GET
route and its D1-only binding check. It checks the resulting output hash too.
Unknown input, reapplication and overwriting an existing output all fail closed.
No production bundle, companion modules, settings or secrets belong in Git.
The generated output has mode 0600 and is outside the repository.

## API Contract

### GET /api/gmone/status

Uses the exact production `authenticateDeviceKey`: registered, non-revoked
device key hash lookup in D1. Incoming internal auth headers are stripped by the
unchanged router before authentication. Query/header/body `deviceId` hints never
select a different device. Collector, old view/upload and AI tokens do not gain
read access. There is no new provisioning or access grant.

The route performs only two D1 reads: authentication and `latestGmoneStatus`.
It does not fetch Firebase, call a remote server, read KV, merge sources, start a
collector refresh, or write last-seen timestamps. Even the SNAPSHOTS binding is
unnecessary for this GET. Other routes keep their existing binding requirement.

HTTP 200, with `Cache-Control: no-store`:

```json
{
  "vehicleStatus": {
    "ok": true,
    "source": "gmone-direct-android",
    "clientScope": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "updatedAt": "2026-10-28T11:00:00.000Z",
    "collectedAt": "2026-10-28T11:00:01.000Z",
    "receivedAt": "2026-10-28T11:00:02.000Z",
    "ageSeconds": 1,
    "stale": false,
    "data": {"fuel": "63"},
    "health": {},
    "module": {},
    "diagnostic": {}
  }
}
```

`clientScope` is present only when the stored value is valid 64hex, normalized
to lowercase. No row, unparseable JSON or non-object/array `status` produces
`{"vehicleStatus":null}`. Invalid credentials return 401; D1 failures return a
redacted 503 `gmone_status_unavailable`, including authentication lookup failures.
These responses inherit the existing no-store JSON headers.

### POST /api/gmone/status

Existing device-key authentication and the existing collector-token route are
preserved. Collector identity stays the configured legacy device; device identity
stays the authenticated device. The body cannot override either identity.

Android body:

```json
{
  "schemaVersion": "wayon-gmone-v1",
  "source": "gmone-direct-android",
  "clientScope": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "collectedAt": "2026-10-28T11:00:01.000Z",
  "vehicleUpdatedAt": "2026-10-28T11:00:00.000Z",
  "status": {"fuel": "63"}
}
```

- `status` must be a non-null, non-array, nonempty object after the unchanged
  recursive production secret/identifier sanitizer. Root `deviceId` is removed.
  Collector `health`, `module`, `diagnostic`, `vehicle` and other safe fields keep
  their existing payload shape; no new database columns or migrations are needed.
- Optional `clientScope`, when present, must be a string of exactly 64 hex digits.
  Null, empty, nonhex and other types fail with 400 `invalid_client_scope`.
  The parent app computes HMAC-SHA256(cloudKey, `gmone-acct-v1:` + normalizedEmail).
  This server treats it as opaque provenance, not credentials or authorization.
  No raw email/password is required or sent. Unscoped collectors remain supported.
- `collectedAt` must be an explicit ISO date-time with timezone, no older than
  24 hours and no more than 120 seconds ahead of server receipt. `vehicleUpdatedAt`
  must be an explicit ISO date-time at/after 2000-01-01 and no more than 120 seconds
  ahead of either collection or server receipt. Vehicle state itself can be old.
  Android must provide actual vehicle time; legacy collectors may omit it or send
  null. Invalid time is rejected, never silently replaced with the current time.
- ISO offsets through +/-14:00 and 1-9 fractional digits are accepted; invalid
  calendar rollovers, timezone-free dates, epoch numbers and leap seconds are
  rejected. Storage normalizes UTC at millisecond precision. Python collector
  microsecond `+00:00` timestamps remain accepted.
- Source must be a nonblank string of at most 64 characters. Missing source keeps
  the existing status-source/`gmone-direct` fallback.
- The raw stream is limited to 262144 bytes **before JSON parsing**, regardless of
  missing/false Content-Length or later secret stripping. Over-limit bodies are
  cancelled with 413. Invalid UTF-8/JSON/read errors return 400. Object traversal
  is limited to 4096 nodes and depth 32; prototype-manipulation keys are rejected.

### Atomic Ordering and ACK

The single `INSERT ... ON CONFLICT(id) DO UPDATE ... WHERE` compares existing and
incoming rows inside SQLite/D1. There is no snapshot pre-read and no read/write
race. Known vehicle timestamps outrank unknown legacy timestamps; unknown cannot
replace known. Among known snapshots, actual vehicle epoch wins regardless of
upload receipt order. Among unknown legacy snapshots, collection time orders them.

At the same epoch, the candidate must contain every existing non-null/nonempty
status leaf path. False and zero are real values. A strictly richer superset may
replace basic even if its collection time is earlier. Equal coverage requires
an equal/newer collection time. A subset or incomparable partial snapshot is
rejected even if received later. Consequently full Android `gmone_details.module`
survives delayed basic uploads. A genuinely newer epoch can replace a richer old
epoch; old fields are never merged into a new state.

Success retains `{"ok":true,"deviceId":...,"collectedAt":...,"receivedAt":...}`.
A rejected write returns **409**
`{"ok":false,"stored":false,"error":"snapshot_not_newer"}` and does not ACK.
Missing/failed/unexpected D1 change metadata returns 503 without ACK.

Only an accepted write with the **collector token** and a **non-Android source**
may execute the original refresh completion condition `requested_at <= collectedAt`.
Android writes never ACK the collector queue, including when accidentally sent
with a collector token. A device-key caller cannot gain ACK permission by claiming
collector source. DB/ACK failures report 503 without exposing error details.
The row may already be saved if the subsequent ACK fails: these two operations
are intentionally not represented as an all-or-nothing transaction.

## Reproduce

Use an existing Node 24 runtime with built-in `node:sqlite`. No installs needed.
Run from this patch directory. Substitute private paths as appropriate.

```sh
export WAYON_FAST_STATE_BASELINE=/private/cloud-relay-candidate/worker.js
export WAYON_FAST_STATE_CANDIDATE=/private/cloud-fast-state-candidate/worker.js
node patch.mjs "$WAYON_FAST_STATE_BASELINE" "$WAYON_FAST_STATE_CANDIDATE"
node --test status.test.mjs
MINIFLARE_MODULE=/existing/node_modules/miniflare node runtime.mjs
```

The mock/SQLite suite constructs the candidate in memory and can run without an
output file. If `WAYON_FAST_STATE_CANDIDATE` is set, its exact bytes are compared.
The runtime uses the same in-memory hash-pinned candidate. Only the two unrelated
private companion-module imports are replaced by throwing test stubs; production
router, credential hashing/authentication, sanitizer, handler and SQL execute.
Remote fetch is an explicit throwing trap. All credentials/data are synthetic.

## Verified and Limits

2026-10-28: **59/59** Node tests pass, including baseline defect reproductions,
mock write/ACK/stream/auth failures, real SQLite ordering and collector isolation.
**98 assertions** pass in actual workerd + local D1, including 40 concurrent
uploads, same-epoch richness, cross-device/header overrides, revocation, raw-size
limits, scope round-trip, collector ACK/rejected-write behavior and GET without KV.
Versions: Node 24.19.0, SQLite 3.53.3, Miniflare 5.20260921.0-alpha,
workerd 1.20260921.1; compatibility date `2026-05-14`.

This is not deployed D1, a production latency measurement, or a physical vehicle
test. No UI/vehicle control commands were issued. The parent's observed v30 first
ready time of 10638ms is not a measured improvement from this candidate.

The store remains one latest row per **device**, not one row per account. The app
must reject mismatched/absent scopes for account-specific cache reuse. The server
does not validate the HMAC against an email, and does not merge account snapshots.
Existing `/api/json` Firebase merging is unchanged: use this standalone GET for
the isolated D1 cache path. `source=gmone-direct-android` and even `stale=false`
mean stored provenance, **not a fresh direct observation or engine-command
permission**. The app must tag loaded cache as `cached=true` and require its
independent fresh command gate. Existing staleness is based on collection age
(24 hours), not the age of the vehicle's last actual update.

Richness is a conservative status-leaf coverage rule, not a semantic completeness
classifier. Same-path conflicting values use collection order; ancillary top-level
collector diagnostics are carried from the accepted envelope, not merged or used
to rank Android basic/full status. Submillisecond timestamp differences collapse
to milliseconds. No production load, geo-replica behavior, clock-skew calibration,
or end-to-end Android cold-start benchmark was performed here. Parent owns final
review, private companion-module/binding preservation and any deployment.
