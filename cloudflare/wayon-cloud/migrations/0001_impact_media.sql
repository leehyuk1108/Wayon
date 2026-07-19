ALTER TABLE impact_events ADD COLUMN capture_status TEXT;
ALTER TABLE impact_events ADD COLUMN captured_at TEXT;
ALTER TABLE impact_events ADD COLUMN capture_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE impact_events ADD COLUMN wide_snapshot_id TEXT;
ALTER TABLE impact_events ADD COLUMN driver_snapshot_id TEXT;

UPDATE impact_events
SET capture_status = 'not_available'
WHERE capture_status IS NULL;
