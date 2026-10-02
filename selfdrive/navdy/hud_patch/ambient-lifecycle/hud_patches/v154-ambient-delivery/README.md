# Ambient delivery recovery (2026-10-02)

## Evidence boundary

The reported incident was 2026-10-01 20:22-20:33 KST. The retained Navdy
journals begin at 21:33:30, so they do not establish the first disconnect's
trigger. Do not label a particular commit or the hardware as the proven cause.

Before this patch, the live HUD was v153r2, installed October 1 at 14:44:23:

- SHA-256: `9c9fa979378baf7eb7c16e72e8c6c3979f95edc496220cb8f81473ccc6ec0fc3`
- Actual APK readback through comma ADB matched the local base.
- HUD process remained alive; comma was offroad and the Navdy display asleep.
- Retained logs show repeated direct-connect timeouts/status 133, with no
  service discovery or notification setup succeeding.
- The 04:20 October 2 scan saw an unrelated peripheral, but not the remembered
  ambient main module. Later post-install scans intermittently saw the main
  module again, but connections still failed with status 133. Saved device
  presence alone is not evidence of a live radio or an established connection.
- The remembered Pocket Link main-module identity predates the recent patches;
  the original CarLED app also scans Pocket main modules and RZ-Slave submodules.

Evidence directory: `output/ambient-disconnect-20261002/`.

## Historical comparison

Older commits below are in `/Users/hyuklee/Documents/sunnypilot`. The Java path
at these revisions is
`selfdrive/navdy/hud_patch/engaged-path-v7-alert-banner-speed-warning/src/com/navdy/hud/app/ambient/AmbientLightController.java`.

| Revision | Change relevant to this investigation |
| --- | --- |
| `6165173b46`, Aug 28 | ACK settling changed from 120 ms to a configurable default of 10 ms; paced START/color writes changed from 350 to 120 ms. ATT writes still had no shared in-flight queue. |
| `795700f212`, Aug 28 | A 10-second failed direct connection immediately fell back to scan. |
| `ee231515bc`, Aug 28 | Reduced redundant brightness synchronization/state-change traffic. |
| `5a2df9caa5`, Sep 3 | Added RGB/brightness color-transition frames and transport-aware frame handling. |
| `0c4facf198`, Sep 3 | Waited for connectivity/transport availability during fades and restored targets after reconnect. |
| v149, Sep 26 | Filtered module identity and remembered validated addresses; increased status-133 retry delay. |
| v151, Sep 29 | Accepted one-percent automatic-brightness changes and restarted polling after data recovery/overspeed. Packet format and fade duration did not change. |
| v152, Sep 30 | Far-lead UI; ambient classes unchanged from v151. |
| v153/r2, Oct 1 | Serialized callback state changes, rejected stale sessions, added setup deadline, and prevented fresh vehicle payloads bypassing retry cooldown. Live module reconnection was not established after that installation. |

The recent brightness fix can expose existing transport races more often by
actually delivering previously skipped changes. This is a hypothesis, not an
incident-log finding. The older transport bugs are independently reproducible.

## Reproduced defects and changes

1. Lighting writes and protocol ACK writes used the same Android characteristic
   without a common ATT completion gate. A fixed 10 ms pause is not proof that
   Android completed the previous write. Both now use `AmbientWriteLane` with
   immutable byte snapshots and actual characteristic-write completion.
2. Android temporarily rejecting a write previously closed the connection
   immediately. The lane retries at 30 ms, bounded to ten attempts. New queued
   packets cannot bypass that delay. Unsent brightness/color frames coalesce;
   handshake and ACK frames do not.
3. The old 1.2-second timeout silently discarded the outstanding command and
   flushed the remaining queue. A final OFF could be lost with no active light
   state or queued packet left to trigger recovery. Unconfirmed delivery now
   remains a reconnect reason; reconnect restores the controller's current
   desired state, including OFF.
4. Final OFF also has an independent 1.5-second protocol-response deadline.
   An Android ATT-success callback is not sufficient confirmation. Recognized
   module ACKs and validated frames can acknowledge delivery; negative replies
   cannot. This is protocol receipt, not optical proof that strips are dark.
