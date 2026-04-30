# Manual Pipeline Reference

Fallback instructions for running the audit pipeline manually, if `run_audit.py` fails. Under normal operation, the orchestrator handles all of this.

## Environment Setup

```bash
SCRIPTS="${CLAUDE_PLUGIN_ROOT}/scripts"
PYTHON_CMD="python3"  # or "python" — whichever passed pre-flight
export PYTHONIOENCODING=utf-8  # Unicode survival on Windows cp1252
rm -rf .rulesense-tmp
mkdir -p .rulesense-tmp
printf '*\n' > .rulesense-tmp/.gitignore
```

## Stage 1 — Deterministic Pipeline

The four scripts pipe directly:

```bash
$PYTHON_CMD "$SCRIPTS/discover.py" --project-root "$(pwd)" \
  | $PYTHON_CMD "$SCRIPTS/extract.py" \
  | $PYTHON_CMD "$SCRIPTS/score_mechanical.py" \
  | $PYTHON_CMD "$SCRIPTS/score_semi.py" \
  > ".rulesense-tmp/scored_semi.json"
```

## Stage 2 — Build Judgment Prompts

### Small corpus (≤20 rules)

```bash
$PYTHON_CMD "$SCRIPTS/build_prompt.py" \
  --input ".rulesense-tmp/scored_semi.json" \
  --output ".rulesense-tmp/prompt.md"
```

### Large corpus (>20 rules)

```bash
mkdir -p ".rulesense-tmp/batches"
$PYTHON_CMD "$SCRIPTS/build_prompt.py" \
  --batch-dir ".rulesense-tmp/batches" \
  --input ".rulesense-tmp/scored_semi.json"
```

Produces `batch_manifest.json` with this shape:

```json
{
  "batch_count": 3,
  "batch_size_target": 12,
  "total_rules": 34,
  "batches": [
    {"file": "prompt_001.md", "rule_ids": ["R001", "R002", "...", "R012"]},
    {"file": "prompt_002.md", "rule_ids": ["R013", "R014", "...", "R024"]},
    {"file": "prompt_003.md", "rule_ids": ["R025", "R026", "...", "R034"]}
  ]
}
```

Key names: `file` (prompt filename) and `rule_ids` (array of rule ID strings).

## Stage 3 — Parse Judgments

**F8 is a parallel signal.** Score it in the judgment data anyway — `compose.py` routes F8 to the `hook_opportunities` corpus-level array and the per-rule `f8_value`/`is_hook_candidate` fields but excludes it from the composite score. F3 still contributes to the composite.

Write judgment data via a temp Python script (see SKILL.md Phase 2 for the format), then validate:

### Small corpus

```bash
$PYTHON_CMD "$SCRIPTS/parse_judgment.py" ".rulesense-tmp/scored_semi.json" \
  --input ".rulesense-tmp/raw_judgment.txt" \
  --output ".rulesense-tmp/judgment_patches.json"
```

### Large corpus (per batch)

```bash
EXPECTED_IDS="R001,R002,...,R012"  # from this batch's rule_ids

$PYTHON_CMD "$SCRIPTS/parse_judgment.py" ".rulesense-tmp/scored_semi.json" \
  --expected-ids "$EXPECTED_IDS" \
  --input ".rulesense-tmp/raw_judgment.txt" \
  --output ".rulesense-tmp/batches/patches_NNN.json"
```

After all batches:

```bash
$PYTHON_CMD "$SCRIPTS/merge_batch_patches.py" \
  ".rulesense-tmp/batches" ".rulesense-tmp/scored_semi.json" \
  --output ".rulesense-tmp/judgment_patches.json"
```

## Stage 4 — Compose and Report

```bash
$PYTHON_CMD "$SCRIPTS/compose.py" \
  ".rulesense-tmp/scored_semi.json" ".rulesense-tmp/judgment_patches.json" \
  --output ".rulesense-tmp/audit.json"

$PYTHON_CMD "$SCRIPTS/report.py" --input ".rulesense-tmp/audit.json"
# Add --verbose or --json as needed
```

## Manual Rewrite Scoring

If `rewrite_scorer.py` or `run_audit.py --score-rewrites` fails, build a minimal `scored_semi.json` for each rewrite:

```json
{
  "schema_version": "1.0",
  "pipeline_version": "1.1.0",
  "project_context": {"stack": [], "entity_index": {}},
  "config": {},
  "source_files": [{"path": "", "globs": [],
                     "glob_match_count": 0, "default_category": "mandate",
                     "line_count": 1, "always_loaded": true}],
  "rules": [
    {"id": "RW001", "file_index": 0, "text": "<REWRITE TEXT HERE>",
     "line_start": 1, "line_end": 1, "category": "mandate",
     "referenced_entities": [],
     "staleness": {"gated": false, "missing_entities": []},
     "factors": {}}
  ]
}
```

Every rule needs `"factors": {}` — `score_mechanical.py` writes into this dict.

Pipe through `score_mechanical.py | score_semi.py`, score F3/F8, then run `compose.py`.

### compose.py output fields per rule

`score` (float 0.0-1.0), `dominant_weakness` (factor code or null), `factors` (dict), `contributions`, `layers`, `leverage`, `floor`, `pre_floor_score`, `scored_count`, `mechanical_score`.

There is no `grade` field — compute from score: A ≥ 0.80, B ≥ 0.65, C ≥ 0.50, D ≥ 0.35, F < 0.35.

## Cleanup

```bash
rm -rf .rulesense-tmp
```
