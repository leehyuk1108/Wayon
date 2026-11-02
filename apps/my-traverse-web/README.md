# My Traverse Web

An authenticated, home-screen-installable companion to My Traverse Next. The
build reads the Android assets without editing them; the web adapter provides
server-backed vehicle state, maps, trip history, gallery, live video and Web Push.

Production: https://my-traverse-web.hyuklee.workers.dev

## Build and Test

Use Node 24 and run `npm ci`, then `npm test`. The pretest script rebuilds both
assets and the Worker, so workerd integration tests cannot use an older bundle.
For the optional real-browser XSS regression test, set
`TRAVERSE_PLAYWRIGHT_MODULE` to an installed Playwright module and
`TRAVERSE_BROWSER_EXECUTABLE` to Chrome. A skipped browser test is not a pass.

`npm run dev` starts local Wrangler. Production uses the ignored
`wrangler.local.json`; do not commit deployment credentials, D1 identifiers,
session cookies or captured vehicle data. Apply `server/schema.sql` to a separate
D1 database. Existing installations also need the `push_claims.result` column.

## Boundaries

- Android UI assets and launcher artwork are the source of truth. Icons are
  generated from `mipmap-xxxhdpi/ic_launcher.webp` at 180, 192 and 512 pixels.
  Versioned Apple touch, manifest and notification URLs avoid stale icon caches.
- Vehicle data comes from the existing Wayon service binding, not phone storage.
  Original observation timestamps and stale/missing states remain meaningful.
- Login uses an HttpOnly, Secure, SameSite cookie. Mutations require an exact
  origin and CSRF token. No privileged Wayon token is sent to the browser.
- Command support is deliberately off unless `COMMANDS_ENABLED=1` and verified
  `GMONE_UUID_HASH` and `GMONE_VEHICLE_HASH` pins are present. Both account and
  fixed Comma device identity are checked; email alone is insufficient.
- Commands require a separate 15-minute GMOne account session. The explicit
  15-command allowlist covers locks, remote start/stop, windows, trunk, lights,
  panic and sunroof. Native Bluetooth, module writes and timed ventilation are
  not implemented in the PWA. GMOne passwords are not retained for auto-login.
- Foreground restoration and periodic session checks refresh command grants
  without restarting live video. Expired account grants do not disable ordinary
  vehicle viewing; an expired web login locks the web app.
- Source tests use mock commands only. Server acceptance is not evidence that a
  vehicle physically completed a command. Unknown results are never replayed.
- Service-worker caching is limited to icons, never vehicle data or API replies.

## Push and Deployment

The new Worker needs `LOGIN_CODE_HASH`, `ACCOUNT_ENCRYPTION_KEY`,
`ACCOUNT_FINGERPRINT`, `DEVICE_ID`, `WAYON_DEVICE_KEY`, `VAPID_PUBLIC_KEY`,
`VAPID_PRIVATE_KEY` and `MY_TRAVERSE_WEB_PUSH_TOKEN` secrets. Pin actual owner
identity separately before enabling commands. Never put secret values here.

The existing Wayon Worker uses the hash-pinned patch under
`cloudflare/wayon-cloud/patches/web-push-20261102`. Do not deploy unrelated local
changes in the main Wayon Worker. Existing Android FCM behavior remains separate
from the bounded Web Push fanout.

Web Push uses encrypted VAPID requests with `redirect: 'manual'`; workerd rejects
`redirect: 'error'` before transmission. Only provider 404/410 removes a
subscription. Other failures remain observable without deleting subscriptions.

On iPhone, add the site to the Home Screen, open it there, log in and enable
notifications. Existing home-screen artwork may require removal and re-addition
after an icon change. Recheck notification permission afterward.

See `docs/my_traverse_iphone_pwa_20261102.md` for actual validation and limits.
The follow-up account/control verification is recorded in
`docs/my_traverse_web_controls_20261102.md`.
