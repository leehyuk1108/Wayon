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

- Keeps Zone 1 ambient lighting on the existing screen-driven automatic
  brightness curve while fixing the independent Zone 2 brightness channel at
  30 percent.
- Keeps the stock driving HUD visible while openpilot is disengaged and shows
  set speed, openpilot status, turn-signal, and BSM icons in dashboard positions.
- Uses the same Android system typeface for the center speed while disengaged as
  the custom engaged speed, while retaining the stock 66sp size and layout.
- Binds the dashboard temperature view when the layout is inflated, reads
  standard OBD ambient-air-temperature PID `0x46` immediately, and limits
  subsequent reads to once every five seconds.
- Moves status icons to the engaged layout and shows the custom path, lanes,
  current speed, and music only while openpilot is actively engaged.
- Shows fixed white accelerator and brake pedal icons side by side while
  openpilot is engaged. Physical accelerator output fills the accelerator
  circle in blue and GM friction-brake output fills the brake circle in red,
  without a separate outline. Coast leaves both icons unfilled and
  disengagement hides the pair.
- Shows music as `artist - title` in both stock and engaged layouts, and restores
  the current track whenever the dashboard view is recreated.
- Draws all four `modelV2.laneLines` as classified dashed or solid lines.
- Renders classified yellow markings as center lines, with unknown markings
  retaining the legacy animated 56px/24px dashed fallback.
- Animates lane dashes at 18-80 pixels per second based on vehicle speed.
- Keeps only one pending dash-animation repaint so repeated socket updates
  cannot multiply render callbacks and stall the Navdy main thread.
- Uses 3.2px lane strokes, 2.8px road-edge strokes, and a stronger
  0x55-to-0xff distance gradient so projected boundaries remain legible.
- Draws `modelV2.roadEdges` as red solid lines only when `1 - roadEdgeStd` is
  at least 0.5, with alpha `confidence * 210 + 25`. Every path, lane, and
  road-edge line is capped at 10 projected points.
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
- Keeps the stock SmartDash camera card at its original dashboard-relative
  position. The full-screen openpilot mirror remains attached but its parent is
  hidden, preventing a duplicate card from appearing higher on the physical
  640x480 panel.
- The hidden mirror still tracks the latest camera speed and distance for
  protocol compatibility. Three-digit limits shrink to 26sp so 100 and 110
  remain centered inside the stock 62px speed-sign circle.
- Uses the same Android system typeface and normal weight as the music-title row
  for camera distance, without changing its stock 16sp size or position.
- Displays camera distances below 1000m in meters and converts 1000m or more
  to a rounded one-decimal kilometre value, such as `1340m` to `1.3km`.
- Detects CommANav mobile-enforcement notifications from their explicit
  `Tmap Mobile Camera SDI`/`이동식` type marker and changes both HUD camera
  circles from a red rim to a blue rim.
- Returns the detected `cameraType` through the existing USB socket feedback;
  ICBM ignores `mobile` cameras while fixed, box, rear-enforcement, and section
  camera limits continue to use automatic cruise-button speed control.
- Retains the last valid path while fast state-only payloads update icons,
  speed, set speed, alerts, and music independently.
- Coalesces socket updates on the Android main looper so an overloaded frame
  queue keeps only the newest vehicle state instead of replaying stale frames.
- Omits full per-frame payload/state logging to reduce allocation and log I/O on
  the Navdy hardware.
- Recovers from a dead Android Bluetooth GATT binder by discarding the stale
  connection and characteristics, preserving the pending ambient command, and
  scheduling a fresh scan instead of remaining falsely connected.
