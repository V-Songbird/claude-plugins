'use strict';

const repo = require('../repo/subscription.js');
const { audit } = require('../../../../lib/audit.js');

// Subscription rules for the billing service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchSubscription({ account_id, id }) {
  if (!account_id) throw new Error('subscriptionService: missing account_id');
  const row = await repo.getSubscription(account_id, id);
  if (!row) return null;
  audit('billing.subscription.read', { account_id, id });
  return row;
}

async function pageSubscriptions({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listSubscriptions(account_id, size, page * size);
  const total = await repo.countSubscriptions(account_id);
  return { rows, total, page, size, account_id };
}

async function createSubscription({ account_id, values }) {
  const created = await repo.insertSubscription(account_id, values);
  audit('billing.subscription.create', { account_id });
  return created;
}

async function removeSubscription({ account_id, id }) {
  await repo.deleteSubscription(account_id, id);
  audit('billing.subscription.delete', { account_id, id });
}

module.exports = { fetchSubscription, pageSubscriptions, createSubscription, removeSubscription };
