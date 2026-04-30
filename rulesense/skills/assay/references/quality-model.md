# Quality Model

Formal specification of the per-rule, per-file, and per-corpus quality scores. This document is the contract — the audit implements exactly what is described here.

## What the score measures (the lens)

Rules in CLAUDE.md and `.claude/rules/` are instructions FOR Claude to follow, not documentation for humans. This score measures **structural clarity for Claude**:

- **F1 Verb strength** — How binding is this? Does Claude know whether to treat it as mandatory or optional?
- **F2 Framing polarity** — Can Claude bind trigger and action to the same noun? Positive imperatives are sturdier than prohibitions.
- **F3 Trigger-action distance** — Will Claude recognize the firing moment? The closer the trigger to the action, the more reliable.
- **F4 Load-trigger alignment** — Will the rule be in Claude's context window when it fires? Scoped rules only load when their glob matches.
- **F7 Concreteness** — Does Claude have specifics to match against? Abstract principles give Claude nothing to act on.
- **F8 Enforceability ceiling** — Could a hook do this more reliably than text? Reported as a parallel signal; see §4 Layer Overlay.

## What the score does NOT measure

Compliance — whether Claude actually follows the rule. The calibration experiment (n=40, see §6) established that rule-text features cannot predict compliance: baseline behavior (what Claude does without the rule) dominates by ~15×. No amount of weight tuning closes this gap.

**The commitment**: this plugin optimizes structural clarity — the part authors can control. Compliance is a separate concern that depends on Claude's training, the conversation context, and the user's prompt framing.

---

## 1. The Formula

### Per-rule Score

```
score = linear * floor

where:
  linear = Σ(w_i * F_i) / Σ(w_i)   for i ∈ {F1, F2, F3, F4, F7}
  floor  = min(smooth_floor(F7, 0.2), smooth_floor(F4, 0.2), staleness_gate())

  smooth_floor(x, t) = min(1.0, x / t)
  staleness_gate()   = 0.05 if any entity referenced by the rule does not exist
                        in the current codebase, else 1.0
```

The 5 composite factors (F1, F2, F3, F4, F7) are scored per `factor-rubrics.md`. They measure Claude-comprehension: does Claude know when the rule fires, what to do, and have the specifics to act on?

F8 (enforceability ceiling) is scored but **not included in the composite**. F8 measures tool-selection optimality — whether a hook or linter would enforce the rule more reliably than text. Rules with F8 < 0.40 are reported as "Hook opportunities", a parallel signal. See §4 (Layer Overlay) and §5 (Factor Definitions).

F5 (position in file) is not a per-rule factor — it applies only at per-file composition. F6 (example density) is not a separate factor; its meaning is absorbed by F7 (concreteness).

The score is a plain weighted mean with soft floors. There are no contribution caps — under the placeholder weights no single factor's natural contribution exceeds 0.294, so the weighted mean already prevents single-factor domination without additional machinery.

### Per-file Score

```
file_score = position_weighted_mean(rule_scores) * length_penalty

where:
  position_weighted_mean = Σ(pos_weight_i * score_i) / Σ(pos_weight_i)

  pos_weight_i = smooth triangular interpolation between the file edges and midpoint:

    pct_i      = rule.line_start / line_count                     # ∈ [0, 1]
    triangle   = 1.0 - abs(2.0 * pct_i - 1.0)                     # 0 at edges, 1 at midpoint
    pos_weight_i = edge_weight - (edge_weight - middle_weight) * triangle

    edge_weight   = weights.json::position_weights.edge            (default 1.0)
    middle_weight = weights.json::position_weights.middle          (default 0.80)

  # Result: pos_weight_i = 1.0 exactly at the top/bottom lines,
  # linearly ramps down to 0.80 at the exact file midpoint, and back up.
  # No step function — a rule at line 20 of a 100-line file scores essentially
  # the same as a rule at line 21.

  length_penalty = 1.0                               if lines <= 120
                   max(0.6, 1.0 - 0.005*(lines-120)) if lines > 120
```

**Assumption — position weighting**: The position weights encode a Claude-cognitive claim — that Claude's parsing attention is stronger at the edges of a file than in the middle. This is an author-judgment heuristic consistent with general attention patterns in sequence models; it is **not** empirically validated against Claude's actual rule-following behavior. The calibration experiment tested composite-vs-compliance at the rule level, not position effects. Treat the position weighting as "the author believes this, and it affects the score" rather than "this is measured".

