#!/usr/bin/env node
// Denies `git add`/`git commit` commands that stage benchmark run data.
// Run data (records/, records-archive/, results/) never publishes — ADR 0004,
// .claude/rules/benchmark-data.md.
let raw = '';
process.stdin.on('data', (d) => { raw += d; });
process.stdin.on('end', () => {
  let input;
  try { input = JSON.parse(raw); } catch { process.exit(0); }
  const cmd = String((input.tool_input && input.tool_input.command) || '');
  if (!/\bgit\b[^\n;|&]*\b(add|commit)\b/.test(cmd)) process.exit(0);
  const runData = /records-archive|benchmarks[\/\\][^\s"';|&]*\b(records|results)\b/.test(cmd);
  if (!runData) process.exit(0);
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: 'Benchmark run data never publishes (ADR 0004): records/, records-archive/ and results/ stay local. Stage the harness setup, not the run output.'
    }
  }));
  process.exit(0);
});
