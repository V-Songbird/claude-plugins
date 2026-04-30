"""Orchestrator for the rulesense pipeline.

Consolidates pipeline mechanics into single commands to reduce
the number of bash invocations (and permission prompts) Claude needs.

Modes:
  --prepare --project-root PATH   Run discover→extract→score→build_prompt
  --finalize [--verbose] [--json] Parse judgments→compose→report
  --prepare-fix                   Select qualifying rules for rewrite
  --score-rewrites                Score rewrites mechanically→build_prompt
  --finalize-fix [--verbose] [--json]  Parse rewrite judgments→finalize→report
  --score-draft <draft.json>      Score draft rules for the build skill
  --finalize-draft                Compose draft scores after F3/F8 judgment
  --prepare-placement             Run placement detectors on audit.json,
                                  output candidates JSON for Phase 3d
  --write-promotions --project-root PATH
                                  Assemble .rulesense/PROMOTIONS.md and
                                  atomically remove moved rules from source;
                                  reads the moves payload from stdin
  --cleanup                       Remove .rulesense-tmp/
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# F-24/F-28: Force UTF-8 on all stdio on Windows.
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
import _lib

SCRIPTS_DIR = Path(__file__).parent
PYTHON = sys.executable
TMP_DIR = ".rulesense-tmp"
BATCH_THRESHOLD = 20

# Friendly fix suggestions keyed by dominant weakness factor code.
# Source of truth: report.py _FRIENDLY_FIXES
_FRIENDLY_FIXES = {
    "F1": "Start with a clear action verb: Use, Always, Never, Run",
    "F2": "Flip from 'don't do X' to 'do Y instead'",
    "F3": "Add a trigger: 'When editing X...' or 'Before committing...'",
    "F4": "Move to a scoped rule file with paths: frontmatter, or broaden the language",
    "F7": "Add a file path, code example, or before/after comparison",
}

# Grade thresholds — duplicated from report.py for minimal coupling.
_LETTER_GRADES = [(0.80, "A"), (0.65, "B"), (0.50, "C"), (0.35, "D")]

_FRIENDLY_STRENGTHS = {
    "F1": "Strong action verb",
    "F2": "Clear positive framing",
    "F3": "Specific trigger context",
    "F4": "Well-scoped to the right files",
    "F7": "Concrete examples or file paths",
}

_FRIENDLY_PROBLEMS = {
    "F1": "Weak verb",
    "F2": "Phrased as a prohibition",
    "F3": "Unclear trigger",
    "F4": "Loaded in the wrong context",
    "F7": "Too vague",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _subprocess_env() -> dict:
    """Return env dict with PYTHONIOENCODING=utf-8 for subprocess calls."""
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    return env


def _run_subprocess(cmd: list[str], stdin_data: str | None = None,
                    timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a subprocess with error checking. Exits on failure."""
    result = subprocess.run(
        cmd,
        input=stdin_data,
        capture_output=True,
        text=True,
        encoding='utf-8',
        env=_subprocess_env(),
        timeout=timeout,
    )
    if result.returncode != 0:
        script_name = Path(cmd[1]).name if len(cmd) > 1 else cmd[0]
        print(f"{script_name} failed (exit {result.returncode}): {result.stderr}",
              file=sys.stderr)
        sys.exit(1)
    return result