**Assumption — length penalty**: The 120-line threshold and 0.005/line decay are heuristic choices below Anthropic's documented ~200-line soft ceiling. The penalty encodes a Claude-cognitive claim — that Claude's ability to apply rules from a file degrades as the file grows — with a specific degradation curve. The threshold and curve are author judgment; the degradation direction is consistent with context-window economics but the exact shape is unvalidated. Per-fixture pre-registration validated that scores move in the expected direction when length changes, not that the magnitude matches Claude's actual behavior.

### Per-corpus Score

```
corpus_score = Σ(load_prob_r * score_r * severity_r) / Σ(load_prob_r * severity_r)

where:
  - sum is over all mandate-category rules across all files
  - load_prob: 1.0 for always-loaded files, user-configurable per-file
    for glob-scoped files (default 0.5), set in .rulesense.config
  - severity: 1.0 default, overridable per-file in .rulesense.config
```

Non-mandate rules (override, preference) are excluded from `corpus_score` and reported in a separate "guideline quality" line item.

### Effective Corpus Quality (headline metric)

```
effective_corpus_quality = Σ(load_prob_f * severity_f * file_score_f) / Σ(load_prob_f * severity_f)

where:
  - sum is over mandate-rule-bearing files only
  - file_score incorporates position weighting and length penalty
```

This is the **headline metric** reported by `rulesense`. It differs from the per-rule `corpus_score` above because it incorporates file-level penalties (position weighting, length penalty). The per-rule `corpus_score` is reported as a diagnostic comparison ("rule-average ignoring file length penalty") but is NOT the headline.

The distinction matters for projects with files exceeding 120 lines — the effective score will be lower than the rule average because the length penalty applies.

### Worked Example

Rule: "Validate all request bodies at the handler boundary using Zod. Example: `CreateUserSchema.parse(req.body)`"
File: `.claude/rules/api.md` with `globs: "src/api/**/*.ts"`

| Factor | Value | Weight | w*F | Reasoning |
|--------|-------|--------|-----|-----------|
| F1 (verb strength) | 0.85 | 1.5 | 1.275 | "Validate" = bare imperative |
| F2 (framing polarity) | 0.85 | 1.0 | 0.850 | Positive imperative |
| F3 (trigger distance) | 0.80 | 1.3 | 1.040 | "At the handler boundary" = soon (same task) |
| F4 (load-trigger align) | 0.95 | 1.0 | 0.950 | Glob matches API files, rule is about API validation |
| F7 (concreteness) | 0.80 | 2.0 | 1.600 | Names Zod, request bodies, handler boundary; one inline code example (`CreateUserSchema.parse`) |

Parallel signal (not in composite):
| F8 (enforceability) | 0.65 | — | — | Partially enforceable (schema validation linter). Reported as a hook-opportunity signal. |

```
linear = (1.275 + 0.850 + 1.040 + 0.950 + 1.600) / 6.8
       = 5.715 / 6.8
       = 0.840

floor = min(smooth_floor(0.80, 0.2), smooth_floor(0.95, 0.2), 1.0)
      = min(1.0, 1.0, 1.0) = 1.0

score = 0.840 * 1.0 = 0.84
```

Layer overlay:
```
Clarity    = (1.5*0.85 + 1.0*0.85 + 2.0*0.80) / 4.5
           = (1.275 + 0.850 + 1.600) / 4.5 = 0.83
Activation = (1.3*0.80 + 1.0*0.95) / 2.3
           = (1.040 + 0.950) / 2.3 = 0.87
```

Dominant weakness: `argmax(w*(1-F))` over composite factors = F7 at `2.0*(1-0.80) = 0.40`. Improving concreteness (e.g., adding more specific examples) would lift the score most.

---

## 2. Soft Floors

Soft floors kill the score for rules that fail a minimum-viability check, but do so continuously rather than as a cliff.

```
smooth_floor(x, threshold) = min(1.0, x / threshold)
```

