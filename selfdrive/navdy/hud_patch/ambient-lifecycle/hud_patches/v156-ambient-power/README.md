# Ambient Power Lifecycle

User-approved change, 2026-10-02: disable Navdy's automatic low-voltage full
shutdown while retaining display sleep and the offroad ambient CPU wake lock.
This is not a battery-protection feature. Continuous operation can discharge the
parked vehicle battery. Hardware power loss cannot be prevented by this patch.

## Scope

Exact base APK: `output/ambient-disconnect-20261002/Hud-v155r2-signed.apk`

Base SHA-256:
`9f241b73188d6d98419609aed45c5ea4b16b9cba35f0bc2cd65f566a77d29df1`

Installed artifact: `output/ambient-power-20261002/Hud-v156-signed.apk`

Installed SHA-256:
`4e819112d0ad57eb908766f47c94247d585c0040107087a5a62ec033950e9ad2`

1. The low-voltage branch in `ObdManager$Anon5` now reports voltage without
   putting the OBD device to sleep or posting a shutdown event. Its normal
   voltage telemetry publication remains intact. Suppressing only the final
   Android shutdown would leave the earlier OBD-sleep side effect behind.
2. Both the shutdown worker and final power API reject `LOW_VOLTAGE` and
   `CRITICAL_VOLTAGE`. Other shutdown reasons, including high temperature, are
   preserved. No voltage thresholds or stored vehicle profiles were changed.
3. Normal intentional shutdown first requests ambient OFF, blocks other light
   producers, and asynchronously waits up to 1.5 seconds for a module protocol
   response. Android ATT success alone is not sufficient. Timeout is recorded
   as unconfirmed, not as lights-off success. The original shutdown continues
   on its original TaskManager background executor. Thermal, power-loss and
   accelerated shutdown are not delayed.
4. GATT connects explicitly request LE transport, with the old overload as a
   compatibility fallback. Two unanswered attempts require a fresh scan rather
   than continuing to alternate remembered/bonded-device connects. Existing
   validated address, main-module matching, slave exclusion and backoff remain.
5. v155 OFF priority, reverse/data-loss gates, automatic brightness recovery,
   door timers, RGB values, fade timing, phone connection and HUD layout remain.

No comma vehicle-control code or production power bridge was replaced. The
live bridge differs from the local checkout; do not deploy the older copy.

## Evidence And Attribution

Before installation, a complete low-voltage shutdown was observed at 15:39:
11.8 V reported, `CRITICAL_VOLTAGE` shutdown, Bluetooth disabled, then a new
kernel boot. Other failures also occurred while Navdy remained powered, so
low-voltage shutdown is not the sole established explanation for BLE failures.

The user-assisted ignition test used local SSH at `192.168.35.175`:

- 16:43:12: Onroad transition recorded.
- 16:43:18-26: the existing comma bridge disabled/re-enabled Navdy Bluetooth.
  This was not a manual reset by this task. Navdy's kernel boot ID did not change.
- 16:44:13: connection still failed with GATT 133. The user confirmed that
  ambient lighting never came on. Ignition alone did not recover it in this test.
- After installation, the initial direct/LE attempts also timed out.
- The user physically disconnected/reconnected main-module power.
- 16:54:24.788: GATT connection succeeded; service discovery and notifications
  succeeded at 16:54:25.642 and 16:54:25.671.
- 16:54:59.851: OFF submitted; protocol response at 16:54:59.914.
- 16:57:45.166: real offroad door-open event.
- 16:57:57.373: real door-close event.
- 16:58:18.578: OFF submitted; response at 16:58:18.652. This matches the
  configured 20-second hold plus approximately one-second fade. The user
  independently confirmed physical illumination and subsequent extinguishing.

Recovery therefore coincides with the physical main-module power cycle. Do not
claim that transport changes alone fixed the unreachable module, or that its
original lockup trigger is established. Earlier GATT-133/status-62 failures
preceded service discovery, not just a rejected brightness command.

## Verification

```sh
python3 hud_patches/v156-ambient-power/test_power.py
python3 hud_patches/v156-ambient-power/build.py \
  output/ambient-disconnect-20261002/Hud-v155r2-signed.apk \
  output/ambient-disconnect-20261002/v155r2-build \
  output/ambient-power-20261002/NEW-build \
  output/ambient-power-20261002/NEW-unsigned.apk
```

- Five host tests passed, including existing delivery/OFF queue regressions,
  LE and compatibility connect paths, bounded shutdown continuation, protocol
  response versus ATT callbacks, and strict changed-method assertions.
- 22,731 unrelated decoded files are byte-identical. Only `classes.dex` and
  `classes2.dex` differ among non-signature APK payloads; resources, manifest,
  native libraries and UI assets are unchanged. Both DEX versions remain 035.
- Existing certificate SHA-256:
  `afe4eff90076c92ed8e087ec49a5d7257f5d473916243daafb16dc41e8b40bcf`.
- Pre-install isolated ART probe: 46 checks passed. Post-install probe loaded
  the installed APK directly and passed 50 checks, including both real
  low-voltage shutdown entry points returning before accessing any device
  handles. Other shutdown reasons were checked as policy, not physically run.
- Probe instances use fake settings and null transport, never loop the main
  Looper, never post shutdown events, and cannot issue BLE commands. The final
  probe process was PID 9725; its synthetic vehicle/door messages are NOT real
  observations. Production HUD PID was 8216 in this test window.
- The initial ordinary ADB update failed with `INSTALL_FAILED_DEXOPT` while the
  old package remained installed. Whole-APK compilation was checked separately.
  After removing only this task's temporary probe DEX/cache files and staging
  the same APK on `/cache`, data-preserving `pm install -r` returned `Success`.
  This sequence does not independently prove the first install error's cause.
- Installed APK readback SHA-256 matches above. Profile, saved module address,
  and pairing-registry hashes are unchanged. No wipe, uninstall or reboot.
- Production logs confirm suppression at reported 11.7-11.8 V while the display
  is asleep and Bluetooth remains connected. These are Navdy voltage readings,
  not an independently calibrated battery-terminal measurement.
- Shutdown lifecycle review: the original `androidShutdown(reason, false)`
  calls Android `PowerManager.reboot("quiet")`, not an in-process display sleep.
  The shutdown-only output barrier therefore does not persist across a
  successful quiet reboot. Ordinary `enterSleepMode()` does not set this
  barrier. No additional wake-path modification was needed.
- Continuous post-recovery capture completed from 16:55:23 through 17:11:23
  KST (960 seconds). All 32 power samples retained the same kernel boot ID,
  display OFF and the offroad controller wake lock. All recorded state was
  Offroad. No production BLE disconnect or connection attempt was recorded;
  16 rate-limited low-voltage suppression messages were recorded. The final
  Bluetooth service snapshot still shows one GATT connection to the saved
  main module. See `evidence/capture-summary.json` and `final-bluetooth.txt`.

Installation evidence and bounded capture are on comma under
`/data/tmp/navdy-v156/`; local copies belong under
`output/ambient-power-20261002/evidence/`. The temporary Mac HTTP endpoint and
Cloudflare download tunnel were stopped after the verified artifact transfer.

## Remaining Limits

An independently powered module that loses BLE can retain its last state.
Host OFF queue priority and shutdown preparation cannot guarantee extinguishing
after sudden power removal or a peripheral firmware lockup. An absolute
fail-dark guarantee needs a module-side watchdog or independent power interlock.
No such hardware guarantee is claimed here. Long-term reliability and an actual
post-patch onroad reverse maneuver are distinct from the isolated regression
tests and the physically confirmed offroad door test above.
