'use strict';

// Staging environment. Points at the shared staging cluster.
module.exports = {
  env: 'staging',
  api: { host: 'staging.internal.acme.test', port: 8443 },
  db: {
    host: 'db-staging.internal.acme.test',
    port: 5432,
    user: 'acme_staging',
    password: 'St4ging-Pg-2024!weakish',
    pool: { size: 20 },
  },
  redis: { url: 'redis://cache-staging.internal.acme.test:6379' },
  featureFlags: { newCheckout: true, asyncInvoices: false },
};
