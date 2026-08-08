'use strict';

const { db } = require('../../../../lib/db.js');

// TicketAdmin reads and writes for the support area.

async function getTicketAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM ticket_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listTicketAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM ticket_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateTicketAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE ticket_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getTicketAdminById(id);
}

module.exports = { getTicketAdminById, listTicketAdmins, updateTicketAdmin };
