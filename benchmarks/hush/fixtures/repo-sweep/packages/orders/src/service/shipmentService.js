'use strict';

const { db } = require('../../../../lib/db.js');

// ShipmentService reads and writes for the orders area.

async function getShipmentServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM shipment_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listShipmentServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM shipment_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateShipmentService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE shipment_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getShipmentServiceById(id);
}

module.exports = { getShipmentServiceById, listShipmentServices, updateShipmentService };