With threshold = 0.2:
- x = 0.00 → multiplier = 0.00 (rule is null)
- x = 0.05 → multiplier = 0.25 (severe penalty)
- x = 0.10 → multiplier = 0.50 (substantial penalty)
- x = 0.20 → multiplier = 1.00 (no penalty — floor cleared)
- x > 0.20 → multiplier = 1.00 (floor is a floor, not a ceiling)

**Applied to**: F7 (specificity) and F4 (load-trigger alignment). These are the factors where near-zero values make a rule fundamentally deficient regardless of other factor quality.

The `staleness_gate()` is a separate check: if any entity referenced by the rule (file path, API name, package) does not exist in the current codebase, the entire score is multiplied by 0.05. This is distinct from F4's load-trigger alignment — F4 measures whether the *loading scope* matches the *trigger scope*, while staleness measures whether the *referenced entities* still exist. Both can independently kill the score.

**Rationale**: Tukey biweight-style soft thresholding avoids the user-confusion of hard step functions. A user who improves specificity from 0.00 to 0.10 sees the score go from ~0 to ~half, not from ~0 to ~full. The gradient matches the intuition that "fixing the worst problem produces a big improvement."

---

## 3. Contribution Caps

The formula is a plain weighted mean. Under the `quality-heuristic-0.1` weights, no single factor's natural contribution (`w_i / Σw`) exceeds 0.294 (F7 at `2.0/6.8`). The weighted mean already prevents single-factor domination: a rule with one perfect factor and four at zero scores `w_i / Σw ≤ 0.294` — low enough that the substitution-prevention property holds without additional machinery. Adding caps that never bind is dead code that claims a property it doesn't enforce.

**Substitution prevention**: Achieved by the soft floors (§2), which kill the score when specificity (F7) or load-trigger alignment (F4) is near zero. These are the two failure modes where single-factor compensation is genuinely dangerous — a well-worded rule that references nonexistent code, or a specific rule loaded in the wrong context. The weighted mean handles the rest.

---

## 4. Layer Overlay (Reporting Spec)

After computing the per-rule linear score, also compute and report two layer scores for diagnostic purposes. Layer scores are for strategic guidance ("where do I start fixing?") — they do NOT participate in score computation.

```
Clarity    = (1.5*F1 + 1.0*F2 + 2.0*F7) / (1.5+1.0+2.0)
           = (1.5*F1 + 1.0*F2 + 2.0*F7) / 4.5

Activation = (1.3*F3 + 1.0*F4) / (1.3+1.0)
           = (1.3*F3 + 1.0*F4) / 2.3
```

Each layer uses the same weights as the main formula, normalized within the layer.

**F8 is a parallel signal**, not a layer. It's reported separately as "Hook opportunities" — a list of rules that would be more reliably enforced by a hook or linter than as text Claude reads. F8 does not contribute to Clarity, Activation, or the composite score.

**Display format:**
```
Comprehension: 0.84 (Grade: A)
  Clarity     (verb, polarity, specificity):      0.83
  Activation  (trigger distance, load alignment): 0.87

Hook opportunities: 3 rules (listed separately)
```

The layer names map to actionable questions:
- Low Clarity → "Rewrite the rule to be clearer and more specific"
- Low Activation → "Scope the rule better or move the trigger closer to the action"
- Hook opportunities → "Consider migrating these rules to hooks or linter config"

---

## 5. Factor Definitions

Full definitions, measurement procedures, and scoring tables are in `factor-rubrics.md`. Summary:

| # | Factor | Layer | Tier | Measures |
|---|--------|-------|------|----------|
| F1 | Verb strength | Clarity | Mechanical | Modal commitment: must/always > should > prefer/try to |
| F2 | Framing polarity | Clarity | Mechanical | Positive imperative > prohibition > hedged preference |
| F3 | Trigger-action distance | Activation | Judgment | Immediate > soon > distant > abstract |
| F4 | Load-trigger alignment | Activation | Semi-mechanical | Glob scope matches internal trigger condition? |
| F7 | Concreteness | Clarity | Semi-mechanical | Concrete nouns, code markers, and examples vs abstract guidance |
| F8 | Enforceability ceiling | **Parallel** | Judgment | Could a hook/linter do this strictly better? *(not in composite)* |

