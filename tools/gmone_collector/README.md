# GMOne direct collector

This replaces the Android accessibility scraper with a headless process that
talks to the official GMOne server, archives vehicle data locally, and
publishes the existing `/car_status` schema or the authenticated Wayon GMOne
ingest endpoint consumed by My Traverse and Wayon Cloud.

The direct status endpoint is preferred. The official app's current screen can
also be newer than its Firebase RTDB node because direct refresh responses and
FCM pushes are saved into app-local SharedPreferences. The collector therefore
persists every successful direct result and uses authenticated RTDB only as a
timestamp-guarded fallback.

## Safety boundary

The background client permits only these protocol operations:

- `8`: account login
- `21`: vehicle status read
- `45`: running-cycle history read
- `59`: installed MultiPack option read
- `63`: MultiPack information read
- `70`: EV charge history read

Vehicle control operation `19` and every other mutation are rejected by the
collector. A separate `gmone_control.py` module contains the official app's 12
named commands, but it is disabled by default and is not imported or called by
the background process. See `PROTOCOL.md` for the complete capability map.

Passwords and session tokens are never written to the repository, logs, state
file, or local database. The database sanitizer also removes VIN, account UUID,
email, phone number, IMEI, ICCID, and token/key fields from nested payloads.

The official Firebase API key is loaded from `GMONE_FIREBASE_API_KEY` or the
macOS Keychain service `com.wayon.gmone-collector.firebase-api-key`. Although
the key is part of the public app configuration, it is kept out of this
repository. Firebase ID tokens are retained in memory only, and authenticated
URL query parameters are redacted from errors.

## macOS verification

Store the account in macOS Keychain under service
`com.wayon.gmone-collector.password`. The Keychain item's account field is the
login email and its secret is the password.

Run one read without publishing:

```bash
python3 -m tools.gmone_collector.gmone_collector --once --dry-run --json
```

Run one read and publish the compatible Firebase fields:

```bash
python3 -m tools.gmone_collector.gmone_collector --once --json
```

For temporary background verification on this Mac, install
`com.wayon.gmone-collector.plist` into `~/Library/LaunchAgents/`. It checks the
official cached status every minute without asking the vehicle to refresh and
reuses the in-memory session token until authentication expires. Copy both
`gmone_collector.py` and `gmone_store.py` to
`~/Library/Application Support/Wayon/GmoneCollector/` first; macOS blocks a
LaunchAgent from directly reading source files under `Documents`.

When the in-vehicle module is asleep, GMOne returns
`inside_not_connected`. The collector then reads the official app cache. If
both sources are unavailable, it updates only diagnostic fields and does not
erase the last valid fuel, mileage, oil, battery, range, or tire data.
Official cache data older than 24 hours is treated as stale and is never
published over newer My Traverse data. The threshold can be changed with
`--max-cache-age-hours` when needed.

Successful raw status, option, module-info, and EV responses are archived at
`~/.local/share/wayon/gmone.sqlite3`. Running cycles are deduplicated by server
timestamp, so subsequent refreshes append history instead of replacing it. The
small cursor file at `~/.local/state/wayon/gmone-collector.json` tracks the last
cycle already requested.

## HYUKLEE-SERVER deployment

HYUKLEE-SERVER runs Windows 11. Install Python 3.12 and `keyring`, store the
GMOne password, official Firebase API key, and dedicated Wayon GMOne token in
Windows Credential Manager, and run the collector from Task Scheduler. The
login email may be set as `GMONE_EMAIL`; credentials must not be placed in task
arguments or Git.

```text
GMONE_EMAIL=...
WAYON_CLOUD_URL=https://wayon-cloud.hyuklee.workers.dev
```

Recommended service command:

```bash
python -m tools.gmone_collector.gmone_collector \
  --poll-seconds 60 \
  --wayon-url https://wayon-cloud.hyuklee.workers.dev \
  --no-firebase
```

The process checks `/api/gmone/refresh` every 30 seconds while sleeping. Normal
polls read only the official cached status; the operation-21 vehicle request is
sent only after this endpoint reports a pending manual or scheduled request.
My Traverse schedules that request once per hour only while its automatic
refresh setting is enabled. Each
successful upload replaces one `gmone_latest` D1 row; it does not append a row
on every poll. The server package uses the same SQLite archive and cursor file.
Keep the data and log directories readable only by the service account.