def _run_pipeline(project_root: str) -> str:
    """Run the 4-stage scoring pipeline via Popen chain.

    discover.py → extract.py → score_mechanical.py → score_semi.py

    Returns the raw stdout JSON string from score_semi.py.
    """
    env = _subprocess_env()
    common = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                  text=True, encoding='utf-8', env=env)

    p1 = subprocess.Popen(
        [PYTHON, str(SCRIPTS_DIR / "discover.py"), "--project-root", project_root],
        stdin=subprocess.DEVNULL, **common)
    p2 = subprocess.Popen(
        [PYTHON, str(SCRIPTS_DIR / "extract.py")],
        stdin=p1.stdout, **common)
    p1.stdout.close()
    p3 = subprocess.Popen(
        [PYTHON, str(SCRIPTS_DIR / "score_mechanical.py")],
        stdin=p2.stdout, **common)
    p2.stdout.close()
    p4 = subprocess.Popen(
        [PYTHON, str(SCRIPTS_DIR / "score_semi.py")],
        stdin=p3.stdout, **common)
    p3.stdout.close()

    stdout, stderr4 = p4.communicate(timeout=120)

    # Wait for all upstream processes
    p3.wait()
    p2.wait()
    p1.wait()

    # Check errors in pipeline order
    for name, proc, stderr_val in [
        ("discover.py", p1, None),
        ("extract.py", p2, None),
        ("score_mechanical.py", p3, None),
        ("score_semi.py", p4, stderr4),
    ]:
        if proc.returncode != 0:
            err = stderr_val if stderr_val is not None else proc.stderr.read()
            print(f"{name} failed (exit {proc.returncode}): {err}",
                  file=sys.stderr)
            sys.exit(1)

    return stdout


def _read_tmp_json(filename: str) -> dict | list:
    """Read a JSON file from the temp directory."""
    path = Path(TMP_DIR) / filename
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _write_tmp_json(filename: str, data: dict | list) -> None:
    """Write a JSON file to the temp directory."""
    path = Path(TMP_DIR) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _flatten_judgments(input_path: str, flat_output_path: str) -> str:
    """Flatten batched judgment format to a flat array for parse_judgment.py.

    If input is already a flat array, returns input_path (no copy).
    If input is batched ({"batches": [...]}), flattens batches[*].judgments
    into a single array and writes to flat_output_path.

    Returns the path to use for parse_judgment.py --input.
    """
    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        # Already a flat array — use as-is
        return input_path

    if isinstance(data, dict) and "batches" in data:
        flat = []
        for batch in data["batches"]:
            flat.extend(batch.get("judgments", []))
        with open(flat_output_path, 'w', encoding='utf-8') as f:
            json.dump(flat, f, indent=2, ensure_ascii=False)
        return flat_output_path

    # Unknown format — pass through and let parse_judgment.py handle errors
    return input_path


def _run_scoring_pipe(input_json: str) -> str:
    """Run score_mechanical.py → score_semi.py with JSON string input.

    Pure data pipe — does not construct headers or modify input.
    The caller is responsible for building the complete pipeline-compatible
    JSON (schema_version, pipeline_version, source_files, rules, etc.).

    Returns the raw JSON stdout string from score_semi.py.
    """
    result1 = _run_subprocess(
        [PYTHON, str(SCRIPTS_DIR / "score_mechanical.py")],
        stdin_data=input_json,
    )
    result2 = _run_subprocess(
        [PYTHON, str(SCRIPTS_DIR / "score_semi.py")],
        stdin_data=result1.stdout,
    )
    return result2.stdout


def _letter_grade(score: float) -> str:
    """Map a 0.0-1.0 quality score to a letter grade."""
    for threshold, grade in _LETTER_GRADES:
        if score >= threshold:
            return grade
    return "F"


def _friendly_summary(rule: dict) -> str:
    """Build a friendly 1-line summary from the rule's factors."""
    dw = rule.get("dominant_weakness")
    if dw:
        return _FRIENDLY_PROBLEMS.get(dw, "Review and improve")

    # No dominant weakness — highlight top strengths.
    factors = rule.get("factors", {})
    scored = []
    for fn in ("F1", "F2", "F3", "F4", "F7"):
        fdata = factors.get(fn, {})
        val = fdata.get("value")
        if val is not None:
            scored.append((val, fn))
    scored.sort(reverse=True)
    top = [_FRIENDLY_STRENGTHS[fn] for _, fn in scored[:3]
           if fn in _FRIENDLY_STRENGTHS]
    return ", ".join(top) if top else "Well-structured rule"


