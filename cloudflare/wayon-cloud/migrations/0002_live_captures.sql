CREATE TABLE IF NOT EXISTS live_captures (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  duration_s REAL,
  content_type TEXT NOT NULL,
  camera_layout TEXT NOT NULL,
  kv_key TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  metadata_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS live_captures_device_captured_idx
  ON live_captures(device_id, captured_at DESC);
