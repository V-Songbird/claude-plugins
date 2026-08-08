'use strict';

// Every router this service mounts, in order.
const routers = [
  require('./routes/public/health.js'),
  require('./routes/public/status.js'),
  require('./routes/public/version.js'),
  require('./routes/accounts/login.js'),
  require('./routes/accounts/logout.js'),
  require('./routes/accounts/profile.js'),
  require('./routes/accounts/invite.js'),
  require('./routes/accounts/team.js'),
  require('./routes/accounts/apiKey.js'),
  require('./routes/billing/invoice.js'),
  require('./routes/billing/subscription.js'),
  require('./routes/billing/coupon.js'),
  require('./routes/billing/refund.js'),
  require('./routes/catalog/product.js'),
  require('./routes/catalog/variant.js'),
  require('./routes/catalog/category.js'),
  require('./routes/catalog/search.js'),
  require('./routes/orders/order.js'),
  require('./routes/orders/shipment.js'),
  require('./routes/orders/return.js'),
  require('./routes/orders/fulfilment.js'),
  require('./routes/support/ticket.js'),
  require('./routes/support/macro.js'),
  require('./routes/support/sla.js'),
  require('./routes/internal.js'),
];

module.exports = { routers };