# ---------------------------------------------------------------------------
# Mode implementations
# ---------------------------------------------------------------------------

def cmd_prepare(project_root: str) -> None:
    """--prepare: discover → extract → score → build_prompt."""
    tmp = Path(TMP_DIR)
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    (tmp / ".gitignore").write_text("*\n", encoding="utf-8")

    # Run the 4-stage pipeline
    stdout = _run_pipeline(project_root)
    scored = json.loads(stdout)
    _write_tmp_json("scored_semi.json", scored)

    rule_count = len(scored.get("rules", []))
    batch_mode = rule_count > BATCH_THRESHOLD

    scored_path = str(tmp / "scored_semi.json")

    if batch_mode:
        batch_dir = str(tmp / "batches")
        _run_subprocess([
            PYTHON, str(SCRIPTS_DIR / "build_prompt.py"),
            "--batch-dir", batch_dir,
            "--input", scored_path,
        ])
        manifest = _read_tmp_json("batches/batch_manifest.json")
        metadata = {
            "rule_count": rule_count,
            "batch_count": manifest["batch_count"],
            "batch_mode": True,
            "prompt_files": [
                str(tmp / "batches" / b["file"])
                for b in manifest["batches"]
            ],
            "single_prompt": None,
            "manifest": str(tmp / "batches" / "batch_manifest.json"),
        }
    else:
        prompt_path = str(tmp / "prompt.md")
        _run_subprocess([
            PYTHON, str(SCRIPTS_DIR / "build_prompt.py"),
            "--input", scored_path,
            "--output", prompt_path,
        ])
        metadata = {
            "rule_count": rule_count,
            "batch_count": 0,
            "batch_mode": False,
            "prompt_files": [],
            "single_prompt": prompt_path,
            "manifest": None,
        }

    _lib.write_json_stdout(metadata)


def cmd_finalize(verbose: bool = False, use_json: bool = False) -> None:
    """--finalize: parse judgments → compose → report."""
    tmp = Path(TMP_DIR)
    scored_path = str(tmp / "scored_semi.json")
    judgments_path = str(tmp / "all_judgments.json")
    flat_path = str(tmp / "_flat_judgments.json")
    patches_path = str(tmp / "judgment_patches.json")
    audit_path = str(tmp / "audit.json")

    # Flatten batched judgments if needed
    effective_input = _flatten_judgments(judgments_path, flat_path)

    # parse_judgment.py
    _run_subprocess([
        PYTHON, str(SCRIPTS_DIR / "parse_judgment.py"),
        scored_path,
        "--input", effective_input,
        "--output", patches_path,
    ])

    # compose.py
    _run_subprocess([
        PYTHON, str(SCRIPTS_DIR / "compose.py"),
        scored_path, patches_path,
        "--output", audit_path,
    ])

    # report.py
    report_cmd = [PYTHON, str(SCRIPTS_DIR / "report.py"), "--input", audit_path]
    if verbose:
        report_cmd.append("--verbose")
    if use_json:
        report_cmd.append("--json")

    result = subprocess.run(
        report_cmd,
        capture_output=True, text=True, encoding='utf-8',
        env=_subprocess_env(), timeout=60,
    )
    if result.returncode != 0:
        print(f"report.py failed (exit {result.returncode}): {result.stderr}",
              file=sys.stderr)
        sys.exit(1)

    sys.stdout.write(result.stdout)


def cmd_prepare_fix() -> None:
    """--prepare-fix: select qualifying rules from audit.json."""
    audit = _read_tmp_json("audit.json")
    rules = audit.get("rules", [])
    files = audit.get("files", [])

    qualifying = []
    for r in rules:
        if r.get("category") != "mandate":
            continue
        if r.get("score", 1.0) >= 0.50:
            continue

        # Resolve file path: compose.py adds rule["file"] directly (compose.py:491)
        file_path = r.get("file", "")
        if not file_path:
            fi = r.get("file_index", 0)
            if fi < len(files):
                file_path = files[fi].get("path", "")

        dw = r.get("dominant_weakness")
        qualifying.append({
            "rule_id": r["id"],
            "file": file_path,
            "line_start": r.get("line_start", 0),
            "text": r.get("text", ""),
            "score": r.get("score", 0),
            "dominant_weakness": dw,
            "action": _FRIENDLY_FIXES.get(dw, "Review and improve"),
        })

    output = {
        "qualifying_count": len(qualifying),
        "rules": qualifying,
    }
    _lib.write_json_stdout(output)


