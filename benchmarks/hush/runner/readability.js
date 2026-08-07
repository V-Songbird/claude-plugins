#!/usr/bin/env node
'use strict';
// Reading effort: how hard is the one message an arm shipped, for a reader who
// is tired and skimming?
//
// caps.js scores the final message against hush's OWN stated caps. That is the
// right meter for "did hush keep its promise" and the wrong meter for "is hush
// easier to read than a rival", because a rival never agreed to hush's numbers.
// This file scores every arm on measures that predate all of them: Flesch
// Reading Ease and Flesch-Kincaid Grade Level, mean words per sentence, and the
// share of long words. Published formulas, same code both sides, no arm's own
// contract in the scoring.
//
// Two extra columns are claims BOTH sides make out loud, so they are contested
// ground rather than one tool's rulebook: does the message open with the answer
// instead of a preamble, and does it hand the reader something to run.
//
// KNOWN CEILING, stated the way caps.js states its own. This is a regex pass
// over markdown, not a parser and not a reader. Syllables are counted by a
// vowel-group heuristic that is wrong on some words in every English text, and
// it is wrong the same way for every arm — which is what makes the comparison
// fair and the absolute number soft. Flesch was fitted to prose, not to a
// bulleted engineering report, so a grade level here is a relative signal
// between two texts scored by this same version, never a literacy verdict.
// Fenced blocks are excluded from the prose measures, because code is not
// something a reading-ease formula has an opinion about; whether a message
// carries code is reported as its own column instead.
//
//   node runner/readability.js --records records/claims2-sonnet-4c486329
//   node runner/readability.js --tag full

const fs = require('node:fs');
const path = require('node:path');
const { unitsOf, countWords } = require('./caps.js');

const ROOT = path.resolve(__dirname, '..');
const FENCE = /```[\s\S]*?(?:```|$)/g;

// --- syllables ---------------------------------------------------------------

/**
 * Vowel-group syllable count, the standard heuristic every readability tool
 * uses when it has no dictionary. Deliberately simple: a dictionary would move
 * the absolute numbers a little and the arm-to-arm gap almost not at all.
 */
function syllables(word) {
  const w = word.toLowerCase().replace(/[^a-z]/g, '');
  if (!w) return 0;
  if (w.length <= 3) return 1;
  const trimmed = w
    .replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '')
    .replace(/^y/, '');
  const groups = trimmed.match(/[aeiouy]{1,2}/g);
  return Math.max(1, groups ? groups.length : 1);
}

/** Words the formulas see: inline code collapses to one opaque token, because
 *  `src/net/retryPolicy.js` is a name the reader recognizes, not four words of
 *  prose. Same rule caps.js already applies to its word counts. */
