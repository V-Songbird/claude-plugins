#!/usr/bin/env node
'use strict';

// Replays the whole window through the router and prints what it decided for
// every notification, then a summary. It reports behavior — it does not know
// the rules, so it never says whether a decision was right.

const path = require('node:path');
const events = require(path.join(__dirname, 'events.js'));
const { hourOf } = require(path.join(__dirname, 'src', 'lib.js'));
const { route, createState } = require(path.join(__dirname, 'src', 'router.js'));

const out = [];
const p = (s) => out.push(s);

p('router-sim 1.3.0  replaying a 36-hour window');
p(`${events.length} notifications, 12 subjects, 4 priorities`);
p('');
p('   at  hh   id         priority  subject             -> channels');
p('  ---- --  ---------  --------  ------------------  ------------------');

const state = createState();
const byChannel = new Map();
const byPriority = new Map();
let dropped = 0;
let errors = 0;

for (const e of events) {
  let channels;
  try {
    channels = route(e, state);
  } catch (err) {
    errors++;
    p(`  ${String(e.at).padStart(4)} ${String(hourOf(e.at)).padStart(2, '0')}  ${e.id}  ${e.priority.padEnd(8)}  ${e.subject.padEnd(18)}  !! ${err.name}: ${err.message}`);
    continue;
  }
  if (!Array.isArray(channels)) {
    errors++;
    p(`  ${String(e.at).padStart(4)} ${String(hourOf(e.at)).padStart(2, '0')}  ${e.id}  ${e.priority.padEnd(8)}  ${e.subject.padEnd(18)}  !! route() returned ${typeof channels}, expected an array`);
    continue;
  }
  if (channels.length === 0) dropped++;
  for (const c of channels) byChannel.set(c, (byChannel.get(c) || 0) + 1);
  const pk = `${e.priority}`;
  if (!byPriority.has(pk)) byPriority.set(pk, new Map());
  const pm = byPriority.get(pk);
  for (const c of channels) pm.set(c, (pm.get(c) || 0) + 1);
  p(`  ${String(e.at).padStart(4)} ${String(hourOf(e.at)).padStart(2, '0')}  ${e.id}  ${e.priority.padEnd(8)}  ${e.subject.padEnd(18)}  -> ${channels.length ? channels.join(', ') : '(dropped)'}`);
}

p('');
p('deliveries per channel');
for (const [c, n] of [...byChannel].sort((a, b) => b[1] - a[1])) {
  p(`  ${c.padEnd(8)} ${String(n).padStart(5)}`);
}
p('');
p('channels per priority');
for (const prio of ['low', 'normal', 'high', 'critical']) {
  const pm = byPriority.get(prio) || new Map();
  const parts = [...pm].sort((a, b) => b[1] - a[1]).map(([c, n]) => `${c}=${n}`);
  p(`  ${prio.padEnd(9)} ${parts.length ? parts.join('  ') : '(none)'}`);
}
p('');
p('deliveries by hour of day');
for (let h = 0; h < 24; h++) {
  const inHour = events.filter((e) => hourOf(e.at) === h).length;
  p(`  ${String(h).padStart(2, '0')}:00  ${String(inHour).padStart(4)} notifications`);
}
p('');
p(`dropped: ${dropped}   route() errors: ${errors}`);
process.stdout.write(out.join('\n') + '\n');
process.exit(errors ? 1 : 0);
