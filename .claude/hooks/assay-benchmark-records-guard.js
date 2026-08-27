#!/usr/bin/env node
// Two mechanical guards promoted from .claude/rules/ (assay):
// 1. git add/commit of benchmark run data (records/, records-archive/, results/)
//    never publishes — ADR 0004, .claude/rules/benchmark-data.md.
// 2. a "version" field in any plugin.json — the root marketplace.json owns
//    every plugin's version, .claude/rules/plugin-layout.md.
let raw = '';
process.stdin.on('data', (d) => { raw += d; });
process.stdin.on('end', () => {
  let input;
  try { input = JSON.parse(raw); } catch { process.exit(0); }
  const tool = String(input.tool_name || '');
  const ti = input.tool_input || {};
  const deny = (reason) => {
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: reason
      }
    }));
    process.exit(0);
  };
  if (tool === 'Bash' || tool === 'PowerShell') {
    const cmd = String(ti.command || '');
    if (/\bgit\b[^\n;|&]*\b(add|commit)\b/.test(cmd) &&
        /records-archive|benchmarks[\/\\][^\s"';|&]*\b(records|results)\b/.test(cmd)) {
      deny('Benchmark run data never publishes (ADR 0004): records/, records-archive/ and results/ stay local. Stage the harness setup, not the run output.');
    }
    process.exit(0);
  }
  if (tool === 'Edit' || tool === 'Write') {
    const base = String(ti.file_path || '').split(/[\\/]/).pop();
    const text = String(ti.content != null ? ti.content : (ti.new_string != null ? ti.new_string : ''));
    if (base === 'plugin.json' && /"version"\s*:/.test(text)) {
      deny('Versions live only in the root .claude-plugin/marketplace.json — a version field in plugin.json would silently mask it. Bump the marketplace entry instead.');
    }
    process.exit(0);
  }
  process.exit(0);
});
