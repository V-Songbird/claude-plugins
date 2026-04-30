"""Rewrite scorer: mechanical scoring and finalization for --fix mode rewrites.

Two-phase invocation:

  Phase 1 — score rewrites mechanically:
    python rewrite_scorer.py --score-rewrites audit.json rewrites_input.json > rewrite_semi.json

    Reads audit.json (for source_file context) and rewrites_input.json (list of
    {rule_id, original_text, suggested_rewrite, file, line_start, old_score,
    old_dominant_weakness, projected_score}). Builds proper scored_semi.json with
    all rewrites as rules, pipes through score_mechanical.py | score_semi.py once,
    outputs the result.

  Phase 2 — compose final scores + apply safety gates:
    python rewrite_scorer.py --finalize rewrite_semi.json judgment_patches.json audit.json > rewrites.json

    Reads scored rewrites + judgment patches + original audit. Runs compose.py,
    applies regression / volatility / self-verification gates, outputs the
    rewrites list ready to inject into audit.json.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _lib

SCRIPTS_DIR = Path(__file__).parent
PYTHON = sys.executable


def _letter_grade(score: float) -> str:
    if score >= 0.80:
        return "A"
    if score >= 0.65:
        return "B"
    if score >= 0.50:
        return "C"
    if score >= 0.35:
        return "D"
    return "F"


def score_rewrites(audit_path: str, rewrites_input_path: str) -> dict:
    """Phase 1: mechanically score all rewrites through the pipeline."""
    with open(audit_path, encoding="utf-8") as f:
        audit = json.load(f)

    with open(rewrites_input_path, encoding="utf-8") as f:
        rewrites_input = json.load(f)

    if not rewrites_input:
        return {"schema_version": "0.1", "pipeline_version": "0.1.0",
                "project_context": {}, "config": {}, "source_files": [], "rules": []}

    # Get source file info from audit for F4 scoring context
    source_files = audit.get("source_files", [{"path": "", "globs": [],
                                                "glob_match_count": 0,
                                                "default_category": "mandate",
                                                "line_count": 1,
                                                "always_loaded": True}])
    if not source_files:
        source_files = [{"path": "", "globs": [], "glob_match_count": 0,
                         "default_category": "mandate", "line_count": 1,
                         "always_loaded": True}]

    # Build rules for the scoring pipeline
    rules = []
    for i, rw in enumerate(rewrites_input):
        rules.append({
            "id": rw.get("rule_id", f"RW{i+1:03d}"),
            "file_index": 0,
            "text": rw["suggested_rewrite"],
            "line_start": rw.get("line_start", 1),
            "line_end": rw.get("line_start", 1),
            "category": "mandate",
            "referenced_entities": [],
            "staleness": {"gated": False, "missing_entities": []},
            "factors": {},
        })

    # Build the input for score_mechanical.py
    pipeline_input = {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_context": audit.get("project_context", {"stack": []}),
        "config": audit.get("config", {}),
        "source_files": [source_files[0]],  # use first source file for F4 context
        "rules": rules,
    }

    # Pipe through score_mechanical.py | score_semi.py
    input_json = json.dumps(pipeline_input, ensure_ascii=False)

    p1 = subprocess.Popen(
        [PYTHON, str(SCRIPTS_DIR / "score_mechanical.py")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8",
    )
    p2 = subprocess.Popen(
        [PYTHON, str(SCRIPTS_DIR / "score_semi.py")],
        stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8",
    )
    p1.stdout.close()
    p1.stdin.write(input_json)
    p1.stdin.close()

    stdout, stderr2 = p2.communicate(timeout=60)
    p1.wait()

    if p1.returncode != 0:
        print(f"score_mechanical.py failed: {p1.stderr.read()}", file=sys.stderr)
        sys.exit(1)
    if p2.returncode != 0:
        print(f"score_semi.py failed: {stderr2}", file=sys.stderr)
        sys.exit(1)

    result = json.loads(stdout)

    # Fragmentation check (Axo-folio regression, 2026-04-17): score_rewrites
    # treats the rewrite text as a pre-extracted single rule, but extract.py
    # runs again on the next audit pass after the rewrites are written to
    # source files. If a rewrite contains a splitter pattern (`, and`, `;`, etc.)
    # it will fragment into orphan rules that all score F. Detect here and
    # emit a structured warning in each rule's output so the caller can revise
    # before applying.
    import extract as _extract  # local to avoid unused import in other modes

    # Attach original rewrite metadata to each rule for Phase 2
    for i, rule in enumerate(result.get("rules", [])):
        if i < len(rewrites_input):
            rw = rewrites_input[i]
            rule["_rewrite_meta"] = {
                "rule_id": rw.get("rule_id"),
                "original_text": rw.get("original_text", ""),
                "file": rw.get("file", ""),
                "line_start": rw.get("line_start", 0),
                "old_score": rw.get("old_score", 0),
                "old_dominant_weakness": rw.get("old_dominant_weakness"),
                "projected_score": rw.get("projected_score"),
            }
            fragments = _extract.would_fragment(rw["suggested_rewrite"])
            if len(fragments) > 1:
                rule["_rewrite_meta"]["would_fragment"] = True
                rule["_rewrite_meta"]["fragment_count"] = len(fragments)
                rule["_rewrite_meta"]["fragments_preview"] = [f[:80] for f in fragments]
                print(
                    f"WARNING: {rw.get('rule_id', f'RW{i+1:03d}')} rewrite would fragment into "
                    f"{len(fragments)} rules when re-extracted. First fragment: "
                    f"{fragments[0][:80]!r}. Revise to use `or` instead of `, and`, "
                    "drop semicolons, or collapse to a single directive.",
                    file=sys.stderr,
                )

    return result


def finalize_rewrites(rewrite_semi_path: str, patches_path: str, audit_path: str) -> list[dict]:
    """Phase 2: compose final scores, apply safety gates, produce rewrites list."""
    with open(rewrite_semi_path, encoding="utf-8") as f:
        rewrite_semi = json.load(f)

    with open(audit_path, encoding="utf-8") as f:
        audit = json.load(f)

    # Write temp files for compose.py
    tmp_dir = tempfile.mkdtemp()
    scored_tmp = os.path.join(tmp_dir, "scored.json")
    with open(scored_tmp, "w", encoding="utf-8") as f:
        json.dump(rewrite_semi, f, ensure_ascii=False)

    # Run compose.py
    result = subprocess.run(
        [PYTHON, str(SCRIPTS_DIR / "compose.py"), scored_tmp, patches_path],
        capture_output=True, text=True, timeout=60, encoding="utf-8",
    )

    # Clean up
    os.unlink(scored_tmp)
    os.rmdir(tmp_dir)

    if result.returncode != 0:
        print(f"compose.py failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    composed = json.loads(result.stdout)
    composed_rules = composed.get("rules", [])

    # Get original rule data from audit for safety gates
    audit_rules = {r["id"]: r for r in audit.get("rules", [])}

    rewrites = []
    for rule in composed_rules:
        meta = rule.get("_rewrite_meta", {})
        rule_id = meta.get("rule_id", rule.get("id", "?"))
        old_score = meta.get("old_score", 0)
        new_score = rule.get("score", 0)
        old_grade = _letter_grade(old_score)
        new_grade = _letter_grade(new_score)
        projected = meta.get("projected_score")

        # Safety gate 1: Regression
        if new_score < old_score:
            continue  # DROP

        # Compute factor improvements
        orig_rule = audit_rules.get(rule_id, {})
        orig_factors = orig_rule.get("factors", {})
        new_factors = rule.get("factors", {})
        improvements = {}
        for fn in ("F1", "F2", "F3", "F4", "F7", "F8"):
            old_val = orig_factors.get(fn, {}).get("value")
            new_val = new_factors.get(fn, {}).get("value")
            if old_val is not None and new_val is not None and new_val > old_val:
                improvements[fn] = [round(old_val, 2), round(new_val, 2)]

        # Safety gate 2: Judgment volatility (F8 is parallel signal, not composite)
        old_f3 = orig_factors.get("F3", {}).get("value")
        new_f3 = new_factors.get("F3", {}).get("value")
        f3_delta = abs((new_f3 or 0) - (old_f3 or 0))
        jv_flagged = f3_delta > 0.20

        # Safety gate 3: Self-verification
        svd = abs(new_score - projected) if projected is not None else 0.0

        rewrites.append({
            "rule_id": rule_id,
            "file": meta.get("file", ""),
            "line_start": meta.get("line_start", 0),
            "original_text": meta.get("original_text", ""),
            "suggested_rewrite": rule.get("text", ""),
            "old_score": round(old_score, 3),
            "new_score": round(new_score, 3),
            "old_grade": old_grade,
            "new_grade": new_grade,
            "old_dominant_weakness": meta.get("old_dominant_weakness"),
            "new_dominant_weakness": rule.get("dominant_weakness"),
            "factor_improvements": improvements or None,
            "judgment_volatility": {
                "flagged": jv_flagged,
                "f3_delta": round(f3_delta, 2),
                "old_f3": old_f3,
                "new_f3": new_f3,
            },
            "projected_score": projected,
            "self_verification_delta": round(svd, 3),
        })

    return rewrites


def main():
    if len(sys.argv) < 2:
        print("Usage:", file=sys.stderr)
        print("  rewrite_scorer.py --score-rewrites <audit.json> <rewrites_input.json> [--output file]", file=sys.stderr)
        print("  rewrite_scorer.py --finalize <rewrite_semi.json> <patches.json> <audit.json> [--output file]", file=sys.stderr)
        sys.exit(1)

    # Extract --output flag from args
    output_path = None
    filtered = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        else:
            filtered.append(args[i])
            i += 1

    if not filtered:
        print("Missing mode argument", file=sys.stderr)
        sys.exit(1)

    mode = filtered[0]
    positional = filtered[1:]

    if mode == "--score-rewrites":
        if len(positional) != 2:
            print("Usage: rewrite_scorer.py --score-rewrites <audit.json> <rewrites_input.json> [--output file]", file=sys.stderr)
            sys.exit(1)
        result = score_rewrites(positional[0], positional[1])
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        else:
            _lib.write_json_stdout(result)

    elif mode == "--finalize":
        if len(positional) != 3:
            print("Usage: rewrite_scorer.py --finalize <rewrite_semi.json> <patches.json> <audit.json> [--output file]", file=sys.stderr)
            sys.exit(1)
        rewrites = finalize_rewrites(positional[0], positional[1], positional[2])
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(rewrites, f, indent=2, ensure_ascii=False)
        else:
            json.dump(rewrites, sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")

    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
