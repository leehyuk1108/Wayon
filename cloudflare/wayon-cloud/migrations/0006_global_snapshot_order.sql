CREATE INDEX IF NOT EXISTS snapshots_captured_idx
  ON snapshots(captured_at DESC);
