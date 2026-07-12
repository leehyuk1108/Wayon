# Engaged Path v6 Alert Banner

Base APK: `build_outputs/Hud-engaged-path-v5-signed.apk`

Base SHA-256:

`21c714a8fa48149d000d1c98b4e6b4b0d67668dd43bbb147d9eddb2105a66dd8`

Output APK: `build_outputs/Hud-engaged-path-v6-alert-banner-signed.apk`

Output SHA-256:

`3d827e7c0e7cb1258a25efd5c83bfc28fe74d2e6ea0ea5c98b55693011e6d834`

The `src` directory contains the Java source for the alert banner. The `smali`
directory contains the complete replacement classes used in the APK, including
the receiver integration. Replace these files in the apktool-decoded base APK,
then rebuild, zipalign, and sign with `build_keys/navdy-test.jks`.

Behavior:

- Reads `alertText1`, `alertText2`, `alertType`, `alertStatus`, and `alertSize`.
- Slides a 640x100 banner down at y=120 over the driving HUD.
- Uses black, orange, or red based on alert status.
- Does not restart animation for repeated copies of the same event.
- Slides up and hides when the alert clears.
