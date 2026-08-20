-- 20250128_create_invoices
-- Applied in production on 2025-01-28.
-- Applied migrations are history: editing one does not rename anything in a
-- database that already ran it, and it breaks the down step.

-- up
CREATE TABLE IF NOT EXISTS invoices (
  id          BIGSERIAL PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES accounts (account_id),
  payload     JSONB   NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS invoices_account_id_idx ON invoices (account_id);

-- down
DROP INDEX IF EXISTS invoices_account_id_idx;
DROP TABLE IF EXISTS invoices;
