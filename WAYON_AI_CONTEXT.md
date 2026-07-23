# Wayon AI Context

This is the single-file handoff for an AI working with the owner's Wayon
vehicle system. It is self-contained: read this file before using Wayon data.

Last verified: 2026-07-20 KST

Gateway baseline commit: `a1eeb531` on `leehyuk1108/Wayon`, branch `Sunnypilot`

Cloud Worker: `wayon-cloud`

Cloud URL: `https://wayon-cloud.hyuklee.workers.dev`

## 1. Agent boot instructions

1. Answer the owner in Korean unless another language is requested.
2. For any current-state question, call `wayon_get_context` or
   `GET /api/ai/context` first.
3. Read `freshness.stale`, `telemetryUpdatedAt`, and `telemetryAgeSeconds`
   before describing data as current or live.
4. Keep every unit exactly as labeled. Do not silently convert or combine
   electrical measurements.
5. Treat exact location, routes, and driver-camera images as sensitive.
6. This AI interface is read-only. Never claim it controlled the car, comma,
   Navdy, ambient lighting, locks, SSH, or software updates.
7. Impact sensor data is evidence of motion, not proof of collision or damage.
8. Do not modify driving, steering, braking, acceleration, CAN safety, or driver
   monitoring behavior unless the owner explicitly starts a separate coding
   task and validates the vehicle state.

## 2. What Wayon is

Wayon is the owner's integrated vehicle platform built around a comma device
running a customized Sunnypilot branch. It connects these components:

- **comma device / Sunnypilot**: reads vehicle and device state, runs openpilot,
  records routes, detects offroad impacts, and uploads low-rate telemetry.
- **Wayon Cloud**: Cloudflare Worker API and dashboard. D1 stores structured
  state/history; KV stores JPEG snapshots.
- **Firebase vehicle status**: legacy/additional vehicle information consumed by
  Wayon Cloud and My Traverse.
- **My Traverse**: Android and Wear OS app for vehicle status, trips, parking,
  lock, impact notifications, and impact camera viewing.
- **Navdy HUD**: receives a separate live HUD stream from comma. It is not part
  of the read-only AI API described here.
- **Ambient lighting controller**: controlled through the Navdy-side Bluetooth
  integration. It is not exposed to this AI API.
- **Offroad remote SSH**: separate Cloudflare tunnel used for maintenance only
  while comma is offroad. AI read credentials do not grant SSH access.

Primary local source trees:

- Sunnypilot/Wayon: `/Users/ijonghyeog/Documents/sunnypilot`
- My Traverse: `/Users/ijonghyeog/AndroidStudioProjects/carcontroller_b`
- Navdy work: `/Users/ijonghyeog/Documents/navdy`

Git remotes for the comma source tree:

- Working fork: `git@github.com:leehyuk1108/Wayon.git`
- Active branch: `Sunnypilot`
- Historical base remote: `https://github.com/HyukLee-og/sunnypilot.git`

## 3. System architecture

```text
Vehicle CAN + comma sensors/cameras
                 |
                 v
  carState / pandaStates / deviceState / selfdriveState / GPS
                 |
                 v
      system.wayon_cloud_uploader
       |          |            |
       |          |            +--> JPEG snapshot upload
       |          +--> route summaries
       +--> telemetry + queued vehicle/impact events
                 |
                 v
         Cloudflare Worker
          |      |      |
          |      |      +--> Firebase vehicle status fetch
          |      +--> KV: wide/driver JPEG images
          +--> D1: latest state, trips, events, image metadata
                 |
        +--------+------------------+
        |                           |
        v                           v
  My Traverse / dashboard      Read-only AI API
                                   |
                         OpenAPI or local MCP server
```

The telemetry uploader reuses messages already available on comma. It does not
add raw CAN polling and does not increase the vehicle communication frequency.

Configured upload cadence:

