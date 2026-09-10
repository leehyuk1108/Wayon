# Cloud budget changes: rollout and compatibility

## Clients are different

- `Wayon/Sunnypilot` is used with **My Traverse New**
  (`com.example.carcontroller.next`). Its established `/api/json`, GMOne,
  ambient, widget and notification paths must remain supported.
- `carrotpilot/wip` is intended to use **Hylink Dev** (`app.hylink.mobile.debug`).
  Vehicle-side Hylink integration is a separate, still-pending stage.
- This Worker serves both clients. Do not replace either client's API with
  the other or transplant vehicle-control features into Hylink.

## Implemented in this change

1. Add migration `0009_sync_cursor_indexes.sql` for trips, impact events and
   snapshots. Cursor queries seek on `(timestamp, id)` with a matching index.
   Existing opaque cursors, field names, authentication and pagination limits
   are unchanged. No stored records are deleted or rewritten.
2. Wayon telemetry and route retries back off independently and add jitter.
   Successful telemetry keeps the existing 30 s onroad / 300 s offroad default
   heartbeat and existing event-change checks. Invalid cadence configuration
   falls back or is bounded. No control, Panda, GM, camera or power-off code changes.

## Deployment order

1. Record the actual deployed Worker revision and existing D1 indexes. Back up
   schema/data through the established operational process.
2. Apply only migration 0009, checking remaining daily write allowance first:
   creating indexes also consumes writes. Do not blindly replay all historical
   migrations (the repository has two different 0004 migrations).
3. Deploy the compatible Worker and test both My Traverse New and Hylink keys.
   Verify unauthorized and cross-device reads remain denied, old cursors work,
   and idle sync reads no longer grow linearly with accumulated history.
4. Update one offroad Wayon device, then the remaining vehicles after verification.
   A Git branch update is not proof of Worker, database or vehicle deployment.

Rollback: the previous Worker and uploader remain compatible with the additive
indexes. Keep the indexes during an application rollback; no destructive
schema rollback is required.

## Local validation

```sh
node --test cloudflare/wayon-cloud/test*.mjs
python3 cloudflare/wayon-cloud/test_sync_query_plan.py
python3 system/test_wayon_cloud_policy.py
python3 -m py_compile system/wayon_cloud_uploader.py
```

The SQLite test checks 10,000 records across five devices and timestamp ties.
The exhausted-cursor case decreased from 52,018 to 29 SQLite VM instructions in
the local fixture. **These are not billed D1 row counts or a production saving
guarantee.** Measure D1 row reads after migration and deployment.

## Not implemented or authorized by this patch

- No media deletion, KV migration, new R2 binding, paid subscription or
  retention-policy change. Existing APK/media archives must not be purged.
- No modification to the separate server's sync scheduler; its deployed source
  must be identified before adding empty-poll backoff.
- No Hylink camera/SSH services added to carrotpilot yet.
- No change to Tidbyt, health-bridge or unrelated vehicle controls.

The remaining storage stage needs a selected destination and retention policy,
preserved old-KV reads, verified copy checksums and an approved deletion step.
Do not advertise five-vehicle readiness from the request tests alone.
