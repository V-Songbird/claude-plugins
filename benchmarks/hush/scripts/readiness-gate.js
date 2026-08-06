#!/usr/bin/env node
'use strict';

// The 1.0 readiness gate.
//
//   node scripts/readiness-gate.js                    audit this harness + the
//                                                     marketplace's hush plugin
//   node scripts/readiness-gate.js --root DIR         audit another checkout that
//                                                     carries both halves itself
//   node scripts/readiness-gate.js --plugin-root DIR  point the plugin half at a
//                                                     hush checkout elsewhere
//
// Since the benchmark suite moved out of the shipped plugin, the evidence
// lives in two homes: the plugin checkout (its tests, README, hooks, skills)
// and this harness (the runner, the retained records, the published claims,
// and the benchmark evidence tests). The gate reads each point's artifacts
// from the home that owns them; a fixture checkout that carries both halves
// under one root still audits exactly as before.
//
// Ten points decide whether hush can leave alpha. They are written out below,
// verbatim, each one beside the check that proves it — this file is the
// checklist, so a point cannot drift away from its evidence. Every check runs
// something: the tests that already prove the invariant, or the artifact whose
// content is the claim. Each point reports MET or NOT MET, names what it used,
// and one unmet point exits non-zero. There is no warning level: a point that
// is not proven is not met.
//
// Slower than the unit suite on purpose — it shells out to `node --test` once
// per evidence file, about 20 seconds in all. It is a release-boundary tool,
// not something to run in a loop. tests/readiness_gate.test.js breaks each
// check's evidence on purpose and asserts the matching point flips, because a
// gate nobody can fail proves nothing.

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { readRecords } = require('../benchmarks/runner/records.js');
const { buildClaims } = require('../benchmarks/runner/publish.js');

// The harness home (this checkout) and the plugin's default home (the
// marketplace repo checks hush out as a sibling of benchmarks/).
const HARNESS_ROOT = path.join(__dirname, '..');
const SIBLING_PLUGIN = path.resolve(__dirname, '..', '..', '..', 'hush');
const RECORDS_DIR = 'benchmarks/records';
// One published claim set per batch, beside the records that regenerate it.
const publishedClaimsPath = (batchId) => `${RECORDS_DIR}/${batchId}/published/claims.md`;

// --- running the evidence ----------------------------------------------------

