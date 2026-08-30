'use strict';

const { buildRows } = require('./report');
const { toTable } = require('./format');

const USAGE = 'usage: cli.js report';

function main(argv) {
  const command = argv[0];
  if (command !== 'report') {
    process.stderr.write(USAGE + '\n');
    return 1;
  }
  process.stdout.write(toTable(buildRows()) + '\n');
  return 0;
}

process.exit(main(process.argv.slice(2)));
