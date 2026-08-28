#!/usr/bin/env node
'use strict';
// Usefulness: does the one message an arm shipped hand the reader anything to
// navigate by — a marked outcome, a link to the file they must open, a table
// where the facts are parallel — or is it a wall of plain sentences?
//
// readability.js scores how hard the words are. This scores what the message
// gives the eye. They are different questions: a message can read at grade 2
// and still bury the one fact that matters in the middle of a paragraph.
//
// MORE IS NOT BETTER, and the bands say so. Signaling goes negative when it is
// mis-aimed: highlighting the wrong content damages comprehension AND the
// reader's own sense of what they understood. So the columns below are read
// against a band, never maximised — one or two bold marks, a handful of
// blocks, a table only where rows are genuinely parallel. Plain Claude's 8.6
// bold marks per message is not eight times better than one, it is noise with
// a bold face on.
//
// KNOWN CEILING, stated the way caps.js and readability.js state theirs. This
// is a regex pass over markdown, not a parser and not a reader. It counts
// marks; it cannot tell whether a mark landed on the right words. Fenced
// blocks are excluded from the prose counts and reported as their own column,
// because a code block is content, not a signpost. Every arm is scored by the
// same code, which is what makes the comparison fair and each absolute number
// soft.
//
//   node runner/structure.js --records records/rm280-7e554675
//   node runner/structure.js --tag full --by-segment

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const FENCE = /```[\s\S]*?(?:```|$)/g;

// The bands a message is read against, not scored out of. Sources for the two
// that come from outside this harness are in the usefulness-criteria report.
const BANDS = {
  bold: [1, 3],     // signaling, bounded — same marks every time
  blocks: [2, 4],   // segmenting — chunk by meaning
};

const inBand = (n, [lo, hi]) => n >= lo && n <= hi;

/** Markdown affordances in one final message. */
function analyzeMessage(text) {
  const src = String(text || '');
  const prose = src.replace(FENCE, '\n');
  const lines = prose.split('\n');
  const tableRows = lines.filter((l) => /^\s*\|.*\|/.test(l)).length;
  const bold = (prose.match(/\*\*[^*\n]+\*\*/g) || []).length;
  // A block is a paragraph, a list, or a table — whatever a blank line sets off.
  const blocks = prose.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean).length;
  const links = [...prose.matchAll(/\[[^\]\n]+\]\(([^)\n]+)\)/g)].map((m) => m[1]);
  const anchored = links.filter((t) => /:\d+/.test(t)).length;

  return {
    // Linking is the only thing here that is about navigation rather than
    // emphasis: it is the difference between naming a file and handing the
    // reader the file. Anchored is the stricter half — a target carrying the
    // line, `path/file.js:37`, drops the reader on the spot, where a bare path
    // still leaves them to find the place themselves.
    links: links.length,
    anchoredLinks: anchored,
    bold,
    codeSpans: (prose.match(/`[^`\n]+`/g) || []).length,
    tableRows,
    hasTable: tableRows > 0,
    bullets: lines.filter((l) => /^\s*(?:[-*+]|\d+\.)\s+\S/.test(l)).length,
    headings: lines.filter((l) => /^\s*#{1,6}\s+\S/.test(l)).length,
    blocks,
    hasFence: (src.match(/```/g) || []).length >= 2,
    boldInBand: inBand(bold, BANDS.bold),
    blocksInBand: inBand(blocks, BANDS.blocks),
  };
}

// --- many records ------------------------------------------------------------

const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);
const pct = (rows, f) => (rows.length ? (100 * rows.filter(f).length) / rows.length : 0);