- Onroad telemetry: normally every 15 seconds.
- Offroad telemetry: normally every 300 seconds.
- Offroad periodic snapshots: normally every 3600 seconds.
- Route points: sampled/downsampled for summaries; they are not a real-time
  high-frequency trace.

The uploader enforces a minimum telemetry interval of 5 seconds even if a bad
configuration requests a shorter interval.

## 4. Authentication and security boundary

AI requests use a dedicated secret named `WAYON_AI_READ_TOKEN`.

Local credential file:

```text
~/.config/wayon/ai.credentials.json
```

Expected format:

```json
{
  "endpoint": "https://wayon-cloud.hyuklee.workers.dev",
  "token": "owner-supplied-secret"
}
```

The real file must remain mode `0600` and must never be committed, pasted into
prompts, or printed in logs. A local AI running as the owner can use this file.
A hosted AI must receive the token through its encrypted Bearer-auth secret UI.

Security properties:

- AI token is accepted only by `/api/ai/*` routes.
- All AI routes use `GET`.
- AI token cannot call upload endpoints.
- AI token cannot use legacy view-token endpoints.
- AI token cannot open remote SSH.
- AI token cannot update software or control vehicle functions.
- Snapshot access uses database snapshot IDs, not caller-supplied KV keys.

To rotate the AI token:

```sh
cd /Users/ijonghyeog/Documents/sunnypilot/cloudflare/wayon-cloud
openssl rand -hex 32
npx wrangler secret put WAYON_AI_READ_TOKEN
```

Update the local credential file separately after rotation. Never place the
token directly in a shell history command.

## 5. Connecting another AI

### 5.1 OpenAPI / ChatGPT Action

Import this URL:

```text
https://wayon-cloud.hyuklee.workers.dev/wayon-ai-openapi.json
```

Configure HTTP Bearer authentication with `WAYON_AI_READ_TOKEN`. Use the system
prompt in section 13 of this file.

### 5.2 MCP / Codex / Claude Desktop

MCP server:

```text
/Users/ijonghyeog/Documents/sunnypilot/cloudflare/wayon-cloud/ai/wayon_mcp_server.mjs
```

It requires Node.js 18 or newer, has no npm dependencies, uses stdio JSON-RPC,
and reads the credential file above.

Codex configuration:

```toml
[mcp_servers.wayon]
command = "/opt/homebrew/bin/node"
args = ["/Users/ijonghyeog/Documents/sunnypilot/cloudflare/wayon-cloud/ai/wayon_mcp_server.mjs"]
startup_timeout_sec = 30
enabled = true
```

Claude Desktop configuration:

```json
{
  "mcpServers": {
    "wayon": {
      "command": "/opt/homebrew/bin/node",
      "args": [
        "/Users/ijonghyeog/Documents/sunnypilot/cloudflare/wayon-cloud/ai/wayon_mcp_server.mjs"
      ]
    }
  }
}
```

Restart the AI client after changing MCP configuration.

Available MCP tools:

- `wayon_get_context`: current normalized state plus recent history.
- `wayon_list_trips`: recent trip summaries.
- `wayon_get_trip`: one trip with route points.
- `wayon_list_impacts`: impact measurements and associated image IDs.
- `wayon_list_vehicle_events`: lock/unlock and parked-unlocked events.
- `wayon_list_snapshots`: snapshot metadata and impact associations.
- `wayon_get_snapshot_image`: returns a JPEG as an MCP image content block.

## 6. HTTP API

Base URL:

```text
https://wayon-cloud.hyuklee.workers.dev
```

Every request below requires:

```http
Authorization: Bearer WAYON_AI_READ_TOKEN
```

Endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/ai/context` | Current normalized context and recent history |
| GET | `/api/ai/trips?limit=25` | Trip summaries |
| GET | `/api/ai/trips/:tripId` | Trip with route points |
| GET | `/api/ai/impacts?limit=25` | Impact history and image IDs |
| GET | `/api/ai/events?limit=50` | Lock and parked-unlocked history |
| GET | `/api/ai/snapshots?limit=25` | Camera snapshot metadata |
| GET | `/api/ai/images/:snapshotId` | Authorized JPEG image |

Context query limits:

```text
/api/ai/context?impacts=8&events=20&snapshots=12
```

Example without exposing the token in the command:

```sh
TOKEN=$(python3 -c 'import json, pathlib; print(json.loads(pathlib.Path.home().joinpath(".config/wayon/ai.credentials.json").read_text())["token"])')
curl -H "Authorization: Bearer $TOKEN" \
  'https://wayon-cloud.hyuklee.workers.dev/api/ai/context'
```

## 7. `/api/ai/context` contract

Top-level response:

```json
{
  "schemaVersion": "wayon-ai-context-v1",
  "generatedAt": "ISO-8601 UTC",
  "access": {},
  "freshness": {},
  "live": {},
  "firebaseVehicleStatus": {},
  "latestTrip": {},
  "recentImpacts": [],
  "recentVehicleEvents": [],
  "recentSnapshots": [],
  "rawTelemetry": {}
}
```

### 7.1 Freshness

Fields:

- `telemetryUpdatedAt`: time comma uploaded the latest telemetry.
- `telemetryAgeSeconds`: age when the API response was generated.
- `staleAfterSeconds`: 45 onroad, 600 offroad.
- `stale`: authoritative stale decision for ordinary AI answers.
- `expectedUploadIntervalSeconds`: normally 15 onroad, 300 offroad.

Rules:

- If `stale` is true, say “last reported” and include the update time.
- Do not call a stale position the current parking position.
- `gps.freshAtUpload` only means GPS was fresh when comma uploaded it.
- Offroad speed is intentionally reported as zero.

### 7.2 `live.vehicle`

Potential fields:

- `speedMps`, `speedKph`, `speedSource`
- `rawSpeedMps`, `accelerationMps2`, `yawRateRadPerSec`
- `standstill`, `gear`
- `steeringAngleDeg`, `steeringRateDegPerSec`, `steeringPressed`
- `gasPressed`, `brakePressed`, `parkingBrake`, `brakeHoldActive`
- `leftBlinker`, `rightBlinker`
- `leftBlindspot`, `rightBlindspot`
- `doorOpen`, `seatbeltUnlatched`
- `fuelGauge`, `charging`
- `can.valid`, `can.timeout`, `can.errorCounter`
- `steeringFault.temporary`, `steeringFault.permanent`
- `cruise.enabled`, `cruise.available`, `cruise.standstill`
- `cruise.nonAdaptive`, `cruise.speedMps`, `cruise.speedKph`
- `location.latitude`, `location.longitude`, `location.bearingDeg`
- `location.accuracyM`, `location.source`, `location.freshAtUpload`

Detailed `carState` data is available only while onroad. Offroad returns
`available: false` with reason `offroad`.

Vehicle display speed prefers `vEgoCluster` when nonzero and otherwise uses
`vEgo`. This is not GPS speed.

### 7.3 `live.openpilot`

Fields:

- `state`: `disabled`, `preEnabled`, `enabled`, `softDisabling`, or `overriding`.
- `enabled`: openpilot is logically enabled.
- `active`: controls are actively commanding where applicable.
- `engageable`: current conditions allow an engagement attempt.
- `experimentalMode`, `personality`
- `alert.text1`, `alert.text2`, `alert.type`
- `alert.status`, `alert.size`, `alert.sound`, `alert.hudVisual`

Do not treat `enabled`, `active`, and `engageable` as synonyms.

### 7.4 `live.electrical`

Fields and meaning:

- `vehicleBusVoltageV`: Panda/comma interface vehicle supply voltage in volts.
- `vehicleCurrentMa`: interface current reading in milliamps.
- `estimatedVehicleInputPowerW`: `voltage V * current mA / 1000`.
- `commaDevicePowerDrawW`: `deviceState.powerDrawW`.
- `commaSomPowerDrawW`: system-on-module power reading.
- `offroadEnergyUsedWh`: cumulative offroad energy value converted to Wh.
- `estimatedCarBatteryCapacityWh`: comma's battery-capacity estimate in Wh.

Important limitations:

- Estimated input power is not total vehicle electrical consumption.
- Interface current and comma device power are different measurements.
- A zero device power reading can be a sensor/platform behavior; use SoM power
  and freshness before concluding the device consumes zero power.
- Never use these values to infer battery health without a time series and
  vehicle-specific context.

### 7.5 `live.thermal`

Fields:

- `status`: comma thermal status such as `ok`, `overheated`, or `critical`.
- `fanPercent`: desired fan percentage.
- `temperaturesC.cpu`: per-core/list CPU temperatures.
- `temperaturesC.gpu`: GPU temperature list.
- `temperaturesC.dsp`, `memory`, `modem`, `pmic`
- `temperaturesC.intake`, `exhaust`, `gnss`, `bottomSoc`, `max`
- `temperaturesC.zones`: named thermal zones where available.

All temperatures are Celsius. Use `max` plus `status`; do not diagnose a fault
from one sensor sample alone.

### 7.6 `live.system`

Fields:

- `deviceType`
- `usage.freeSpacePercent`
- `usage.memoryPercent`, `usage.gpuPercent`
- `usage.cpuPercent`: list per CPU/core
- `network.type`, `network.strength`, `network.metered`
- `screenBrightnessPercent`

### 7.7 `live.commaInterface`

This is a curated `pandaStates` health view:

- Panda type, ignition line/CAN state, voltage/current/power estimate
- fault status and fault list
- uptime, heartbeat loss, interrupt load
- RX/TX overflow and SPI error counters
- harness status
- controls allowed flags
- safety model/parameter and safety counters

These values describe interface/safety state. They do not authorize an AI to
send CAN or change safety configuration.

### 7.8 Firebase vehicle status

`firebaseVehicleStatus` is fetched from:

```text
https://mycarserver-fb85e-default-rtdb.firebaseio.com/car_status.json
```

It may contain battery, fuel, range, odometer, tire pressure, oil, and DTC data.
The wrapper `updatedAt` is the Cloud fetch time, not necessarily the time every
underlying vehicle field was measured. Prefer an embedded source timestamp when
one exists.

### 7.9 Raw telemetry

`rawTelemetry` preserves the complete latest comma upload for forward
compatibility. Prefer normalized `live` fields for ordinary answers. Use raw
telemetry only when a normalized field is missing or when debugging schema.

## 8. Trips and location

Trip summaries include:

- start/end times
- duration and distance
- start/end coordinates
- route point count
- average and maximum speed where available

`wayon_get_trip` or `/api/ai/trips/:tripId` includes route points. Route data is
downsampled and should not be interpreted as lane-level ground truth.

Location selection can fall back in this order when fresh GPS is unavailable:

1. Fresh GPS message.
2. Latest completed trip endpoint.
3. Last stored valid position.

Always pair location with freshness and source.

## 9. Vehicle events

Known event types:

- `door_lock` with `locked: true`: vehicle lock became active.
- `door_lock` with `locked: false`: vehicle lock became inactive.
- `parking_unlocked`: vehicle remained unlocked after offroad transition for
  the configured delay, normally 180 seconds.

Events include occurrence time, Cloud receive time, notification count, and raw
details. A missing event does not prove the physical lock never changed; CAN,
device power, network, or upload availability may have interrupted observation.

## 10. Impact detection

Impact detection runs on comma while offroad. Current configured policy:

- IMU samples must warm up and arm.
- Vehicle lock state must be known and locked.
- Lock must remain stable for the lock arm delay, normally 3 seconds.
- Unlock pauses detection immediately.
- Detector uses dynamic acceleration, jerk, gyro, impulse/strong thresholds,
  and cooldown logic.
- A detected event requests wide-road and driver-camera JPEG capture.
- Events/media remain queued locally until Cloud upload succeeds.

Impact fields:

- `severity`
- `peakDynamicG`
- `peakTotalG`
- `peakJerkGPerSec`
- `peakGyroRadPerSec`
- `durationMs`, `sampleCount`, `sensorClipped`
- event location when available
- `capture.status`, `capture.capturedAt`, `capture.attempts`
- wide and driver snapshot IDs/image URLs

Capture status meanings:

- `pending`: event exists; media upload not complete.
- `complete`: both wide and driver images stored.
- `partial`: only one image stored.
- `failed`: capture attempts ended without usable images.
- `not_requested` or `not_available`: no image was requested/available.

An impact can be a door slam, vehicle shake, road vibration, or other motion.
Never assert collision or damage solely from this event.

## 11. Image workflow

To inspect an impact image:

1. Call `wayon_list_impacts`.
2. Select the intended event by ID and timestamp.
3. Read `capture.wideSnapshotId` or `capture.driverSnapshotId`.
4. Call `wayon_get_snapshot_image` with that ID.
5. State camera type and capture timestamp when discussing the image.

HTTP equivalent:

```text
GET /api/ai/images/:snapshotId
```

The response is `image/jpeg`. Driver-camera images are private cabin data. Do
not retrieve them merely because they are available; retrieve only for an
explicit owner request relevant to the task.

## 12. What this gateway does not expose

Current AI API does not provide:

- raw CAN frames
- live radar tracks or modelV2 lane/path arrays
- live Navdy rendering state
- ambient Bluetooth control
- camera video streams
- SSH shell access
- process restart, reboot, update, or Git operations
- steering, acceleration, braking, or lock commands

Those systems may exist elsewhere in Wayon, but absence from this API must not
be filled by guessing. A future read-only endpoint must be added deliberately if
an AI needs one of these data sources.

## 13. Copy-ready system prompt

```text
You are the owner's read-only Wayon vehicle assistant.

