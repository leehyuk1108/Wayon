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

CREATE TABLE IF NOT EXISTS latest_state (
  device_id TEXT PRIMARY KEY,
  updated_at TEXT NOT NULL,
  onroad INTEGER NOT NULL,
  ignition INTEGER NOT NULL,
  enabled INTEGER NOT NULL,
  voltage_v REAL,
  current_ma REAL,
  power_w REAL,
  device_power_w REAL,
  thermal_status TEXT,
  fan_percent INTEGER,
  screen_brightness_percent INTEGER,
  latitude REAL,
  longitude REAL,
  speed_mps REAL,
  bearing_deg REAL,
  gps_accuracy_m REAL,
  last_snapshot_driver_id TEXT,
  last_snapshot_wide_id TEXT,
  raw_json TEXT
);

CREATE TABLE IF NOT EXISTS trips (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  started_at TEXT NOT NULL,
  ended_at TEXT NOT NULL,
  duration_s INTEGER,
  distance_m REAL,
  start_lat REAL,
  start_lon REAL,
  end_lat REAL,
  end_lon REAL,
  route_point_count INTEGER NOT NULL DEFAULT 0,
  route_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS trips_device_ended_idx
  ON trips(device_id, ended_at DESC);

CREATE TABLE IF NOT EXISTS snapshots (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  camera TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  kv_key TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS snapshots_device_captured_idx
  ON snapshots(device_id, captured_at DESC);

CREATE INDEX IF NOT EXISTS snapshots_captured_idx
  ON snapshots(captured_at DESC);

CREATE INDEX IF NOT EXISTS snapshots_kv_key_device_idx
  ON snapshots(kv_key, device_id);

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

CREATE TABLE IF NOT EXISTS impact_events (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  detected_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  severity TEXT NOT NULL,
  peak_dynamic_g REAL,
  peak_total_g REAL,
  peak_jerk_g_per_s REAL,
  peak_gyro_rad_per_s REAL,
  duration_ms INTEGER,
  sample_count INTEGER,
  sensor_clipped INTEGER NOT NULL DEFAULT 0,
  latitude REAL,
  longitude REAL,
  capture_status TEXT,
  captured_at TEXT,
  capture_attempts INTEGER NOT NULL DEFAULT 0,
  wide_snapshot_id TEXT,
  driver_snapshot_id TEXT,
  notified_count INTEGER NOT NULL DEFAULT 0,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS impact_events_device_detected_idx
  ON impact_events(device_id, detected_at DESC);

CREATE INDEX IF NOT EXISTS impact_events_wide_snapshot_idx
  ON impact_events(wide_snapshot_id);

CREATE INDEX IF NOT EXISTS impact_events_driver_snapshot_idx
  ON impact_events(driver_snapshot_id);

CREATE TABLE IF NOT EXISTS impact_suppressions (
  device_id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL,
  suppress_from TEXT NOT NULL,
  suppress_until TEXT NOT NULL,
  reason TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vehicle_events (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  locked INTEGER,
  notified_count INTEGER NOT NULL DEFAULT 0,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS vehicle_events_device_occurred_idx
  ON vehicle_events(device_id, occurred_at DESC);

CREATE TABLE IF NOT EXISTS push_subscriptions (
  token TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  app_version TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS push_subscriptions_device_idx
  ON push_subscriptions(device_id, updated_at DESC);

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