def cmd_score_rewrites() -> None:
    """--score-rewrites: mechanical scoring + build_prompt for rewrites."""
    tmp = Path(TMP_DIR)
    audit_path = str(tmp / "audit.json")
    rewrites_path = str(tmp / "rewrites_input.json")
    rewrite_semi_path = str(tmp / "rewrite_semi.json")

    # Phase 1: mechanical scoring
    _run_subprocess([
        PYTHON, str(SCRIPTS_DIR / "rewrite_scorer.py"),
        "--score-rewrites", audit_path, rewrites_path,
        "--output", rewrite_semi_path,
    ])

    # Count rules and decide batch mode
    rewrite_semi = _read_tmp_json("rewrite_semi.json")
    rule_count = len(rewrite_semi.get("rules", []))
    batch_mode = rule_count > BATCH_THRESHOLD

    if batch_mode:
        batch_dir = str(tmp / "rewrite_batches")
        _run_subprocess([
            PYTHON, str(SCRIPTS_DIR / "build_prompt.py"),
            "--batch-dir", batch_dir,
            "--input", rewrite_semi_path,
        ])
        manifest = _read_tmp_json("rewrite_batches/batch_manifest.json")
        metadata = {
            "rule_count": rule_count,
            "batch_count": manifest["batch_count"],
            "batch_mode": True,
            "prompt_files": [
                str(tmp / "rewrite_batches" / b["file"])
                for b in manifest["batches"]
            ],
            "single_prompt": None,
            "manifest": str(tmp / "rewrite_batches" / "batch_manifest.json"),
        }
    else:
        prompt_path = str(tmp / "rewrite_prompt.md")
        _run_subprocess([
            PYTHON, str(SCRIPTS_DIR / "build_prompt.py"),
            "--input", rewrite_semi_path,
            "--output", prompt_path,
        ])
        metadata = {
            "rule_count": rule_count,
            "batch_count": 0,
            "batch_mode": False,
            "prompt_files": [],
            "single_prompt": prompt_path,
            "manifest": None,
        }

    _lib.write_json_stdout(metadata)


def cmd_finalize_fix(verbose: bool = False, use_json: bool = False) -> None:
    """--finalize-fix: parse rewrite judgments → finalize → inject → report."""
    tmp = Path(TMP_DIR)
    rewrite_semi_path = str(tmp / "rewrite_semi.json")
    judgments_path = str(tmp / "rewrite_judgments.json")
    flat_path = str(tmp / "_flat_rewrite_judgments.json")
    patches_path = str(tmp / "rewrite_patches.json")
    audit_path = str(tmp / "audit.json")
    rewrites_path = str(tmp / "rewrites.json")

    # Flatten batched judgments if needed
    effective_input = _flatten_judgments(judgments_path, flat_path)

    # parse_judgment.py
    _run_subprocess([
        PYTHON, str(SCRIPTS_DIR / "parse_judgment.py"),
        rewrite_semi_path,
        "--input", effective_input,
        "--output", patches_path,
    ])

    # rewrite_scorer.py --finalize
    _run_subprocess([
        PYTHON, str(SCRIPTS_DIR / "rewrite_scorer.py"),
        "--finalize", rewrite_semi_path, patches_path, audit_path,
        "--output", rewrites_path,
    ])

    # Inject rewrites into audit.json
    audit = _read_tmp_json("audit.json")
    rewrites = _read_tmp_json("rewrites.json")
    audit["rewrites"] = rewrites
    _write_tmp_json("audit.json", audit)

    # report.py
    report_cmd = [PYTHON, str(SCRIPTS_DIR / "report.py"), "--input", audit_path]
    if verbose:
        report_cmd.append("--verbose")
    if use_json:
        report_cmd.append("--json")

    result = subprocess.run(
        report_cmd,
        capture_output=True, text=True, encoding='utf-8',
        env=_subprocess_env(), timeout=60,
    )
    if result.returncode != 0:
        print(f"report.py failed (exit {result.returncode}): {result.stderr}",
              file=sys.stderr)
        sys.exit(1)

    sys.stdout.write(result.stdout)