**Numbering note**: F5 (position in file) is not a per-rule factor — it applies only at per-file composition. F6 (example density) is not a separate factor — its meaning is absorbed by F7 (concreteness, formerly specificity). The gaps in the numbering are preserved because factor IDs are stable identifiers, not ordinal indices.

**Epistemic anchor**: F1 and F2 are mechanically scored (deterministic regex and lookup tables) to provide an introspection-independent anchor for the overall quality score. F4 is semi-mechanical — it uses bag-of-words keyword overlap between glob path components and rule text, not deterministic glob matching. While F4's procedure is testable and reproducible, it involves semantic similarity heuristics that place it closer to F7 than to the strict determinism of F1/F2.

**F6 / F7 relationship**: F6 and F7 had a corpus correlation of 0.85 at n=40 in the calibration experiment — they were measuring the same underlying property (presence of concrete code markers). F6 was merged into F7 by dropping F6 from the pipeline. F7 now absorbs example density into the concreteness measurement.

---

## 6. Scoring Commitment

**The model is a structural-clarity heuristic, not a compliance predictor.** Factor decomposition is useful for identifying which part of a rule is weak (`dominant_weakness`) and driving rewrite suggestions. The composite score does NOT predict how often Claude will follow the rule — that depends on baseline compliance (what Claude does without the rule), which cannot be estimated from rule-text features alone.

Users who need compliance predictions should measure compliance directly on their own test suite.

---

## 7. Factor Scoring Rubrics

Full rubrics are in `factor-rubrics.md`. Each factor has:

- **Mechanical factors (F1, F2)**: Deterministic lookup tables and regex procedures. No LLM judgment. Reproducible across runs.
- **Semi-mechanical factors (F4, F7)**: F4 uses bag-of-words keyword overlap (testable but not strictly deterministic). F7 uses counting algorithms (concrete nouns, code markers, inline references, examples) with LLM fallback for ambiguous cases. F7 absorbs what was previously a separate F6 example-density factor.
- **Judgment factors (F3, F8)**: 4-5 level rubrics with worked examples per level. LLM applies a constrained rubric factor-by-factor, not as an overall score.

---

## 8. Rule Extraction

Full algorithm is in `instruction-parser.md`. Summary:

1. Strip metadata (frontmatter, headings, blank lines, annotations)
2. Identify chunk boundaries (bullets > section breaks > sentence boundaries)
3. Classify chunks as rule candidates or prose
4. Merge clarification chunks into preceding rules
5. Split compound rules with multiple independent directives
6. Assign categories (per-rule annotation > file default > mandate)
7. Record line numbers for position weighting
8. Output ordered list of rule records

---

## Weights

**`weights.json` version: `quality-heuristic-0.1`**.

| Factor | Weight |
|--------|--------|
| F1 (verb strength) | 1.5 |
| F2 (framing polarity) | 1.0 |
| F3 (trigger-action distance) | 1.3 |
| F4 (load-trigger alignment) | 1.0 |
| F7 (concreteness) | 2.0 |
| **Total** | **6.8** |

F8 (enforceability, weight 1.5) is retained as a parallel signal — see §4.

These weights reflect author judgment about the relative importance of the 5 factors for structural clarity. They are NOT calibrated against compliance data — the calibration experiment showed that no weight calibration produces a predictive model at this feature set. Changing weights changes the heuristic, not the predictive power. The plugin commits to quality ≠ compliance: the composite measures structural clarity, not how often Claude follows the rule.

---

## Rule Categories

Rules are classified into three categories that determine scoring behavior:

| Category | Floor | Scoring Adjustment |
|----------|-------|--------------------|
| **Mandate** (default) | 0.50 | Standard rubric, all factors at normal weight |
| **Override** | 0.25 | F1, F3 expected-weak — breakdown notes this |
| **Preference** | 0.25 | F1 and F2 reweighted — no penalty for hedged verbs |

Categories are declared via:
- File-level: `default-category: mandate` in YAML frontmatter
- Per-rule: `<!-- category: override -->` comment immediately before the rule

Non-mandate rules are excluded from the main `corpus_score` and reported under a separate "guideline quality" metric.

---

## Per-file Metrics (Reported)

In addition to `file_score`, the following metrics are computed and reported per file but not composited into the score:

