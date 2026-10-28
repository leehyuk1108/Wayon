# Background Vehicle State

`gmone_background.py` collects status independently of the Android application.
The phone's existing cache-first reader and account-scoped snapshot publisher
remain enabled. The background process must use the same verified account,
Cloud device ID and application-derived scope.

## Runtime

- Poll the official cached status every 60 seconds. A changed source observation
  is uploaded to Wayon Cloud D1 without opening the phone app.
- If no recent observation exists, request status at most once per hour. An
  explicit refresh can request it sooner, with a five-minute minimum gap and a
  persisted maximum of 36 requests per 24 hours. These requests may wake the
  vehicle communications module. Parked battery impact has not been measured.
- No lock, engine, window, horn, DTC scan/clear or other control operations.
  Only login (8), status (21, `refresh_dtc=false`) and result (66) are permitted.
  History cursors come only from prior server responses (zero on first read),
  never an inferred wall-clock value. Responses are capped at 512 KiB.
- Preserve observation timestamps. Upload time does not make old information
  current. Offline vehicles retain their previous information, not fabricated
  updates. This is polling, not an instantaneous vehicle event subscription.
- Persist the newest pending snapshot before upload. Network errors retry with
  bounded backoff. Only successful ACK or explicit `snapshot_not_newer` conflict
  removes it. Check the Cloud device identity before every upload cycle.
- GMOne login and official-cache failures back off to one hour. Cloud outages
  do not reset GMOne authentication or initiate new direct vehicle reads.

## Windows Installation

Install under the existing user-owned `%LOCALAPPDATA%\Wayon\GMOne` directory.
Keep credentials in the existing Windows Credential Manager; never copy them
into JSON, task arguments, logs or the repository. `config/gmone.json` contains
the existing email only. `config/background.json` contains only:

```json
{
  "url": "https://wayon-cloud.hyuklee.workers.dev",
  "deviceId": "verified-existing-device-id",
  "clientScope": "64-lowercase-hex-from-the-installed-app",
  "accountFingerprint": "sha256-of-normalized-email-for-local-mismatch-check"
}
```

The account fingerprint is a local consistency check, not authentication and
not an anonymization guarantee. The client scope must come from the app's
existing HMAC derivation, never a newly invented identifier.

Copy `gmone_background.py`, `gmone_collector.py`, `gmone_store.py` and
`install_background_task.ps1` to `app/`. Run the installer as the existing
credential-owning user only after stopping/reviewing the old collector task.
It backs up and replaces **Wayon GMOne Collector**. Logs rotate; health and
retry state reside in `data/`. Preserve the existing private directory ACLs.

**The Windows user must remain logged in and the server must be awake/online.**
The task uses that user's interactive credential session, runs at logon, and
has a five-minute recovery watchdog plus crash restart. Locking the desktop is
fine; logging out or rebooting without logging back in is not supported. SSH
sessions cannot read these credentials (`1312`); this is not bypassed. No
unattended Windows-login password or credential export is configured.

The phone may be closed or force-stopped. The Mac and Comma do not run this
collector and do not need to remain connected to it.

## Cloud And Rollback

The pinned patch under `cloudflare/wayon-cloud/patches/background-vehicle-state-20261028`
changes only collector refresh ACK semantics. No database migration,
new token, binding change or full working-tree Worker deployment is required.
The app uses the preserved source `updatedAt` for its cache-age policy. Existing
legacy `/api/json` merge and `ageSeconds` behavior are deliberately unchanged;
this patch does not repair that older reader's receipt-based freshness policy.
A cache receipt cannot satisfy a direct refresh.

Do not restore/re-enable the legacy collector after installing this patch:
it does not send the new `refreshStartedAt` ACK contract and can repeatedly
request direct reads. On failure stop the new task, preserve its state/logs,
and leave collection stopped while diagnosing. Roll back the Cloud deployment
independently if needed; do not re-register the backed-up XML or automatically
restart the old task.

## Verification

Run the three focused collector test files with `--confcutdir=tools/gmone_collector`
and `-n 0`. Cloud tests exercise the authenticated handlers, source age,
ordering, refresh timing and real local D1 concurrent writes. These do not
measure parked battery drain or physical vehicle sensor changes.

### 2026-10-28 Installation Evidence

- Final Python suite: 98 passed. Dependency-free native Windows state/lock
  tests: 2 passed. Cloud handler tests: 12 passed; workerd/D1: 73 assertions.
- The phone package was force-stopped and its process absent. The independent
  Windows task obtained a successful op-21/66 result and Cloud stored source
  `gmone-direct`, observation `2026-10-28T14:46:52.512Z`, receipt
  `2026-10-28T14:46:53.092Z`. Account scope matched, 17 top-level status fields
  were present, and the explicit refresh was marked complete. First status
  response was 63,424 bytes, below the 512 KiB cap.
- Restarting only the collector preserved the same latest observation, cleared
  outbox and five-attempt budget without another vehicle query. The task
  remained Running and continued its passive checks. Windows process inspection
  found one venv launcher and its child, not two independent collectors.
- Phone v32 was reopened without reinstalling. Native cached state appeared in
  the log at 5 ms; later cache selections at 1,522/3,399 ms preceded direct-ready
  at 10,997 ms and full-ready at 11,561 ms. These are native callback timings,
  not first-pixel measurements. Actual cover-display screenshot showed vehicle
  state and its new update time. The phone was returned to HOME.
- Claude reviewed the final collection/authentication logic and deployment
  procedure statically. Runtime evidence was collected separately by Codex.

Failures found during installation were not counted as success: a generated
wall-clock history cursor caused HTTP 400, so cursors now come only from server
responses; one accepted request timed out; a later completed async result was
incorrectly rejected for lacking a second login object. The final code checks
explicit authentication failures on the outer response and accepts the known
nested result format, with end-to-end regression coverage.

Not tested: Windows reboot before/after user logon, long parked battery draw,
multi-day reliability, or physical changes to doors/engine/windows. No such
vehicle commands were issued. Hourly automatic eligibility and daily budgets
were tested with clocks; the successful real-device read used the ordinary
manual-refresh queue while the phone app remained closed.
