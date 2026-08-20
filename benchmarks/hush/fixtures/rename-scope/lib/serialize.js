'use strict';

// Internal row -> public JSON. The keys on the RIGHT are the public API. They
// are documented in docs/openapi.yaml and every client reads them by name, so
// they are frozen: an internal rename must not reach this side of the map.

const WIRE = {
  account_id: 'account_id',   // public field name — frozen by the API contract
  created_at: 'created_at',
  updated_at: 'updated_at',
};

function serialize(kind, row) {
  const out = { object: kind };
  for (const [internal, wire] of Object.entries(WIRE)) {
    if (row[internal] !== undefined) out[wire] = row[internal];
  }
  for (const [k, v] of Object.entries(row)) {
    if (!WIRE[k] && k !== 'payload') out[k] = v;
  }
  return out;
}

module.exports = { serialize, WIRE };
