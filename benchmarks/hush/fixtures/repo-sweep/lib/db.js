'use strict';

// The database handle every module shares.
//
// `query(sql, params)` is the old positional form. It is deprecated: the
// driver's next major drops it, and it cannot carry the per-call options the
// new form takes. `execute({ sql, params })` is the replacement.

const calls = [];

const db = {
  /** @deprecated use execute({ sql, params }) */
  async query(sql, params) {
    calls.push({ form: 'query', sql, params });
    return [];
  },

  async execute({ sql, params, timeoutMs } = {}) {
    calls.push({ form: 'execute', sql, params, timeoutMs });
    return [];
  },
};

module.exports = { db, calls };
