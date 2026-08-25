# Hylink

Hylink is an Android companion for a vehicle connected to Wayon Cloud.
It is a separate application from My Traverse and uses a distinct package ID:
`app.hylink.mobile`.

## Implemented features

- Current vehicle location and Wayon telemetry
- Onroad/offroad, ignition, speed, bearing, GPS quality, voltage, current, and power
- openpilot state, availability, engageability, personality, mode, and current alert
- Cloud trip history with distance/time/speed insights and route playback on a map
- Parking and impact snapshots with camera, size, capture, and sensor metadata
- Recorded 360-degree photos and 10/30-second clips with layout and storage data
- Offroad 360-degree Live view and capture
- Impact force, jerk, gyro, duration, sample, and capture status
- Device CPU/GPU/memory/storage usage and detailed thermal sensors
- Network quality, screen state, electrical flow, and estimated offroad energy
- Panda connection, harness, safety model, counters, fault health, and uptime
- Offroad-only remote SSH terminal through the per-device Wayon relay

Only Wayon Cloud data, camera, and remote-session endpoints are used. Account
vehicle status and lock state bundled by the Cloud are removed before rendering. Hylink
contains no vehicle commands, account integration, diagnostic clearing, remote
start, door lock, climate, window, widget command, or Wear OS command code.

## Configuration

The Wayon Cloud key is entered in the app and stored in its private Android
preferences. No key is committed or embedded in the APK.

The first terminal connection creates a dedicated 3072-bit RSA key inside the
app-private, non-backed-up files directory. Its public key must be added to the
comma device's SSH key list once. The private key never leaves the phone. Wayon
still restricts the relay to the Dongle ID bound to the supplied Cloud key, and
the device-side relay stops on Onroad transition.

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
