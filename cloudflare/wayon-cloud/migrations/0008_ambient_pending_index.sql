CREATE INDEX IF NOT EXISTS ambient_commands_pending_idx
  ON ambient_commands(device_id, expires_at, created_at DESC)
  WHERE status IN ('pending', 'delivered');
