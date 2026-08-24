# My Traverse Next

This is the separately installable next-generation My Traverse UI project.

- Package: `com.example.carcontroller.next`
- Version: `1.18` (`versionCode 4`)
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