Use Wayon tools as direct evidence. Before answering any current vehicle or
comma question, call wayon_get_context. Check freshness.stale,
telemetryUpdatedAt, and telemetryAgeSeconds. If stale, describe values as last
reported and include the update time.

Preserve units exactly. Distinguish vehicleBusVoltageV, vehicleCurrentMa,
estimatedVehicleInputPowerW, commaDevicePowerDrawW, and commaSomPowerDrawW.
They are not interchangeable. Temperatures are Celsius. Distinguish OpenPilot
enabled, active, and engageable.

Treat precise location, trip routes, and driver-camera images as sensitive.
Only retrieve or disclose them when the owner explicitly requests them. An
impact event is sensor evidence, not proof of collision or damage.

This interface is read-only. It cannot control the car, comma, Navdy, ambient
lighting, locks, steering, acceleration, brakes, SSH, reboots, updates, or Git.
Never claim an action was performed. If requested data is not exposed, say so
instead of guessing.

For impact images, list impacts first, select the event by ID/time, and then use
wayon_get_snapshot_image with its wideSnapshotId or driverSnapshotId.

Answer in Korean unless the owner requests another language. Keep conclusions
grounded in returned timestamps, values, status flags, and source fields.
```

## 14. Common task recipes

### “현재 콤마 온도와 전압 알려줘”

1. Call `wayon_get_context`.
2. Verify freshness.
3. Report `live.electrical.vehicleBusVoltageV`.
4. Report `live.thermal.temperaturesC.max` and useful CPU/GPU values.
5. Include thermal status and telemetry time.

### “지금 주행 중이야?”

Use `live.onroad`, `live.ignition`, `live.vehicle.speedKph`, and freshness. Do
not rely on only one field.

### “오픈파일럿 인게이지 상태야?”

Use `live.openpilot.enabled` and `live.openpilot.active`. Include state and
freshness. Do not infer from speed.

### “최근 충격과 사진 보여줘”

List impacts, report event metrics/time/capture status, then load only requested
wide or driver image by snapshot ID.

### “주차 위치 알려줘”

Use `live.vehicle.location`, location source, telemetry time, and stale state.
If stale, call it the last reported position.

### “최근 주행 분석해줘”

List trips, select a trip ID, fetch its route, then analyze duration, distance,
speeds, and route points. State that route data is downsampled.

## 15. Source-of-truth files

An AI should not need these files to understand the system, but these are the
implementation locations when code changes are requested:

- Telemetry, routes, event/media upload:
  `system/wayon_cloud_uploader.py`
- Impact and lock daemon:
  `system/wayon_impactd.py`
- Impact detector, lock parser, event queue:
  `system/wayon_impact.py`
- Vehicle event queue/reminder:
  `system/wayon_vehicle_events.py`
- Worker API/auth/storage:
  `cloudflare/wayon-cloud/src/worker.js`
- D1 schema:
  `cloudflare/wayon-cloud/schema.sql`
- Impact media migration:
  `cloudflare/wayon-cloud/migrations/0001_impact_media.sql`
- OpenAPI document:
  `cloudflare/wayon-cloud/public/wayon-ai-openapi.json`
- MCP server:
  `cloudflare/wayon-cloud/ai/wayon_mcp_server.mjs`
- Device configuration example:
  `cloudflare/wayon-cloud/device_config.example.json`

Cloud storage:

- D1 database binding: `DB`, database `wayon_cloud`
- KV binding: `SNAPSHOTS`, namespace `WAYON_SNAPSHOTS`
- D1 tables: `latest_state`, `trips`, `snapshots`, `impact_events`,
  `vehicle_events`, `push_subscriptions`

## 16. Deployment and verification

Deploy Worker:

```sh
cd /Users/ijonghyeog/Documents/sunnypilot/cloudflare/wayon-cloud
npx wrangler deploy
```

Install uploader on comma while safely offroad:

```sh
scp /Users/ijonghyeog/Documents/sunnypilot/system/wayon_cloud_uploader.py \
  wayon-comma:/tmp/wayon_cloud_uploader.py
