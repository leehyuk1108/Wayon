# My Traverse iPhone Web Layout

## Scope

Base: `2ab215c86664058298a63713a37abd2edf29231c`,
`codex/my-traverse-source`. Only `apps/my-traverse-web` presentation, build,
verification and this document change. The Android Next source, server, bridge,
authentication, command guards, Comma, Navdy and phone APK remain unchanged.

## Changes

- Load web overrides after the native stylesheet. Remove the dead body safe-top
  rule while moving the stylesheet, so the top inset still has exactly one owner.
- Use a dynamic viewport and flexible map height. The service rail ends 12 pixels
  above navigation when content fits; short screens scroll instead of clipping.
- Keep the original dark icon-led layout. Make service titles/descriptions more
  legible, allow wrapping, maintain small-screen alignment and right-aligned fuel.
- Accommodate landscape notches once, retain bottom home-indicator space, and
  keep finder controls inside safe margins. Clip the outer finder map instead of
  permitting its oversized tiles to programmatically scroll the controls.
- Enlarge sunroof targets to 44 pixels and add accessible names, keyboard
  activation and current-page state to existing navigation handlers.
- Permit browser zoom and text selection in inputs; use 16-pixel settings inputs
  and a scrollable login form for short viewports. No command handler changes.

## Independent Review

Claude bridge conversation: `My Traverse iPhone 디자인 검토`, session
`8aa7ce62-e672-4ff4-a9d5-437fad1f924f`.
Three read-only rounds reviewed source, exact patches and synthetic-data images.
Claude identified stylesheet order, finder specificity, safe-area assumptions,
small-screen 4-pixel misalignment and a double landscape inset. The latter two
were corrected and re-reviewed with no new serious source concern.
Claude did not execute a simulator or tests; Codex performed the runtime checks.

## Verification

- Final `npm test`: 333 passed, zero skipped, including real Chromium renderer
  tests and workerd/D1 authentication/command contract regressions.
- `npm run check:layout`: WebKit 27.2 and Chromium, nine viewport sizes each:
  320x568, 375x667, 390x844, 393x852, 430x932, 440x956, 844x390, 667x375,
  1280x900. Final 18 passed, zero failures, zero mutation requests.
- Test-only safe insets enter the stylesheet before first layout. Checks cover
  footer position, section alignment, reachable cards, 44-pixel targets, existing
  navigation, full-screen finder, notch clearance, long fuel/timestamp text,
  200% rem sizing and login at a 390x320 reduced viewport.
- Initial new finder assertions failed: actual parent map scroll offsets moved
  controls even after animation completed. Ancestor geometry identified the map
  surface, not the page or tab, as the scrolling element. `overflow: clip` fixes
  that path; final tests require zero outer-map scroll and reachable controls.
- Screenshot cases wait for a real public map surface before capture. Synthetic
  vehicle values and public Seoul City Hall coordinates are used. Network access
  is restricted to local assets and public map tile hosts; all non-GET requests
  are aborted. External tile availability can affect this integration check.
- Android source verified independently with Git comparison, not merely the
  build's informational flag. Main asset SHA-256 remains
  `d26971b235a51fa52aaeda6e1c7e92e7dbb61c0758c8189ab4c49aafebf7e6c5`.

## Limits

No Xcode/iOS Simulator runtime is installed on this Mac. WebKit with injected
insets is not a physical iPhone or iOS standalone session. Actual OS keyboard,
VoiceOver, Dynamic Type, pinch/long-press interaction and iPhone refresh remain
unverified. The 200% check enlarges rem-based text, not every native px label.
Original sheets/toasts outside the modified layout still use their existing
safe-area rules. No real vehicle command is issued for this UI task.

Screenshots and JSON reports are ignored under
`apps/my-traverse-web/output/playwright/iphone/`; production screenshots stay
private. The independent review files remain in the agent bridge archive.

## Deployment

PWA production version: `aadadba3-4a5f-4f22-9c38-da4f254fba61` at
`https://my-traverse-web.hyuklee.workers.dev`.
Only index, PWA CSS and PWA JS assets changed; server modules were unchanged.
Actual production CSS/JS/bridge bytes match the local build. Authenticated
WebKit and Chrome checks at 390x844 with 47/34 test insets measured footer bottom
844, rail-to-nav gap 12, horizontal overflow zero and a single 47-pixel top inset.
Vehicle/info/settings navigation rendered with no uncaught JS exceptions and
zero mutation requests. The production WebKit screenshot was visually inspected.
No Wayon Worker, database migration, credentials or subscription changes.
