-- 20250505_create_emails
-- Applied in production on 2025-05-05.
-- Applied migrations are history: editing one does not rename anything in a
-- database that already ran it, and it breaks the down step.

-- up
CREATE TABLE IF NOT EXISTS emails (
  id          BIGSERIAL PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES accounts (account_id),
  payload     JSONB   NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS emails_account_id_idx ON emails (account_id);

-- down
DROP INDEX IF EXISTS emails_account_id_idx;
DROP TABLE IF EXISTS emails;
