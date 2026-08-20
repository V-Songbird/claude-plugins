'use strict';

const repo = require('../repo/webhook.js');
const { audit } = require('../../../../lib/audit.js');

// Webhook rules for the notify service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchWebhook({ account_id, id }) {
  if (!account_id) throw new Error('webhookService: missing account_id');
  const row = await repo.getWebhook(account_id, id);
  if (!row) return null;
  audit('notify.webhook.read', { account_id, id });
  return row;
}

async function pageWebhooks({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listWebhooks(account_id, size, page * size);
  const total = await repo.countWebhooks(account_id);
  return { rows, total, page, size, account_id };
}

async function createWebhook({ account_id, values }) {
  const created = await repo.insertWebhook(account_id, values);
  audit('notify.webhook.create', { account_id });
  return created;
}

async function removeWebhook({ account_id, id }) {
  await repo.deleteWebhook(account_id, id);
  audit('notify.webhook.delete', { account_id, id });
}

module.exports = { fetchWebhook, pageWebhooks, createWebhook, removeWebhook };
