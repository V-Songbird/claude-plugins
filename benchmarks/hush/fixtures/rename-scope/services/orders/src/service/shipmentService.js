'use strict';

const repo = require('../repo/shipment.js');
const { audit } = require('../../../../lib/audit.js');

// Shipment rules for the orders service. The account_id travels with every
// call so a caller can never read across accounts by accident.

async function fetchShipment({ account_id, id }) {
  if (!account_id) throw new Error('shipmentService: missing account_id');
  const row = await repo.getShipment(account_id, id);
  if (!row) return null;
  audit('orders.shipment.read', { account_id, id });
  return row;
}

async function pageShipments({ account_id, page = 0, size = 50 }) {
  const rows = await repo.listShipments(account_id, size, page * size);
  const total = await repo.countShipments(account_id);
  return { rows, total, page, size, account_id };
}

async function createShipment({ account_id, values }) {
  const created = await repo.insertShipment(account_id, values);
  audit('orders.shipment.create', { account_id });
  return created;
}

async function removeShipment({ account_id, id }) {
  await repo.deleteShipment(account_id, id);
  audit('orders.shipment.delete', { account_id, id });
}

module.exports = { fetchShipment, pageShipments, createShipment, removeShipment };
