# Report Schema Reference

Output format specifications for the quality audit. Referenced by Phase 4 of the audit skill.

---

## Markdown Report Template

```markdown
# Rules Quality Audit

**Project**: [working directory path]
**Date**: [audit date]
**Files scanned**: [count]
**Rules extracted**: [count]
**Model version**: [Claude model used for judgment factors]

---

## Corpus Quality: C (0.52)

Dominant weakness across corpus: F7

**What this score is and is not**

This measures how clearly Claude can parse each rule in your corpus. It does NOT predict
whether Claude will follow these rules — compliance depends on what Claude
already does for each rule's target behavior and requires direct measurement.

The N lowest-quality rules account for most of the quality gap.

*(Effective: incorporates file length penalties. Rule-average: 0.XX over N mandate rules)*

Guideline quality (override + preference rules): B (0.XX) (N rules, reported separately)

**Note**: The headline metric is `effective_corpus_quality`, which
incorporates per-file length penalties and position weighting. The diagnostic
`corpus_quality` (rule-average ignoring file length) is reported as a
comparison, not the headline. Letter grades use half-open intervals:
A ∈ [0.80, 1.00], B ∈ [0.65, 0.80), C ∈ [0.50, 0.65), D ∈ [0.35, 0.50), F ∈ [0.00, 0.35).

---

## Per-rule Scores

| File | Rule (truncated) | Grade | Score | Category | Dominant Weakness | Action |
|------|-------------------|-------|-------|----------|-------------------|--------|
| .claude/rules/api.md:7 | "Validate all request bodies..." | A | 0.84 | mandate | F7 (concreteness) | Add more concrete markers |
| CLAUDE.md:15 | "Try to prefer functional..." | D | 0.42 | mandate | F7 (concreteness) | Rewrite: concrete trigger |
| .claude/rules/commits.md:3 | "Run prettier before commit" | C | 0.59 | mandate | F3 (distant trigger) | Add trigger proximity — "when modifying X files, run prettier" |

*Sorted by leverage: (load_prob × severity × (1 - score)) descending.*

*Rules with low F8 (e.g., "Run prettier before commit") appear in a separate "Hook opportunities" section — see below. Hook opportunities are a parallel signal; they don't affect the comprehension grade above.*

### Detailed breakdown (per rule)

For each rule in the table above, the following detail is available:

```
File: .claude/rules/api.md:7
Rule: "Validate all request bodies at the handler boundary using Zod.
       Example: CreateUserSchema.parse(req.body)"
Category: mandate
Score: 0.84

  F1 verb strength:        0.85  (contribution: 0.188)
  F2 framing polarity:     0.85  (contribution: 0.125)
  F3 trigger-action dist:  0.80  (contribution: 0.153)
  F4 load-trigger align:   0.95  (contribution: 0.140)
  F7 concreteness:         0.80  (contribution: 0.235)  ← dominant weakness

  Clarity: 0.83 | Activation: 0.87
  Dominant weakness: F7 — add more concrete markers (file paths, function names, schema examples)
  Action: Rewrite with more specifics

  Parallel signal (not in composite):
  F8 enforceability: 0.65 → is_hook_candidate: false (above 0.40 threshold)
