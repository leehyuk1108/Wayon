# Carrot Integration, 2026-10-28

Version 30 (`2.0-preview.21-carrot-live`) preserves the installed version-27
GMOne controls, background refresh, timers and widgets, and adds the Carrot
integration fixes. The source snapshot includes that previously uncommitted
version-27 baseline so the new build does not silently lose existing features.

- Panorama-only wide/driver live with binary WLP1 heartbeat and bounded recovery.
- Photo and 10/30-second capture gallery, including older clip layouts.
- Comma telemetry freshness and device-input-voltage provenance.
- Ambient acknowledgment distinguishes settings receipt from physical delivery.
- Full route analysis and explicit partial-coverage labels.

The Carrot device port is documented in
`carrotpilot/WIP-FR:docs/my_traverse_carrot_20261028.md`. The deployed Cloud patch
and regression tests are preserved under
`cloudflare/wayon-cloud/patches/carrot-trip-coverage-20261028/`.
The subsequent OPEN-socket/reconnect lifecycle patch is under
`cloudflare/wayon-cloud/patches/relay-lifecycle-20261028/`; it preserves the
existing auth and separate live/SSH namespaces. Both patches were applied to
exact production exports, without deploying the unrelated dirty Worker source.

Build with JDK 17 or newer and the configured Android SDK (verified with JDK 17):

```sh
./gradlew --no-daemon -Pkotlin.compiler.execution.strategy=in-process \
  :app:assembleRelease :app:testReleaseUnitTest
node --test test_*.cjs
```

Use private `google-services.json` and `local.properties` for the existing
Firebase setup. Sign with the original private key and use `adb install -r` to
retain app data. No credentials, APKs, private images or vehicle logs are stored
in this source commit.

Verified on the phone: same-certificate update, status, panoramic live/reopen,
photo and both saved clip durations, trip list and detailed analysis. Comma
camera/encoder exit was checked after closing live. Physical door/impact push,
ambient LEDs and ignition handover require a separate parked hardware test.
No engine, locking or window command was issued during verification.

Version 30 separates JPEG upload from the live WebSocket using the existing
authenticated HTTPS capture endpoint. This removes large-photo queueing ahead
of heartbeats. It rejects stale camera images, bounds upload time and marks a
photo saved only after the server acknowledges an ID. The server timestamps
photos at receipt; delayed/aborted requests are not automatically retried.

Both-camera freshness controls the live save buttons. A stalled connection is
marked delayed and detached for at most six retries per view; a late callback
cannot reset or unlock a newer session. The matching Carrot relay closes its
Cloud socket on current-owner local EOF rather than leaving a frozen viewer.

Final checks: 60 release unit tests and 46 JavaScript tests passed. Two real
phone JPEG uploads succeeded, the new photo opened in the gallery, and native
encoders delivered 1,400/1,401 frames in 70 seconds. A temporary video delay was
observed and recovered; this does not establish mobile-network or overnight
stability. The separate native heartbeat-expiry test received Cloud close 1012
and successfully reopened, without changing the device's 12-second heartbeat.
