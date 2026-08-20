'use strict';

const repo = require('../repo/pageview.js');
const { audit } = require('../../../../lib/audit.js');

// Pageview rules for the analytics service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchPageview({ account_id, id }) {
  if (!account_id) throw new Error('pageviewService: missing account_id');
  const row = await repo.getPageview(account_id, id);
  if (!row) return null;
  audit('analytics.pageview.read', { account_id, id });
  return row;
}

async function pagePageviews({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listPageviews(account_id, size, page * size);
  const total = await repo.countPageviews(account_id);
  return { rows, total, page, size, account_id };
}

async function createPageview({ account_id, values }) {
  const created = await repo.insertPageview(account_id, values);
  audit('analytics.pageview.create', { account_id });
  return created;
}

async function removePageview({ account_id, id }) {
  await repo.deletePageview(account_id, id);
  audit('analytics.pageview.delete', { account_id, id });
}

module.exports = { fetchPageview, pagePageviews, createPageview, removePageview };