function proseWords(text) {
  return (text.replace(/`[^`\n]+`/g, 'code').match(/[A-Za-z][A-Za-z'-]*/g) || []);
}

// --- one message -------------------------------------------------------------

// Openers both tools ban by name. hush: "skip self-narration (Let me..., Now
// I'll...)". The rival's rule 10 bans the same list plus the pleasantries.
// Matching on the first prose line only — a "Let me know" in the last line is a
// closer, a different rule, and not what this column is about.
const PREAMBLE = /^\s*(great|good|excellent|perfect|sure|certainly|absolutely|of course|no problem|happy to|thanks|thank you|let me\b|let's\b|i'?ll\b|i am going to|i'?m going to|now i|first,? i|to answer|looking at|i see|i notice|i've|i have (?:now )?(?:looked|checked|reviewed))/i;

/** A line the reader could act on: a fenced block, or an inline-code span that
 *  looks like a command rather than a bare identifier. */
const RUNNABLE = /```|`[^`\n]*\s[^`\n]*`/;

function analyzeMessage(text) {
  const src = String(text || '');
  const prose = src.replace(FENCE, '\n');

  const units = unitsOf(prose);
  const words = units.flatMap((u) => proseWords(u));
  const syl = words.reduce((n, w) => n + syllables(w), 0);
  const hard = words.filter((w) => syllables(w) >= 3).length;

  const sentences = units.length;
  const wordCount = words.length;
  // Flesch (1948) and Flesch-Kincaid (Kincaid et al. 1975), unmodified.
  const wps = sentences ? wordCount / sentences : 0;
  const spw = wordCount ? syl / wordCount : 0;
  const ease = sentences && wordCount ? 206.835 - 1.015 * wps - 84.6 * spw : null;
  const grade = sentences && wordCount ? 0.39 * wps + 11.8 * spw - 15.59 : null;

  const firstLine = prose.split('\n').map((l) => l.trim()).find((l) => l && !/^[#>|]/.test(l)) || '';

  return {
    lines: prose.split('\n').filter((l) => l.trim()).length,
    words: countWords(prose),
    sentences,
    proseWords: wordCount,
    wordsPerSentence: wps,
    hardWordPct: wordCount ? (100 * hard) / wordCount : 0,
    ease,
    grade,
    answerFirst: firstLine ? !PREAMBLE.test(firstLine) : false,
    hasRunnable: RUNNABLE.test(src),
  };
}

// --- many records ------------------------------------------------------------

const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);
function median(xs) {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/**
 * arm -> reading-effort totals, optionally sliced by segment. Rates carry their
 * denominator, and a formula that had nothing to score reports null rather than
 * a zero that would drag an average toward "impossible to read".
 */
function readabilityReport(records, { bySegment = false } = {}) {
  const scored = [];
  for (const r of records) {
    if (!r || r.error || !r.finalText) continue;
    scored.push({ arm: r.arm, task: r.task, segment: r.segment || 'unsegmented', ...analyzeMessage(r.finalText) });
  }

  const roll = (rows) => {
    const eases = rows.map((s) => s.ease).filter((n) => n != null);
    const grades = rows.map((s) => s.grade).filter((n) => n != null);
    return {
      runs: rows.length,
      words: median(rows.map((s) => s.words)),
      lines: median(rows.map((s) => s.lines)),
      wordsPerSentence: mean(rows.map((s) => s.wordsPerSentence).filter((n) => n > 0)),
      hardWordPct: mean(rows.map((s) => s.hardWordPct)),
      ease: mean(eases),
      grade: mean(grades),
      answerFirstPct: rows.length ? (100 * rows.filter((s) => s.answerFirst).length) / rows.length : 0,
      runnablePct: rows.length ? (100 * rows.filter((s) => s.hasRunnable).length) / rows.length : 0,
    };
  };

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
  return { runs: scored.length, arms };
}

// --- CLI ---------------------------------------------------------------------

function readRecordsDir(dir) {
  return fs.readdirSync(dir)
    .filter((f) => f.endsWith('.json') && f !== 'batch.json')
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));
}

const n1 = (x) => (x == null ? '-' : x.toFixed(1));

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
    console.error('Usage: readability.js --records <dir> | --tag <tag> [--by-segment]');
    process.exit(1);
  }

  const report = readabilityReport(readRecordsDir(dir), { bySegment });
  const arms = Object.keys(report.arms).sort(
    (a, b) => (a === 'baseline' ? -1 : b === 'baseline' ? 1 : a.localeCompare(b)));

  console.log(`reading effort — ${path.relative(ROOT, dir)}`);
  console.log('higher ease is easier; lower grade, fewer words per sentence and fewer long words are easier\n');
  const head = ['arm', 'runs', 'words', 'lines', 'w/sent', 'long%', 'ease', 'grade', 'answer1st%', 'runnable%'];
  console.log(head.join('\t'));
  for (const arm of arms) {
    const a = report.arms[arm];
    console.log([arm, a.runs, n1(a.words), n1(a.lines), n1(a.wordsPerSentence), n1(a.hardWordPct),
      n1(a.ease), n1(a.grade), n1(a.answerFirstPct), n1(a.runnablePct)].join('\t'));
  }

  if (bySegment) {
    const segs = [...new Set(arms.flatMap((arm) => Object.keys(report.arms[arm].segments || {})))];
    for (const seg of segs) {
      console.log(`\n--- ${seg} ---`);
      console.log(head.join('\t'));
      for (const arm of arms) {
        const a = report.arms[arm].segments?.[seg];
        if (!a) continue;
        console.log([arm, a.runs, n1(a.words), n1(a.lines), n1(a.wordsPerSentence), n1(a.hardWordPct),
          n1(a.ease), n1(a.grade), n1(a.answerFirstPct), n1(a.runnablePct)].join('\t'));
      }
    }
  }
}

if (require.main === module) main();

module.exports = { syllables, proseWords, analyzeMessage, readabilityReport, PREAMBLE };
