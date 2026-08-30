<!--
  Shared plugin README template for this marketplace.
  Copy this into <plugin>/README.md, fill the placeholders, and DELETE every guidance comment.
  All plugins here share this lean shape, tone, and style.

  THE GOLDEN RULE: short, and it should sound like a person wrote it, not a pitch deck.
  If a reader sees a wall of text or marketing hype, they won't read it.
  Write for a regular user / "vibe coder", not an engineer. Aim for ~60-110 lines of prose;
  worked proof (diffs, honest tables, charts) is exempt from the count — trim the words
  around the proof, never the proof.
  razor/, hush/, and foreman/ are the reference implementations — all three share one
  section order: header → badges → NAV → TL;DR → What is this? → Why you'd want it → How it works →
  Install → What you can do → <one feature section> → Benchmarks → Under the hood → Settings →
  Good to know → License (optional sections dropped where they don't apply, never reordered).

  NAV: a centered line of in-page links sits between the badges and the TL;DR — 4-5 entries,
  Install first and bolded, so a reader who only wants the files never scrolls the pitch.
  Every entry must point at a real "## " heading in the same file. GitHub builds an anchor
  from the heading TEXT, so renaming a section breaks its link with nothing to warn you;
  scripts/git-hooks/check-readme-nav.js resolves every anchor and runs in the pre-commit
  hook and in CI. Rename a section, fix the nav in the same commit.

  TL;DR: every README opens with a blockquote directly under the badges — 2-3 sentences,
  under ~50 words: the pain, what the plugin does about it, and one defensible number if you
  have one. Many readers stop there. Write it last, place it first.

  VOICE: a warm, patient friend showing a tired developer their favorite tool at the end of
  a long day. The reader is smart but running on empty — short sentences, everyday words,
  benefit first. Five habits carry it:
    1. Short sentences. Aim under ~15 words each, one idea per sentence. A sentence that
       needs a semicolon or a parenthesis is two sentences — split it.
    2. Everyday words. When a plain word is just as true as the technical one, use the plain
       one ("the file that lists your dependencies", not "the manifest"). Swapping a word is
       free; explaining one costs a line. Gloss an unavoidable term in a few plain words, in
       the same sentence.
    3. Benefit first. Open every section with what the reader gets, never with mechanism.
       The takeaway is the first sentence — the reader should be able to stop anywhere and
       leave with the point.
    4. Concrete, not abstract. Give the real number ("$0.159 an average session") over "much
       cheaper." And never write a line that implies the reader should already have known
       something.
    5. Easy to skim. Paragraphs of 2-3 short sentences around one idea. Bold lead-ins on
       bullets, one idea per bullet. Name the thing instead of a vague "it"/"this" when the
       reader might lose track.
  Still reach for the vivid, memorable comparison over the safe abstract one ("every session
  forgets everything the moment it ends," not "state isn't persisted between sessions"). A light
  joke, a wink, a little warmth is welcome — but clarity wins every tie, and the joke is never
  at the reader's expense. House rules, first two non-negotiable:
    - No profanity, ever. Crude isn't a substitute for funny — if a line only lands because of
      a swear word, cut the word and find the cleaner, sharper version of the same joke.
    - Never make the joke at a real project's or a real person's expense. You MAY name a
      competitor here — this is the README, the one surface where naming a rival is allowed, and
      "beating the giants" framing is welcome — but name it to out-compete it on the merits, not
      to belittle it. Sell on our own numbers; let the comparison do the talking.
    - The README is the ONLY place a competitor/reference name may appear. Everywhere else in
      this marketplace — CHANGELOGs, manifests, code comments, test names, commit messages, PR
      text — still contrasts with a generic category ("a plugin that just tells the model to be
      brief"); the real names live only in gitignored private notes (docs/research/). A
      pre-commit + commit-msg hook enforces this, skipping README.md and always guarding commits.
    - Self-deprecating humor about the PROBLEM ("AI assistants love to add things") or about
      the genre of README this is ("does it actually work, or is this just vibes") is fair game.
  Still no jargon in the plain-language sections (no "context traffic", "PreToolUse", "n=6",
  "tokens", schema/field names) — a joke about jargon is fine, actual jargon isn't.

  House rules:
  - Keep ONLY what a user actually wants to read. Cut mechanism deep-dives, reference tables
    (schemas, hook internals, exhaustive config), comparison tables, and any "Tests" section
    (testing lives in CONTRIBUTING.md). Deep detail stays in the code / a linked schema doc.
  - Sections marked (optional) may be dropped when they don't apply.
  - Badges: License (static, never goes stale) and a "Works with Claude Code" badge are fine.
    Do NOT hard-code a version number badge — this marketplace's single source of truth for
    version is the root `marketplace.json` (see CONTRIBUTING.md), and a version baked into the
    README would drift the moment it's released. If you want a version badge, it has to read
    the number dynamically (e.g. from a shields.io endpoint) — otherwise leave it out.
  - The logo needs two files: `assets/logo.svg` (dark fill, shown in light mode) and
    `assets/logo-dark.svg` (identical artwork, fill swapped to white, shown in dark mode).
    The `<picture>`/`<source media="prefers-color-scheme">` markup below picks the right one.
  - For a caveat that deserves visual weight (an honest limit, a non-destructive guarantee),
    use a GitHub alert (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`) instead of an italic aside —
    matches how the plain-language sections already read at a skim. Sparingly: 1-2 per README.
    Reserve `[!WARNING]`/`[!CAUTION]` for real risk (data loss, a destructive command) — a cost
    or scope caveat is a `[!NOTE]`, not a warning.

  ---
  VOICE EXEMPLAR (synthetic, house-written — a fictional plugin, so nothing real is named).
  The VOICE paragraph above is the spec; this is what it sounds like in practice, so a specific
  line's tone can be checked against an example instead of a summary. Delete this whole appendix
  along with the rest of this comment on copy; it is reference material for calibrating tone,
  never content that ships in a plugin's README.

  # gutter

  Your AI assistant writes beautiful commit messages for code that doesn't compile.
  gutter makes it check first.

  ## What is this?

  Every AI coding tool ships the same demo: flawless code, first try, confetti. Then you
  use one for a week. You meet its favorite sentence: "This should work now." Should. The
  most load-bearing word in modern software.

  gutter is a few small hooks — scripts that run at the right moment. They turn "should
  work" into "ran it, exit code 0, here's the line that proves it." No dashboard, no
  subscription, no whitepaper about synergy. It sits quietly and catches what rolls past.

  ## How it works

  | When | What happens |
  |---|---|
  | The assistant claims something works | gutter checks whether anything was actually run |
  | Nothing was | One gentle nudge: run it, or just say plainly that you didn't |
  | Something ran, and it failed | The failure gets quoted back before "done" is allowed |

  That's the whole trick. You could do this yourself, every time, forever, and never once
  get tired of it. You will not. That's what gutter is for.

  ## Good to know

  gutter reads what happened — it can't read minds. A test that passes for the wrong reason
  sails right through. Catching that one is still on you. And if you'd rather gutter stayed
  quiet, it will: one setting, documented below, no hard feelings.

  Does it actually work, or is this just vibes? The receipts are in the repo — every claim
  above maps to a test you can run in about two seconds.
-->

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg" />
    <img src="assets/logo.svg" alt="<plugin>" width="240" />
  </picture>
  <h1><plugin></h1>
  <p><strong><!-- one-line value prop: a blunt clause + its consequence, plain language --></strong></p>
</div>

<p align="center">
    <a href="https://github.com/V-Songbird/<!-- plugin name -->/stargazers"><img src="https://img.shields.io/github/stars/V-Songbird/<!-- plugin name -->?style=social" alt="GitHub stars"/></a>
    <a href="https://https://github.com/V-Songbird/<!-- plugin name -->/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/spec-kit" alt="License"/></a>
    <a href="https://docs.anthropic.com/en/docs/claude-code"><img src="https://img.shields.io/badge/Claude_Code-E5582B" alt="License"/></a>
</p>

<p align="center">
    <a href="#install"><strong>Install</strong></a> &nbsp;·&nbsp;
    <a href="#what-is-this">What is this?</a> &nbsp;·&nbsp;
    <a href="#what-you-can-do">What you can do</a> &nbsp;·&nbsp;
    <a href="#benchmarks">Benchmarks</a> &nbsp;·&nbsp;
    <a href="#settings">Settings</a>
</p>

> **TL;DR** — <!-- 2-3 sentences, under ~50 words: the pain, what the plugin does about it,
     one defensible number if you have one. The only part many readers see. -->

---

## What is this?

<!-- 2-3 short plain sentences. Open with the pain the user already feels, then what the plugin
     does about it. No mechanism, no jargon. -->

## Why you'd want it

<!-- 3-4 bullets, each a **bold lead-in** + one sentence. Benefits the user feels, not features. -->

- **<benefit>.** <one sentence>

## How it works

<!-- (optional — only when the plugin has a real set of distinct triggers/moments worth naming, e.g.
     razor's gates or hush's compression points.) A short 2-row-to-6-row table — "Moment" / "What
     happens" — reads faster than bullets and gives the section its own visual shape. Bullets are
     fine too if a table feels forced for your plugin. Still zero jargon — no hook names, no env
     vars, no schema. Skip this section entirely if "Why you'd want it" is already trigger-framed
     (e.g. "After each commit, it notices X and records it") — don't add a section that just
     restates the bullets above. razor and hush are the reference implementations. -->

| Moment | What happens |
| --- | --- |
| <trigger/moment> | <what happens, one sentence> |

## Install

Inside Claude Code, run:

```
/plugin marketplace add V-Songbird/foundry
/plugin install <plugin>@foundry
```

<!-- one line: when it takes effect; "nothing to configure" if true; any one-time step, stated simply.
     If there's a sibling plugin, close the section with a one-line cross-sell ("Running <sibling>
     too? They fire on different moments of a session, so neither notices the other.") — the
     early ad lives here; any pair NUMBERS stay in Benchmarks where they're earned, and a
     pair section only exists while it carries a measurement. -->

## What you can do

<!-- (optional — only if the plugin has user-facing commands/skills.) ONE compact table for
     every user-facing command — never a separate section per command. A feature that needs
     its own pitch gets the single slot below instead, and only one plugin-wide. A must-know
     caveat for a command goes right under the table: one plain sentence, or one alert
     (`> [!IMPORTANT]`) if it's a guarantee worth visual weight. At most one alert here.
| You want to… | Command |
| --- | --- |
| <plain outcome> | `/<plugin>:<command>` |
-->

## <one feature, named as what the reader gets>

<!-- (optional — AT MOST ONE per README, and most plugins should have none.) Earn this slot
     only when a real feature is invisible where it stands: off by default, or buried in a
     settings row nobody reads. A section here is the discovery fix. Anything already obvious
     from "What is this?" or a command in the table above does NOT get one.
     Title it as the payoff in the reader's words, never the internal feature name
     ("Why-notes that find you later", not "The decision log").
     TWO short paragraphs, hard cap. First: the pain, what turning it on does, and — if it's
     off by default — say so plainly and why. Second: at most one adjacent surprise the
     reader may already have hit. Then link out to a sibling doc for everything else
     (`decision-log.md` alongside the README, same pattern as a schema doc). Reference
     material, config tables, and file formats live in that doc, NEVER inlined here. -->

## The numbers

<!-- (optional — drop it entirely rather than inventing numbers.) SHORT. The front page carries
     the headline and the honest loss, and NOTHING else; the full tables live in
     `docs/BENCHMARKS.md`. In order:
       1. One or two sentences on what a test session actually is, in plain words.
       2. Two or three small tables, each under its own bold question — "Does it still work?",
          "How much noise?". Two rows each: `no plugin`, then your plugin in bold.
       3. A `> [!IMPORTANT]` box titled "Where <plugin> doesn't win", naming the real losses and
          linking to the full page. Disclosing the loss is the trust lever.
       4. One italic line: numbers move between runs, run it yourself, link `benchmarks/`.
     Never put a per-run number, a batch tag, a sample size, an arm name, or a p-value here. -->

## Going deeper

<!-- REQUIRED once the plugin has more than one page. This is the pressure valve that keeps the
     front page readable: everything technical lives behind it. A borderless two-column table,
     link on the left, one plain-words line on the right. The standard set:

| | |
| --- | --- |
| [How <plugin> works](docs/HOW-IT-WORKS.md) | What runs and when |
| [Settings](docs/SETTINGS.md) | Every switch and number, and what each one does |
| [The numbers](docs/BENCHMARKS.md) | Full results, including where it loses |
| [Run the benchmarks](benchmarks/) | The harness, so you can check any of it yourself |

     Add a row per extra page; drop a row the plugin has no page for. `docs/` is gitignored by
     default and each published page is allow-listed by name in the plugin's `.gitignore`, so
     local research notes can share the folder without ever shipping. -->

## Good to know

<!-- (optional) 1-3 short, user-facing gotchas only — the things a user might actually hit.
     Not developer-only caveats. -->

- <gotcha>

## License

MIT — see [LICENSE](./LICENSE).
