# Hylink

Hylink is a read-only Android companion for a vehicle connected to Wayon Cloud.
It is a separate application from My Traverse and uses a distinct package ID:
`app.hylink.mobile`.

## Implemented features

- Current vehicle location and Wayon telemetry
- Onroad/offroad, ignition, speed, voltage, thermal, and openpilot status
- Cloud trip history with route playback on a map
- Parking and impact snapshots
- Recorded 360-degree photos and 10/30-second clips
- Offroad 360-degree Live view and capture
- Recent impact events

Only Wayon Cloud read endpoints and the camera Live session are used. Hylink
contains no vehicle commands, account integration, diagnostic clearing, remote
start, door lock, climate, window, widget command, or Wear OS command code.

## Configuration

The Wayon Cloud key is entered in the app and stored in its private Android
preferences. No key is committed or embedded in the APK.

The default Cloud address is:

```text
https://wayon-cloud.hyuklee.workers.dev
```

Override it for a local build with `wayon.cloudUrl` in `local.properties` or
the `WAYON_CLOUD_URL` environment variable.

## Build

Use JDK 17 or newer:

```bash
./gradlew :app:testDebugUnitTest :app:assembleDebug
```
