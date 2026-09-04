#!/usr/bin/env node
"use strict";

// CONTRIBUTING.md's "no shared runtime between plugins" rule means a plugin
// cannot require() a file out of a sibling: each is installed from its own
// independent repo, with no guarantee this monorepo is on disk. So the few
// genuinely shared helpers ship as a verbatim copy per plugin.
//
// The half a human reviewer cannot hold: a copy only drifts once, quietly,
// in whichever plugin was not the one being fixed. safe-write.js drifted
// twice that way -- the trusted-roots block, then the whole-path realpath --
// and both times the stale copy was the one that skipped a security check,
// while its own header still promised the copies were identical.
//
// A missing plugin checkout is not drift: submodules are not always
// initialized, so an absent file is skipped rather than failed.
//
//   node check-shared-copies.js       -- this repo's submodule checkouts

const fs = require("fs");
const path = require("path");

/** Every helper duplicated across plugins, and the function that must match. */
const SHARED = [
  { file: "hooks/lib/safe-write.js", fn: "safeWriteFileSync", plugins: ["hush", "razor"] },
];

const repoRoot = () => path.join(__dirname, "..", "..");

/**
 * The named function's source, from its `function` line to the first line that
 * is a bare `}`. Comments above it are excluded on purpose: each plugin's
 * header speaks for that plugin, and only the behavior has to be identical.
 * Returns null when the file has no such function.
 */
function functionBody(source, name) {
  const lines = source.split("\n");
  const start = lines.findIndex((l) => l.startsWith(`function ${name}(`));
  if (start < 0) return null;
  const end = lines.findIndex((l, i) => i > start && l === "}");
  if (end < 0) return null;
  return lines.slice(start, end + 1).join("\n");
}

/** One problem string per shared helper whose copies disagree. */
function checkShared(root = repoRoot(), shared = SHARED) {
  const problems = [];
  for (const { file, fn, plugins } of shared) {
    const bodies = new Map();
    for (const plugin of plugins) {
      const full = path.join(root, plugin, file);
      let source;
      try {
        source = fs.readFileSync(full, "utf8");
      } catch {
        continue; // submodule not checked out
      }
      const body = functionBody(source, fn);
      if (body === null) {
        problems.push(`${plugin}/${file} has no top-level function ${fn}() to compare`);
        continue;
      }
      bodies.set(plugin, body);
    }
    const distinct = new Set(bodies.values());
    if (distinct.size > 1) {
      problems.push(
        `${fn}() differs between ${[...bodies.keys()].join(" and ")} (${file}). ` +
        `These copies stand in for a shared module, so a fix in one is a fix owed to ` +
        `the other -- diff them and land both halves in the same change.`
      );
    }
  }
  return problems;
}

function main() {
  const problems = checkShared();
  if (problems.length === 0) return 0;

  process.stderr.write("\nShared-copy check:\n\n");
  for (const p of problems) process.stderr.write(`  - ${p}\n`);
  process.stderr.write("\n");
  return 1;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = { main, functionBody, checkShared, SHARED };
