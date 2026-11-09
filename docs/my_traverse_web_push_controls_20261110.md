# My Traverse Web: instant reopen, remembered controls and cloud web push (2026-11-10)

Owner request: the iPhone web app flashed the password form for about half a second on
every open, every vehicle-tab control was disabled, and web notifications did not match the
Android app. The day's extras-tab redesign from the Android assets was also published.

## Causes

- `client/pwa.js` started locked and showed the password form until `/api/session` replied.
- The web GMOne login stored only a 15-minute token and never the password, so controls
  turned off 15 minutes after each multipack sign-in. Android keeps the typed credentials
  (`GmoneAccountStore`) and authenticates for each command.
- Production `push_claims` held only the three 2026-11-02 tests, all posted from a Mac
  directly to `/api/internal/notify`. wayon-cloud's fanout posted to the same-account
  workers.dev URL with a public `fetch`, without a service binding or
  `global_fetch_strictly_public`; nothing from the cloud ever reached the web Worker.

## Changes

- Reopen: a device that logged in before (non-secret local hint) shows the app immediately
  and checks the session behind it; the form appears only when the server says the session
  is gone. First opens wait briefly without showing the form.
- Controls: the typed GMOne email/password are stored only inside that web session's
  encrypted D1 `account` value and never returned to the browser. A fresh GMOne login is
  made right before every command; a well-formed refusal erases the login without sending,
  while transport or malformed replies keep it and send nothing. Web logout, account
  sign-out, expired sessions (on session checks/logins and a daily 18:23 UTC cron) remove it.
  `account_rev` rejects a login that finishes after a sign-out. Sessions created earlier must
  sign in to GMOne once more. D1 Time Travel can still hold older row versions for its window.
- Cloud web push: `cloudflare/wayon-cloud/patches/web-push-binding-20261110` sends the same
  fanout request through the new `MY_TRAVERSE_WEB` service binding (one line); without the
  binding the original public fetch remains.

## Deployment and verification

- Codex cross-review twice: 5 findings fixed (expired-session credentials, binding comparison,
  sign-out race, malformed-reply handling, rollback ownership); the remaining request-only
  cleanup was closed with the daily cron.
- Web tests: 347 of 351 passed, 3 browser tests skipped, 1 failed only because Codex's
  uncommitted `MainActivity.kt` adds a 36th JavaScript interface (`openRssiCalibration`).
  Command runtime 69/69. wayon patch runtime 3/3 (patched active bundle in workerd).
- Production: `my-traverse-web` D1 gained `sessions.account_rev` (17 rows kept). Web Worker
  `105e5351` (previous `35dac14c`), all 11 secrets and 4 bindings unchanged, cron attached.
  wayon-cloud `51eba5be` (previous `3c8dd130`): worker.js `050963db…`, companion modules
  byte-identical, 24 bindings equal field for field plus `MY_TRAVERSE_WEB`.
- End to end: the comma sent one test impact through wayon-cloud `/api/push/test` (its device
  key stayed on the device). Android FCM: 1 notified. Web `push_claims` recorded
  `wayon_impact:…:true` at 03:36:13 KST with `{"sent":1,"failed":0}`.
- Not verified: the iPhone actually displaying it, the iPhone first paint, physical vehicle
  commands from the web, and real GMOne refusal/password-change responses.
