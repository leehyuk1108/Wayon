CREATE TABLE IF NOT EXISTS ambient_commands (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  status TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  acknowledged_at TEXT,
  ack_json TEXT
);

CREATE INDEX IF NOT EXISTS ambient_commands_device_created_idx
  ON ambient_commands(device_id, created_at DESC);
