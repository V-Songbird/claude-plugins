'use strict';

// Test double for the platform's query layer. Records what it was asked to run.

const calls = [];

const db = {
  async execute({ sql, params } = {}) {
    calls.push({ sql, params });
    return [];
  },
};

module.exports = { db, calls };