def cmd_score_draft(draft_path: str) -> None:
    """--score-draft: mechanically score draft rules for the build skill.

    Takes a simple JSON input {rules: [{id, text}], file, category} and
    builds the full pipeline-compatible schema internally, then runs
    score_mechanical → score_semi and builds the judgment prompt.

    Fragmentation pre-flight: before running the scoring pipeline, each
    draft rule text is checked against extract.py's splitter rules. A
    rule that would fragment on the next audit pass would score F as
    orphan clauses — so instead of scoring, we short-circuit with
    `status: "needs_revision"` so the build skill can silently revise
    and re-score. Users never see a spurious F caused by extraction.
    """
    with open(draft_path, encoding="utf-8") as f:
        draft = json.load(f)

    rules = draft["rules"]
    target_file = draft.get("file", ".claude/rules/draft.md")
    category = draft.get("category", "mandate")

    # Fragmentation pre-flight — must run before the scoring pipeline so
    # fragmenting rules never produce scored output. See rewrite_scorer.py
    # (Axo-folio regression, 2026-04-17) for the parallel check on the
    # rewrite path.
    import extract as _extract
    fragmenting = []
    for r in rules:
        fragments = _extract.would_fragment(r["text"])
        if len(fragments) > 1:
            fragmenting.append({
                "id": r["id"],
                "text": r["text"],
                "fragment_count": len(fragments),
                "fragments_preview": [f[:120] for f in fragments],
                "reason": (
                    "Rule contains a splitter pattern (`, and` / ` and ` "
                    "between independent imperatives, `;` outside a code "
                    "span, or ` — ` followed by a clause with its own "
                    "verb). On the next audit pass extract.py would "
                    "fragment it into multiple rules that each score F. "
                    "Revise to use `or`, drop semicolons, or collapse to "
                    "a single directive."
                ),
            })

    if fragmenting:
        # Ensure tmp dir exists for consistency with the success path even
        # though we write no scored_semi / prompt yet.
        tmp = Path(TMP_DIR)
        tmp.mkdir(parents=True, exist_ok=True)
        if not (tmp / ".gitignore").exists():
            (tmp / ".gitignore").write_text("*\n", encoding="utf-8")
        _lib.write_json_stdout({
            "status": "needs_revision",
            "fragmenting_rules": fragmenting,
        })
        return

    # Build pipeline-compatible input — _run_scoring_pipe is a dumb pipe,
    # so we construct the complete schema here.
    source_files = [{
        "path": target_file,
        "globs": [],
        "glob_match_count": None,
        "default_category": category,
        "line_count": len(rules) + 5,
        "always_loaded": True,
    }]

    pipeline_rules = []
    for i, r in enumerate(rules):
        pipeline_rules.append({
            "id": r["id"],
            "file_index": 0,
            "text": r["text"],
            "line_start": 5 + i,
            "line_end": 5 + i,
            "category": category,
            "referenced_entities": [],
            "staleness": {"gated": False, "missing_entities": []},
            "factors": {},
        })

    pipeline_input = {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_context": {"stack": []},
        "config": {},
        "source_files": source_files,
        "rules": pipeline_rules,
    }

    # Ensure tmp dir exists (non-destructive — don't wipe if already present).
    tmp = Path(TMP_DIR)
    tmp.mkdir(parents=True, exist_ok=True)
    if not (tmp / ".gitignore").exists():
        (tmp / ".gitignore").write_text("*\n", encoding="utf-8")

    # Run mechanical scoring pipeline.
    input_json = json.dumps(pipeline_input, ensure_ascii=False)
    scored_raw = _run_scoring_pipe(input_json)
    scored = json.loads(scored_raw)
    _write_tmp_json("draft_scored_semi.json", scored)

    # Build judgment prompt.
    scored_path = str(tmp / "draft_scored_semi.json")
    prompt_path = str(tmp / "draft_prompt.md")
    _run_subprocess([
        PYTHON, str(SCRIPTS_DIR / "build_prompt.py"),
        "--input", scored_path,
        "--output", prompt_path,
    ])

    # Output per-rule mechanical scores + prompt path.
    output_rules = []
    for rule in scored.get("rules", []):
        output_rules.append({
            "id": rule["id"],
            "text": rule["text"],
            "factors": rule.get("factors", {}),
            "needs_judgment": True,
        })

    _lib.write_json_stdout({
        "status": "ok",
        "rules": output_rules,
        "judgment_prompt": str(tmp / "draft_prompt.md"),
    })


