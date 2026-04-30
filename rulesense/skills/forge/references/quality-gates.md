# Quality Gates

Validation checklist for generated rules. Gates are quality-based: rules that pass all gates will score above their category floor when audited.

Run these checks after writing rule files and before reporting success.

---

## Quality Gate

Every new rule must meet the quality floor for its declared category:

| Category | Floor | Meaning |
|----------|-------|---------|
| **Mandate** | 0.50 | Rule is expected to be clear for Claude to parse and apply (strong verbs, concrete, scoped) |
| **Override** | 0.25 | Acknowledges expected-weak factors for exception rules |
| **Preference** | 0.25 | Hedged verbs are intentional; scored on clarity/specificity instead |

Score each rule using the 5-factor comprehension composite (F1/F2/F3/F4/F7) plus the F8 parallel signal (see `../assay/references/factor-rubrics.md` and `../assay/references/quality-model.md`).

If a rule scores below floor:
1. Show the per-factor breakdown with cap status
2. Identify the dominant weakness
3. Suggest a rewrite that would lift the score above floor
4. If the user insists on keeping the original text, proceed — note it will appear in future audits

---

## Structural Gates

These checks ensure the rule integrates cleanly with the existing instruction set:

### No Stale References
Every file path, tool name, framework, or package referenced in a directive must exist in the project. Verify with Glob or Read.

### No Dead Globs
For every `globs:` pattern in frontmatter, run `Glob("<pattern>")` against the repository. Zero matches = dead pattern. Fix before writing.

### No Contradictions
Read all existing rules and new rules together. No two directives should conflict. If a new rule intentionally overrides an existing one, use `<!-- category: override -->` and make the override explicit.

### Proper Scoping
Rules with specific trigger language ("when editing API files", "for test files") must have matching `globs:` frontmatter. Do not make subsystem-specific rules always-loaded.

Ask: "Does this rule apply when editing ANY file?" If no, scope it with `globs:`.

### Reasonable Density
Each rule file should stay under 120 lines / 30 rules. If approaching limits, split into focused files with appropriate `globs:` scoping. (Anthropic's documented ceiling is ~200 lines; 120 is a practitioner's soft limit that leaves headroom.)

---

## Enforceability Check

For each new rule, check whether a hook or linter could enforce it:

- **Hook candidate**: "Run X before/after Y" where X is a deterministic shell command → suggest PreToolUse/PostToolUse hook instead
- **Linter candidate**: indentation, import ordering, naming case, semicolons, trailing commas, line length, bracket style → suggest linter/formatter config instead

These rules score low on F8 (enforceability ceiling). F8 is a parallel signal — low-F8 rules appear in the audit's "Hook opportunities" section but do NOT drag down the comprehension composite. The builder should flag them and let the user decide whether to keep the text rule or migrate to mechanical enforcement.

---

## Pre-write Checklist

Before writing any rule file:

- [ ] Rule scores above category floor (Claude-comprehension quality gate)
- [ ] No stale references
- [ ] Glob patterns match existing files
- [ ] No contradictions with existing rules
- [ ] Scoped rules have `globs:` frontmatter matching their trigger
- [ ] File won't exceed density limits
- [ ] Enforceability alternatives surfaced to user
- [ ] Category declared if not mandate (`default-category:` in frontmatter or `<!-- category: X -->`)