5. Repeated unanswered connection attempts back off to 60 seconds rather than
   repeatedly cycling connection and scan throughout the night. This does not
   turn off recovery permanently or change the first connection attempt.
6. Journal retention grew from 64 KiB per file to 1 MiB per file (two files).
   Final OFF submission/response is recorded without logging every fade frame.
7. Cold-start review exposed another recovery gap: a newly created HUD
   controller assumes zero current brightness, while independently powered
   strips may still be on. Its OFF fade waits for a connection, but the empty
   queue and inactive flag can make `needsConnection()` false. The session now
   starts with reconciliation pending; only a module response retires it.
   In the live v154 reboot, the existing delayed OFF path did eventually cause
   retries; this guard removes reliance on that path, not a claim that every
   observed cold boot previously failed to retry.

Module response framing was checked against the local decompiled CarLED 1.3.3
`DataPack.java` and `BleConnector.java`: FF ACK, FC/F0/F3 negative replies, and
2E/type/length/payload/checksum frames. Fragmented/novel firmware responses have
not been verified on the currently unreachable module.

## Scope and validation

- Built over the exact installed APK, not the older Java source snapshot.
- Existing UI, phone pairing, navigation, lighting policies, RGB values, zone
  brightness, door timers, and fade timing are unchanged.
- Three automated tests pass, including executable Java regression harnesses
  for stale callbacks, service/CCCD errors, ACK/state serialization, busy
  retries/exhaustion, queue coalescing, lost OFF, negative responses, and backoff.
- 22,732 unrelated decoded files are byte-identical. Only `classes2.dex`
  differs among APK payload entries. Both DEX headers remain Android-5-compatible
  version 035. Signing certificate matches the installed APK.
- Signed APK SHA-256:
  `6d0a43740302555fa6398ca45dc6e623d5ce409bf7a04525e6505b964307040d`
  (`Hud-v154r2-signed.apk`, including initial reconciliation).

```sh
python3 hud_patches/v154-ambient-delivery/test_delivery.py
python3 hud_patches/v154-ambient-delivery/build.py \
  output/ambient-disconnect-20261001/Hud-v153r2-signed.apk \
  output/ambient-disconnect-20261001/v153r2-build \
  output/ambient-disconnect-20261002/NEW-build-directory \
  output/ambient-disconnect-20261002/NEW-unsigned.apk
```

Signing uses the existing local key; credentials are intentionally not included.
The build script refuses a different base hash or an existing output directory.

## Device verification

- Both updates used `install -r` with `Success`; final v154r2 installation was
  2026-10-02 04:35:42 KST. No data clear, uninstall, pairing reset, or comma
  reboot was performed. Temporary download servers/tunnels were stopped.
- Final installed APK readback SHA-256 matches the signed v154r2 hash above.
- One Navdy-only reboot was completed between the first and final update.
  `sys.boot_completed=1`; final HUD/connection-service and Bluetooth processes
  are running. Observed logs contain no AndroidRuntime crash from this patch.
- Final power observation: `mWakefulness=Asleep`, display `OFF`, Bluetooth
  enabled. The existing offroad ambient CPU wake lock is retained intentionally;
  this is display sleep, not a claim that the entire CPU is suspended.
- Live retry cooldown reached 20, 40, and 60 seconds without a process restart
  before the final update. Final v154r2 cold-start retries also executed.
- At 04:36:46.350, the Bluetooth controller reported HCI reason 62 (`0x3E`),
  followed by Android GATT status 133 for the saved main-module address.
  The Bluetooth Core specification defines this as failure to establish the
  link/synchronize, rather than a rejected brightness command:
  https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-54/out/en/architecture%2C-mixing%2C-and-conventions/controller-error-codes.html
- At 04:37:17, GATT showed zero connections. No successful service discovery,
  CCCD setup, or OFF protocol reply has been observed. **Physical recovery and
  actual strip brightness/off state remain unverified.**

This establishes the current failure stage, not the cause of the reported
October 1 first disconnect. The missing incident journal prevents that stronger
claim. A power/interference/peripheral-firmware condition or an interaction with
previous traffic cannot be distinguished from these records alone. A controlled
main-module power cycle and a fresh connect/OFF-response observation are the
next useful checks when physical access is available; do not erase pairing or
keep rebooting Navdy in lieu of that evidence.
