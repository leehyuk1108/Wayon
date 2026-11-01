-- Additive only. Apply before the patched Worker, never modify existing rows.
CREATE TABLE IF NOT EXISTS parking_snapshot_frames_v1 (
  device_id TEXT NOT NULL,
  event_id TEXT NOT NULL CHECK(length(event_id) BETWEEN 1 AND 96),
  frame_index INTEGER NOT NULL CHECK(frame_index BETWEEN 0 AND 11),
  frame_count INTEGER NOT NULL CHECK(frame_count BETWEEN 2 AND 12 AND frame_index < frame_count),
  parked_at TEXT NOT NULL CHECK(length(parked_at) <= 40),
  parked_ms INTEGER NOT NULL,
  phase TEXT NOT NULL CHECK(phase IN ('approach', 'parked')),
  captured_at TEXT NOT NULL CHECK(length(captured_at) <= 40),
  captured_ms INTEGER NOT NULL,
  snapshot_id TEXT NOT NULL UNIQUE,
  kv_key TEXT NOT NULL UNIQUE,
  size_bytes INTEGER NOT NULL CHECK(size_bytes BETWEEN 4 AND 2097152),
  image_sha256 TEXT NOT NULL CHECK(length(image_sha256) = 64),
  driver_snapshot_id TEXT UNIQUE,
  driver_kv_key TEXT UNIQUE,
  driver_size_bytes INTEGER,
  driver_sha256 TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY(device_id, event_id, frame_index),
  CHECK(captured_ms BETWEEN parked_ms - 120000 AND parked_ms),
  CHECK(phase != 'approach' OR captured_ms < parked_ms),
  CHECK(frame_index != frame_count - 1 OR (phase = 'parked' AND captured_ms = parked_ms)),
  CHECK((driver_snapshot_id IS NULL AND driver_kv_key IS NULL AND driver_size_bytes IS NULL AND driver_sha256 IS NULL) OR
    (phase = 'parked' AND driver_snapshot_id IS NOT NULL AND driver_kv_key IS NOT NULL AND
     driver_size_bytes BETWEEN 4 AND 2097152 AND length(driver_sha256) = 64))
);
CREATE INDEX IF NOT EXISTS parking_snapshot_frames_v1_expiry
  ON parking_snapshot_frames_v1(device_id, parked_ms);