| Metric | Definition | Purpose |
|--------|-----------|---------|
| `prohibition_ratio` | count(rules with F2 < 0.60) / total rules | Files above ~60% prohibitions may be harder to act on consistently |
| `trigger_scope_coherence` | stddev of F4 across rules in the file | High stddev = file mixes well-scoped and poorly-scoped rules |
| `concreteness_coverage` | fraction of rules with F7 >= 0.60 | What percentage of rules have substantive concrete markers or examples |
| `dead_zone_count` | high-scoring rules (> 0.70) placed near the file midpoint where the smooth position weight dips below ~0.90 | High-quality rules placed where position weighting discounts them (see §1 assumption) |

**Assumption note for `dead_zone_count`**: This metric depends on the position-weighting assumption documented in §1 Per-file Score. If Claude's parsing attention doesn't actually follow a triangular distribution, the "dead zone" isn't a dead zone — it's just the middle of the file. The metric is retained because the position weighting is also retained; both depend on the same unvalidated author-judgment claim about Claude's attention. Users acting on `dead_zone_count` should treat it as "rules the scoring model discounts" rather than "rules Claude ignores".

---

## Dominant Weakness

For each rule, the **dominant weakness** is the factor whose improvement would lift the score most:

```
dominant_weakness = argmax_i(w_i * (1 - F_i))
```

This identifies the factor with the largest gap between its current contribution and its maximum possible contribution, weighted by importance. The dominant weakness is reported in the per-rule table and drives the "suggested action" column and the `--fix` mode rewrite prompts.

---

## Corpus-Level Gap Threshold (`gap_threshold`)

The per-corpus "what to fix first" ranking uses a cumulative-leverage Pareto threshold to pick the smallest set of mandate rules whose improvement would close most of the corpus-level quality gap.

```
For mandate rules sorted by leverage (descending):
  count the rules needed until cumulative leverage ≥ gap_threshold × total_leverage
```

- **Parameter:** `weights.json::gap_threshold` (default `0.63`).
- **Meaning:** "The N rules listed cover `gap_threshold × 100`% of the corpus's total leverage." At the default of 0.63, the "what to fix first" list covers ~63% of the total achievable quality improvement.
- **Consumer:** `report.py::_count_gap_rules` (used by the markdown report to decide how many rules to surface in the "biggest problem" summary).
- **Tunable:** Raising the threshold lists more rules (broader coverage, longer list); lowering it lists fewer (higher-leverage-only).

## Parallel-Factor Configuration (`parallel_factors`)

F8 (enforceability ceiling) is not in the composite; it reports as a parallel signal that populates the "Hook opportunities" section. Its configuration lives under `weights.json::parallel_factors.F8`:

| Field | Purpose | Consumed by |
|---|---|---|
| `threshold` (default `0.40`) | Rules with `F8 < threshold` are flagged as hook candidates. | `compose.py::_F8_HOOK_THRESHOLD` |
| `role` (`"hook_opportunity_signal"`) | Semantic tag documenting F8's non-composite role. | Documentation only |

---

## Numerical Precision Invariant

The audit emits scores and derived metrics at two different precisions depending on the surface:

| Surface | Precision | Scope |
|---|---|---|
| `audit.json` (all 0.0–1.0 scores) | 3 decimal places | `rules[].score`, `rules[].pre_floor_score`, `rules[].floor`, `rules[].dominant_weakness_gap`, `rules[].f8_value`, `rules[].layers.*`, `rules[].contributions.*`, `rules[].mechanical_score`, `rules[].leverage`, `files[].file_score`, `files[].length_penalty`, `files[].prohibition_ratio`, `files[].trigger_scope_coherence`, `files[].concreteness_coverage`, `effective_corpus_quality.score`, `corpus_quality.rule_mean_score`, `guideline_quality.score` |
| Markdown report (`report.py`) | 2 decimal places | All per-rule and per-file tables, rewrite comparisons, factor breakdowns |
| HTML overview (`generate_overview.py`) | 2 decimal places | All visible score rendering |

**Why this split:** 3-decimal JSON preserves fidelity for diff-comparison across audit runs (a 0.7723 → 0.7841 delta is visible in the data even when both round to `0.78` in the markdown). 2-decimal rendering keeps user-facing output readable. JSON consumers that diff audits over time should always read from `audit.json` directly, not parse the markdown.
