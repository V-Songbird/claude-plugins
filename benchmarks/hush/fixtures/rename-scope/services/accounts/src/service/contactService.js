'use strict';

const repo = require('../repo/contact.js');
const { audit } = require('../../../../lib/audit.js');

// Contact rules for the accounts service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchContact({ account_id, id }) {
  if (!account_id) throw new Error('contactService: missing account_id');
  const row = await repo.getContact(account_id, id);
  if (!row) return null;
  audit('accounts.contact.read', { account_id, id });
  return row;
}

async function pageContacts({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listContacts(account_id, size, page * size);
  const total = await repo.countContacts(account_id);
  return { rows, total, page, size, account_id };
}

async function createContact({ account_id, values }) {
  const created = await repo.insertContact(account_id, values);
  audit('accounts.contact.create', { account_id });
  return created;
}

async function removeContact({ account_id, id }) {
  await repo.deleteContact(account_id, id);
  audit('accounts.contact.delete', { account_id, id });
}

module.exports = { fetchContact, pageContacts, createContact, removeContact };
