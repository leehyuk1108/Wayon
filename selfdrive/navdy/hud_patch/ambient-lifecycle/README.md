# Navdy Ambient Lifecycle v156

This is the source record for the ambient/power patch installed and verified on
2026-10-02. It supersedes the ambient portion of the historical
`engaged-path-v7-alert-banner-speed-warning` source snapshot. It does not change
the driving controller, phone bridge, navigation UI, or comma boot behavior.

## Source Of Truth

- `hud_patches/v153-*` through `v156-*` retain the patch dependency chain,
  readable Java helpers, regression tests, build scripts and device probes.
- `snapshot/` contains the exact 43 ambient-class smali inputs and three power
  integration classes used for the installed v156 build. `snapshot.sha256`
  records their hashes. These are source inputs, not a complete decoded APK.
- `release.json` pins the base APK, installed APK and signing certificate.
- [Verification and limitations](hud_patches/v156-ambient-power/README.md)
  distinguish isolated tests, device ACKs, physical observations and unresolved
  peripheral failures. Existing historical READMEs are not current release IDs.

The only portability changes to the archived patch scripts are `JAVA_HOME`
support in the test harness and `NAVDY_V155_DECODE` for its input tree. Runtime
patch code is unchanged from the installed build.

## Test And Build

From this directory, using a JDK with `java` and `javac`:

```sh
shasum -a 256 -c snapshot.sha256
NAVDY_V155_DECODE=/absolute/path/to/verified-v155r2-decode \
  python3 hud_patches/v156-ambient-power/test_power.py
python3 hud_patches/v156-ambient-power/build.py \
  /absolute/path/to/Hud-v155r2-signed.apk \
  /absolute/path/to/verified-v155r2-decode \
  output/v156-build output/Hud-v156-unsigned.apk
```

All five tests require the exact base decode for the changed-method scope test.
The builder requires the existing apktool, Android SDK/D8 and Java tools under
`~/.cache/navdy-build-tools`; see its pinned input hash and tool paths. Sign with
the existing private key, verify its certificate, then install using an explicit
ADB serial and `install -r`, requiring `Success` and an installed-APK readback
hash. Do not uninstall or wipe data to work around signature/dex errors.

APKs, signing keys, raw device logs and account credentials are deliberately not
committed. A fresh Git clone is a source checkout, not a ready-to-install APK.
Obtain the hash-pinned base and signing key through the existing private local
artifact storage. Do not substitute an old v39/v67 APK or apply this overlay to
an arbitrary base. The installed artifact is retained on the build Mac under
`~/Documents/navdy/output/ambient-power-20261002/Hud-v156-signed.apk`.

## Reboot And Recovery

This patch is installed persistently in Android's `/data/app`, not injected into
a running process. The inspected comma bridge/boot code does not reinstall an
old HUD APK on startup. A comma Git pull does not update or downgrade the Navdy
APK; the two deployments must be verified separately. This source-only commit
does not restart either device and does not introduce a boot-time installer.

Low/critical-voltage automatic shutdown is disabled at the owner's explicit
request. Display sleep remains enabled. This removes that battery-protection
behavior and can discharge a parked vehicle's battery. Thermal shutdown and
manual shutdown remain available.

The main module recovered only after its physical power cycle in this test.
Neither the 16-minute stable observation nor host-side OFF delivery guarantees
recovery from a locked peripheral or sudden power loss. A hardware watchdog or
independent power interlock is required for an absolute fail-dark guarantee.
