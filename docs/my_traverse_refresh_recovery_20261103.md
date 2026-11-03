# My Traverse Refresh Recovery

## Confirmed Failure

Both Android Next and the iPhone PWA read the same GMOne snapshot service.
On November 3, the common observation stopped at 15:48:58 KST while the Windows
collector remained running. A requested refresh at 16:41:55 reached the collector
at 16:42:19 and failed with `AuthenticationError`.

The collector reserved `handledRequest` before obtaining any successful result.
After authentication recovered at 16:44:25, the request was therefore excluded
from retries. The error field was also cleared by a successful passive polling
cycle, despite the Cloud request remaining pending. The initiating reason for
the official session rejection (expiry versus another client's login) was not
established by those logs.

## Scope

Only the Windows collector implementation and its tests/documentation change.
No Android APK, PWA UI, Cloudflare Worker, database schema, account credentials,
vehicle controls, Comma, Navdy or Jetson code is changed.

- Acquire a current official session immediately before a budgeted direct read.
- Persist attempt reservations separately from server-confirmed completion.
- Retry failed reads at most three times per request, at least 300 seconds apart.
  Preserve the 36-attempt daily limit, hourly automatic cadence, restart state,
  one-hour request validity and account/device checks.
- Recover previously consumed but unacknowledged legacy requests without resetting
  counters. Never manufacture a newer observation time.
- Retain a direct-read outbox through network failures and passive-cache changes.
  Retry upload before considering another vehicle read, including the same-loop
  upload-success case. A newer server snapshot may win while the valid direct
  response separately acknowledges its refresh.
- Keep sanitized failure history; successful login alone is not a completed read.

## Verification

- Baseline source with the new recovery tests: 14 failed, 5 passed.
- Final focused Python suite: 115 passed.
- Windows staged-source native state, restart, legacy migration and exclusive-lock
  tests: 4 passed; no network or vehicle commands in these tests.
- Staged and installed collector SHA256:
  `aa030d5ffbb05cb7d76092ba1a6d10e3d8264d690f66aca04ee599e0019bf056`.
- The existing Windows scheduled task was stopped, its source/state/health/task
  definition backed up, and only `app/gmone_background.py` replaced. State was
  byte-identical before restart; credentials/configuration were untouched.
- First production read after deployment: direct operation/result succeeded,
  observation `2026-11-03T08:00:28.760Z`, receipt/refresh completion
  `2026-11-03T08:00:26.851Z`. The source clock runs ahead of the receipt clock;
  these are source timestamps, not independent physical sensor sampling proof.
- The previously pending 16:41 request completed without resetting the request
  budget. A subsequent poll recorded server-confirmed completion and empty outbox.
- Actual iPhone PWA home and Android Next vehicle-status screen both displayed
  the new 17:00 observation without reinstalling either app.

## Actual App Refresh

- Issued pull-to-refresh in the actual iPhone PWA through iPhone Mirroring and
  in the installed Android Next app through its phone debugging connection.
  Neither action used a simulated browser or a replacement test API client.
- The shared request was recorded at `2026-11-03T08:08:20.246Z`. The collector
  began its read at `08:08:22.439Z` and uploaded the successful observation from
  `08:08:35.326Z`. The Cloud acknowledged completion at `08:08:35.962Z`, about
  15.7 seconds after the request. This timing is one observation, not a latency
  guarantee.
- Android visibly showed `update complete` and its observation label changed
  from 17:00 to 17:08. The iPhone's `Updated from vehicle` label also changed to
  17:08 and its waiting indicator disappeared. No reinstall, account change or
  UI redesign was needed.
- A subsequent server poll confirmed `pending: false`, the matching
  `completedRequest`, `activeJob.status: completed`, and an empty outbox.
  The read counter increased from 14 to 15, not once per client. There was no
  collection or upload error in this verification interval.
- Final focused suite rerun: 115 passed; `git diff --check` passed. The source,
  tests and this record are published together on `codex/my-traverse-source`;
  unrelated working-tree changes are excluded.

Private runtime receipts and screenshots remain outside Git under
`Documents/my-traverse-refresh-20261103`.

The five-minute vehicle-read minimum still applies to repeated refresh taps.
Fetching an existing server snapshot is not the same as requesting a new vehicle
observation. No physical door/engine actions or long-duration reliability test
are implied by this deployment.
