#!/usr/bin/env node
'use strict';
// Cap conformance: does the message hush actually shipped obey the limits
// hush's own output style states?
//
// The harness already reports what a session cost and how much it said. It has
// never reported whether the one final message honors its own contract — the
// line cap, the per-sentence word cap, the banned punctuation. This scores that
// from `finalText`, a field every run record already carries, so it needs no
// new batch and costs nothing to run.
//
// KNOWN CEILING, and it matters. This is a regex pass over markdown, not a
// parser. It cannot see whether a sentence was long because the reader asked
// for depth, it splits sentences on punctuation so an abbreviation mid-line can
// end a unit early, and it makes one judgment call the style does not make: a
// fenced block is exempt from every count, because fenced blocks are where
// `Never compress` content lives. Numbers from this file are comparable between
// two arms scored by the same version. They are NOT a verdict on the style
// contract, and this file must never become the definition of the caps — the
// style prose is that definition, and this is a second, independent reading of
// it. Where the two disagree, the style wins and this file is wrong.
//
// Deliberately not wired into report.js or publish.js: those build the public
// claims, and a published number needs the readiness gate behind it.
//
//   node runner/caps.js --records records/claims2-sonnet-4c486329
//   node runner/caps.js --tag full

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
// The hush plugin checks out as a sibling of benchmarks/ in the marketplace
// repo, the same path metrics.js already reaches across.
const STYLE = path.resolve(__dirname, '../../../hush/output-styles/hush.md');

// --- the caps, read from the style rather than copied out of it --------------
// verify-style.js already treats the canonical style file as the source of
// truth for every invariant. Same rule here: a cap hard-coded in this file
// would keep scoring the old number after someone changed the style, and no
// test would notice. Parsing throws instead, loudly, at the one place that
// knows both numbers.
function readCaps(styleText) {
  const lineCap = styleText.match(/(\d+) lines, tops/);
  const wordCap = styleText.match(/(\d+) words per sentence, tops/);
  if (!lineCap || !wordCap) {
    throw new Error('caps.js: could not read the line and word caps from the style file — the wording changed, so update this parser rather than guessing');
  }
  return { lineCap: Number(lineCap[1]), wordCap: Number(wordCap[1]) };
}

function loadCaps() {
  return readCaps(fs.readFileSync(STYLE, 'utf8'));
}

// --- one message ------------------------------------------------------------

const FENCE = /```[\s\S]*?(?:```|$)/g;

/** Inline code is one word (a path is a name, not a sentence). Also the one
 *  place punctuation inside an identifier must not be mistaken for prose. */
const collapseCode = (s) => s.replace(/`[^`\n]+`/g, 'X');

/** A markdown link reads as its label — the target in parentheses is plumbing,
 *  not prose, so it must not count as words or as a parenthetical aside. */
const collapseLinks = (s) => s.replace(/\[([^\]\n]*)\]\(([^)\s]*)\)/g, '$1');

const countWords = (s) => (collapseCode(s).match(/\S+/g) || []).length;

/**
 * The units a cap applies to: "15 words per sentence or bullet". A bullet
 * holding two sentences is two units, which is what the style means.
 *
 * Table rows and headings are not sentences — a row carries fields, and the
 * style routes repeated fields into a table on purpose, so scoring those rows
 * as prose would punish the shape it asks for.
 */
function unitsOf(prose) {
  const out = [];
  for (const raw of prose.split('\n')) {
    const line = raw.trim();
    if (!line) continue;
    if (line.startsWith('|')) continue;                 // table row
    if (/^#{1,6}\s/.test(line)) continue;               // heading
    const body = line.replace(/^>\s*/, '').replace(/^([-*+]|\d+\.)\s+/, '').trim();
    if (!body || /^[-|:\s]+$/.test(body)) continue;     // table separator, bare marker
    // A sentence may close inside markup — the style asks for a bold topic
    // lead, so "**Fixed it.** Here is why." is two sentences with `**` sitting
    // between the period and the space. Let the closers through or the two
    // merge into one unit and score as a single long sentence.
    for (const piece of body.split(/(?<=[.!?][*_`"')\]]*)\s+/)) {
      const unit = piece.trim();
      if (unit) out.push(unit);
    }
  }
  return out;
}

/** Score one final message against one set of caps. */
function analyzeMessage(text, caps) {
  const src = String(text || '');
  const fenced = src.match(FENCE) || [];
  const prose = collapseLinks(src.replace(FENCE, '\n'));

  const lines = src.replace(FENCE, '\n').split('\n').filter((l) => l.trim()).length;
  const units = unitsOf(prose).map((text) => ({ text, words: countWords(text) }));
  const over = units.filter((u) => u.words > caps.wordCap);
  const longest = units.reduce((w, u) => (w === null || u.words > w.words ? u : w), null);

  // Banned marks, counted outside inline code so a `a;b` identifier is not a
  // semicolon and `fn(x)` is not an aside.
  const bare = collapseCode(prose);

  return {
    lines,
    overLineCap: lines > caps.lineCap,
    units: units.length,
    overWordCap: over.length,
    semicolons: (bare.match(/;/g) || []).length,
    // razor: a one-character group like "(a)" is read as an enumeration label
    // and not counted, so this under-reports the style's literal wording. The
    // rule bans the mark because it smuggles a second fact, and a single letter
    // smuggles none. Upgrade path if that judgment ever needs testing: drop the
    // {2,} and report both counts side by side.
    parenUnits: units.filter((u) => /\([^)]{2,}\)/.test(collapseCode(u.text))).length,
    fencedBlocks: fenced.length,
    longestWords: longest ? longest.words : 0,
    longestText: longest ? longest.text : '',
    // The over-cap shape matters more than the count: a message one word over
    // is a rounding argument, one at triple the cap is a different rule.
    overBands: bands(over.map((u) => u.words), caps.wordCap),
  };
}

