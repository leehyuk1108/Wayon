# My Traverse MultiPack Battery Voltage

## Scope and Cause

The requested display source is MultiPack/GMOne, not Comma input voltage.
Both Android Next and the iPhone PWA share the Next `main.html` asset. Previously
the summary preferred Comma whenever a Cloud key existed, and each Comma
heartbeat wrote directly to the vehicle-info voltage. That replaced the
MultiPack value even after successful vehicle-status retrieval.

The summary and info card now use only the voltage supplied by `updateCarStatus`
(the existing variable retains its historical `latestFirebaseBatteryVoltage`
name). Comma heartbeat processing still updates its telemetry state but rerenders
the same MultiPack value instead of substituting its own. Missing MultiPack
voltage clears the info card to `--V`; the summary retains the battery level if
available, otherwise `--`. This change does not add a Comma fallback or a new
freshness policy.

No CSS, layout, controls, warning thresholds, timestamps, collector, database,
main Wayon Worker or vehicle-device code was changed. In particular this does
not change Comma low-voltage shutdown decisions or notification policies.

## Regression Checks

- New callback-order, heartbeat, missing-value and Cloud-key tests against the
  previous source: five failed, one passed. Fixed source: all six passed.
- Full Android Next JavaScript suite: 82 passed.
- Release JVM suite: 81 passed; release assembly succeeded.
- The same six voltage tests against the built PWA HTML: six passed.
- Full PWA suite with an installed Chromium browser: 337 passed, no skips.
- WebKit and Chromium layout checks across ten viewports each: 20 passed,
  no failures and no mutation requests. These are synthetic rendering checks,
  separate from the actual-phone observations below.
- Existing bundled Playwright lacked its matching WebKit binary. The layout
  rerun used the already installed matching Playwright/WebKit pair; no browser
  dependency or product source was changed to conceal this environment issue.

## Android Installation

- Installed release `40 / 2.0-preview.31-multipack-voltage` over the existing
  `com.example.carcontroller.next` app with `install -r`: Success.
- Preserved the installed v39 APK privately before installation. Existing data,
  account configuration and first-install time were retained.
- Existing v39 and new v40 signing certificates match:
  `55a14240fb656db17c66c695a61ae5679982a5ae24e233563a43211c5125fa94`.
- Signed local APK and actual installed `base.apk` SHA256 match:
  `dd0bd500415506a9e78c1281981c8ef49bcef4fc674e4228b15aac1108c9e504`.
- The actual Galaxy info screen showed **12.4V** at 17:20 KST, retaining the
  MultiPack observation label **17:08**. Prior Comma-selected display was 12.0V.

## iPhone Deployment

- Published PWA version `232bcd6e-7d1b-4218-88de-a3a2effa598e` at 100 percent.
  Only the changed `index.html` asset was uploaded; the other 36 were reused.
- Verified production assets against the local build, unchanged production
  bindings/settings and unchanged main Wayon Worker version/hash.
- An already open iPhone PWA document still showed Comma's 11.9V. After closing
  that app document through iPhone Mirroring and reopening it from the home
  screen, the actual info card showed **12.4V** at 17:23 KST, with the same
  **17:08** source observation. No logout, reinstallation or cache-data wipe.
- Shared HTML SHA256:
  `219099c96f865d0436c3a6bd58f294fa1010017ce0b13f954edea7e077158e82`.

These are checks of source selection and display, not a new physical battery
measurement or proof of sensor accuracy. No vehicle-control commands were sent.
Private APKs and Android screenshots remain under
`Documents/my-traverse-voltage-20261103`; deployment receipts remain outside Git.
