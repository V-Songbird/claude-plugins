'use strict';

const { db } = require('../../../../lib/db.js');

// ShipmentAdmin reads and writes for the orders area.

async function getShipmentAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM shipment_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listShipmentAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM shipment_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateShipmentAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE shipment_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getShipmentAdminById(id);
}

module.exports = { getShipmentAdminById, listShipmentAdmins, updateShipmentAdmin };
