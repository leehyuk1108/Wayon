CREATE TABLE IF NOT EXISTS impact_suppressions (
  device_id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL,
  suppress_from TEXT NOT NULL,
  suppress_until TEXT NOT NULL,
  reason TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gmone_latest (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  collected_at TEXT NOT NULL,
  vehicle_updated_at TEXT,
  payload_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gmone_refresh_requests (
  id TEXT PRIMARY KEY,
  requested_at TEXT NOT NULL,
  completed_at TEXT
);
