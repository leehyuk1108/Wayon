CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires INTEGER NOT NULL,
  account TEXT, email TEXT
);
CREATE TABLE IF NOT EXISTS rate_limits (
  id TEXT PRIMARY KEY, count INTEGER NOT NULL, expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS command_claims (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL, command TEXT NOT NULL,
  created INTEGER NOT NULL, result TEXT
);
CREATE TABLE IF NOT EXISTS command_lock (
  id INTEGER PRIMARY KEY CHECK(id=1), until_ms INTEGER NOT NULL
);
INSERT OR IGNORE INTO command_lock (id, until_ms) VALUES (1, 0);
CREATE TABLE IF NOT EXISTS web_subscriptions (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL, subscription TEXT NOT NULL,
  expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS push_claims (
  id TEXT PRIMARY KEY, created INTEGER NOT NULL, result TEXT
);
