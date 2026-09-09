# Ambient command delivery

Commands are persisted before the Worker notifies the existing device SSH
relay (`wayon-ambient-command-v1`). The notification contains no lighting
payload. The authenticated device fetches its latest unexpired command and
uses the existing apply/ack path.

The relay writes a coalescing wake token under `/dev/shm`. The uploader checks
that local token, not D1, while idle. It fetches once at startup, after relay
reconnection, and when a new token arrives. Failed fetch/apply/ack attempts retry
with a 5-to-60-second backoff. Notifications received during a fetch remain
pending. Offline devices recover still-valid commands after reconnecting;
expired commands are not applied.

Apply `migrations/0008_ambient_pending_index.sql` before deploying. The GET
endpoint no longer performs expiry UPDATEs. Status responses derive expiry
from the timestamp. Older polling clients remain compatible and benefit from
the partial pending-command index.

## Deployment notes (2026-09-09)

- Server deployment: `5fb7ebfe-8dea-4c13-af90-7f0a1d7ef307`.
- Source changes: `0d59a4824`, `69078804a` on `wayon/Sunnypilot`.
- The live Worker bundle matched the `wayon-sunnypilot-lead` checkout exactly
  before modification. Deployment used that checkout to preserve newer health
  report changes absent from the branch base.
- Device uploader had unrelated drive-report edits. Only the notification
  scheduler patch was applied to that file; those edits were retained.
- Restarting the uploader alone reused the manager's pre-imported old module.
  An offroad device reboot was required to activate the new scheduler.
- Device scheduler tests: 3 passed. Device relay tests: 9 passed.
- Worker tests cover persistence before notification, offline pending commands,
  expired status without writes, client control-message rejection, and existing
  SSH authentication and relay behavior.
- The live query plan uses `ambient_commands_pending_idx`. A post-reboot
  50-second server trace observed 2 command GETs, compared with the previous
  roughly 5.5-second polling. Reconnect checks are expected and are not idle
  timer polling. Lighting was not changed for verification.
