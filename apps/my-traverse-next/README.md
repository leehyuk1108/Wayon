# My Traverse Next

## Trip Fuel in the Drive Report and Full Trip List (v43)

Version `43 / 2.0-preview.34-vehicle-care` shows comma CAN trip fuel from
`analysis.fuel` (`wayon-trip-fuel-v1`) inside the existing drive report: km/L
sits beside distance, time, average and top speed in trip detail (the five
values scale with the phone width), each trip card gains a fourth 연비 stat
when the trip has fuel data, and 상세 분석 gets a 연료 group (litres, idle fuel,
L/100km, gauge start/end, counted distance, oil life). Older trips are
unchanged. The Worker is unchanged: it already stores the whole `analysis`.

The full trip list request now steps down from 1000 to 600 and 300 trips on a
server error. On 2026-11-09 the Worker answered 700 trips (15.8 MB) but threw
Cloudflare 1101 / HTTP 500 for 850 and 1000, so the app had been left with the
25 startup trips.

Build: `./gradlew :app:testReleaseUnitTest :app:assembleRelease` with an init
script that points Gradle's debug signing config at the original debug
keystore (`~/.android/hylink-signing/original-debug.keystore`, certificate
SHA-256 `55a14240…`). The default `~/.android/debug.keystore` on this Mac is a
different key and cannot update the installed app.

## MultiPack Battery Voltage (v40)

Version `40 / 2.0-preview.31-multipack-voltage` uses the MultiPack/GMOne
vehicle-status battery voltage in both the battery summary and vehicle-info
card. Comma telemetry no longer overrides those values, regardless of callback
order or Cloud-key presence. Missing MultiPack voltage displays `--V` in the
info card, without falling back to Comma. Observation freshness, other battery
fields, warning policies, controls and layout are unchanged.

The iPhone PWA builds from this same HTML. Android update installation and PWA
deployment were verified separately on the actual phones; see
[`my_traverse_multipack_voltage_20261103.md`](../../docs/my_traverse_multipack_voltage_20261103.md).

## Parking Sign Notifications (v39)

Version `39 / 2.0-preview.30-parking-sign` adds the `wayon_parking_sign` FCM
receiver and the private `wayon_parking_sign_alerts` notification channel. The
server publishes only corroborated readable floor/zone/pillar/bay clues, not an
exact parking-space assertion. Unreadable results remain silent.

Background notification delivery uses the existing visible FCM path; foreground
delivery uses the native receiver with bounded IDs/text, strict timestamp
validation, ten-minute expiry and persistent event deduplication. Notification
permission and channel settings are respected. Tapping opens the existing app;
this change does not add a result page or alter the home screen.

Release JVM tests: 81 passed. Existing JavaScript tests: 76 passed. All 26
non-generated APK assets match installed v38 byte-for-byte; only the two generated
DEX profile assets differ. Device installation and live push receipt must be
verified separately from these source/build checks.

This is the separately installable next-generation My Traverse UI project.

- Package: `com.example.carcontroller.next`
- Version: `2.0-preview.9` (`versionCode 18`)
- Debug package: `com.example.carcontroller.source`
- Debug label/version: `My Traverse Source` / `1.18-source`
- Reference APK SHA-256:
  `69bd3d715a4c880de3264139a66d1d9bb875ee1e4918e6d186b29c014a219965`
- UI baseline: the exact `main.html` and `wayon_live.js` assets from the
  reference APK

## Included Features

- Current vehicle status, parking location, trip history, and Wayon Cloud feed
- Lock, unlock, remote start, ventilation, and heat-ejection commands
- Dynamic lock/unlock control with long-press confirmation
- Phone widgets and Wear OS command/status synchronization
- Parking impact, door-lock, and unlocked-vehicle notifications
- Impact snapshots and camera history
- Offroad dual-camera 360 Live view, recording, and saved Live captures
- Bluetooth-based local driving behavior retained for non-Cloud setups
- Independent MultiPack account login and direct vehicle-status refresh
- Independent Zone 1/Zone 2 ambient RGB, brightness, and duration controls through Wayon Cloud
- Compact ambient cards with clear automatic/manual status and expandable situation controls

The current UI assets are kept unchanged so layout, styling, animation, and
interaction match the installed app. Native Live session handling that existed
only in the patched APK has been restored as Kotlin source.