ssh wayon-comma 'cd /data/openpilot && python3 -m py_compile /tmp/wayon_cloud_uploader.py && cp /tmp/wayon_cloud_uploader.py system/wayon_cloud_uploader.py'
```

The manager preimports Python modules. Killing only `wayon_cloud_uploader` after
replacing its file can fork the old in-memory module again. A safe offroad comma
reboot is required to guarantee loading the new uploader.

Minimum verification checklist:

1. Unauthenticated `/api/ai/context?nonce=...` returns `401`.
2. AI token can read `/api/ai/context`, trips, events, and snapshots.
3. AI token receives `401` from `POST /api/telemetry`.
4. Context reports `rawTelemetry.schemaVersion = wayon-telemetry-v2`.
5. Numeric temperatures and SoM power are non-null when sensors report them.
6. MCP tool list contains seven Wayon tools.
7. Snapshot tool returns an image block with JPEG magic bytes `FF D8`.
8. No credential or token exists in Git diff/history.

Last end-to-end verification on 2026-07-20 confirmed:

- telemetry schema `wayon-telemetry-v2`
- read-only context schema `wayon-ai-context-v1`
- numeric voltage/current/power and CPU/GPU/max temperatures
- impact/event/snapshot listing
- MCP JPEG image response
- unauthenticated AI request rejected
- AI token rejected by write and legacy read endpoints

These values are proof of that test only, not permanent live values. Always call
the current context for a new answer.

## 17. Change discipline

- Keep AI API read-only.
- Never reuse upload, SSH, push-registration, or view credentials as AI token.
- Do not increase onroad telemetry cadence without measuring comma load and
  getting owner approval.
- Add new values from already published cereal services where possible.
- Preserve top-level telemetry fields for existing dashboard/app compatibility.
- Add schema versions when response contracts change.
- Normalize units at the producer/API boundary and document them here.
- Test auth denial as well as successful reads.
- Test image bytes, not only metadata.
- Update this file whenever endpoints, fields, intervals, or safety boundaries
  change so it remains the single-file handoff.
