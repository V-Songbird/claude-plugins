'use strict';

const { db } = require('../../../../lib/db.js');

// ReturnService reads and writes for the orders area.

async function getReturnServiceById(id) {
  const rows = await db.query('SELECT * FROM return_services WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listReturnServices(limit, offset) {
  return db.query('SELECT * FROM return_services ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function updateReturnService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE return_services SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getReturnServiceById(id);
}

module.exports = { getReturnServiceById, listReturnServices, updateReturnService };
