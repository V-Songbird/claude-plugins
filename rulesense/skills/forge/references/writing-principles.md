# Rule writing — checklist, principles, and `paths:` scoping

Load when drafting rules in Phase 3 Step 1 or when deciding whether a rule needs `paths:` frontmatter.

## Rule-writing checklist — apply all to every drafted rule

- **Include a concrete trigger (WHEN).** Name specific files or actions: "When creating `.tsx` files in `src/components/`" — not "for React work".
- **Include an explicit action (WHAT).** Name the exact code pattern: "Use `const Component: FC<Props> = ...` with an explicit Props interface" — not "write clean components".
- **Include a brief intent clause (WHY) in one sentence.** Example: "...because the team standardized on hooks for consistent code-review patterns." The intent clause lets Claude resolve edge cases the literal wording does not cover.
- **Ensure exactly one interpretation.** Re-read the rule as if you were executing it. If you can list two different actions the rule might dictate, rewrite until only one action remains.
- **Resolve ambiguity in the rule text, not in surrounding documentation.** Claude may not load neighboring prose when the rule fires, so embedded clarifications must travel with the rule itself.

## Extractor self-check — required before submitting drafts for scoring

The audit's `extract.py` splits compound directives on specific patterns. A draft that looks fine to human eyes but contains a splitter will fragment into orphan clauses on the next audit, and each fragment scores F because it's a sentence fragment — destroying user confidence in rules you just told them were Grade A.

Before handing a draft to `--score-draft`, verify every rule text passes every check:

- [ ] No `, and ` or ` and ` between two clauses that each have their own imperative verb. Use `or`, a comma + participle, or split into the single most important directive. (Fine: "Use `useState` and `useReducer` interchangeably" — only one verb. Not fine: "Name tests as sentences, and avoid mutating shared fixtures" — two verbs.)
- [ ] No `;` outside a code span. Split into two separate bullets or join with a participle.
- [ ] No ` — ` (em-dash + space) followed by an independent clause with its own imperative verb. Em-dash attached to a parenthetical, example, or adjective phrase is fine.
- [ ] The rule reads as exactly one directive when read aloud. If you hear two imperatives, it will extract as two rules — one of which will lose its trigger and grade F.

Failing any check, revise BEFORE calling `--score-draft`. The script runs this same check as a pre-flight and will refuse to score a fragmenting draft (it returns `status: "needs_revision"` and lists the offenders), so passing a fragmenting draft just forces an extra revision round-trip.

## Drafting rules for the whole set

- Draft each rule to cover a different angle of the topic. Do not restate the same constraint in two rules.
- Include at least one of each type when the topic allows: a **structural** rule (where files go, what to name them), a **quality** rule (what the content should look like), and a **process** rule (when or how to do it).
- Draw concrete examples from the user's actual project — use file paths, directory names, and tool names detected in Phase 2. Do not invent examples.
- Write every rule in the trigger-action pattern: `"When [trigger], [action]."` Reject descriptive statements and abstract principles.
- After drafting, check each rule's enforceability. If enforcement belongs in a hook or linter config, surface that in the output and suggest the alternative mechanism.

## Writing principles

- **Positive imperatives over prohibitions**: "Use X" sticks better than "Never do Y".
- **Concrete triggers over abstract principles**: "When creating .tsx files, use functional components" over "Prefer functional components when possible".
- **At least one example**: Rules without examples are undersupported. Add a concrete case.
- **Specific nouns over abstract guidance**: Name the API, the file path, the pattern. "Use good judgment" is not a rule.
- **Check enforceability**: If a shell command could enforce it, suggest a hook instead.
- **Check linter coverage**: If a linter rule exists for it, suggest the config instead.

## Scoping with `paths:` frontmatter

Rules applying only to specific files need YAML frontmatter. Use `paths:` (the canonical field per Claude Code docs):

```yaml
---
paths:
  - "src/api/**/*.ts"
default-category: mandate
---
```

Verify patterns match files with `Glob` before proposing.
