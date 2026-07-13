# Engaged Path v11 Disengaged Status Icons

Base APK: `build_outputs/Hud-engaged-path-v10-split-rate-signed.apk`

Base SHA-256:

`e683b1b40ce0691d5ca9e48ebd2bc3b507d10bab485be0acd3f61aefc9242ad9`

Output APK: `build_outputs/Hud-engaged-path-v11-disengaged-icons-signed.apk`

Output SHA-256:

`337126b46210dee8be081ba6fcf8622b942a979f55d6bd06af214f74c667af57`

The `src` directory contains the Java source for the alert banner. The `smali`
directory contains the complete replacement classes used in the APK, including
the receiver integration. Replace these files in the apktool-decoded base APK,
then rebuild, zipalign, and sign with `build_keys/navdy-test.jks`.

Behavior:

- Keeps the stock driving HUD visible while openpilot is disengaged and shows
  set speed, openpilot status, turn-signal, and BSM icons in dashboard positions.
- Moves status icons to the engaged layout and shows the custom path, lanes,
  current speed, and music only while openpilot is actively engaged.
- Keeps the alert banner independent so no-entry and disengagement alerts can
  still appear over the stock HUD.
- Reads `alertText1`, `alertText2`, `alertType`, `alertStatus`, and `alertSize`.
- Slides a 640x100 banner down at y=120 over the driving HUD.
- Uses black, orange, or red based on alert status.
- Does not restart animation for repeated copies of the same event.
- Slides up and hides when the alert clears.
- Uses the same camera speed limit as the ambient-light overspeed warning.
- Changes the openpilot current-speed value to red only while current speed is
  greater than the camera speed limit, then restores white immediately.
- Keeps the camera-speed comparison double in `v8/v9` so Android 5 verifies
  `OpenpilotStateReceiver` without clobbering the log tag in `v3`.
- Retains the last valid path while fast state-only payloads update icons,
  speed, set speed, alerts, and music independently.
