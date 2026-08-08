'use strict';

const { db } = require('../../../../lib/db.js');

// TeamAdmin reads and writes for the accounts area.

async function getTeamAdminById(id) {
  const rows = await db.execute({ sql: 'SELECT * FROM team_admins WHERE id = ?', params: [id] });
  return rows[0] || null;
}

async function listTeamAdmins(limit, offset) {
  return db.execute({ sql: 'SELECT * FROM team_admins ORDER BY created_at DESC LIMIT ? OFFSET ?', params: [limit, offset] });
}

async function updateTeamAdmin(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.execute({ sql: 'UPDATE team_admins SET ' + set + ' WHERE id = ?', params: [...keys.map((k) => patch[k]), id] });
  return getTeamAdminById(id);
}

module.exports = { getTeamAdminById, listTeamAdmins, updateTeamAdmin };
