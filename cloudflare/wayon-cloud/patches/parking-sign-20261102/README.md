# Parking sign recognition push (2026-11-02)

Offline, hash-pinned patch only. No deployment, credential provisioning, commit,
parent Worker/schema edit, server edit, or handoff-log write is included.

## Pins and usage

- Baseline Worker SHA256: `74402c332a51ffde4c00fdd99fc53e7a04830764f082d2a91e37b3a4096232cf`
- Candidate Worker SHA256: `0c24e5e60b85663712389c33974435742fe4183fe417744ab7ea01a183f87ed5`
- Migration: `schema.sql`, additive `parking_sign_notifications` table only.
- `patch.mjs` refuses an unknown/repeated baseline and an existing output path.
  `unpatch(candidate)` restores the exact pinned baseline for offline verification.
- The parent owns live baseline revalidation, migration, secrets, deployment and
  rollback. Preserve all other modules and bindings. Do not reset/delete claim
  rows on rollback; an uncertain delivery must never become a fresh send.

```sh
NODE=/Users/hyuklee/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node
PATCH=/Users/hyuklee/Documents/sunnypilot/cloudflare/wayon-cloud/patches/parking-sign-20261102
BASE=/Users/hyuklee/Documents/parking-vision-review-20261102/cloud-candidate/worker.js
"$NODE" "$PATCH/patch.mjs" "$BASE" /absolute/new/private/candidate-worker.js
"$NODE" --test "$PATCH/notice.test.mjs"
"$NODE" "$PATCH/runtime.mjs"
```

Test overrides: `WAYON_PARKING_SIGN_BASELINE`, `WAYON_PARKING_SIGN_MODULE_DIR`,
`MINIFLARE_MODULE`, `WAYON_PARKING_PYTHON`. Defaults use the supplied baseline,
its two companion modules, installed Miniflare and `parking/venv/bin/python`.
Python fixture imports run with bytecode writes disabled.

## HTTP contract

`POST /api/parking/recognition`, `Content-Type: application/json`,
`Authorization: Bearer <WAYON_PARKING_NOTIFY_TOKEN>`.

The dedicated handler runs before generic device-key authentication. Only the
nonempty dedicated secret is accepted; it cannot equal `WAYON_AI_READ_TOKEN`.
Scope is exactly `WAYON_AI_DEVICE_ID || WAYON_LEGACY_FIREBASE_DEVICE_ID`, matching
the existing AI scope fallback. The selected ID must be valid and registered
with `revoked_at IS NULL`. Body deviceId must match. Caller headers/query never
select scope. The AI read token remains GET-only and cannot POST this endpoint.

Exact payload keys (unknown keys, including caller title/body, are rejected):

```json
{
  "eventId": "parking-example",
  "jobId": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "deviceId": "registered-owner-device",
  "parkedAt": "2026-11-02T02:00:00.000000+00:00",
  "completedAt": "2026-11-02T02:01:00.123456+00:00",
  "readings": [{
    "kind": "pillar",
    "text": "B12",
    "status": "readable",
    "evidence": [
      {"frameIndex": 0, "box": [0.1, 0.2, 0.4, 0.8], "capturedAt": "2026-11-02T01:59:59Z", "sha256": "0000000000000000000000000000000000000000000000000000000000000000", "phase": "approach"},
      {"frameIndex": 1, "box": [0.1, 0.2, 0.4, 0.8], "capturedAt": "2026-11-02T02:00:00Z", "sha256": "1111111111111111111111111111111111111111111111111111111111111111", "phase": "parked"}
    ]
  }],
  "phaseHint": "mixed",
  "test": false
}
```

- Body maximum **32768 UTF-8 bytes**, agreed with the server after the initial
  16KiB request. Stream byte counting applies even to missing/forged lengths.
