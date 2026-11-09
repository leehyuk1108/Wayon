-- Additive: account sign-out/login revision so an in-flight multipack login cannot write back after sign-out.
ALTER TABLE sessions ADD COLUMN account_rev INTEGER NOT NULL DEFAULT 0;
