-- A timestamp alone is not a cursor: multiple devices can upload in the same
-- second. Match both the seek predicate and ORDER BY without rescanning history.
-- Additive migration; no existing data, keys, or API cursors are changed.
CREATE INDEX IF NOT EXISTS trips_sync_cursor_idx ON trips(created_at, id);
CREATE INDEX IF NOT EXISTS snapshots_sync_cursor_idx ON snapshots(created_at, id);
CREATE INDEX IF NOT EXISTS impact_events_sync_cursor_idx ON impact_events(received_at, id);
