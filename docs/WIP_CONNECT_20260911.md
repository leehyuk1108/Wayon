# Hylink Dev 1.6.1 — simple wip connection

Package `app.hylink.mobile.debug`, versionCode 9. Keep the approved dashboard.
Apple Design onboarding/accessibility principles were applied to the visible key entry,
inline validation/retry status, 48px+ targets and large-text reflow, without adding a top settings bar.

## Connect

With ignition off, join the comma's private Wi-Fi/hotspot network and open
`http://<comma IP>:1108`. The page contains only the key and a copy button.
Opening it automatically registers the device and enables telemetry, live/photos,
impact detection and remote terminal. Existing enrollments keep the same key.
This all-enabled default replaces the previous per-feature choices at the user's request.
Only a same-LAN, same-origin POST activates defaults; GET polling never re-enables
sharing stopped from the comma settings. Opening the page again does re-enable it.
Paste the key into Hylink's **Vehicle → Wayon Cloud key** (also available on an unconnected home).
The server checks a replacement key before the app saves it, retaining the old key on failure.
Do not share the key: it grants access to the selected vehicle's data and enabled remote features.

## Driving vs parking

The comma uploader remains onroad and offroad: 30s/300s heartbeat, important changes
at minimum 5s/15s cadence; ignition transitions update without waiting for the heartbeat.
The app's existing 30-second foreground polling/cache/backoff policy is unchanged.
This is sampled telemetry, not real-time CAN streaming or a guarantee to capture every transient alert.

Key page, qlog summaries, parking photos, IMU detection, live/clip capture and SSH
remain offroad-only on the comma. UI displays the received capability flags, requires
a recent explicit ignition-off state and explains disabled permissions.
Old vehicle senders without capability fields retain their offroad-only UI fallback.
Never use the phone gate instead of the device's independent freshness/ignition/voltage/temperature gate.

Impact detail links received photos by impact/snapshot ID. These are post-event
photos, not pre-impact recordings. Cloud upload retries reuse original photos.
Phone background FCM push is not implemented in this Hylink package; records appear when fetched.
No vehicle actuation, My Traverse New change or production Cloud change is included.

SSH now uses a dedicated offroad sshd on wip with short-lived per-session public keys,
without asking users to manually append their phone public key. No automatic shell commands
are executed by opening the app. Its input executor is separate from the blocking output loop.
App pause closes Live/SSH, and key change fences late native requests.

## Verification

- Gradle Android debug build and unit tests.
- `scripts/check-wip-onboarding.js` via Playwright CLI: key format, pending/error/retry,
  onroad speed/status remains visible, live/SSH consent gates, logout, 24 layouts
  (320/390/768/1100 widths × 100%/200% text × 3 tabs) and key-sheet reflow.
- Visual screenshot inspection of actual browser-rendered key entry.
- wip source tests and the real Wayon Worker source's offline telemetry contract.
- Existing signing certificate SHA-256:
  `55a14240fb656db17c66c695a61ae5679982a5ae24e233563a43211c5125fa94`.
  The Mac default debug keystore differs: re-sign with the restored original key held outside Git.
- Final APK SHA-256: `0027f43bc8ab84038697c6aab152563d122deeba247410e1dbff54c735fd5a7d`.
- Simple key page: automatic enrollment, stable key, copy API/HTTP fallback calls,
  stopped-state clearing, failure recovery and 16 light/dark/large-text layouts.
  Clipboard APIs are mocked to leave the user's actual system clipboard unchanged.

No connected phone was available for this build. No Trailblazer comma is remotely
accessible: real installation/boot, camera/IMU, SSH/systemd and driving-transition
acceptance are pending. Builds and mocked state transitions are not those checks.

The old README note about manually adding a phone SSH public key applies only to
older senders; wip-2's explicitly enabled remote feature handles short-lived keys.