def cmd_finalize_draft() -> None:
    """--finalize-draft: compose draft scores after F3/F8 judgment.

    Reads draft_scored_semi.json + draft_judgments.json from the tmp dir,
    runs parse_judgment → compose, then outputs structured results
    with letter grades, pass/fail, and friendly summaries.

    Uses draft_* prefixed files to avoid collision with the audit
    pipeline's scored_semi.json / all_judgments.json / audit.json.
    """
    tmp = Path(TMP_DIR)
    scored_path = str(tmp / "draft_scored_semi.json")
    judgments_path = str(tmp / "draft_judgments.json")
    flat_path = str(tmp / "_draft_flat_judgments.json")
    patches_path = str(tmp / "draft_patches.json")
    audit_path = str(tmp / "draft_audit.json")

    # Flatten batched judgments if needed.
    effective_input = _flatten_judgments(judgments_path, flat_path)

    # parse_judgment.py
    _run_subprocess([
        PYTHON, str(SCRIPTS_DIR / "parse_judgment.py"),
        scored_path,
        "--input", effective_input,
        "--output", patches_path,
    ])

    # compose.py
    _run_subprocess([
        PYTHON, str(SCRIPTS_DIR / "compose.py"),
        scored_path, patches_path,
        "--output", audit_path,
    ])

    # Read draft_audit.json and build final output with grades.
    audit = _read_tmp_json("draft_audit.json")
    weights = _lib.load_data("weights")
    category_floors = weights["category_floors"]

    output_rules = []
    for rule in audit.get("rules", []):
        score = rule.get("score", 0)
        cat = rule.get("category", "mandate")
        floor = category_floors.get(cat, 0.50)
        grade = _letter_grade(score)
        passed = score >= floor

        output_rules.append({
            "id": rule["id"],
            "text": rule.get("text", ""),
            "score": round(score, 2),
            "grade": grade,
            "dominant_weakness": rule.get("dominant_weakness"),
            "pass": passed,
            "friendly_summary": _friendly_summary(rule),
        })

    all_pass = all(r["pass"] for r in output_rules)

    _lib.write_json_stdout({
        "rules": output_rules,
        "all_pass": all_pass,
        "floor": category_floors.get("mandate", 0.50),
    })


