# Instruction Parser

Algorithm for extracting discrete rules from Claude Code instruction files (.claude/rules/*.md, CLAUDE.md). Each extracted rule becomes the unit of analysis for quality scoring.

Extraction stability is a prerequisite for reproducibility — two runs of this algorithm on the same file must produce the same rule count and boundaries.

---

## Algorithm

### Input

A single instruction file (markdown).

### Output

An ordered list of **rule records**, each containing:
- `text`: the full text of the rule (one or more sentences/lines)
- `line_start`: line number where the rule begins
- `line_end`: line number where the rule ends
- `category`: `mandate` (default), `override`, or `preference`
- `file_path`: path to the source file

### Steps

**Step 1 — Strip metadata.** Remove from consideration:
- YAML frontmatter (everything between opening `---` and closing `---` at file top)
- Blank lines
- Lines that are only markdown headings (`#`, `##`, etc.)
- Lines that are only horizontal rules (`---`, `***`, `___`)
- HTML comments that are category annotations (`<!-- category: X -->`) — extract the category value, do not treat as rule text

**Step 2 — Identify chunk boundaries.** Remaining lines are grouped into chunks. Boundary signals, in precedence order:

1. **Bullet/list item boundary** (highest precedence): A line starting with `- `, `* `, or `1. ` (or any numbered list marker) begins a new chunk. Continuation lines (indented text following a list item without a new bullet marker) belong to the same chunk.

2. **Section break boundary**: A blank line (already stripped in Step 1, but its *position* is preserved as a boundary marker) between non-list prose paragraphs separates chunks.

3. **Sentence boundary** (lowest precedence, applies only within prose paragraphs): Within a paragraph that is not a list, each sentence ending with `.`, `!`, or `?` followed by a space and a new capitalized word is a potential chunk boundary. Apply only when the paragraph contains multiple imperative sentences.

**Precedence rule**: When signals conflict (e.g., a sentence boundary inside a bullet point), the higher-precedence signal wins. A sentence boundary inside a bullet item does NOT split the chunk — the entire bullet item is one chunk.

**Step 3 — Classify chunks.** For each chunk, determine whether it is a **rule candidate** or **prose**.

A chunk is a **rule candidate** if it contains at least one of:
- An imperative verb from the F1 lookup table (must, always, never, use, ensure, run, prefer, avoid, do not, etc.)
- A constraint keyword: "only", "required", "forbidden", "mandatory"
- A conditional directive pattern: "when X, do Y", "if X, then Y", "for X files, Y"

A chunk is **prose** if:
- It contains no imperative verb or constraint keyword
- It begins with explanatory markers: "This means", "This is because", "The reason", "Note that", "Background:", "Overview:", "For context"
- It describes a mechanism without a directive: "The CI pipeline runs...", "The deploy agent handles..."
- It is a pure reference statement: "See [file] for details" (with no directive verb)

**Step 4 — Merge clarification chunks.** A prose chunk immediately following a rule candidate is a **clarification** if:

- It lacks an imperative verb, AND
- It begins with: "This means", "For example", "i.e.", "e.g.", "In other words", "Specifically", "That is", OR
- It is an indented continuation of the previous chunk, OR
- It is a code block (fenced with ` ``` `)

Merge clarification chunks into the preceding rule candidate. The merged text becomes the rule's `text` field. The clarification enriches the rule (and will boost its F7 concreteness score) but is not a separate rule.

**Step 5 — Split compound rules.** A single chunk may contain multiple independent directives. Split when:

- A bullet item contains comma-separated imperatives with different objects: "Use TypeScript for all new code, prefer interfaces over types, and avoid `any`" → 3 rules
- A bullet item contains "and" or ";" joining directives with different subjects or objects: "Run tests before committing and ensure no warnings remain" → 2 rules

Do NOT split when:
- The "and" joins two parts of the same action: "Edit the .bnf source and regenerate" → 1 rule (two steps of one process)
- The compound describes scope, not separate directives: "When editing API routes or middleware" → 1 rule

**Split heuristic**: If the parts after splitting could each stand alone as a complete instruction (they each have a verb and an object), split them. If one part would be incomplete without the other, don't split.

**Step 6 — Assign categories.** For each rule:

1. Check for a `<!-- category: X -->` annotation on the line immediately preceding the rule's chunk. If found, set `category = X`.
2. If no per-rule annotation, use the file's `default-category` from YAML frontmatter. If present, set `category = default-category`.
3. If neither exists, set `category = mandate`.

Valid category values: `mandate`, `override`, `preference`.

**Step 7 — Assign line numbers.** Record `line_start` and `line_end` for each rule based on its position in the original file (before Step 1 stripping). This enables the per-file position weighting in the scoring formula.

**Step 8 — Output.** Return the ordered list of rule records.

---

## Discard Rules

The following are discarded (not extracted as rules) even if they contain imperative-sounding language:

- **Headings used as labels**: "## Naming Conventions" is structural, not a directive
- **Table headers and table-of-contents entries**
- **Pure reference pointers**: "See `docs/architecture.md` for the full diagram"
- **YAML frontmatter fields**: `globs:`, `default-category:`, etc.
- **Metadata statements**: "Stack: generic", "Version: 1.0"

---

## Handling Ambiguous Cases

When a chunk is borderline between rule candidate and prose:

1. Apply the **removal test**: "If this chunk were deleted, would Claude's behavior change on any task?" If yes → rule candidate. If no → prose.
2. If still ambiguous after the removal test, classify as a rule candidate. Over-extraction is preferable to under-extraction because a low-scoring rule (caught by the quality model) is better than a missed rule (invisible to the audit).

---

## Worked Example

Given this file content:

```markdown
---
globs: "src/api/**/*.ts"
default-category: mandate
---

# API Rules

- Validate all request bodies at the handler boundary.
- Return consistent error shapes: `{ error: string, code: number }`.
  This ensures clients can parse errors uniformly.
- Use middleware for cross-cutting concerns (auth, logging) — not inline checks.

## Database Access

<!-- category: preference -->
- Prefer transactions for queries spanning multiple tables.
- Consider using read replicas for heavy read operations where latency is acceptable.

The API layer uses Express with TypeScript strict mode enabled.
```

**Extraction result:**

| # | text | line_start | line_end | category |
|---|------|------------|----------|----------|
| 1 | "Validate all request bodies at the handler boundary." | 7 | 7 | mandate |
| 2 | "Return consistent error shapes: `{ error: string, code: number }`. This ensures clients can parse errors uniformly." | 8 | 9 | mandate |
| 3 | "Use middleware for cross-cutting concerns (auth, logging) — not inline checks." | 10 | 10 | mandate |
| 4 | "Prefer transactions for queries spanning multiple tables." | 14 | 14 | preference |
| 5 | "Consider using read replicas for heavy read operations where latency is acceptable." | 15 | 15 | preference |

**Not extracted:**
- Line 1-4: YAML frontmatter (stripped)
- Line 6: heading (stripped)
- Line 12: heading (stripped)
- Line 13: category annotation (consumed, not a rule)
- Line 17: prose ("The API layer uses Express...") — no imperative verb, describes mechanism

Rule 2 merges with its clarification ("This ensures clients can parse errors uniformly.") per Step 4.
Rules 4 and 5 get `category: preference` from the `<!-- category: preference -->` annotation per Step 6.
