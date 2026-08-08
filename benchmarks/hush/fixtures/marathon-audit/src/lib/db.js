'use strict';

const calls = [];

const db = {
  async execute({ sql, params } = {}) {
    calls.push({ sql, params });
    return [];
  },
};

module.exports = { db, calls };
