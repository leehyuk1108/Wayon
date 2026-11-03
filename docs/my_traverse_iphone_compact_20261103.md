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

Final PWA version: `7eae6173-d7bf-4f40-8d04-6f29397a078f`.
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
