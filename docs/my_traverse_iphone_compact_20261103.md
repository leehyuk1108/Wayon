# My Traverse Compact iPhone Layout

## Scope

Web-only CSS and the existing isolated layout checks on `codex/my-traverse-source`.
Keep the original labels, icons, navigation, account state, notification
subscriptions and command guards. Do not edit Android Next, the Wayon backend,
Comma or Navdy for this presentation change.

## Layout

- Use a fixed 42px-at-default-text-size status title instead of 50--68px
  viewport-scaled type. Keep rem sizing and wrapping for text enlargement.
- Reduce the command dock from 72px to 60px, fuel values from 21px to 18px,
  and service cards to 160px wide with a 112px minimum height.
- Keep all command/navigation hit areas at least 44px. Only the visual icons,
  typography and spacing shrink; no command handler or disabled state changes.
- Let the map absorb remaining height. Short screens retain scroll access.
- Use `100vh` for installed standalone windows, retaining `100dvh` for normal
  browser tabs. Installed WebKit can report a viewport excluding the status bar:
  https://bugs.webkit.org/show_bug.cgi?id=254868
- The actual mirrored iPhone initially showed a separate dark strip below the
  footer. After the standalone height change, the new compact title loaded and
  the footer background reached the display edge. The user then requested less
  remaining space inside the footer too: use a 44px navigation target with
  bottom padding `max(8px, safe-area-inset-bottom - 14px)` (20px for a 34px inset).
  This leaves home-indicator clearance without a second large bottom band.

## Verification

- `npm test`: 337 passed, zero skips. Existing authentication, command safety,
  bridge and real Chromium regressions remain unchanged.
- `npm run check:layout`: WebKit and Chromium use synthetic vehicle data,
  local application assets and public Seoul City Hall map tiles. All non-GET
  requests are blocked. Assertions cover title/card/dock sizes, footer height
  and bottom alignment, 44px targets, text enlargement, short keyboards,
  navigation, finder controls, landscape insets and scroll reachability.
- A new 402x874 fixture simulates the short `dvh` value and explicitly enables
  the real standalone CSS rule. It is not an iOS simulator or a physical shell;
  actual iPhone Mirroring is a separate check.
- Android Next HTML SHA-256 remains
  `d26971b235a51fa52aaeda6e1c7e92e7dbb61c0758c8189ab4c49aafebf7e6c5`.
- Production verification must compare CSS/JS bytes, preserve Worker bindings,
  and account for the existing per-response CSP nonce in HTML. Do not deploy
  the unrelated dirty Wayon worker or issue real vehicle commands for UI tests.

## Deployment

Initial compact PWA version: `7eae6173-d7bf-4f40-8d04-6f29397a078f`.
Only `/pwa.css` changed among production assets. Both browser engines pass all
ten cases (20 total), with zero mutation requests, after the final footer change.
CSS/JS bytes and nonce-normalized HTML match the local build; Worker settings
and bindings are unchanged. Wayon remains version
`6ba010db-cb2e-419d-9fab-79369da18d6b`, with its prior worker hash unchanged.

Physical mirroring confirmed the smaller title/cards and the removal of the
separate bottom strip after the first deployment. The final, tighter footer
still needs a cold reload on the phone: the mirroring app-switcher dismissal
gesture did not consistently close the PWA, so the user was asked to reopen it.
Do not describe the desktop standalone fixture as proof of that final physical
footer spacing, or claim physical keyboard/rotation checks that were not run.

## Follow-up: Safe Insets and Taps

The user reopened the compact version and requested slightly higher bottom tabs,
a lower status badge/settings button, and no accidental double-tap page zoom.

- Restore the full bottom safe-area inset, keeping the 44px navigation targets.
  On a 34px-inset iPhone, this raises the tabs by 14px versus the initial compact
  version. The background still reaches the screen edge; no fake home indicator
  is drawn. The operating system controls the real indicator's visibility.
- Move the status group from 18px to 30px below the map's top, and the settings
  target from 8px to 20px. Preserve their alignment and the single top inset.
  Keep the existing smaller title, cards, icons and command dock.
- Use `touch-action: manipulation` on the page and nested scrolling surfaces.
  This suppresses browser double-tap zoom while retaining pan/pinch gestures:
  https://webkit.org/blog/5610/more-responsive-tapping-on-ios/
  Keep the scalable viewport and the original map/photo gesture handlers. Do
  not add global touch-event cancellation or touch any vehicle-command handler.
- Extend the isolated layout checks with exact top offsets, badge/settings
  alignment, full bottom clearance, computed gesture policy, a scalable viewport,
  unchanged custom photo gestures and two synthetic taps without page scaling.
  A synthetic tap check is not a physical iPhone gesture test.
- An initial run passed 19/20 layouts; the finder check caught its existing
  transition at translateY(-6px). Wait for its opacity/transform to settle before
  measuring, rather than relaxing geometry assertions or changing the UI.

Follow-up deployment: `b6b3459c-bb7a-436c-b118-d3f9de1e59cd`, 100% active.
Only `/pwa.css` was uploaded. Production CSS/JS bytes, nonce-normalized HTML and
Worker bindings match; Wayon remains on `6ba010db-cb2e-419d-9fab-79369da18d6b`
with the same worker hash. Android source and server/bridge code are unchanged.

Final checks: 337 functional tests passed with zero skips; WebKit/Chromium passed
all 20 layout cases with zero mutation requests. The standalone WebKit screenshot
was inspected for top alignment and bottom clearance. Actual iPhone Mirroring
reconnected, but the existing app retained the old page. App-switcher gestures
did not dismiss it reliably; a user cold reopen was requested. Physical final
spacing, home-indicator visibility and double-tap/pinch behavior remain pending,
not proved by the desktop fixture.

### Physical Follow-up at 11:27 KST

After the user reopened the app, iPhone 16 Pro Mirroring showed the final layout:
the badge/settings were visibly lower, aligned and readable, and the bottom tabs
were higher with clearance below them. The settings target opened the settings
tab, and the bottom vehicle tab returned to the unchanged home screen.

Three mirrored double-click/tap sequences on the fuel label, service heading and
observation timestamp left the page scale and element positions unchanged. No
vehicle-command buttons were touched and no account/notification settings were
changed. This is real-device mirrored input, not a manual finger gesture test.
Pinch input is unavailable in this tool and remains unverified physically. The
home-indicator space is present, but its persistent visibility was not observed
in the final screenshots; do not claim the OS indicator is always visible.

No further runtime changes or deployment were needed; this follow-up only
records the physical results for the already deployed CSS.
