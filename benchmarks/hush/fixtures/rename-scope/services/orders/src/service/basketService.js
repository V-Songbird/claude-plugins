'use strict';

const repo = require('../repo/basket.js');
const { audit } = require('../../../../lib/audit.js');

// Basket rules for the orders service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchBasket({ account_id, id }) {
  if (!account_id) throw new Error('basketService: missing account_id');
  const row = await repo.getBasket(account_id, id);
  if (!row) return null;
  audit('orders.basket.read', { account_id, id });
  return row;
}

async function pageBaskets({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listBaskets(account_id, size, page * size);
  const total = await repo.countBaskets(account_id);
  return { rows, total, page, size, account_id };
}

async function createBasket({ account_id, values }) {
  const created = await repo.insertBasket(account_id, values);
  audit('orders.basket.create', { account_id });
  return created;
}

async function removeBasket({ account_id, id }) {
  await repo.deleteBasket(account_id, id);
  audit('orders.basket.delete', { account_id, id });
}

module.exports = { fetchBasket, pageBaskets, createBasket, removeBasket };