function bands(lengths, cap) {
  const out = { [`${cap + 1}-${cap + 5}`]: 0, [`${cap + 6}-${2 * cap}`]: 0, [`${2 * cap + 1}-${3 * cap}`]: 0, [`${3 * cap + 1}+`]: 0 };
  const keys = Object.keys(out);
  for (const n of lengths) {
    if (n > 3 * cap) out[keys[3]]++;
    else if (n > 2 * cap) out[keys[2]]++;
    else if (n > cap + 5) out[keys[1]]++;
    else out[keys[0]]++;
  }
  return out;
}

// --- many records -----------------------------------------------------------

const sum = (rows, key) => rows.reduce((n, r) => n + r[key], 0);

/**
 * arm -> totals, plus the single worst sentence and the tasks that carry the
 * breaches. A rate needs its denominator beside it, so units ships with every
 * count that is measured per unit.
 */
function capReport(records, caps) {
  const scored = [];
  for (const r of records) {
    if (!r || r.error || !r.finalText) continue;
    scored.push({ arm: r.arm, task: r.task, segment: r.segment || 'unsegmented', ...analyzeMessage(r.finalText, caps) });
  }

  const arms = {};
  for (const arm of [...new Set(scored.map((s) => s.arm))]) {
    const rows = scored.filter((s) => s.arm === arm);
    const worst = rows.reduce((w, s) => (w === null || s.longestWords > w.longestWords ? s : w), null);
    const byTask = {};
    for (const s of rows) if (s.overWordCap) byTask[s.task] = (byTask[s.task] || 0) + s.overWordCap;
    const overBands = {};
    for (const s of rows) for (const [band, n] of Object.entries(s.overBands)) overBands[band] = (overBands[band] || 0) + n;

    arms[arm] = {
      runs: rows.length,
      units: sum(rows, 'units'),
      overWordCap: sum(rows, 'overWordCap'),
      overWordCapPct: rows.length ? (100 * sum(rows, 'overWordCap')) / Math.max(1, sum(rows, 'units')) : NaN,
      overLineCap: rows.filter((s) => s.overLineCap).length,
      semicolons: sum(rows, 'semicolons'),
      parenUnits: sum(rows, 'parenUnits'),
      overBands,
      worst: worst ? { task: worst.task, words: worst.longestWords, text: worst.longestText } : null,
      overWordCapByTask: Object.fromEntries(Object.entries(byTask).sort((a, b) => b[1] - a[1])),
    };
  }
  return { caps, runs: scored.length, arms };
}

// --- CLI --------------------------------------------------------------------

function readRecordsDir(dir) {
  return fs.readdirSync(dir)
    .filter((f) => f.endsWith('.json') && f !== 'batch.json')
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));
}

function main() {
  const argv = process.argv.slice(2);
  const at = (flag) => (argv.includes(flag) ? argv[argv.indexOf(flag) + 1] : null);
  const tag = at('--tag');
  const recordsArg = at('--records');
  const dir = recordsArg
    ? path.resolve(ROOT, recordsArg)
    : tag
      ? path.join(ROOT, 'results', tag, 'runs')
      : null;
  if (!dir) {
    console.error('Usage: caps.js --records <dir> | --tag <tag>');
    process.exit(1);
  }

  const caps = loadCaps();
  const report = capReport(readRecordsDir(dir), caps);
  const baselineFirst = Object.keys(report.arms).sort(
    (a, b) => (a === 'baseline' ? -1 : b === 'baseline' ? 1 : a.localeCompare(b)));

  console.log(`cap conformance — ${path.relative(ROOT, dir)}`);
  console.log(`caps read from the style: ${caps.lineCap} lines, ${caps.wordCap} words per sentence or bullet\n`);
  console.log(['arm', 'runs', 'units', `>${caps.wordCap}w`, 'rate', `>${caps.lineCap} lines`, ';', '(aside)', 'longest'].join('\t'));
  for (const arm of baselineFirst) {
    const a = report.arms[arm];
    console.log([
      arm, a.runs, a.units, a.overWordCap, `${a.overWordCapPct.toFixed(1)}%`,
      a.overLineCap, a.semicolons, a.parenUnits, `${a.worst?.words ?? 0}w`,
    ].join('\t'));
  }
  for (const arm of baselineFirst) {
    const a = report.arms[arm];
    console.log(`\n${arm}: over-cap bands ${JSON.stringify(a.overBands)}`);
    console.log(`${arm}: over-cap sentences by task ${JSON.stringify(a.overWordCapByTask)}`);
    if (a.worst) console.log(`${arm}: longest [${a.worst.words}w ${a.worst.task}] ${a.worst.text}`);
  }
}

if (require.main === module) main();

module.exports = { readCaps, loadCaps, analyzeMessage, capReport, unitsOf, countWords };
