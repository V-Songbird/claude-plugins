'use strict';

const repo = require('../repo/funnel.js');
const { audit } = require('../../../../lib/audit.js');

// Funnel rules for the analytics service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchFunnel({ account_id, id }) {
  if (!account_id) throw new Error('funnelService: missing account_id');
  const row = await repo.getFunnel(account_id, id);
  if (!row) return null;
  audit('analytics.funnel.read', { account_id, id });
  return row;
}

async function pageFunnels({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listFunnels(account_id, size, page * size);
  const total = await repo.countFunnels(account_id);
  return { rows, total, page, size, account_id };
}

async function createFunnel({ account_id, values }) {
  const created = await repo.insertFunnel(account_id, values);
  audit('analytics.funnel.create', { account_id });
  return created;
}

async function removeFunnel({ account_id, id }) {
  await repo.deleteFunnel(account_id, id);
  audit('analytics.funnel.delete', { account_id, id });
}

module.exports = { fetchFunnel, pageFunnels, createFunnel, removeFunnel };
