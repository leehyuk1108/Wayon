# Engaged Path v39 Curve-Aware Vehicle Yaw and Distance Scale

Base APK: `build_outputs/Hud-engaged-path-v38-curve-yaw-signed.apk`

Base SHA-256:

`0e9cd3e05d9a57bd80f9c2a43dcaeabbabaf1b827decea841dd834b54b7b5f6e`

Output APK: `build_outputs/Hud-engaged-path-v39-curve-yaw-distance-scale-signed.apk`

Output SHA-256:

`958b1a6a8a05c98a74dc76003b651db802ff2ea990882fc4d5d21f532922ced1`

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
- Binds the dashboard temperature view when the layout is inflated, reads
  standard OBD ambient-air-temperature PID `0x46` immediately, and limits
  subsequent reads to once every five seconds.
- Moves status icons to the engaged layout and shows the custom path, lanes,
  current speed, and music only while openpilot is actively engaged.
- Shows music as `artist - title` in both stock and engaged layouts, and restores
  the current track whenever the dashboard view is recreated.
- Draws all four `modelV2.laneLines` as animated 56px/24px dashed lines.
- Animates lane dashes at 18-80 pixels per second based on vehicle speed.
- Draws `modelV2.roadEdges` as solid lines only when `1 - roadEdgeStd` is at
  least 0.5. Every path, lane, and road-edge line is capped at 10 projected points.
- Reads GM long-range radar targets through the Navdy bridge without publishing
  them to `liveTracks`, `radarState`, or any controls process.
- Uses camera lane geometry to classify radar targets into left, current, and
  right lanes, and marks a target as fused when it matches a `modelV2.leadsV3`
  camera lead.
- Draws radar-only vehicles in white, camera-only vehicles in green, and fused
  vehicles in cyan. Thirteen pre-rendered rounded vehicle sprites preserve smooth
  shading without adding 3D work to the Navdy runtime.
- Preserves the straight-road perspective from screen-center thresholds, then
  adds each vehicle's local `modelV2` lane or path tangent at its distance.
- Selects the nearest mirrored sprite from Y 0 through 24 degrees in four-degree
  steps. Payloads without `yawDeg` retain the v37 screen-position fallback.
- Scales markers continuously from 58.5px nearby to 12px at 80m so distant
  vehicles no longer appear almost as large as close vehicles.
- Uses the confirmed X -6 degree body rotation, 13 degree camera FOV, and 2.25x
  distance-based marker scale for every lane.
- Keeps the alert banner independent so no-entry and disengagement alerts can
  still appear over the stock HUD.
- Reads `alertText1`, `alertText2`, `alertType`, `alertStatus`, and `alertSize`.
- Slides a 640x100 banner down at y=120 over the driving HUD.
- Uses black, orange, or red based on alert status.
- Uses translucent alpha 160 for normal, 170 for `userPrompt`, and 180 for
  critical alerts so HUD information remains visible behind the banner.
- Does not restart animation for repeated copies of the same event.
- Slides up and hides when the alert clears.
- Uses the same camera speed limit as the ambient-light overspeed warning.
- Changes the openpilot current-speed value to red only while current speed is
  greater than the camera speed limit, then restores white immediately.
- Applies the same camera overspeed red/white behavior to the stock current
  speed shown while openpilot is disengaged.
- Keeps the camera-speed comparison double in `v8/v9` so Android 5 verifies
  `OpenpilotStateReceiver` without clobbering the log tag in `v3`.
- Retains the last valid path while fast state-only payloads update icons,
  speed, set speed, alerts, and music independently.
- Coalesces socket updates on the Android main looper so an overloaded frame
  queue keeps only the newest vehicle state instead of replaying stale frames.
- Omits full per-frame payload/state logging to reduce allocation and log I/O on
  the Navdy hardware.
