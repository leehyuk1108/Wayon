# Engaged Path v15 Road Edges

Base APK: `build_outputs/Hud-engaged-path-v14-music-metadata-signed.apk`

Base SHA-256:

`ddb225baa5510140003423778dfac9b0d06a0762d8455c373d41f24708f5e4e9`

Output APK: `build_outputs/Hud-engaged-path-v15-road-edges-signed.apk`

Output SHA-256:

`6f7581a3287fbd5ba7402dad3f3cf68344a928845537d7882295d36336b3576c`

The `src` directory contains Java sources for the alert banner and outside
temperature view. The `smali` directory contains the complete replacement
classes used in the APK, including the receiver integration. The `res` directory
contains the replacement dashboard layout. Replace these files in the
apktool-decoded base APK, then rebuild, zipalign, and sign with
`build_keys/navdy-test.jks`.

Behavior:

- Keeps the stock driving HUD visible while openpilot is disengaged and shows
  set speed, openpilot status, turn-signal, and BSM icons in dashboard positions.
- Uses the same Android system typeface for the center speed while disengaged as
  the custom engaged speed, while retaining the stock 66sp size and layout.
- Binds the dashboard temperature view when the layout is inflated and refreshes
  standard OBD ambient-air-temperature PID `0x46` every five seconds.
- Moves status icons to the engaged layout and shows the custom path, lanes,
  current speed, and music only while openpilot is actively engaged.
- Shows music as `artist - title` in both stock and engaged layouts, and restores
  the current track whenever the dashboard view is recreated.
- Draws the left and right `modelV2.roadEdges` as dim boundary lines while
  engaged. Every path, lane, and road-edge line is capped at 10 projected points.
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
