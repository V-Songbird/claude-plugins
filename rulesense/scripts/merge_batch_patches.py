"""Merge per-batch judgment patches into a single judgment_patches.json.

Reads all patches_*.json files from a directory, merges by rule ID,
validates that the union covers all expected rule IDs, and writes the
merged result to stdout.

Usage:
    python merge_batch_patches.py <batch_dir> <scored_semi.json>
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# F-24/F-28: Force UTF-8 on all stdio on Windows.
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


def merge_patches(batch_dir: str, scored_semi_path: str) -> dict:
    """Merge all patches_*.json files from batch_dir.

    Returns the merged judgment_patches.json structure.
    Later batches overwrite earlier ones for duplicate rule IDs (shouldn't
    happen but handles it gracefully).
    """
    batch_path = Path(batch_dir)
    patch_files = sorted(batch_path.glob("patches_*.json"))

    if not patch_files:
        print("FATAL: No patches_*.json files found in batch directory", file=sys.stderr)
        sys.exit(1)

    merged_patches = {}
    schema_version = None
    model_version = "unknown"

    for pf in patch_files:
        with open(pf, encoding="utf-8") as f:
            raw = f.read()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Defense-in-depth: extract JSON from mixed content (e.g., warning
            # text that Claude wrote alongside the JSON judgment output)
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(raw[start:end + 1])
            else:
                print(f"FATAL: Cannot parse JSON from {pf.name}", file=sys.stderr)
                sys.exit(1)

        # Track schema version consistency
        sv = data.get("schema_version")
        if schema_version is None:
            schema_version = sv
        elif sv != schema_version:
            print(f"WARNING: schema_version mismatch in {pf.name}: "
                  f"'{sv}' vs '{schema_version}'", file=sys.stderr)

        mv = data.get("model_version", "unknown")
        if mv != "unknown":
            model_version = mv

        patches = data.get("patches", {})
        for rule_id, patch_data in patches.items():
            if rule_id in merged_patches:
                print(f"WARNING: Duplicate rule {rule_id} across batches, "
                      f"last one wins (from {pf.name})", file=sys.stderr)
            merged_patches[rule_id] = patch_data

    # Validate coverage against scored_semi.json
    with open(scored_semi_path, encoding="utf-8") as f:
        scored_data = json.load(f)

    expected_ids = {r["id"] for r in scored_data.get("rules", []) if "id" in r}
    merged_ids = set(merged_patches.keys())

    missing = expected_ids - merged_ids
    if missing:
        print(f"WARNING: {len(missing)} rule IDs missing after merge: "
              f"{', '.join(sorted(missing)[:10])}", file=sys.stderr)

    extra = merged_ids - expected_ids
    if extra:
        print(f"WARNING: {len(extra)} unexpected rule IDs in patches: "
              f"{', '.join(sorted(extra)[:10])}", file=sys.stderr)

    return {
        "schema_version": schema_version or "0.1",
        "model_version": model_version,
        "patches": merged_patches,
    }


def main():
    # Extract optional --output flag
    output_path = None
    positional = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        else:
            positional.append(args[i])
            i += 1

    if len(positional) < 2:
        print("Usage: merge_batch_patches.py <batch_dir> <scored_semi.json> [--output file]",
              file=sys.stderr)
        sys.exit(1)

    batch_dir = positional[0]
    scored_semi_path = positional[1]

    result = merge_patches(batch_dir, scored_semi_path)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
