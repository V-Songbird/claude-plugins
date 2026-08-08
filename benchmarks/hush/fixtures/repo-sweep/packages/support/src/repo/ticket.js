'use strict';

const { db } = require('../../../../lib/db.js');
const { cache } = require('../../../../lib/cache.js');

// Ticket reads and writes for the support area.

async function getTicketById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM tickets WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listTickets(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM tickets ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function cachedTicket(id) {
  const hit = await cache.query('tickets:' + id);
  if (hit) return hit;
  const row = await getTicketById(id);
  await cache.set('tickets:' + id, row);
  return row;
}

async function updateTicket(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE tickets SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getTicketById(id);
}

module.exports = { getTicketById, listTickets, updateTicket, cachedTicket };
