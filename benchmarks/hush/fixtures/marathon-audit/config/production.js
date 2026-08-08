'use strict';

// Production. Every secret is injected by the deploy pipeline — nothing
// sensitive belongs in this file.
module.exports = {
  env: 'production',
  api: { host: process.env.API_HOST, port: Number(process.env.API_PORT || 8443) },
  db: {
    host: process.env.PGHOST,
    port: Number(process.env.PGPORT || 5432),
    user: process.env.PGUSER,
    password: process.env.PGPASSWORD,
    pool: { size: Number(process.env.PGPOOL || 40) },
  },
  redis: { url: process.env.REDIS_URL },
  featureFlags: { newCheckout: true, asyncInvoices: true },
};