```

---

## Per-file Scores

| File | Mean Quality | Prohibition Ratio | Concreteness Coverage | Dead-zone Rules | Trigger Coherence |
|------|-----------------|-------------------|----------------------|-----------------|-------------------|
| .claude/rules/api.md | 0.74 | 0.10 | 0.60 | 1 | 0.05 (coherent) |
| CLAUDE.md | 0.44 | 0.45 | 0.20 | 3 | 0.35 (mixed) |

---

## Positive Findings

These rules score above 0.80 — leave them alone or use as templates for rewrites:

| File | Rule | Score | Why it works |
|------|------|-------|--------------|
| .claude/rules/api.md:3 | "ALWAYS use project-aware methods..." | 0.85 | Strong verb, concrete API names, specific alternative |

---

## Top 3 Highest-Leverage Rewrites

1. **CLAUDE.md:15** — "Try to prefer functional components when possible"
   Current score: 0.42 → Projected: 0.82
   Dominant weakness: F7 (specificity: 0.35)
   Rewrite: "Use functional components for all new React files. Example: components/Button.tsx — function, not class."

2. **CLAUDE.md:22** — "Run prettier before committing"
   Current score: 0.59 → Projected: N/A (better as a hook)
   Dominant weakness: F3 (trigger-action distance: 0.45 — "before committing" is a distant future event)
   Parallel signal: F8=0.15 → appears in "Hook opportunities" section
   Action: Convert to PreToolUse hook on Bash(git commit*). Remove from CLAUDE.md.

3. **CLAUDE.md:8** — "Always validate parsed output shape"
   Current score: 0.47 → Projected: 0.72
   Dominant weakness: F7 (specificity: 0.25)
   Rewrite: "Validate all parsed external data with Zod schemas. Example: `const parsed = ExternalSchema.parse(rawData)` — fail loudly on shape mismatch."

---

*N rules excluded by .rulesense-ignore.*
```

## --fix Mode Diff Format

When `--fix` is passed, append a `## Suggested Rewrites` section. Include rewrites for all rules scoring below their category floor.

```markdown
## Suggested Rewrites

### Rewrite for CLAUDE.md:15 (score: 0.42 → projected: 0.82)

\`\`\`diff
- Try to prefer functional components when possible
+ Use functional components for all new React files.
+ Example: components/Button.tsx — function, not class.
+ Convert class components only when adding new behavior to them.
\`\`\`

Factors improved: F1 (0.20 → 0.85), F7 (0.35 → 0.85)
```

Rewrites are suggestions. Do NOT write files — only show diffs in the report.

## JSON Output Schema

When `--json` is passed, output the full report as a JSON object:

```json
{
  "schema_version": "0.1",
  "pipeline_version": "0.1.0",
  "project": "/path/to/project",
  "date": "2026-04-11",
  "files_scanned": 5,
  "rules_extracted": 24,
  "methodology": {
    "weights_version": "quality-heuristic-0.1",
    "pipeline_version": "0.1.0",
    "model_version": "claude-opus-4-6"
  },

  "effective_corpus_quality": {
    "score": 0.520,
    "methodology": "file-score weighted aggregate over mandate-rule-bearing files"
  },

  "corpus_quality": {
    "rule_mean_score": 0.580,
    "rule_count": 18,
    "note": "diagnostic: rule-average ignoring file length penalty"
  },

  "guideline_quality": {
    "score": 0.620,
    "rule_count": 6
  },

  "rules": [
    {
      "id": "R001",
      "file": ".claude/rules/api.md",
      "line_start": 7,
      "line_end": 8,
      "text": "Validate all request bodies at the handler boundary using Zod.",
      "category": "mandate",
      "score": 0.770,
      "pre_floor_score": 0.767,
      "floor": 1.000,
      "leverage": 0.230,
      "factors": {
        "F1": {"value": 0.85, "method": "lookup", "matched_verb": "validate", "matched_score_tier": 0.85, "matched_position": 0},
        "F2": {"value": 0.85, "method": "classify", "matched_category": "positive_imperative"},
        "F3": {"value": 0.80, "level": 3, "reasoning": "same-task action"},
        "F4": {"value": 0.95, "method": "glob_match"},
        "F7": {"value": 0.80, "method": "count", "concrete_count": 3, "abstract_count": 0},
        "F8": {"value": 0.65, "level": 2, "reasoning": "schema validation partially lintable"}
      },
      "contributions": {
        "F1": 0.188, "F2": 0.125, "F3": 0.153,
        "F4": 0.140, "F7": 0.235
      },
      "layers": {
        "clarity": 0.830,
        "activation": 0.870
      },
      "dominant_weakness": "F7",
      "dominant_weakness_gap": 0.400,
      "failure_class": "ambiguity",
      "degraded": false,
      "degraded_factors": [],
      "scored_count": 5,
      "skipped_floors": [],
      "mechanical_score": 0.870,
      "staleness": {"gated": false, "missing_entities": []},
      "f8_value": 0.650,
      "is_hook_candidate": false
    }
  ],

  "files": [
    {
      "path": ".claude/rules/api.md",
      "file_score": 0.720,
      "length_penalty": 1.000,
      "prohibition_ratio": 0.10,
      "trigger_scope_coherence": 0.05,
      "concreteness_coverage": 0.60,
      "dead_zone_count": 1
    }
  ],

  "positive_findings": [
    {
      "file": ".claude/rules/api.md",
      "line": 3,
      "text": "ALWAYS use project-aware methods...",
      "score": 0.850
    }
  ],

  "rewrite_candidates": [
    {
      "rule_id": "R015",
      "score": 0.420,
      "dominant_weakness": "F7"
    }
  ],

  "hook_opportunities": [
    {
      "id": "R007",
      "text": "Never force-push to main.",
      "file": "CLAUDE.md",
      "line_start": 12,
      "f8_value": 0.30,
      "suggested_enforcement": "Git hook (pre-commit / pre-push)"
    }
  ],

  "conflicts": [
    {
      "type": "polarity_mismatch",
      "rule_a": {
        "id": "R003",
        "text": "NEVER edit files in src/main/gen/ directly.",
        "file": "CLAUDE.md",
        "line_start": 5,
        "polarity": "prohibition"
      },
      "rule_b": {
        "id": "R012",
        "text": "Use src/main/gen/ cached results for faster access.",
        "file": ".claude/rules/api.md",
        "line_start": 8,
        "polarity": "positive_imperative"
      },
      "shared_markers": ["src/main/gen/"]
    }
  ]
}
```