/** One evidence test file, run for real. Exit status is the verdict. */
function runTestFile(file, root) {
  const env = { ...process.env };
  // A nested runner inherits the parent's IPC wiring otherwise.
  delete env.NODE_TEST_CONTEXT;
  delete env.NODE_CHANNEL_FD;
  // A release gate must not inherit the developer's shell at all: not the off
  // switches, not the tuning knobs (HUSH_TEMPLATE, HUSH_SIDECAR, HUSH_CAP_*)
  // that quietly change what a transform does under the evidence tests.
  for (const k of Object.keys(env)) if (k.startsWith('HUSH_')) delete env[k];
  const started = Date.now();
  const r = spawnSync(process.execPath, ['--test', '--test-reporter=tap', path.join(root, file)],
    { cwd: root, encoding: 'utf8', env, timeout: 600000 });
  const out = r.stdout || '';
  const count = (re) => Number((out.match(re) || [])[1] || 0);
  return { pass: r.status === 0, tests: count(/^# tests (\d+)/m), fail: count(/^# fail (\d+)/m), ms: Date.now() - started };
}

// --- shapes ------------------------------------------------------------------
// A check returns { met, claim, evidence: [string], missing }. `claim` is what
// holding the point means here; `evidence` is what was actually run or read.

const met = (claim, evidence) => ({ met: true, claim, evidence, missing: null });
const unmet = (claim, evidence, missing) => ({ met: false, claim, evidence, missing });

/**
 * The common shape: named test files carry the point, optionally alongside
 * artifact checks for the half of a point no test covers. Anything unmet takes
 * the whole point down with it. `runner` picks the home the files run in:
 * ctx.tests for plugin evidence, ctx.harnessTests for benchmark evidence.
 */
function proves(ctx, files, claim, extras = [], runner = 'tests') {
  const runs = files.map((f) => ctx[runner](f));
  const plural = (n) => `${n} test${n === 1 ? '' : 's'}`;
  const evidence = runs.map((r) => `${r.file} — ${r.pass ? `${plural(r.tests)}, all passing` : `${r.fail} of ${plural(r.tests)} FAILING`}`
    + ` (${(r.ms / 1000).toFixed(1)}s)`).concat(extras.map((e) => e.evidence));
  const missing = runs.filter((r) => !r.pass).map((r) => `${r.file} does not pass`)
    .concat(extras.filter((e) => !e.met).map((e) => e.missing));
  return missing.length ? unmet(claim, evidence, missing.join('; ')) : met(claim, evidence);
}

/** An artifact check: the document's content is the claim, so read it. */
function documents(ctx, file, patterns, label) {
  let text;
  try {
    text = ctx.read(file);
  } catch (err) {
    return { met: false, evidence: `${file} — unreadable (${err.code || err.message})`, missing: `${file} cannot be read` };
  }
  const gaps = patterns.filter((p) => !p.test(text));
  return gaps.length
    ? { met: false, evidence: `${file} — ${label}: NOT stated`, missing: `${file} no longer states ${label}` }
    : { met: true, evidence: `${file} — ${label}, in the user's own words` };
}

/** Records are read through the harness's own hash verification, once per run. */
function retained(ctx) {
  if (ctx.cachedRecords) return ctx.cachedRecords;
  let value;
  try {
    const { runs, batches } = readRecords(path.join(ctx.root, RECORDS_DIR));
    // Errored runs stay in: they are records on disk, and the completeness
    // check publish.js runs needs to see them as present rather than missing.
    value = { runs, batches, error: null };
  } catch (err) {
    value = { runs: [], batches: [], error: err.code === 'ENOENT' ? 'directory does not exist' : err.message };
  }
  ctx.cachedRecords = value;
  return value;
}

const moneyFigures = (text) => [...new Set(text.match(/\$\d+\.\d+/g) || [])];

/** A readable sample of a long figure list — the count is the point, not the roll call. */
const someOf = (list, n = 6) => (list.length > n ? `${list.slice(0, n).join(', ')} and ${list.length - n} more` : list.join(', '));

/**
 * True when a published dollar figure is a COST the claim set generated, at
 * the figure's own precision.
 *
 * Traced against the claim set's cost list, never against every number in the
 * markdown: that page is full of numbers that are not money — percentage
 * deltas, run counts, `n`, token traffic, latencies — and at two decimal places
 * a `+50.0%` regression happily backs a `$50.00` README claim it has nothing to
 * do with. This point exists precisely to fail a cost figure the records do not
 * produce, so the collision has to be impossible rather than unlikely.
 */
function figureIsGenerated(figure, claims) {
  const want = Number(figure.slice(1));
  const digits = (figure.split('.')[1] || '').length;
  return (claims.costs || []).some((c) => Number(c.toFixed(digits)) === want);
}

// --- the ten points ----------------------------------------------------------
// Verbatim from the product contract's 1.0 readiness definition. Adding a
// feature never moves this list; proving one of these does.

const POINTS = [
  {
    n: 1,
    point: 'Disable means no Hush behavior.',
    check: (ctx) => proves(ctx, ['tests/disable_conformance.test.js'],
      'HUSH_DISABLE=1 leaves every hook registered in hooks/hooks.json completely inert — no stdout, no file '
      + 'touched — and each inert assertion has an active control on the same payload so it cannot pass vacuously'),
  },
  {
    n: 2,
    point: 'Every lossy view is recoverable until its disclosed expiry.',
    check: (ctx) => proves(ctx, ['tests/transform_properties.test.js'],
      "hooks/lib/transform-manifest.js recoveryGap rejects any rewrite that dropped lines without naming where "
      + 'the rest lives, asserted over seeded generated payloads on what is actually shipped, not on what a '
      + 'transform reports about itself (the expiry itself is point 5)'),
  },
  {
    n: 3,
    point: 'Structured transforms preserve all metadata.',
    check: (ctx) => proves(ctx, ['tests/compress_tool_output.test.js'],
      'fieldGap drops any structured rewrite that lost a field the response arrived with, checked on the '
      + 'delivered shape, so wrapper siblings survive every transform'),
  },
  {
    n: 4,
    point: 'Deletions and failures cannot be silently hidden.',
    check: (ctx) => proves(ctx, ['tests/compress_tool_output.test.js', 'tests/preserve_exit_code.test.js'],
      'a delta names removed lines and where they were removed rather than reporting all-unchanged, failure '
      + 'vocabulary survives the digest, and the real exit code reaches the model'),
  },
  {
    n: 5,
    point: 'Sidecars have a documented lifecycle.',
    check: (ctx) => proves(ctx, ['tests/sidecar_lifecycle.test.js'],
      'a session owns its sidecar namespace, a failed write never costs the output, and session end deletes '
      + 'the directory — with the same lifecycle stated to the user in plain words',
      [documents(ctx, 'README.md', [/deletes that folder when the session ends/i, /a day old/i],
        'when parked output is deleted, and when a crashed session\'s leftovers are swept')]),
  },
  {
    n: 6,
    point: 'Statistics distinguish observation from estimation.',
    // The stats dashboard was cut at 1.0; what remains — and what this point
    // now pins — is the observation record itself: the HUSH_DEBUG manifest
    // logs what each transform actually did (bytes in and out, the action,
    // where recovery lives), and no surface anywhere computes a savings
    // figure for a counterfactual session nobody ran.
    check: (ctx) => proves(ctx, ['tests/hush_debug_manifest.test.js'],
      "hush's record of its own activity is observation — bytes in and out, decisions taken, recovery "
      + 'targets — for every handled output, and nothing in the product prints an estimated savings figure'),
  },
  {
    n: 7,
    point: 'Core, Quiet, Voices, and Draft have separate contracts.',
    check: (ctx) => proves(ctx, ['tests/surface_conformance.test.js'],
      'Core and Quiet switch independently, a surface switch beats every per-hook flag inside it, and the two '
      + 'on-demand surfaces (Voices, Draft) have no hook at all, so neither can start itself',
      [optionalSurfacesStayCold(ctx)]),
  },
  {
    n: 8,
    point: 'Public claims match workload-segment evidence.',
    check: (ctx) => claimsComeFromRecords(ctx),
  },
  {
    n: 9,
    point: 'Configuration and stock-style recovery are stable across updates.',
    check: (ctx) => proves(ctx, ['tests/activate_style.test.js', 'tests/safe_write.test.js'],
      'stock is backed up before anything takes the style slot and restored on demand, and every write is '
      + 'atomic and refuses a symlink, so an interrupted update cannot leave a half-written slot behind'),
  },
  {
    n: 10,
    point: 'The benchmark suite reports uncertainty and publishes auditable run data.',
    check: (ctx) => benchmarkDataIsAuditable(ctx),
  },
];

/** Point 7's other half: nothing on-demand is wired to a hook. */
function optionalSurfacesStayCold(ctx) {
  let wiring;
  let skills;
  try {
    wiring = JSON.stringify(JSON.parse(ctx.read('hooks/hooks.json')));
    skills = fs.readdirSync(path.join(ctx.pluginRoot, 'skills'), { withFileTypes: true })
      .filter((e) => e.isDirectory()).map((e) => e.name);
  } catch (err) {
    return { met: false, evidence: `hooks/hooks.json + skills/ — unreadable (${err.code || err.message})`, missing: 'the hook wiring cannot be read' };
  }
  const wired = skills.filter((s) => wiring.includes(s));
  return wired.length
    ? {
      met: false,
      evidence: `hooks/hooks.json — ${wired.length} of ${skills.length} on-demand skills are wired to a hook`,
      missing: `hooks/hooks.json runs ${wired.join(', ')} — an optional surface that starts itself has no separate contract`,
    }
    : {
      met: true,
      evidence: `hooks/hooks.json — no hook runs any of the ${skills.length} on-demand skills (${skills.join(', ')})`,
    };
}

/**
 * Point 8. A public figure is a claim about a workload; the only thing that can
 * back it is a retained record of that workload's segment. So: records must
 * exist, cover every segment the suite declares, regenerate into the published
 * claim set byte for byte, and account for every figure the README prints.
 */
function claimsComeFromRecords(ctx) {
  const claim = 'every public performance figure in README.md is regenerated from hash-verified run records, '
    + 'per workload segment, each batch complete and published';
  const { runs, batches, error } = retained(ctx);
  let readme = '';
  try { readme = ctx.read('README.md'); } catch { /* reported below through the figure count */ }
  const figures = moneyFigures(readme);
  const evidence = [
    `${RECORDS_DIR}/ — ${runs.length} hash-verified run records${error ? ` (${error})` : ''}`,
    `README.md — ${figures.length} public cost figures${figures.length ? `: ${someOf(figures)}` : ''}`,
  ];

  if (!runs.length) {
    return unmet(claim, evidence,
      `no run records under ${RECORDS_DIR}/, so nothing generates ${figures.length ? someOf(figures) : 'a public figure'}`
      + ' — run the segmented suite, retain its records, and regenerate the claim set with runner/publish.js');
  }

  const segments = Object.keys(JSON.parse(ctx.readHarness('benchmarks/config.json')).segments);

  // Costs are only comparable inside one batch (publish.js refuses a mix),
  // so the claim set is built per batch — a cross-model check is its own
  // batch — and a README figure may trace to any batch's regenerated costs.
  const byBatch = new Map();
  for (const r of runs) {
    const id = r.batchId || '(none)';
    if (!byBatch.has(id)) byBatch.set(id, []);
    byBatch.get(id).push(r);
  }

  const gaps = [];
  const allCosts = { costs: [] };
  for (const [batchId, batchRuns] of [...byBatch.entries()].sort()) {
    // Throws when the batch manifest planned runs whose records are gone.
    const claims = buildClaims(batchRuns, batches);
    allCosts.costs.push(...(claims.costs || []));
    evidence.push(`benchmarks/runner/publish.js — regenerated ${claims.segments.length} segment tables from batch ${claims.batchId}`);

    const covered = new Set(batchRuns.map((r) => r.segment).filter(Boolean));
    const uncovered = segments.filter((s) => !covered.has(s));
    if (uncovered.length) gaps.push(`no records for segment(s) ${uncovered.join(', ')} in batch ${batchId}`);

    const claimsFile = publishedClaimsPath(batchId);
    let published = null;
    try { published = ctx.readHarness(claimsFile); } catch { /* absence is reported below */ }
    if (published === null) gaps.push(`${claimsFile} has never been generated`);
    else if (published.trim() !== claims.markdown.trim()) {
      gaps.push(`${claimsFile} is stale — it does not match what the records regenerate`);
    } else {
      evidence.push(`${claimsFile} — ${published.length} bytes, byte-identical to the regenerated claims`);
    }
  }

  const untraceable = figures.filter((f) => !figureIsGenerated(f, allCosts));
  if (untraceable.length) gaps.push(`${untraceable.length} README figure(s) no record produces: ${someOf(untraceable)}`);

  evidence.push(`batches: ${[...byBatch.keys()].sort().join(', ')}`);
  return gaps.length ? unmet(claim, evidence, gaps.join('; ')) : met(claim, evidence);
}

/**
 * Point 10. Two halves: the statistics report spread (proven by the suite's own
 * tests), and the run data behind them survives the run in a form someone else
 * can check — hash-verified, provenance-stamped, published.
 */
function benchmarkDataIsAuditable(ctx) {
  const { runs, error } = retained(ctx);
  const batchIds = [...new Set(runs.map((r) => r.batchId).filter(Boolean))].sort();
  const unpublished = batchIds.filter((id) => {
    try { return ctx.readHarness(publishedClaimsPath(id)).length === 0; } catch { return true; }
  });

  const audit = (() => {
    if (error) return { met: false, evidence: `${RECORDS_DIR}/ — unreadable: ${error}`, missing: `${RECORDS_DIR}/ cannot be read: ${error}` };
    if (!runs.length) {
      return {
        met: false,
        evidence: `${RECORDS_DIR}/ — 0 retained runs`,
        missing: `${RECORDS_DIR}/ holds no run data, so no number the suite has produced can be re-checked by anyone`,
      };
    }
    const anonymous = runs.filter((r) => !r.batchId || r.seed == null || !r.segment);
    if (anonymous.length) {
      return {
        met: false,
        evidence: `${RECORDS_DIR}/ — ${runs.length} runs, ${anonymous.length} without batch, seed or segment`,
        missing: `${anonymous.length} record(s) carry no batch/seed/segment stamp — an unattributable number is not auditable`,
      };
    }
    if (unpublished.length) {
      return {
        met: false,
        evidence: `${RECORDS_DIR}/ — ${runs.length} runs, all hash-verified and stamped`,
        missing: `${unpublished.map(publishedClaimsPath).join(', ')} has never been generated, so the run data is retained but not published`,
      };
    }
    return {
      met: true,
      evidence: `${RECORDS_DIR}/ — ${runs.length} hash-verified runs, all batch/seed/segment stamped, published per batch (${batchIds.join(', ')})`,
    };
  })();

  return proves(ctx, ['tests/benchmark_evidence.test.js'],
    'every figure is a distribution: n, median, quartiles and a 95% interval per segment, the worst single '
    + 'regression named rather than averaged away — and the runs behind it are retained, tamper-evident and published',
    [audit], 'harnessTests');
}

// --- driving -----------------------------------------------------------------

function runGate({ root = HARNESS_ROOT, pluginRoot = root, runTestFile: runner = runTestFile, points = POINTS } = {}) {
  const cache = new Map();
  const ctx = {
    root,
    pluginRoot,
    // Plugin-side artifacts (README, hooks, the plugin's own tests) come from
    // pluginRoot; harness-side ones (config, records, benchmark evidence)
    // from root. A single-root fixture passes only `root` and gets both.
    read: (rel) => fs.readFileSync(path.join(pluginRoot, rel), 'utf8'),
    readHarness: (rel) => fs.readFileSync(path.join(root, rel), 'utf8'),
    tests: (file) => {
      if (!cache.has(file)) cache.set(file, runner(file, pluginRoot));
      return { file, ...cache.get(file) };
    },
    harnessTests: (file) => {
      const key = `harness:${file}`;
      if (!cache.has(key)) cache.set(key, runner(file, root));
      return { file, ...cache.get(key) };
    },
  };
  const started = Date.now();
  const results = points.map((p) => {
    try {
      return { n: p.n, point: p.point, ...p.check(ctx) };
    } catch (err) {
      // A check that blew up has not proven anything, so it fails closed.
      return { n: p.n, point: p.point, met: false, claim: null, evidence: [], missing: `the check itself failed: ${err.message}` };
    }
  });
  return { root, pluginRoot, results, ok: results.every((r) => r.met), ms: Date.now() - started };
}

function render(report) {
  const out = [`hush 1.0 readiness gate — ${report.results.length} points`,
    report.pluginRoot && report.pluginRoot !== report.root
      ? `harness: ${report.root}\nplugin:  ${report.pluginRoot}`
      : `checkout: ${report.root}`, ''];
  for (const r of report.results) {
    out.push(`${r.met ? '[MET]    ' : '[NOT MET]'} ${r.n}. ${r.point}`);
    if (r.claim) out.push(`          holds when: ${r.claim}`);
    for (const e of r.evidence) out.push(`          evidence:   ${e}`);
    if (!r.met) out.push(`          MISSING:    ${r.missing}`);
    out.push('');
  }
  const failed = report.results.filter((r) => !r.met);
  out.push(`${report.results.length - failed.length} of ${report.results.length} points met in ${(report.ms / 1000).toFixed(1)}s.`);
  out.push(failed.length
    ? `NOT READY FOR 1.0 — point(s) ${failed.map((r) => r.n).join(', ')} unmet. Leaving alpha is blocked until they are.`
    : 'READY FOR 1.0 — every point met.');
  return out.join('\n');
}

function main() {
  const argv = process.argv.slice(2);
  const i = argv.indexOf('--root');
  const p = argv.indexOf('--plugin-root');
  // A bare invocation audits this harness plus the marketplace's own hush
  // checkout; --root keeps the old single-checkout behavior for fixtures.
  const root = i >= 0 ? path.resolve(argv[i + 1]) : HARNESS_ROOT;
  const pluginRoot = p >= 0 ? path.resolve(argv[p + 1]) : i >= 0 ? root : SIBLING_PLUGIN;
  const report = runGate({ root, pluginRoot });
  console.log(render(report));
  process.exit(report.ok ? 0 : 1);
}

if (require.main === module) main();

/** Every test file the gate runs, deduplicated — the suite's own coverage check reads this. */
const evidenceFiles = () => {
  const seen = new Set();
  const fake = (f) => { seen.add(f); return { file: f, pass: true, tests: 0, fail: 0, ms: 0 }; };
  const collect = { root: HARNESS_ROOT, pluginRoot: HARNESS_ROOT, read: () => '', readHarness: () => '', tests: fake, harnessTests: fake };
  for (const p of POINTS) { try { p.check(collect); } catch { /* only the file names matter here */ } }
  return [...seen];
};

module.exports = { runGate, render, runTestFile, POINTS, evidenceFiles, figureIsGenerated, RECORDS_DIR, publishedClaimsPath, HARNESS_ROOT, SIBLING_PLUGIN };
