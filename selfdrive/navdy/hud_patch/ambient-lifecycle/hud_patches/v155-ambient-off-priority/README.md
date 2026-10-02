# Ambient OFF Priority

This patch layers on the verified, installed v154r2 APK. It does not change
vehicle control, pairing, UI, colors, brightness settings, or courtesy timers.

## Findings

- On October 2 at 04:44 KST, the live profile had `reverseOff.enabled=true`
  and `dataWatchdog.enabled=true` (20 seconds). Reverse was not disabled by
  a profile toggle. The currently offroad vehicle does not prove what gear
  data arrived during the user's previous reverse maneuver.
- The module was still intermittently discovered, but connection attempts
  ended with GATT 133 before any successful service discovery or OFF response.
  No BLE command can be claimed delivered in that state.
- `hardAmbientOff()` canceled the fade but did not cancel every effect,
  clear queued colors, or supersede lower-level queued state writes. The
  normal brightness coalescer only removed other brightness packets.
- Producer guards existed, but `sendPacket()` had no final reverse/data-loss
  guard. Reconnect explicitly checked reverse, but not data loss.

These are code defects/hardening gaps. They do not establish the cause of the
October 1 initial disconnect, whose original incident journal is unavailable.

## Changes

1. Hard OFF stops fade, warning steps, pending overspeed changes and brightness
   polling. It clears stale application state in both queue layers. An ATT
   operation already accepted by Android must finish or time out; it is never
   overlapped by a second GATT write.
2. OFF supersedes queued color and brightness frames, while preserving BLE
   handshake and protocol ACK packets. The old application busy flag cannot
   keep OFF behind a withdrawn frame. v154's independent final-OFF response
   deadline/reconnect intent remains active.
3. Both fade entry and packet submission block non-OFF lighting state while
   reversing or after vehicle-data timeout. Reconnect restores OFF first in
   both cases. Existing reverse toggle remains enabled and unchanged.
4. Gear transitions and OFF reasons are saved in the persistent journal.
   Repeated identical OFF reasons are limited to one journal entry per minute.
5. Re-enabling/editing an onroad profile restarts brightness polling after hard
   OFF. This closes a regression found while extending the OFF/ON tests.

## Verification

```sh
python3 hud_patches/v155-ambient-off-priority/test_off_priority.py
python3 hud_patches/v155-ambient-off-priority/build.py \
  output/ambient-disconnect-20261002/Hud-v154r2-signed.apk \
  output/ambient-disconnect-20261002/v154r2-build \
  output/ambient-disconnect-20261002/NEW-v155-build \
  output/ambient-disconnect-20261002/NEW-v155-unsigned.apk
```

- Three local tests passed: executable transport queue regressions, retained
  v154 delivery tests, and controller patch scope assertions.
- 22,734 unrelated decoded files are unchanged. Only `classes2.dex` differs
  among non-signature APK entries. Both APK signer certificates match.
- Signed APK SHA-256:
  `9f241b73188d6d98419609aed45c5ea4b16b9cba35f0bc2cd65f566a77d29df1`
  (`Hud-v155r2-signed.apk`, including brightness-poll recovery).
- `ControllerProbe.java` is a separate test artifact, NOT shipped in the HUD.
  It invokes actual APK methods using test-owned controller state and fake
  Settings data in a separate Android process. GATT/adapter remain null and
  `mConnecting=true` prevents acquisition of Bluetooth. The main Looper is
  never pumped. Timer callbacks are invoked explicitly, not real-time waits.
- On-device isolated ART execution passed 29 checks against the final DEX:
  R with pending frames, door/manual fade producer, warning callbacks,
  reconnect, unknown gear, R-to-D recovery, data-loss recovery, exit courtesy,
  door-close hold and timer expiry, door maximum timer expiry, and master
  OFF/ON with automatic-brightness polling resumed.
- The same probe against the unmodified v154r2 DEX failed at
  `R preempts queued fade no stale ON/color`: a color frame remained queued
  ahead of OFF. This reproduces the queue defect, not the historical BLE failure.
- Evidence: `output/ambient-disconnect-20261002/v155r2-art-probe.txt`,
  `v154-art-baseline.txt`, and `v155r2-tests.txt`.

Probe setup initially failed on missing Android runtime initialization and
Settings-provider access from a standalone process. The final harness uses
`app_process`, a prepared Looper and an in-memory `MockContentResolver` with
test-owned state. Its settings writes cannot reach the real Settings provider.
Earlier `ControllerProbe` exceptions in logcat belong to test processes,
not the installed HUD. Probe vehicle/gear messages likewise must not be treated
as actual driving observations; the production journal is in a different path.

Physical reverse/OFF verification is separate from these software tests. A
protocol ACK is also not optical confirmation of dark strips. An unreachable,
independently powered controller cannot be made fail-dark by host software
alone; that requires a module-side timeout or independent power interlock.

## Installation

- Final `install -r` returned `Success` at 2026-10-02 05:09:10 KST after
  verifying comma was offroad both before download and before installation.
- At 05:09:58 the installed APK readback SHA-256 matched the final hash above.
  HUD PID 4443 and connection-service PID 4481 were alive, Bluetooth enabled,
  boot complete, display OFF and wakefulness Asleep. The intentional ambient
  CPU wake lock remains; this is not full CPU suspension.
- The saved profile was unchanged, including reverse OFF enabled, 20-second
  data watchdog, 1-second fades, 20-second door-close hold, 20-minute door limit,
  and 120-second exit courtesy. No app data or pairing records were cleared.
- Neither comma nor Navdy was rebooted in this follow-up; package updates
  restarted the HUD. Temporary download server and tunnel were stopped.
- Installed-runtime evidence is in `v155r2-device-verification.txt` under the
  output evidence directory. The follow-up BLE observation is recorded separately.
- At 05:11:10 KST, production PID 4443 remained alive. The main module had
  appeared in a scan at 05:10:57, but connection failed with status 133 at
  05:10:58; another attempt was running. Bluetooth was enabled and GATT showed
  zero connections. No successful service discovery or OFF response occurred.
  See `v155r2-final-observation.txt`. **Physical light-off and reverse glare
  resolution remain unverified; software installation is not connection recovery.**