- eventId: `[A-Za-z0-9_-]{1,128}`; jobId: exactly 32 hex digits (canonical lowercase).
- Required boolean test. Readings: 1..16, kind floor/zone/pillar/bay only,
  status readable only, trimmed nonempty text <=32 Unicode code points.
  Controls, format/bidi, surrogate, line/paragraph separator characters reject.
- Evidence: exact five keys shown, 2..12 unique integer frameIndex values 0..11;
  four finite normalized numbers with `0 <= x1 < x2 <= 1`, `0 <= y1 < y2 <= 1`.
- SHA256 is lowercase 64 hex. Each reading needs at least two distinct source
  hashes with a distinct-hash pair separated by >=500000 microseconds. Reusing a
  frameIndex across readings requires identical hash/time/phase (boxes may differ).
- Source time: parkedAt-120s <= capturedAt <= min(parkedAt+60s, completedAt).
  Approach sources cannot be later than parkedAt. phaseHint exactly equals the
  cited phase union: approach, parked or mixed.
- Time strings require ISO calendar date/time plus Z or explicit offset;
  1..6 fractional digits supported. Parked age <=30min, completed age <=10min,
  future <=2min, completed >= parked. Microsecond comparisons preserve boundaries.

Success is always HTTP 202, with the following stable server ACK fields:

```json
{"ok":true,"claimed":true,"status":"accepted","eventId":"parking-example","accepted":true,"duplicate":false,"parkingEventId":"parking-example","jobId":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","test":false}
```

An identical retry returns status `duplicate`, duplicate=true, claimed=true.
Conflicting valid retry content returns HTTP 409 `parking_event_conflict`.
Malformed/stale/unproven input returns 400; auth 401; wrong method 405; oversized
body 413; wrong media type 415; unavailable claim storage/context 503.

## Claim and push semantics

`PRIMARY KEY(device_id,event_id,test)` separates test/real claims. Canonical
JSON and SHA256 are persisted atomically before `ctx.waitUntil` schedules FCM.
Canonicalization fixes property order, sorts evidence indices, normalizes job
hex and UTC timestamps without discarding microseconds. Reading order/text and
all evidence remain fingerprinted; retries must preserve semantic payload.

Once claimed, no resend is allowed even after FCM timeout, rejection, no
subscriptions, partial delivery, or receipt-update failure. Receipt values:
`-1` claimed/unresolved; `-2` failed/uncertain; `0` no recipients; positive sent
count. `finished_at` records completed receipt handling, not phone delivery.
202 means durable claim, **not** FCM acceptance or phone receipt.

FCM data strings: type=`wayon_parking_sign`, parkingEventId, jobId, deviceId,
occurredAt=`new Date(completedAtMs).toISOString()`, notificationTitle,
notificationBody, test=`true`/`false`. No raw images or evidence go to FCM.
Title is fixed Korean parking-surroundings-sign recognition; tests explicitly
append the Korean word for test. Body lists up to three readable signs, notes
any remaining count, always warns that AI transcription is not an exact parking
location, and warns about approach evidence for approach/mixed phases.
Android channel=`wayon_parking_sign_alerts`, tag=parkingEventId. Existing shutdown,
door-lock, impact and parking-unlocked message behavior is preserved.

## Verification and limits

27 actual Miniflare/workerd + D1 tests pass, including concurrent equal/conflicting
claims, held/failed/ambiguous FCM, failed D1 writes, strict validation, spoofed
auth, legacy scope fallback, additive migration and existing notification types.
The contract test calls the real server `wire_fixture()` -> `make_payload()` ->
`service.validate_result()` with generated PNG sources, dispatches its exact
JSON through workerd, then passes both real ACKs to Python `ParkingNotifier.send`.
Both are acknowledged. External FCM and OAuth are intercepted, not contacted.

This proves the isolated contract and at-most-once claim behavior, not OCR
accuracy, live credentials, production D1 migration or physical phone display.
The secret-authorized server supplies provenance; this endpoint does not fetch
the original images to independently establish their contents.
