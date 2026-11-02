-- Additive only. Never purge claims while the same event can be retried.
CREATE TABLE IF NOT EXISTS parking_sign_notifications (
  device_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  test INTEGER NOT NULL CHECK (test IN (0, 1)),
  job_id TEXT NOT NULL,
  parked_at TEXT NOT NULL,
  completed_at TEXT NOT NULL,
  claimed_at TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL CHECK (length(payload_sha256) = 64),
  payload_json TEXT NOT NULL,
  notified_count INTEGER NOT NULL DEFAULT -1,
  finished_at TEXT,
  PRIMARY KEY (device_id, event_id, test)
);
