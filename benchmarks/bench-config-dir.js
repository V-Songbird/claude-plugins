/* bench-config-dir.js — point benchmark runs at a scratch Claude state dir.
 *
 * CLAUDE_CONFIG_DIR relocates Claude Code's WHOLE state directory: the project
 * registry, session transcripts, plugins and settings. Without it every bench
 * cell's temp cwd becomes a permanent entry in ~/.claude.json, and its
 * transcript a permanent folder under ~/.claude/projects. Neither is ever
 * reconciled against disk, so both grow monotonically.
 *
 * The scratch dir is seeded ONCE and reused — a fresh one has no plugins and no
 * settings. Copy, never symlink: a junction would let a plugin update during a
 * run mutate the real install mid-benchmark. Override with BENCH_CONFIG_DIR.
 *
 * Require this before anything reads process.env in a runner that spawns
 * claude; it mutates process.env, so every cleanEnv() / {...process.env} copy
 * downstream inherits the value. Note the scratch registry lives INSIDE the
 * dir as <dir>/.claude.json, not beside it the way ~/.claude.json is.
 */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const DIR = process.env.BENCH_CONFIG_DIR || 'E:/claude-bench-config';
const REAL = path.join(os.homedir(), '.claude');

if (!fs.existsSync(DIR)) {
  fs.mkdirSync(DIR, { recursive: true });
  // The stored login is copied too: without it every cell returns a zero-cost
  // non-answer in ~3s, which the runner rejects as an unusable data point.
  for (const name of ['settings.json', 'CLAUDE.md', 'plugins', '.credentials.json']) {
    const from = path.join(REAL, name);
    if (fs.existsSync(from)) fs.cpSync(from, path.join(DIR, name), { recursive: true });
  }
  // Seed the registry MINUS its project entries. A registry built from scratch
  // has no onboarding or account state, so claude never gets past first run.
  const reg = JSON.parse(fs.readFileSync(path.join(os.homedir(), '.claude.json'), 'utf8'));
  reg.projects = {};
  fs.writeFileSync(path.join(DIR, '.claude.json'), JSON.stringify(reg, null, 2));
}
process.env.CLAUDE_CONFIG_DIR = DIR;

module.exports = DIR;
