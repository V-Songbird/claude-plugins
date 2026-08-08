'use strict';

module.exports = {
  env: 'development',
  api: { host: 'localhost', port: 3000 },
  db: { host: 'localhost', port: 5432, user: 'dev', password: process.env.PGPASSWORD || 'dev', pool: { size: 4 } },
  redis: { url: 'redis://localhost:6379' },
  featureFlags: { newCheckout: false, asyncInvoices: false },
};