### Field Notes

- **Precision**: All score and layer values use 3 decimal places in JSON. Markdown display uses 2.
- `effective_corpus_quality.score`: The headline metric. File-score weighted aggregate over mandate-rule-bearing files, incorporating length penalties and position weighting.
- `corpus_quality.rule_mean_score`: Diagnostic only — rule-average ignoring file length penalty. NOT the headline metric.
- `rules[].factors`: Each factor is a nested object with `value`, `method`, and factor-specific evidence fields. Values may be `null` for factors the model could not score (degraded rules). Includes F8 even though F8 is not a composite factor — F8 is scored and reported as a parallel signal.
- `rules[].contributions`: Per-factor contribution (`w_i * F_i / active_weight`) for the 5 composite factors (F1/F2/F3/F4/F7). `null` for null factors. Sum of non-null contributions equals `pre_floor_score`. F8 is not in `contributions` — it's not part of the composite.
- `rules[].layers`: Two-layer overlay — `clarity` (F1/F2/F7) and `activation` (F3/F4).
- `rules[].dominant_weakness`: Name of the composite factor with the largest gap. Can be F1/F2/F3/F4/F7. **Never F8** — F8 is not a composite factor.
- `rules[].failure_class`: Diagnostic label derived from `dominant_weakness`. One of `"drift"` (F3/F4 — rule not in attention when it fires), `"ambiguity"` (F1/F2/F7 — rule reads multiple ways), or `"conflict"` (rule contradicts another; unmeasured in the current composite). `null` when no `dominant_weakness` is set. Presentation-layer only — does not affect the score.
- `rules[].dominant_weakness_gap`: `w_i * (1 - F_i)` for the dominant weakness. Higher = more leverage from fixing it. Null factors are excluded from this calculation.
- `rules[].degraded`: `true` if any factor has a null value. Score is computed over non-null factors only.
- `rules[].degraded_factors`: List of factor names with null values (e.g., `["F3"]`).
- `rules[].scored_count`: Number of non-null composite factors (5 for fully scored, fewer for degraded).
- `rules[].skipped_floors`: Soft floor factors that were null and therefore skipped (no penalty for unmeasured).
- `rules[].mechanical_score`: Weighted mean over the non-null F1, F2, F4, F7 values (not the canonical mechanical factor set — if any of these are null, they're excluded from both numerator and denominator). Useful as a baseline when judgment factors are null.
- `rules[].f8_value`: F8 factor value, rounded to 3 decimals. Parallel signal only — does not enter the composite score.
- `rules[].is_hook_candidate`: `true` when `f8_value < 0.40`. Flags the rule for the `hook_opportunities` report.
- `rules[].loading`: String: `"always-loaded"` or `"glob-scoped"`. Derived from source file scoping (`paths:` or `globs:` frontmatter).
- `rules[].referenced_entities`: List of `{name, kind, exists}` triples. The entities the staleness gate operates on.
- `rules[].staleness`: Object with `gated` (bool) and `missing_entities` (list of names). When `gated=true`, the staleness multiplier (0.05) crushes the score.
- `rules[].matched_score_tier`: (F1 only) The score tier the matched verb belongs to (e.g., 0.85 for bare_imperative).
- `positive_findings`: Rules scoring > 0.80. **Degraded rules are excluded** — a score based on N/5 factors is not a confirmed positive.
- `rewrite_candidates`: Top 3 rules by leverage.
- `hook_opportunities`: Array of rules with F8 < 0.40, each with `id`, `text`, `file`, `line_start`, `f8_value`, and `suggested_enforcement` (keyword-based suggestion: git hook, linter, Claude Code hook, etc.). Parallel signal — does not affect the comprehension composite.
- `conflicts`: Array of potential conflict pairs between mandate rules. Each element has `type` (currently only `"polarity_mismatch"`), `rule_a` and `rule_b` (each with `id`, `text`, `file`, `line_start`, `polarity`), and `shared_markers` (the concrete markers — paths, APIs, domain terms — that both rules reference). A pair is flagged when one rule reads as a prohibition and another as a positive directive while sharing at least one non-generic concrete marker. Presentation-layer diagnostic — does not affect the composite. False positives are expected; each pair is surfaced as a question for the author, not a verdict.
- `rewrites` (optional, present only with `--fix`): LLM-generated rewrite suggestions for rules below their category floor. See the `--fix Mode Diff Format` section above.

### `rewrites` field shape

When `--fix` is passed, the audit output includes a `rewrites` array:

```json
{
  "rewrites": [
    {
      "rule_id": "R015",
      "file": ".claude/rules/api.md",
      "line_start": 15,
      "original_text": "Try to prefer functional components when possible",
      "suggested_rewrite": "Use functional components for all new React files. Example: components/Button.tsx — function, not class.",
      "old_score": 0.42,
      "new_score": 0.82,
      "old_grade": "D",
      "new_grade": "A",
      "old_dominant_weakness": "F7",
      "new_dominant_weakness": null,
      "factor_improvements": {
        "F7": [
          0.25,
          0.85
        ]
      },
      "judgment_volatility": {
        "flagged": false,
        "f3_delta": 0.05,
        "old_f3": 0.80,
        "new_f3": 0.85
      },
      "projected_score": 0.80,
      "self_verification_delta": 0.02
    }
  ]
}
```

- `judgment_volatility.flagged` is `true` when `|f3_delta| > 0.20`. When flagged, the rendered markdown shows a "judgment changed" warning with pre and post F3 values — indicates that part of the score change came from the F3 judgment factor moving, not from the rewrite targeting F1/F2/F7 directly. F8 is not in this gate — it's a parallel signal and its volatility does not affect the composite.
- `projected_score` is the score the rewrite prompt's logic expected.
- `self_verification_delta` is `|new_score - projected_score|`. If > 0.05, the rendered markdown shows a direction-specific notice and the rewrite is still presented:
  - **Underdelivered** (`new_score < projected_score`): a `**WARNING - Rewrite underdelivered**` line advising the user to review before applying.
  - **Overdelivered** (`new_score > projected_score`): a softer `Note: Rewrite exceeded projection` line clarifying that the improvement is real and the projection was conservative.

  The ±0.05 gate is the acceptance criterion for rewrite projections.
- Regressions are dropped before rendering — any rewrite whose `new_score < old_score` is removed from the array and the original rule is presented unchanged with a "rewrite did not improve" note.

### Schema stability

The `schema_version` field identifies the JSON output format. The current
pre-stable schema is `0.1`. Consumers should branch on `schema_version`
before reading fields — breaking changes between alpha versions are
possible and will be noted in CHANGELOG.md.
