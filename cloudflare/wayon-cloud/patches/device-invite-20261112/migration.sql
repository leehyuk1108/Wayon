-- device-invite-20261112: one-time codes an owner device creates so another comma can register itself.
-- Additive only: the active worker never reads these tables, so applying them before the worker changes nothing.
CREATE TABLE IF NOT EXISTS wayon_device_invites (
  code_hash TEXT PRIMARY KEY,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  used_at TEXT,
  used_by TEXT,
  used_key_hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_wayon_device_invites_creator ON wayon_device_invites(created_by, created_at);
-- Devices registered with an invite. Kept for good (never cleaned with invites): such a device may not invite.
CREATE TABLE IF NOT EXISTS wayon_device_origins (
  device_id TEXT PRIMARY KEY,
  invited_by TEXT NOT NULL,
  invited_at TEXT NOT NULL
);
