# Ambient BLE session recovery

Investigation: 2026-10-01. Reported incident: 2026-09-30 after 22:00 KST.
This patch changes the ambient BLE transport only, not lighting policy, vehicle
control, UI, colors, brightness targets, fade timing, or phone pairing.

## Evidence

- The installed v152 APK matched the expected build. Its ambient controller was
  unchanged from v151. v151 changed brightness recovery; v149 changed candidate
  filtering and GATT-133 backoff.
- Live attempts timed out or returned GATT status 133 before service discovery.
  That status alone does not identify a module, radio, or Android-stack cause.
- On 2026-10-01 at 14:38:15.630 KST, the disconnect handler received status 133.
  Scanning restarted at 14:38:15.710, only 80 ms later, despite the intended
  10-second backoff. `scheduleReconnect()` returned early when `needsConnection()`
  was false, and a subsequent vehicle payload bypassed the delay.
- Other GATT callbacks did not reject retired sessions, shared transport state
  with main-thread work, and accepted failed notification setup as ready. Service
  discovery / notification setup had no bounded recovery deadline.
- The original CarLED 1.3.3 app explicitly searches for `Pocket` main controllers
  and `RZ-Slave` submodules. Preserve these filters and the remembered address;
  do not classify Pocket as an unrelated device merely from its name.
- The available qlogs for `000000f2--38a10e86e2` cover 36 segments, approximately
  35m19s. There was no mid-drive offroad transition; the maximum carState gap was
  0.420 s. These logs do not prove continuous delivery to Navdy and do not record
  Android BLE callbacks. The incident-time Android logcat had already rotated.
  The initial flicker/disconnect trigger therefore remains unconfirmed.

## Changes

- Dispatch GATT callbacks onto the controller Handler; discard retired sessions.
- Copy notification bytes before posting because Android reuses the value object.
- Reject failed connection, service, CCCD, and write callbacks.
- Bound service/notification setup to 10 seconds and reuse disconnect recovery.
- Invalidate the session before disconnect/close and cancel old transport timers.
- Ignore queued scan callbacks when scanning has ended or a connection is active.
- Enforce reconnect deadlines with monotonic time independently of the queue and
  offroad state. Shorter retries cannot shorten an existing longer backoff.
- Keep a bounded diagnostic journal under the app's private files directory:
  `ambient-ble-events.log` plus one rotated file. No per-packet journal writes.

## Build and Tests

Exact base: `build_outputs/Hud-v152-far-lead-signed.apk`

Base SHA-256:
`986ada31a9c855f4ba38abb9e3bdc7e2e0d46dee571de75cc50112f2f3388627`

Final artifact: `output/ambient-disconnect-20261001/Hud-v153r2-signed.apk`

Final SHA-256:
`9c9fa979378baf7eb7c16e72e8c6c3979f95edc496220cb8f81473ccc6ec0fc3`

`v153r2` supersedes the first v153 diagnostic installation by also fixing the
observed offroad backoff bypass. Android package version metadata is unchanged.

```sh
python3 hud_patches/v153-ambient-session/test_session.py
python3 hud_patches/v153-ambient-session/build.py \
  build_outputs/Hud-v152-far-lead-signed.apk \
  output/navdy-far-lead/20260930/production-decode \
  output/ambient-disconnect-20261001/v153r2-build \
  output/ambient-disconnect-20261001/Hud-v153r2-unsigned.apk
```

Use a fresh decode output directory when rebuilding. Sign with the existing
Navdy signing key; never uninstall or clear app data to work around signing.

Host tests cover serialization, all retired callbacks, successful setup deadline
cancellation, setup/write failures, notification copying, retired timers, and
cooldown enforcement at 80 ms / 9.999 s / 10 s. Exact-method comparison preserves
lighting policy and device filters. Both test cases passed.

The build verified 22,732 unrelated decoded files were unchanged. ZIP payload
comparison found only `classes2.dex` changed, excluding APK signatures. Existing
signer certificate SHA-256:
`afe4eff90076c92ed8e087ec49a5d7257f5d473916243daafb16dc41e8b40bcf`

## Device Verification

- Navdy serial `FPI647618N4111AT`, package `com.navdy.hud.app`.
- Downloaded to comma `/data/wayon_updates/` using a temporary Mac download link.
  Checked SHA-256 before `adb -P 5038 -s FPI647618N4111AT install -r`.
- Vehicle was offroad. `install -r` returned `Success`; app data and pairing were
  preserved. No comma reboot or driving-control modification was performed.
- Re-read the installed APK with `pm path` and hashed its bytes: the final
  installed SHA-256 matches the final artifact above. App PID 17918 started at
  14:44:27 KST without an observed AndroidRuntime exception.
- On-device scan-end cooldown: `reconnect deferred ms=5000` at 14:45:47.501;
  the next connection began at 14:45:52.569 (5.068 seconds later). The 10-second
  error deadline is covered by host tests; no fresh status-133 callback occurred
  in this final short observation window to verify that branch again on-device.
- Final observation: `IsOnroad=0`, `mWakefulness=Asleep`, display `OFF`, Bluetooth
  enabled, and GATT client connections `0`. The connection still times out.
- One Bluetooth disable/enable cycle preserved pairing, but did not establish
  the module connection. Adapter scans still found surrounding devices.
- The user is at work and cannot power-cycle the ambient module now. Do not claim
  physical lighting recovery until GATT services, notification setup, and actual
  command acknowledgements are verified. Software tests and installation alone
  do not establish that result.

The temporary HTTP server and Cloudflare tunnel were stopped after download.
Read-only route audit output is in
`output/ambient-disconnect-20261001/route-audit.json`.
