# Server-First Vehicle State

## Current Behavior (Version 34)

The October 29 request supersedes the phone-cache behavior described below.
Opening or resuming the app now clears the vehicle display and reads only the
authenticated, D1-only `GET /api/gmone/status`. It never displays or rewrites the
phone's `VEHICLE_SNAPSHOT_V1`; that obsolete preference is removed on startup.
No automatic direct GMOne vehicle read is started by opening the app.

The lightweight endpoint is polled independently every 30 seconds. Trip/address
feed completion and failures no longer decide whether vehicle data is ready.
Stored server data retains its observation time and account binding and is
labeled as server-stored information, not a new live observation. Unavailable,
wrong-account or invalid-time responses cannot restore a previous phone snapshot.
A transient periodic failure can retain the server response already displayed in
the current session, with its original time.

Manual home/widget refresh uses the existing server collector queue only, not
simultaneous phone and collector requests. It can still wait for the vehicle and
the collector's rate limit; that is separate from displaying stored server data.
Collector completion forces a new status GET. Explicit diagnostics and native
remote-engine safety checks retain their direct, fresh reads. No safety check is
satisfied by a cached server source string.

The status parser preserves top-level module/health/diagnostic fields without
requiring the larger `/api/json` response. Stored settings are not placed in the
editable settings form; the settings tab reads actual settings on an explicit
user entry or its read button. Automatic setup-tab navigation never starts that
transaction.

### Direct Control Buttons

Version 34 removes the secondary open/close and lock/unlock chooser. Each visible
button names the exact command it will send after the existing long press. A
server-observed locked/closed state selects unlock/open; an unlocked/open state
selects lock/close. The original observation time remains visible. This is a
display selection, not proof that the vehicle is still in that state.

Missing, partial, invalid-time, more-than-24-hour-old or implausibly future
closure observations show explicit lock/close actions with neutral, unknown
state. They never assert that the vehicle is locked or closed. Windows require
all four readings before selecting an open action. No phone snapshot is restored.

A long press captures its command at touch start. If a poll changes that command
or disables/hides the button before completion, nothing is sent. Existing native
authentication, cooldown and fresh engine/hood/driving checks remain in place.
An acknowledged action's bounded pending display is not undone by repeatedly
receiving observations older than that action; newer evidence or the existing
expiry still clears it. This also applies to the shared engine display helper,
but cannot authorize an engine command or bypass its native fresh read.

Known limitation: a still-valid server observation can disagree with a physical
change made elsewhere. The single-action home bar then shows the action for that
observation until refresh. Read the explicit command label, not the icon as a
live-state guarantee. There is no additional inverse-action chooser in v34.

### Version 34 Verification

2026-10-29, SM-F966N, wireless ADB:

- Release build, 73 Kotlin tests and 55 JavaScript tests passed. Tests exercise
  cached, unknown, partial, stale and future observations; hold-time command
  changes, early release, disabled/hidden actions and exact mock bridge dispatch.
  Older/undated acknowledgments cannot overwrite pending display before expiry.
- Claude reviewed the pinned final diff and new tests statically. No code blocker
  was found; the stale-observation action-direction limitation above remains.
  Engine display also uses the bounded optimistic helper, while native engine
  authorization and freshness rules remain unchanged.
- Installed with the existing signer and `adb install -r` (`Success`), preserving
  account/settings. Version `34 / 2.0-preview.25-direct-buttons`; local signed APK
  and installed `base.apk` SHA256 both
  `fc3e03a8198f363ff87682cd95ca5d66cf313821878d81f51a32000bc2c4c5fe`.
  The packaged HTML SHA256 matches the source exactly.
- Real cover-display screenshot shows all five command labels without overlap,
  the original vehicle observation time and server-stored label. Cold-start
  server GET took 1,116 ms; native selection 1,126 ms. The next periodic GET took
  626 ms. These are request timings, not a guaranteed first-pixel latency.
- No command or runtime-error entry appeared in the focused startup log. No
  actual engine, door, trunk, window or horn command was sent; dispatch evidence
  is mocked, not physical actuation. The phone was returned to HOME.
- One final packaging attempt failed for low Mac disk space; a bounded-worker
  retry completed successfully without deleting user files or unrelated caches.

### Version 33 Verification

2026-10-29, SM-F966N, wireless ADB:

- Release build, 73 Kotlin tests and 51 JavaScript tests passed. The real
  `switchTab` function is tested for automatic versus user settings entry.
  Claude reviewed the final batch statically; the device tests below were run
  separately.
- Installed with the existing signer and `adb install -r` (`Success`), retaining
  account/settings. Version `33 / 2.0-preview.24-server-state`; local signed APK
  and installed `base.apk` SHA256 both
  `b38fe1f710fc9015b65e00f59e93c58615691b5e312cb68998090acd04d898f1`.
- Final cold launches: server GET 2,065 / 3,501 / 2,145 ms; native selection
  2,075 / 3,509 / 2,154 ms from startup. Activity launch 283 / 234 / 273 ms is
  not a data-ready measurement. No automatic GMOne operations appeared in any
  of the three startup logs.
- Captures at 800 ms show no previously saved fuel/range. Captures started at
  4.50 seconds (completed at 4.99 / 6.08 / 5.18 seconds) show the server state
  with its original observation time and server-stored label. These bounds do
  not establish an exact first-pixel time or a fixed network latency.
- Hot resume: server GET 1,293 ms, native selection 1,303 ms. Independent
  subsequent status reads at roughly 30-second intervals took 665 / 1,897 /
  1,008 ms; no automatic direct vehicle read accompanied them.
- Explicit first settings entry then issued one settings request (`8`, `59`,
  followed by three `66` response polls). The actual settings screen changed
  from reading to `20 settings read`; no settings were saved or changed.
- Production API reads from the Mac took 482 / 615 / 552 ms, with unauthenticated
  access still rejected. No server deployment or collector cadence change was
  needed. Vehicle/engine/door/window commands were not issued.

The historical measurements below refer to v31/v32, not v33.

## Previous Flow

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
- In historical versions 31-33, cached closures did not pick a lock/unlock action
  and the choice dialog remained available. Version 34 supersedes that behavior
  as described above. Cached module data still does not populate the editable
  settings screen.
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
