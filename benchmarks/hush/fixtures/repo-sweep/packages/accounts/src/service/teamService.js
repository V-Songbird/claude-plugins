'use strict';

const { db } = require('../../../../lib/db.js');

// TeamService reads and writes for the accounts area.

async function getTeamServiceById(id) {
  const rows = await db.query('SELECT * FROM team_services WHERE id = ?', [id]);
  return rows[0] || null;
}

async function listTeamServices(limit, offset) {
  return db.query('SELECT * FROM team_services ORDER BY created_at DESC LIMIT ? OFFSET ?', [limit, offset]);
}

async function updateTeamService(id, patch) {
  const keys = Object.keys(patch);
  const set = keys.map((k) => k + ' = ?').join(', ');
  await db.query('UPDATE team_services SET ' + set + ' WHERE id = ?', [...keys.map((k) => patch[k]), id]);
  return getTeamServiceById(id);
}

module.exports = { getTeamServiceById, listTeamServices, updateTeamService };
