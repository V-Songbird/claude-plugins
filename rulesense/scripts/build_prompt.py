"""Assemble the judgment prompt from scored rules + rubric files.

Pure JSON-in → markdown-out. Reads scored_semi.json from stdin, outputs
the assembled prompt to stdout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _lib


def build_prompt(data: dict) -> str:
    """Build the judgment prompt from scored pipeline data."""
    rules = data.get("rules", [])
    project_context = data.get("project_context", {})

    # Load rubric files
    rubric_f3 = _lib.load_data_text("rubric_F3.md")
    rubric_f8 = _lib.load_data_text("rubric_F8.md")

    sections = []

    # Header
    sections.append("# Quality Factor Scoring\n")
    sections.append("Score F3 and F8 for every rule. Where a rule is flagged, also provide the")
    sections.append("requested patch (F1_patch or F7_patch).\n")

    # Project Context
    sections.append("## Project Context")
    stack = project_context.get("stack", [])
    sections.append(f"Stack: {', '.join(stack) if stack else 'unknown'}")

    always_loaded = project_context.get("always_loaded_files", [])
    sections.append(f"Always-loaded files: {', '.join(always_loaded) if always_loaded else 'none'}")

    glob_scoped = project_context.get("glob_scoped_files", [])
    if glob_scoped:
        globs_summary = ", ".join(
            f"{gf.get('globs', ['?'])[0] if gf.get('globs') else '?'}"
            for gf in glob_scoped[:5]
        )
        sections.append(f"Glob-scoped files: {len(glob_scoped)} files covering {globs_summary}")
    else:
        sections.append("Glob-scoped files: none")

    sections.append("")
    sections.append("Note: glob-scoped rules have their trigger anchored to the glob pattern.")
    sections.append('"I\'m editing a file matching this glob" IS the trigger context for F3.\n')

    # Tooling context (informs F8 scoring)
    tooling = project_context.get("tooling", {})
    configured = [name for name, detected in tooling.items() if detected]
    if configured:
        not_detected = [name for name, detected in tooling.items() if not detected]
        sections.append(f"Configured enforcement: {', '.join(configured)}")
        if not_detected:
            sections.append(f"Not detected: {', '.join(not_detected)}")
    else:
        sections.append("No enforcement tooling detected.")
    sections.append("")

    # F3 rubric
    sections.append("## F3: Trigger-Action Distance")
    sections.append(rubric_f3.strip())
    sections.append("")

    # F8 rubric
    sections.append("## F8: Enforceability Ceiling")
    sections.append(rubric_f8.strip())
    sections.append("Score enforceability against this project's detected stack and tooling, not in the abstract.\n")

    # Rules table
    sections.append("## Rules\n")
    sections.append("| ID | File | Globs | Text | Flags |")
    sections.append("|---|---|---|---|---|")

    source_files = data.get("source_files", [])

    for rule in rules:
        rule_id = rule["id"]
        fi = rule.get("file_index", 0)
        sf = source_files[fi] if fi < len(source_files) else {}

        file_path = sf.get("path", "unknown")
        globs = sf.get("globs", [])
        globs_str = ", ".join(globs) if globs else "always-loaded"

        text = rule["text"][:120]
        if len(rule["text"]) > 120:
            text += "..."

        # Build flags column
        flags = _build_flags(rule)

        sections.append(f"| {rule_id} | {file_path} | {globs_str} | \"{text}\" | {flags} |")

    sections.append("")

    # Response format
    sections.append("## Response format\n")
    sections.append("Respond with ONLY a JSON array. No prose, no markdown fences.")
    sections.append("One object per rule. Always include F3 and F8. Include patches only when")
    sections.append("flagged. Reasoning: one sentence, max 80 characters.\n")
    sections.append('[{"id":"R001","F3":{"value":0.80,"level":3,"reasoning":"..."},')
    sections.append('  "F8":{"value":0.65,"level":2,"reasoning":"..."}}]')

    return "\n".join(sections)


def _build_flags(rule: dict) -> str:
    """Build the flags column for a rule in the prompt table."""
    flags = []
    factors = rule.get("factors", {})
    confidence_low = rule.get("factor_confidence_low", [])

    # F1 extraction failure
    f1 = factors.get("F1", {})
    if f1.get("method") == "extraction_failed":
        flags.append("F1: extraction_failed")

    # F7 confidence low (concreteness — absorbs what was previously F6 example density)
    if "F7" in confidence_low:
        f7 = factors.get("F7", {})
        c = f7.get("concrete_count", 0)
        a = f7.get("abstract_count", 0)
        flags.append(f"F7: mech={f7.get('value', '?')} (concrete:{c}, abstract:{a})")

    return "; ".join(flags) if flags else "—"


BATCH_SIZE_DEFAULT = 12
BATCH_THRESHOLD = 20


def partition_rules(rules: list[dict], source_files: list[dict],
                    batch_size: int = BATCH_SIZE_DEFAULT) -> list[list[dict]]:
    """Partition rules into batches for multi-prompt scoring.

    Deterministic: sort by (file_path, line_start), group by file with
    file-cohesion preference. Oversize files split at batch_size boundaries.

    This is a pure function: two calls with identical input produce identical output.
    No dict-iteration-order or filesystem-walking dependencies.

    batch_size=12 and the >20 threshold are initial values, tunable based on
    real-world data from the calibration harness.
    """
    if not rules:
        return []

    # Sort by (file_path, line_start) for deterministic ordering
    def sort_key(rule):
        fi = rule.get("file_index", 0)
        sf = source_files[fi] if fi < len(source_files) else {}
        return (sf.get("path", ""), rule.get("line_start", 0))

    sorted_rules = sorted(rules, key=sort_key)

    # Group consecutive rules by file
    file_groups = []
    current_group = []
    current_fi = None
    for rule in sorted_rules:
        fi = rule.get("file_index", 0)
        if fi != current_fi and current_group:
            file_groups.append(current_group)
            current_group = []
        current_fi = fi
        current_group.append(rule)
    if current_group:
        file_groups.append(current_group)

    # Pack groups into batches with file-cohesion preference
    batches = []
    current_batch = []
    for group in file_groups:
        if len(group) <= batch_size:
            # Group fits in one batch
            if len(current_batch) + len(group) <= batch_size:
                current_batch.extend(group)
            else:
                if current_batch:
                    batches.append(current_batch)
                current_batch = list(group)
        else:
            # Oversize file: split at batch_size boundaries
            if current_batch:
                batches.append(current_batch)
                current_batch = []
            for i in range(0, len(group), batch_size):
                chunk = group[i:i + batch_size]
                batches.append(chunk)

    if current_batch:
        batches.append(current_batch)

    return batches


def build_batch_prompt(data: dict, rule_subset: list[dict], batch_num: int,
                       total_batches: int, is_continuation: bool = False) -> str:
    """Build a prompt for a specific batch of rules.

    Same rubric headers and project context as build_prompt(), but the rules
    table contains only this batch's rules. Continuation batches get a note.
    """
    # Shallow copy with the subset — avoids mutating the caller's data
    batch_data = {**data, "rules": rule_subset}
    prompt = build_prompt(batch_data)

    # Add batch header after the main header
    batch_note = f"\n*Batch {batch_num} of {total_batches}.*"
    if is_continuation:
        fi = rule_subset[0].get("file_index", 0) if rule_subset else 0
        source_files = data.get("source_files", [])
        sf = source_files[fi] if fi < len(source_files) else {}
        file_path = sf.get("path", "unknown")
        batch_note += f"\n*Note: These rules continue from {file_path}. See previous batch for earlier rules from this file.*"

    # Insert after first line
    lines = prompt.split("\n", 1)
    if len(lines) == 2:
        prompt = lines[0] + batch_note + "\n" + lines[1]

    return prompt


def main():
    import os

    # Extract optional flags
    batch_dir = None
    input_path = None
    output_path = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--batch-dir" and i + 1 < len(args):
            batch_dir = args[i + 1]
            i += 2
        elif args[i] == "--input" and i + 1 < len(args):
            input_path = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        else:
            i += 1

    if input_path:
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = _lib.read_json_stdin()
    rules = data.get("rules", [])
    source_files = data.get("source_files", [])

    if batch_dir and len(rules) > BATCH_THRESHOLD:
        # Batch mode
        os.makedirs(batch_dir, exist_ok=True)
        batches = partition_rules(rules, source_files)

        # Track which batches are continuations of a file from the previous batch
        prev_last_fi = None
        manifest_batches = []

        for i, batch in enumerate(batches):
            batch_num = i + 1
            first_fi = batch[0].get("file_index", 0) if batch else None
            is_continuation = (first_fi is not None and first_fi == prev_last_fi)

            prompt = build_batch_prompt(data, batch, batch_num, len(batches), is_continuation)

            prompt_path = os.path.join(batch_dir, f"prompt_{batch_num:03d}.md")
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt)

            manifest_batches.append({
                "file": f"prompt_{batch_num:03d}.md",
                "rule_ids": [r["id"] for r in batch],
            })

            prev_last_fi = batch[-1].get("file_index", 0) if batch else None

        # Write manifest
        manifest = {
            "batch_count": len(batches),
            "batch_size_target": BATCH_SIZE_DEFAULT,
            "total_rules": len(rules),
            "batches": manifest_batches,
        }
        manifest_path = os.path.join(batch_dir, "batch_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    else:
        # Single-prompt mode (backward compatible)
        prompt = build_prompt(data)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(prompt)
                f.write("\n")
        else:
            sys.stdout.write(prompt)
            sys.stdout.write("\n")


if __name__ == "__main__":
    main()
