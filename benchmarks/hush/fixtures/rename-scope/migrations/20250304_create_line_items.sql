-- 20250304_create_line_items
-- Applied in production on 2025-03-04.
-- Applied migrations are history: editing one does not rename anything in a
-- database that already ran it, and it breaks the down step.

-- up
CREATE TABLE IF NOT EXISTS line_items (
  id          BIGSERIAL PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES accounts (account_id),
  payload     JSONB   NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS line_items_account_id_idx ON line_items (account_id);

-- down
DROP INDEX IF EXISTS line_items_account_id_idx;
DROP TABLE IF EXISTS line_items;
