#!/usr/bin/env node
"use strict";

// Root-repo pre-commit gate: a staged submodule pointer bump (mode 160000)
// must land in the same commit as a matching "version"+"source.sha" update
// in .claude-plugin/marketplace.json, or installers either get stale code
// under a new version label, or /plugin update silently skips a real change
// (Claude Code resolves version before it ever looks at the git SHA).

const path = require("path");
const { execSync } = require("child_process");

const MARKETPLACE_PATH = ".claude-plugin/marketplace.json";

function repoRoot() {
  return execSync("git rev-parse --show-toplevel", { encoding: "utf-8" }).trim();
}

// Parses `git diff --cached --raw` output for staged gitlink (submodule)
// pointer changes. Each match line looks like:
// :160000 160000 <oldsha> <newsha> M	<path>
function parseStagedSubmoduleChanges(rawDiffOutput) {
  const changes = [];
  for (const line of String(rawDiffOutput || "").split("\n")) {
    const m = line.match(/^:160000 160000 [0-9a-f]+ ([0-9a-f]+) [A-Z]\d*\t(.+)$/);
    if (m) changes.push({ path: m[2], newSha: m[1] });
  }
  return changes;
}

function findPluginEntry(marketplace, pluginName) {
  return (marketplace && marketplace.plugins ? marketplace.plugins : []).find((p) => p.name === pluginName);
}

// Pure decision logic, no git calls -- fully unit-testable.
function evaluate({ submoduleChanges, marketplaceStaged, marketplace, pluginNames }) {
  const problems = [];
  for (const change of submoduleChanges) {
    const pluginName = path.basename(change.path);
    // Not every submodule is a marketplace plugin -- flint is mounted here the
    // same way but ships no plugin.json and has no marketplace entry, so it has
    // no version or source.sha for this gate to keep in step.
    if (pluginNames && !pluginNames.includes(pluginName)) continue;
    const shortSha = change.newSha.slice(0, 12);

    if (!marketplaceStaged) {
      problems.push(
        `Submodule "${pluginName}" is staged at ${shortSha}, but ${MARKETPLACE_PATH} was not staged in this ` +
          `commit. Update its "version" and "source.sha" for "${pluginName}" and stage it too.`
      );
      continue;
    }

    const entry = findPluginEntry(marketplace, pluginName);
    if (!entry) {
      problems.push(`Submodule "${pluginName}" changed but has no matching entry in ${MARKETPLACE_PATH}.`);
      continue;
    }

    const entrySha = entry.source && entry.source.sha;
    if (entrySha !== change.newSha) {
      problems.push(
        `Submodule "${pluginName}" is staged at ${shortSha}, but ${MARKETPLACE_PATH}'s source.sha for ` +
          `"${pluginName}" is ${entrySha ? entrySha.slice(0, 12) : "(missing)"}. Update "version" and ` +
          `"source.sha" together and re-stage ${MARKETPLACE_PATH}.`
      );
    }
  }
  return problems;
}

function stagedFileNames(root) {
  return execSync("git diff --cached --name-only", { cwd: root, encoding: "utf-8" })
    .split("\n")
    .filter(Boolean);
}

// The plugin names as last committed. A submodule pointer bump for a plugin
// added in this very commit arrives as an ADD, not an M, so parseStagedSubmoduleChanges
// never sees it -- HEAD is therefore a complete list of the plugins this gate governs.
function committedPluginNames(root) {
  try {
    const raw = execSync(`git show HEAD:${MARKETPLACE_PATH}`, { cwd: root, encoding: "utf-8" });
    return (JSON.parse(raw).plugins || []).map((entry) => entry.name);
  } catch {
    return null;
  }
}

function readStagedMarketplaceJson(root) {
  const raw = execSync(`git show :${MARKETPLACE_PATH}`, { cwd: root, encoding: "utf-8" });
  return JSON.parse(raw);
}

function checkConsistency(root) {
  // --no-abbrev is required: without it git truncates SHAs to 7 chars,
  // which never equals the full 40-char source.sha in marketplace.json.
  const rawDiff = execSync("git diff --cached --raw --no-abbrev", { cwd: root, encoding: "utf-8" });
  const submoduleChanges = parseStagedSubmoduleChanges(rawDiff);
  if (submoduleChanges.length === 0) return [];

  const marketplaceStaged = stagedFileNames(root).includes(MARKETPLACE_PATH);
  let marketplace = null;
  if (marketplaceStaged) {
    try {
      marketplace = readStagedMarketplaceJson(root);
    } catch (err) {
      return [`Could not parse staged ${MARKETPLACE_PATH}: ${err.message}`];
    }
  }

  return evaluate({ submoduleChanges, marketplaceStaged, marketplace, pluginNames: committedPluginNames(root) });
}

function main() {
  const root = repoRoot();
  const problems = checkConsistency(root);
  if (problems.length === 0) return 0;

  process.stderr.write("\n[pre-commit] marketplace.json / submodule pointer mismatch:\n\n");
  for (const p of problems) process.stderr.write(`  - ${p}\n`);
  process.stderr.write(
    "\nmarketplace.json is the single owner of version + source.sha for every plugin -- both must change " +
      "together, in this commit.\n\n"
  );
  return 1;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = {
  main,
  parseStagedSubmoduleChanges,
  findPluginEntry,
  evaluate,
  committedPluginNames,
  checkConsistency,
  repoRoot,
  MARKETPLACE_PATH,
};
