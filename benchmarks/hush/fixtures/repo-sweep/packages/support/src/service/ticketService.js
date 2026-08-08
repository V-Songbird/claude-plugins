'use strict';

const { db } = require('../../../../lib/db.js');

// TicketService reads and writes for the support area.

async function getTicketServiceById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM ticket_services WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listTicketServices(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM ticket_services ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateTicketService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE ticket_services SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getTicketServiceById(id);
}

module.exports = { getTicketServiceById, listTicketServices, updateTicketService };
