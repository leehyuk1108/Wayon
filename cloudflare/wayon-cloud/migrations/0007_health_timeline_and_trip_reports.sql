ALTER TABLE trips ADD COLUMN report_json TEXT NOT NULL DEFAULT '{}';

CREATE TABLE IF NOT EXISTS health_events (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  category TEXT NOT NULL,
  severity TEXT NOT NULL,
  title TEXT NOT NULL,
  detail TEXT,
  snapshot_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS health_events_device_occurred_idx
  ON health_events(device_id, occurred_at DESC);
