# Cache-First Vehicle State

## Flow

Version 31 separates first paint from the slow GMOne read. Version 32 also clears
the saved-info label when a direct reply replaces the cached display:

1. Show the last sanitized, account/key-bound phone snapshot without networking.
2. Fetch authenticated `GET /api/gmone/status` independently of `/api/json`.
   This endpoint only reads D1; it does not wait for Firebase, trips or geocoding.
3. Read GMOne in the background. A basic reply can immediately replace the
   display; richer module details follow without blocking the page.
4. Upload both newly observed basic and full replies through one serialized,
   conflated queue. Navigation away after a basic reply does not lose that queued
   update. Server ordering prevents a late basic reply from erasing a full reply.

This does not make a sleeping vehicle continuously report or add a new polling
service. Existing foreground refresh, hourly active-refresh and passive-sync
cadence remain unchanged. The server stores new observations when they arrive.
The first launch without a usable account-specific snapshot still needs a direct
read. Failed uploads retry on a later observation, not through an unbounded queue.

## Provenance And Controls

- Cached data is explicitly labeled `SAVED STATUS` / saved information, with its
  original time. A snapshot expires after seven days and is never retimestamped
  to the current time. Missing or implausible time is refused, not invented.
- Account identity is HMAC-SHA256 of normalized account plus the Cloud key.
  Switching account/key clears local cache, invalidates old response generations
  and prevents late callbacks or queued writes from belonging to the new account.
  Logged-out clients reject scoped account snapshots.
- Cached closures do not pick a lock/unlock/open/close action. The existing choice
  dialog remains available immediately. Cached module data does not populate the
  editable settings screen.
- Engine actions still require the existing native fresh-state, driving, hood,
  module and remote-start rules. Only an observed direct response in this process
  can use the existing 30-second shortcut. A server `source` string is not proof
  of freshness. No command is issued automatically by a snapshot refresh.
- Cached display does not renew DTC observations, widget or Wear freshness.
- The queue has at most one active and one latest pending upload, bounded body
  size and timeouts, no redirects, and no persisted credentials in the queue.

## Server Dependency

Deploy `cloudflare/wayon-cloud/patches/fast-vehicle-state-20261028` before the APK.
It is pinned to the existing production bundle, not the unrelated dirty source
tree. It preserves per-device authentication, bindings, companion modules and
assets. Same-epoch full snapshots are protected by atomic SQLite ordering;
Android uploads never acknowledge the collector's separate refresh queue.

## Verification

2026-10-28:

- Release build and 69 Kotlin tests passed, including scope/age/sanitization,
  exact GET parsing, direct-observation provenance and startup ordering.
- 46 JavaScript tests passed, including saved display, immediate unknown-state
  choices, long-press intent, engine guards and existing panorama/gallery flows.
- 59 server mock/SQLite tests and 98 actual workerd/local-D1 assertions passed,
  including 40 concurrent submissions and invalid-key/header POST rejection.
- Claude bridge reviewed the final app/server/deployment batch statically.
  This is independent review, not runtime proof.
- Prior v30 actual phone observation: first direct-ready at 10,638 ms after the
  refresh began. The production authenticated row was dated September 9; direct
  phone reads had not been republished into that row.
- Production Worker version `aedfed58-9bc0-4f4e-807f-c75c96588dae`, SHA256
  `630b8737898c7788187ce22d39c0d0c8ae9230d22f9b0ac6ab3c788e176d9733`:
  exact three modules and 22 bindings preserved. Unauthenticated GET/POST reject
  with 401. Actual authenticated D1 GET returned 200/no-store in 745, 201 and
  324 ms. These are API timings, not phone first-paint measurements.
- Signed v31 APK SHA256:
  `982ba6a453d555f3b1771ece9db9b03c243e8a891421cea23febddb12762c430`.
  The signer matches v30, so the intended install is `adb install -r`, not a data
  reset or uninstall. The final APK was built after the reviewed corrections.

## Phone Verification

2026-10-28, SM-F966N, Android 17:

- Installed v31 and final v32 with `adb install -r`; both returned `Success`.
  Existing account/settings remained usable. Final version is
  `32 / 2.0-preview.23-fast-state`, installed APK SHA256:
  `b5357c27ea60159311fbf6c9828479e6f7ec99db2ed0b54e407899bb3532518a`.
  The same hash was read back over USB and wireless ADB; the v30 signer is kept.
- The first v31 direct basic/full replies produced two actual server ACKs. An
  authenticated production GET then returned the new account-scoped Android row,
  replacing the September row. Final v32 observation also produced two ACKs;
  GET returned `updatedAt=2026-10-28T12:07:32.000Z`,
  `receivedAt=2026-10-28T12:07:34.223Z`, source `gmone-direct-android`.
- Three final-v32 cold launches selected local saved state in 7, 8 and 7 ms
  after the native refresh began. Screen captures started 1.50 seconds after
  launch and finished at 1.91, 1.77 and 1.76 seconds; all visibly contained saved
  fuel/range and the controls. These are capture bounds, not exact first-pixel
  times. Activity launch times alone (451, 388, 342 ms) are not data-ready times.
- Three earlier v31 cold observations reached direct basic data in 3.734,
  4.810 and 3.714 seconds. Repeated rapid launches later received GMOne's
  "another request is being processed" error. Saved data remained visible;
  this does not prove live vehicle requests always succeed or become faster.
- After spacing requests and reconnecting over wireless ADB, final v32 selected
  cache in 5 ms and direct basic/full in 11.067/11.700 seconds. The actual screen
  showed the new values/time without the leftover saved-info label. The slow
  remote read now runs behind the already-visible saved state.
- The label regression was reproduced by a failing test before the seven-line
  fix. Final release build, 69 Kotlin tests and 46 JavaScript tests passed.
  Claude reviewed the final text diff, with no blocking finding. No new server
  deployment was required for v32.

No remote engine, lock, window or diagnostic-clear command was issued in testing.
Control dispatch and safety rules were covered by tests, not physical actuation.
No Comma, model, vehicle-control or Navdy source was changed for this feature.
