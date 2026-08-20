'use strict';

const repo = require('../repo/email.js');
const { audit } = require('../../../../lib/audit.js');

// Email rules for the notify service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchEmail({ account_id, id }) {
  if (!account_id) throw new Error('emailService: missing account_id');
  const row = await repo.getEmail(account_id, id);
  if (!row) return null;
  audit('notify.email.read', { account_id, id });
  return row;
}

async function pageEmails({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listEmails(account_id, size, page * size);
  const total = await repo.countEmails(account_id);
  return { rows, total, page, size, account_id };
}

async function createEmail({ account_id, values }) {
  const created = await repo.insertEmail(account_id, values);
  audit('notify.email.create', { account_id });
  return created;
}

async function removeEmail({ account_id, id }) {
  await repo.deleteEmail(account_id, id);
  audit('notify.email.delete', { account_id, id });
}

module.exports = { fetchEmail, pageEmails, createEmail, removeEmail };
