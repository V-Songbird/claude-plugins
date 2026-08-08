'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Shipment reads and writes for the orders area.

async function getShipmentById(id) {
  const rows = await db.query('SELECT * FROM shipments WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listShipments(limit, offset) {
  return db.query('SELECT * FROM shipments ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function cachedShipment(id) {
  const hit = await cache.query('shipments:' + id);
  if (hit) return hit;
  const row = await getShipmentById(id);
  await cache.set('shipments:' + id, row);
  return row;
}

async function updateShipment(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE shipments SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getShipmentById(id);
}

module.exports = { getShipmentById, listShipments, updateShipment, cachedShipment };