def cmd_build_overview() -> None:
    """--build-overview: build scaffold for overview_data.json from audit.json."""
    audit = _read_tmp_json("audit.json")
    rules = audit.get("rules", [])
    files = audit.get("files", [])

    # Organization metrics — computed from rule-level fields.
    # audit.json rules have "file" (path) and "loading" ("always-loaded"|"glob-scoped")
    # set by compose.py:490-496.
    claude_md_rules = sum(1 for r in rules if r.get("file", "").endswith("CLAUDE.md"))
    rules_dir = [r for r in rules if not r.get("file", "").endswith("CLAUDE.md")]
    scoped = sum(1 for r in rules_dir if r.get("loading") == "glob-scoped")
    always_in_dir = sum(1 for r in rules_dir if r.get("loading") == "always-loaded")
    claude_md_lines = next(
        (f.get("line_count", 0) for f in files if f.get("path", "").endswith("CLAUDE.md")),
        0,
    )

    scaffold = {
        "audit": audit,
        "organization": {
            "claude_md_rules": claude_md_rules,
            "scoped_rules": scoped,
            "always_loaded_rules_in_rules_dir": always_in_dir,
            "claude_md_lines": claude_md_lines,
        },
        "intentions": [],
        "coverage_gaps": [],
        "generated_at": "",
    }

    _lib.write_json_stdout(scaffold)


def cmd_build_analysis() -> None:
    """--build-analysis: structured analysis data from audit.json for Phase 3."""
    audit = _read_tmp_json("audit.json")
    rules = audit.get("rules", [])
    files = audit.get("files", [])

    mandate = [r for r in rules if r.get("category") == "mandate"]

    # Grade distribution (standard _letter_grade, no E tier)
    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for r in mandate:
        g = _letter_grade(r.get("score", 0))
        grade_counts[g] += 1

    good_count = grade_counts["A"] + grade_counts["B"]
    below_floor = sum(1 for r in mandate if r.get("score", 0) < 0.50)

    # File info
    file_info = []
    for f in files:
        file_info.append({
            "path": f.get("path", "?"),
            "rule_count": f.get("rule_count", 0),
            "file_score": f.get("file_score", 0),
            "grade": _letter_grade(f.get("file_score", 0)),
            "line_count": f.get("line_count", 0),
            "dead_zone_count": f.get("dead_zone_count", 0),
        })

    # Organization metrics (same pattern as cmd_build_overview)
    claude_md_rules = sum(1 for r in rules if r.get("file", "").endswith("CLAUDE.md"))
    rules_dir = [r for r in rules if not r.get("file", "").endswith("CLAUDE.md")]
    scoped = sum(1 for r in rules_dir if r.get("loading") == "glob-scoped")
    always_in_dir = len(rules_dir) - scoped
    claude_md_lines = next(
        (f.get("line_count", 0) for f in files if f.get("path", "").endswith("CLAUDE.md")),
        0,
    )

    # Best/worst (top/bottom 5 mandate rules)
    sorted_mandate = sorted(mandate, key=lambda r: r.get("score", 0), reverse=True)
    best = [{"id": r["id"], "text": r.get("text", "")[:120], "score": r.get("score", 0),
             "grade": _letter_grade(r.get("score", 0)),
             "strength": _friendly_summary(r)}
            for r in sorted_mandate[:5]]
    worst = [{"id": r["id"], "text": r.get("text", "")[:120], "score": r.get("score", 0),
              "grade": _letter_grade(r.get("score", 0)),
              "problem": _FRIENDLY_PROBLEMS.get(r.get("dominant_weakness", ""), "Review")}
             for r in sorted_mandate[-5:]] if sorted_mandate else []

    # Compact rule data for intention map
    rules_for_map = [
        {"id": r["id"], "text": r.get("text", "")[:200],
         "file": r.get("file", ""), "score": r.get("score", 0),
         "grade": _letter_grade(r.get("score", 0)),
         "dominant_weakness": r.get("dominant_weakness"),
         "loading": r.get("loading", "always-loaded")}
        for r in rules
    ]

    ecq = audit.get("effective_corpus_quality", {})
    result = {
        "grade": _letter_grade(ecq.get("score", 0)),
        "score": ecq.get("score", 0),
        "rule_count": len(mandate),
        "good_count": good_count,
        "grade_counts": grade_counts,
        "below_floor_count": below_floor,
        "files": file_info,
        "organization": {
            "claude_md_rules": claude_md_rules,
            "scoped_rules": scoped,
            "always_loaded_rules_in_rules_dir": always_in_dir,
            "claude_md_lines": claude_md_lines,
        },
        "best_rules": best,
        "worst_rules": worst,
        "rules_for_intention_map": rules_for_map,
    }
    _lib.write_json_stdout(result)


