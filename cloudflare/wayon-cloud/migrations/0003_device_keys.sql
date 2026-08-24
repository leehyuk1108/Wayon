CREATE TABLE IF NOT EXISTS wayon_devices (
  device_id TEXT PRIMARY KEY,
  key_hash TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_seen_at TEXT,
  revoked_at TEXT
);

CREATE INDEX IF NOT EXISTS wayon_devices_key_hash_idx
  ON wayon_devices(key_hash);
