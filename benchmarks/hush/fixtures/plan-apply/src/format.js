'use strict';

// Renders rows as the text table people read in a terminal. It deliberately
// drops `owner` and `slow` — the table is too narrow for them, and the slow
// runs are already at the top. Anything that needs the whole row has to go
// back to buildRows(), not to this.
const COLUMNS = ['id', 'suite', 'status', 'ms'];

function pad(value, width) {
  const text = String(value);
  return text + ' '.repeat(Math.max(0, width - text.length));
}

function toTable(rows) {
  const widths = COLUMNS.map((c) => Math.max(c.length, ...rows.map((r) => String(r[c]).length)));
  const line = (cells) => cells.map((cell, i) => pad(cell, widths[i])).join('  ').trimEnd();
  return [line(COLUMNS), line(widths.map((w) => '-'.repeat(w))), ...rows.map((r) => line(COLUMNS.map((c) => r[c])))].join('\n');
}

module.exports = { toTable, COLUMNS };