def cmd_prepare_placement() -> None:
    """--prepare-placement: run placement detectors on audit.json, emit candidates.

    Reads .rulesense-tmp/audit.json (produced by --finalize), runs the three
    placement detectors (hook / skill / subagent) via the placement module,
    and emits a candidates report JSON on stdout.

    Called during Phase 3d of the audit SKILL (see design/placement-analyzer-v1.md
    §8). The outer Claude uses the output to build per-category AskUserQuestion
    prompts and to generate judgment strings for each candidate.
    """
    import placement
    audit = _read_tmp_json("audit.json")
    report = placement.analyze_corpus(audit)
    _lib.write_json_stdout(report)


def cmd_write_promotions(project_root: str) -> None:
    """--write-promotions: assemble PROMOTIONS.md + atomically remove moved rules.

    Reads a moves payload from stdin (see design §4.2), writes
    .rulesense/PROMOTIONS.md and removes the moved rules from their source
    files as a single atomic transaction. Writes the result JSON to stdout.

    On failure (source-file drift, write error), emits a failed-status JSON
    and exits non-zero. No files are modified on failure.
    """
    import placement
    payload = _lib.read_json_stdin()
    result = placement.write_promotions(payload, Path(project_root).resolve())
    _lib.write_json_stdout(result)
    if result["status"] != "ok":
        sys.exit(1)


def cmd_cleanup() -> None:
    """--cleanup: remove .rulesense-tmp/."""
    tmp = Path(TMP_DIR)
    if tmp.exists():
        shutil.rmtree(tmp)


# ---------------------------------------------------------------------------
# Argument parsing and dispatch
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: run_audit.py <mode> [options]", file=sys.stderr)
        print("Modes: --prepare, --finalize, --prepare-fix, --score-rewrites, "
              "--finalize-fix, --score-draft, --finalize-draft, --build-overview, "
              "--build-analysis, --prepare-placement, --write-promotions, "
              "--cleanup",
              file=sys.stderr)
        sys.exit(1)

    mode = args[0]
    rest = args[1:]

    if mode == "--prepare":
        project_root = "."
        i = 0
        while i < len(rest):
            if rest[i] == "--project-root" and i + 1 < len(rest):
                project_root = rest[i + 1]
                i += 2
            else:
                i += 1
        cmd_prepare(project_root)

    elif mode == "--finalize":
        verbose = "--verbose" in rest
        use_json = "--json" in rest
        cmd_finalize(verbose=verbose, use_json=use_json)

    elif mode == "--prepare-fix":
        cmd_prepare_fix()

    elif mode == "--score-rewrites":
        cmd_score_rewrites()

    elif mode == "--finalize-fix":
        verbose = "--verbose" in rest
        use_json = "--json" in rest
        cmd_finalize_fix(verbose=verbose, use_json=use_json)

    elif mode == "--score-draft":
        if not rest:
            print("Usage: run_audit.py --score-draft <draft.json>",
                  file=sys.stderr)
            sys.exit(1)
        cmd_score_draft(rest[0])

    elif mode == "--finalize-draft":
        cmd_finalize_draft()

    elif mode == "--build-overview":
        cmd_build_overview()

    elif mode == "--build-analysis":
        cmd_build_analysis()

    elif mode == "--prepare-placement":
        cmd_prepare_placement()

    elif mode == "--write-promotions":
        project_root = "."
        i = 0
        while i < len(rest):
            if rest[i] == "--project-root" and i + 1 < len(rest):
                project_root = rest[i + 1]
                i += 2
            else:
                i += 1
        cmd_write_promotions(project_root)

    elif mode == "--cleanup":
        cmd_cleanup()

    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