/** arm -> usefulness totals, optionally sliced by segment. */
function structureReport(records, { bySegment = false } = {}) {
  const scored = [];
  for (const r of records) {
    if (!r || r.error || !r.finalText) continue;
    scored.push({
      arm: r.arm, task: r.task, segment: r.segment || 'unsegmented',
      ...analyzeMessage(r.finalText),
    });
  }

  const roll = (rows) => ({
    runs: rows.length,
    links: mean(rows.map((s) => s.links)),
    anchoredLinks: mean(rows.map((s) => s.anchoredLinks)),
    bold: mean(rows.map((s) => s.bold)),
    codeSpans: mean(rows.map((s) => s.codeSpans)),
    bullets: mean(rows.map((s) => s.bullets)),
    headings: mean(rows.map((s) => s.headings)),
    blocks: mean(rows.map((s) => s.blocks)),
    tablePct: pct(rows, (s) => s.hasTable),
    fencePct: pct(rows, (s) => s.hasFence),
    linkedPct: pct(rows, (s) => s.links > 0),
    // Share of the arm's links that carry a line. Null when the arm never
    // linked at all — a zero there would read as "linked badly" when it means
    // "never linked", and those are different failures.
    anchoredPct: rows.reduce((n, s) => n + s.links, 0)
      ? (100 * rows.reduce((n, s) => n + s.anchoredLinks, 0)) / rows.reduce((n, s) => n + s.links, 0)
      : null,
    boldInBandPct: pct(rows, (s) => s.boldInBand),
    blocksInBandPct: pct(rows, (s) => s.blocksInBand),
  });

  const arms = {};
  for (const arm of [...new Set(scored.map((s) => s.arm))]) {
    const rows = scored.filter((s) => s.arm === arm);
    arms[arm] = roll(rows);
    if (bySegment) {
      arms[arm].segments = {};
      for (const seg of [...new Set(rows.map((s) => s.segment))]) {
        arms[arm].segments[seg] = roll(rows.filter((s) => s.segment === seg));
      }
    }
  }
  return { bands: BANDS, runs: scored.length, arms };
}

// --- CLI ---------------------------------------------------------------------

function readRecordsDir(dir) {
  return fs.readdirSync(dir)
    .filter((f) => f.endsWith('.json') && f !== 'batch.json')
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));
}

const n1 = (x) => (x == null ? '-' : x.toFixed(1));
const n2 = (x) => (x == null ? '-' : x.toFixed(2));
const HEAD = ['arm', 'runs', 'bold', 'in-band%', 'link', 'anchored%', 'linked%', 'table%', 'code',
  'bullet', 'head', 'blocks', 'in-band%', 'fence%'];
const row = (arm, a) => [arm, a.runs, n2(a.bold), n1(a.boldInBandPct), n2(a.links),
  n1(a.anchoredPct), n1(a.linkedPct), n1(a.tablePct), n2(a.codeSpans), n2(a.bullets), n2(a.headings),
  n1(a.blocks), n1(a.blocksInBandPct), n1(a.fencePct)].join('\t');

function main() {
  const argv = process.argv.slice(2);
  const at = (flag) => (argv.includes(flag) ? argv[argv.indexOf(flag) + 1] : null);
  const tag = at('--tag');
  const recordsArg = at('--records');
  const bySegment = argv.includes('--by-segment');
  const dir = recordsArg
    ? path.resolve(ROOT, recordsArg)
    : tag
      ? path.join(ROOT, 'results', tag, 'runs')
      : null;
  if (!dir) {
    console.error('Usage: structure.js --records <dir> | --tag <tag> [--by-segment]');
    process.exit(1);
  }

  const report = structureReport(readRecordsDir(dir), { bySegment });
  const arms = Object.keys(report.arms).sort(
    (a, b) => (a === 'baseline' ? -1 : b === 'baseline' ? 1 : a.localeCompare(b)));

  console.log(`usefulness — ${path.relative(ROOT, dir)}`);
  console.log(`read against bands, not maximised: bold ${BANDS.bold.join('-')} marks, `
    + `blocks ${BANDS.blocks.join('-')} per message\n`);
  console.log(HEAD.join('\t'));
  for (const arm of arms) console.log(row(arm, report.arms[arm]));

  if (bySegment) {
    const segs = [...new Set(arms.flatMap((arm) => Object.keys(report.arms[arm].segments || {})))];
    for (const seg of segs) {
      console.log(`\n--- ${seg} ---`);
      console.log(HEAD.join('\t'));
      for (const arm of arms) {
        const a = report.arms[arm].segments?.[seg];
        if (a) console.log(row(arm, a));
      }
    }
  }
}

if (require.main === module) main();

module.exports = { analyzeMessage, structureReport, BANDS };
