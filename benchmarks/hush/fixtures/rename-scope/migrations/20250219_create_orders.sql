-- 20250219_create_orders
-- Applied in production on 2025-02-19.
-- Applied migrations are history: editing one does not rename anything in a
-- database that already ran it, and it breaks the down step.

-- up
CREATE TABLE IF NOT EXISTS orders (
  id          BIGSERIAL PRIMARY KEY,
  account_id  BIGINT NOT NULL REFERENCES accounts (account_id),
  payload     JSONB   NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS orders_account_id_idx ON orders (account_id);

-- down
DROP INDEX IF EXISTS orders_account_id_idx;
DROP TABLE IF EXISTS orders;
