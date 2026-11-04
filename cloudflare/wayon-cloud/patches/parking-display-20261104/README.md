# Parking Display KV Patch

Source-only, not deployed. Never apply the dirty repository `src/worker.js`.
`patch.mjs` accepts only the exact active baseline and the two pinned companion
modules. It adds two routes and this fragment; reversal restores every original
byte, including recognition, auth, notifications and Server API helpers.

- Baseline SHA256: `04b38059cbc64ad95609c0ba31a8073810d697cf0f6e44aa2cad92cdb66dbc7b`
- Candidate SHA256: `5d4724e39018dd23e26ad52ba458da7d1cd469307e96fb99756cb38da9539c20`
- Fragment SHA256: `1f9b59bc9c47b43a84c7cf4f6cb6573d4931bce672cd0f026cbfd610e9984d79`

## Contract

- POST `/api/parking/display` uses only `WAYON_PARKING_NOTIFY_TOKEN`, rejects a
  collision with the AI read token, and binds the owner to `WAYON_AI_DEVICE_ID`
  or its existing legacy fallback. One active-device D1 lookup; no D1 writes.
- GET `/api/parking/latest` remains behind existing device-key authentication
  and request scoping. AI/notify tokens cannot read. Query/header owner spoofing
  cannot change the key. PWA permits only this GET using its existing session.
- Storage is the whole allowlisted JSON object at `parking-display-v1:<owner>`
  in existing `SNAPSHOTS`; TTL is 604800 seconds (seven days). Missing key returns
  `{ok:true,observation:null}`. Stored output adds `ok:true` on GET. All replies
  use `no-store`; no notification, Server API call, network fallback or polling.
- Required envelope: `schemaVersion`, exact `deviceId`, ISO `generatedAt`, and
  `observation` (null or `jobId,eventId,parkedAt,status,result`). Result may be null;
  otherwise only `analysis,frames,inspection` are exposed. Unknown fields,
  including publisher health metadata, URLs and raw images, are not forwarded.
- Input body is capped at 196608 actual UTF-8 bytes, with JSON media/encoding,
  declared length and fatal UTF-8 validation; operations have a five-second
  deadline. Stored JSON is size-checked and validated again before returning.
- Limits: baseline readings 16; inspection readings 32; surroundings 3; frames
  12; alternatives 4; evidence 1-12 unique in-range frame indices and finite,
  ordered normalized boxes. Readable readings/environment need two frames.
  Text limits are 32 code points per reading/alternative and 96 per environment
  label. Control, format, surrogate and line/paragraph separator characters
  reject. Ordinary markup remains literal text; the app renders `textContent`.
- Inspection version/status/confidence and environment enums are allowlisted;
  exact-space/human-verification claims must be false. Coverage counts are
  optional integers 0-96 and never imply complete scene coverage. Frame phase
  is preserved only when explicitly present. No coordinates or percentages.
- Snapshot/replay job prefixes fail the production job ID rule. Recursive
  test/simulation/synthetic/dry-run flag and provenance checks reject marked
  records even inside metadata that would otherwise be stripped. Real sign
  text is not interpreted as a test flag.
- Auth failure is 401, wrong method 405; inherited OPTIONS is unchanged.
  Schema, ordering, storage and timeout failures return only generic 503
  (`parking_display_unavailable` or `parking_latest_unavailable`). POST success
  is exactly `{ok:true,stored:true}`. Private errors are never returned/logged.

## Ordering And Limits

`generatedAt` cannot regress. Equal generation requires the same allowlisted
object and refreshes TTL, so persistent timestamps older than seven days remain
valid on unchanged daily refresh. There is no age-based rejection. When both
observations exist, `parkedAt` cannot regress and a reused job/event identity
cannot change its parking time. Newer failed/no-result records and newer null
observations replace the old object, never merge with an old success. Capture
and parking timestamps remain unchanged for aged-clue UI presentation.

KV is eventually consistent and offers no atomic compare-and-swap. Read/check/
write rejects stale records visible to this request, but cannot guarantee
ordering across concurrent writers or stale replicas. A null observation also
removes the previous parking-time watermark. Use one serialized publisher with
persistent content generation, minimum 30-second spacing, backoff and a daily
unchanged refresh. These publisher controls are outside this patch. An already
issued KV write may complete after a timeout response; retry the same content.
Seven-day TTL is a retention mechanism, not a publisher health guarantee.

## Verification Receipt

Offline only, 2026-11-04:

```sh
node --test cloudflare/wayon-cloud/patches/parking-display-20261104/*.test.mjs apps/my-traverse-web/test/parking.test.mjs
```

25 tests passed; zero failed/skipped; 1.6 seconds. Includes native local workerd
with actual D1/KV, read-only D1 triggers, no outbound calls, both auth routes,
owner spoofing, TTL, stale/latest-failed replacement, malformed/oversized input,
slow operations, unchanged daily refresh, PWA allowlist, byte-exact rollback
and unchanged companion modules. No production service/device access.

Private candidate JSON validated offline without exposing identifiers/text:
completed observation; two baseline readings; completed inspection with six
readings and one environment item; three frames. No production deployment or
live consistency/latency claim is made. Existing dirty `src/worker.js` remained
SHA256 `5298c38f8fcf2009b6165f442cf4c1814cb1eacb61257f0c79d3b5bf8bf5799a`.
