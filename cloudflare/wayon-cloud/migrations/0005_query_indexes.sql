CREATE INDEX IF NOT EXISTS snapshots_kv_key_device_idx
  ON snapshots(kv_key, device_id);

CREATE INDEX IF NOT EXISTS impact_events_wide_snapshot_idx
  ON impact_events(wide_snapshot_id);

CREATE INDEX IF NOT EXISTS impact_events_driver_snapshot_idx
  ON impact_events(driver_snapshot_id);