Debug builds use a separate application ID so they can be installed beside the
production My Traverse app. Backend FCM token registration is disabled only for
that debug package, preventing it from replacing the production app's push
destination; Firebase status data and the rest of the configured integrations
remain available.

## Private Configuration

No vehicle-control URL, account email, API key, Firebase client file, device ID,
or Wayon registration token is committed.

1. Copy `local.properties.example` to `local.properties`.
2. Set the local Android SDK path and private Wayon/Firebase values.
3. Copy `app/google-services.json.example` to `app/google-services.json` and
   replace it with the real Firebase Android client configuration.

The vehicle-control API URL is entered in the app settings at runtime and stored
in the app's private preferences. It is intentionally absent from source and
Gradle configuration. The Wayon Cloud view key is handled the same way.

MultiPack credentials are separate from Wayon Cloud. The app verifies them
directly against the official GMOne login endpoint, encrypts the password with
an Android Keystore AES-GCM key, and stores no session token in source, Gradle
configuration, Firebase, or Wayon Cloud.

The following environment variables can be used instead of Gradle properties:

```text
WAYON_CLOUD_URL
WAYON_DEVICE_ID
WAYON_PUSH_REGISTRATION_TOKEN
WAYON_LIVE_TOKEN
FIREBASE_DATABASE_URL
```

`local.properties` and `app/google-services.json` are ignored by Git. A build
without them still compiles, but Firebase push/status integration remains
disabled until the private configuration is supplied.

## Build

Use JDK 17 or the JDK bundled with Android Studio:

```bash
./gradlew :app:assembleDebug
```

## Map Startup (v36)

The home map waits for vehicle coordinates before requesting tiles, instead of
first requesting `(0, 0)`. Ready raster tiles dismiss the loading shield without
waiting for the vector style or a five-second timer. The vector container stays
transparent until ready; a failed style or WebGL initialization leaves the raster
usable. The vendored Leaflet adapter tolerates cleanup after a failed GL
constructor. Trip-detail readiness cannot dismiss the home map's shield.

Vehicle-state polling, coordinate freshness, command guards, layout and final
vector styling are unchanged. `[MapStartup]` console events contain elapsed
rendering times only, not coordinates or credentials.

Validation on 2026-10-30: 68 JavaScript tests (11 map cases), 73 Kotlin tests and
the release build pass. Run `node --test test_*.cjs` and
`./gradlew :app:testReleaseUnitTest :app:assembleRelease`.
In a Chrome comparison with cached raster tiles and an injected three-second
style delay, the old map became visible at 4091 ms (tiles ready at 71 ms), versus
57 ms (tiles ready at 57 ms) with the fix. Both final vector canvases contained
254525 non-uniform pixels at 494x516; final styling was also visually checked.
Actual source-request failure and GL-constructor failure retained six raster
tiles without an unhandled JavaScript error. These are browser rendering tests,
not measurements of the phone's entire cold startup or the vehicle-feed latency.

## Driving Status (v38)

Version `38 / 2.0-preview.29-driving-status` separates the confirmed operating
state from the vehicle-health headline. Fresh Comma onroad data displays
`DRIVING` even without GPS or while the separate GMOne snapshot is loading.
Fresh ignition-only data displays `ENGINE ON`; parked remote-start countdowns
retain `REMOTE START`. Ordinary warnings remain in the existing detail line and
warning badge. Critical alerts retain their headline and add the operating state
to their detail, rather than hiding either fact.

The existing freshness limits remain unchanged: 45 seconds for onroad/unknown
mode and 660 seconds for offroad heartbeats. Missing, unavailable or stale live
data cannot gain a confirmed operating state. No vehicle commands, command
authorization, server polling, layout, or Comma code were changed.

Validation: `node --test test_*.cjs` passes 76 JavaScript cases, including eight
new policy/actual-renderer tests. Release JVM tests pass 76 cases and the release
APK builds. Offline Chromium checks cover 15 scenarios at 320, 390 and 768 pixels
with no page errors or status-text overlap. Synthetic onroad display checks are
not evidence of a real vehicle drive or command execution.

The Fold7 was updated in place with the existing signer on 2026-11-02. Version
38, app UID and all 19 recorded permission grants were verified. Installed APK
SHA-256: `259c06fbbf5ea7835fc139b6ce05676e69b3340f7e72173b4bbdb9c3d528ebba`.
The real parked home screen and authenticated server-state receipt were checked;
no simulated state was injected into the phone or vehicle. Actual driving
transition verification remains outstanding.
