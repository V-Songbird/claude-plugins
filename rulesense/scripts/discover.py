"""Project discovery: filesystem walking, config loading, stack detection, glob resolution.

This is the ONLY script that touches the filesystem. All other scripts are
pure JSON-in → JSON-out transformations.

Usage:
    python discover.py --project-root /path/to/project > project_context.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

# Allow importing _lib from the same directory
sys.path.insert(0, str(Path(__file__).parent))
import _lib


def find_instruction_files(project_root: Path) -> list[dict]:
    """Find all instruction files: CLAUDE.md and .claude/rules/*.md.

    Checks two locations for CLAUDE.md:
    1. <root>/CLAUDE.md (standard)
    2. <root>/.claude/CLAUDE.md (alternate, used by some projects)
    If both exist, the root-level one wins and a warning is emitted.
    """
    files = []

    # Project-level CLAUDE.md — check both locations
    root_claude_md = project_root / "CLAUDE.md"
    alt_claude_md = project_root / ".claude" / "CLAUDE.md"

    if root_claude_md.exists() and alt_claude_md.exists():
        print("WARNING: Found both CLAUDE.md and .claude/CLAUDE.md. "
              "Using CLAUDE.md (root). The .claude/CLAUDE.md file will be ignored.",
              file=sys.stderr)
        files.append({
            "path": "CLAUDE.md",
            "abs_path": str(root_claude_md),
            "always_loaded": True,
        })
    elif root_claude_md.exists():
        files.append({
            "path": "CLAUDE.md",
            "abs_path": str(root_claude_md),
            "always_loaded": True,
        })
    elif alt_claude_md.exists():
        files.append({
            "path": ".claude/CLAUDE.md",
            "abs_path": str(alt_claude_md),
            "always_loaded": True,
        })

    # .claude/rules/*.md
    rules_dir = project_root / ".claude" / "rules"
    if rules_dir.is_dir():
        for md_file in sorted(rules_dir.glob("*.md")):
            rel = md_file.relative_to(project_root).as_posix()
            # Skip .claude/CLAUDE.md if it ended up in the rules dir walk
            if rel == ".claude/CLAUDE.md":
                continue
            # .rulesense/ is reserved for plugin-internal state and output
            # (PROMOTIONS.md, scratch). Never treat its content as rules.
            # Defense-in-depth: discover does not currently walk into
            # .rulesense/, but an explicit guard prevents future regressions
            # if discovery ever broadens to recursive walks.
            if rel.startswith(".rulesense/") or "/.rulesense/" in rel:
                continue
            files.append({
                "path": rel,
                "abs_path": str(md_file),
                "always_loaded": False,
            })

    return files


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML-like frontmatter from markdown content.

    Returns (frontmatter_dict, content_without_frontmatter).
    Handles simple ``key: value`` pairs and YAML block-list format::

        paths:
          - "src/api/**/*.ts"
          - "lib/**/*.ts"

    Block-list values are stored as the key with a list-typed value.
    Simple key-value pairs are stored as strings.
    """
    fm = {}
    lines = content.split("\n")

    if not lines or lines[0].strip() != "---":
        return fm, content

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return fm, content

    line_idx = 1
    while line_idx < end_idx:
        line = lines[line_idx].strip()
        if not line or line.startswith("#"):
            line_idx += 1
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # Check if next lines are block-list items (  - "value")
            if not value and line_idx + 1 < end_idx:
                next_line = lines[line_idx + 1].strip()
                if next_line.startswith("- "):
                    # Parse block-list YAML
                    items = []
                    line_idx += 1
                    while line_idx < end_idx:
                        item_line = lines[line_idx].strip()
                        if item_line.startswith("- "):
                            item = item_line[2:].strip().strip('"').strip("'")
                            if item:
                                items.append(item)
                            line_idx += 1
                        else:
                            break
                    fm[key] = items
                    continue

            fm[key] = value
        line_idx += 1

    remaining = "\n".join(lines[end_idx + 1:])
    return fm, remaining


def resolve_globs(globs: list[str], project_root: Path) -> int:
    """Count files matching glob patterns against the project directory."""
    count = 0
    for pattern in globs:
        matches = glob.glob(str(project_root / pattern), recursive=True)
        count += len(matches)
    return count


def detect_packages(project_root: Path) -> set[str]:
    """Collect known package names declared in the project's manifest files.

    Returns a set of package identifiers (lowercased) from package.json
    (dependencies/devDependencies/peerDependencies) and pyproject.toml
    ([project.dependencies] names). Used by build_entity_index to mark rules
    that reference known packages as valid entities.

    Keeps staleness detection for *missing* packages out of scope — telling a
    non-package token apart from a misspelled package name is a heuristic we
    have not yet nailed down. See plugin-audit.md F-14 for the full discussion.
    """
    packages: set[str] = set()

    pkg_json = project_root / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, encoding="utf-8") as f:
                pkg = json.load(f)
            for key in ("dependencies", "devDependencies", "peerDependencies"):
                for name in pkg.get(key, {}).keys():
                    packages.add(name.lower())
        except (json.JSONDecodeError, OSError):
            pass

    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        try:
            with open(pyproject, encoding="utf-8") as f:
                content = f.read()
            # Conservative line-scan: "name = ..." inside [project.dependencies]
            # or a dependencies array. Avoids adding a tomllib dependency for
            # plugin machinery. Any extraction miss is non-fatal; package index
            # is additive-only.
            in_deps = False
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    in_deps = "dependencies" in stripped.lower()
                    continue
                if in_deps and "=" in stripped:
                    name = stripped.split("=", 1)[0].strip().strip('"').strip("'")
                    if name and not name.startswith("#"):
                        packages.add(name.lower())
                # "dependencies = [...]" inline-array form
                if stripped.startswith("dependencies") and "[" in stripped:
                    inside = stripped.split("[", 1)[1].rstrip("]")
                    for tok in inside.split(","):
                        tok = tok.strip().strip('"').strip("'")
                        # Strip version specifiers like "requests>=2.0"
                        for sep in (">=", "<=", "==", "~=", ">", "<", "="):
                            if sep in tok:
                                tok = tok.split(sep, 1)[0].strip()
                                break
                        if tok:
                            packages.add(tok.lower())
        except OSError:
            pass

    return packages


def detect_stack(project_root: Path) -> list[str]:
    """Detect project stack from manifest files."""
    stack = []

    # package.json
    pkg_json = project_root / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, encoding="utf-8") as f:
                pkg = json.load(f)
            all_deps = {}
            for key in ("dependencies", "devDependencies", "peerDependencies"):
                all_deps.update(pkg.get(key, {}))

            if "typescript" in all_deps:
                stack.append("typescript")
            if "react" in all_deps or "react-dom" in all_deps:
                stack.append("react")
            if "vue" in all_deps:
                stack.append("vue")
            if "angular" in all_deps or "@angular/core" in all_deps:
                stack.append("angular")
            if "express" in all_deps:
                stack.append("express")
            if "next" in all_deps:
                stack.append("next")
            if not stack:
                stack.append("node")
        except (json.JSONDecodeError, OSError):
            stack.append("node")

    # pyproject.toml
    if (project_root / "pyproject.toml").exists():
        stack.append("python")

    # Cargo.toml
    if (project_root / "Cargo.toml").exists():
        stack.append("rust")

    # go.mod
    if (project_root / "go.mod").exists():
        stack.append("go")

    return stack


def detect_tooling(project_root: Path) -> dict:
    """Detect configured enforcement tooling by file existence.

    Returns a dict of tool_name -> bool. File-existence-based only — no config
    parsing. This informs F8 (enforceability ceiling) scoring: if a linter is
    configured, rules that duplicate its function should score lower on F8.

    The detector list is intentionally extensible. Projects using tools not in
    this list (e.g., biome, lefthook, dprint) won't be detected — their F8
    scores will be slightly less accurate but not wrong.
    """
    tooling = {}

    # JavaScript/TypeScript linters
    tooling["eslint"] = any((project_root / name).exists() for name in [
        ".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.json", ".eslintrc.yml",
        "eslint.config.js", "eslint.config.mjs", "eslint.config.cjs",
    ])

    # Formatters
    tooling["prettier"] = any((project_root / name).exists() for name in [
        ".prettierrc", ".prettierrc.js", ".prettierrc.cjs", ".prettierrc.json",
        ".prettierrc.yml", ".prettierrc.yaml", "prettier.config.js", "prettier.config.cjs",
    ])

    # Git hooks
    tooling["git_hooks"] = (
        (project_root / ".husky").is_dir()
        or (project_root / ".git" / "hooks" / "pre-commit").exists()
    )

    # TypeScript strict mode
    tsconfig = project_root / "tsconfig.json"
    tooling["typescript"] = tsconfig.exists()

    # Python linters
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
            tooling["ruff"] = "[tool.ruff]" in content
            tooling["flake8"] = "[tool.flake8]" in content
        except OSError:
            tooling["ruff"] = False
            tooling["flake8"] = False
    else:
        tooling["ruff"] = False
        tooling["flake8"] = False

    # Pre-commit framework
    tooling["pre_commit"] = (project_root / ".pre-commit-config.yaml").exists()

    return tooling


def load_config(project_root: Path) -> dict:
    """Load .rulesense.config from project root. No walk-up."""
    config = {
        "load_prob_overrides": {},
        "severity_overrides": {},
        "ignore_patterns": [],
    }

    config_path = project_root / ".rulesense.config"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Simple key: value parsing
                    if ":" in line:
                        key, _, value = line.partition(":")
                        key = key.strip().strip('"').strip("'")
                        value = value.strip()
                        try:
                            config["load_prob_overrides"][key] = float(value)
                        except ValueError:
                            pass
        except OSError:
            pass

    return config


def load_ignore_patterns(project_root: Path) -> list[str]:
    """Load .rulesense-ignore patterns from project root. No walk-up."""
    patterns = []
    ignore_path = project_root / ".rulesense-ignore"
    if ignore_path.exists():
        try:
            with open(ignore_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    patterns.append(line)
        except OSError:
            pass
    return patterns


# Hot-path regex pre-compiled at module load. build_entity_index iterates over
# every source file's content; keeping the compiled pattern at module scope
# avoids recompilation if the function is ever called more than once per process.
# F-26: Backtick regex bounded to 200 chars max and excludes newlines.
# Without this, `[^`]+` greedy-matches across fenced code blocks
# (opening ``` to next backtick), producing multi-hundred-char "paths"
# that crash Path.exists() with OSError on Linux.
# Phase C fix: exclude `<` and `>` from backtick-wrapped captures so JSX/HTML
# literals like `<FormattedMessage id="..." />` are not indexed as paths.
# See design/staleness-gate-fix-plan.md.
_PATH_PATTERN = re.compile(
    r'(?:`([^`\n<>]{1,200}/[^`\n<>]{0,200})`'  # backtick-wrapped paths, bounded, no JSX
    r'|(?:^|\s)((?:src|lib|test|tests|components|pages|api|utils|hooks|services|models|types|config|scripts)/[\w/.-]+))'  # bare paths
)

# F-14 (partial): a backtick-wrapped single identifier — no slashes, no
# whitespace, bounded length — is a package-reference candidate. Only used
# when a `packages` set is supplied to build_entity_index.
_IDENTIFIER_PATTERN = re.compile(r'`([@/\w.-]{1,60})`')


def build_entity_index(project_root: Path, source_files: list[dict],
                        packages: set[str] | None = None) -> dict:
    """Build an index of entity existence for staleness checking.

    Scans rule text for file path references and checks existence. When a
    `packages` set is supplied (see detect_packages), backtick-wrapped
    identifiers matching a known package name are also indexed as existing
    entities. Missing-package detection stays out of scope — see F-14.
    """
    index = {}

    for sf in source_files:
        content = sf.get("content", "")
        if not content:
            continue
        for m in _PATH_PATTERN.finditer(content):
            path_ref = m.group(1) or m.group(2)
            if path_ref and path_ref not in index:
                full_path = project_root / path_ref.rstrip("/")
                exists = full_path.exists()
                index[path_ref] = {"kind": "path", "exists": exists}

        if packages:
            for m in _IDENTIFIER_PATTERN.finditer(content):
                token = m.group(1)
                # Skip tokens with a path separator — those are handled by _PATH_PATTERN.
                if "/" in token.lstrip("@"):
                    continue
                if token in index:
                    continue
                if token.lower() in packages:
                    index[token] = {"kind": "package", "exists": True}

    return index


def read_source_file(file_info: dict, project_root: Path) -> dict | None:
    """Read and parse a source file into a SourceFile-compatible dict."""
    abs_path = file_info["abs_path"]
    rel_path = file_info["path"]
    is_primary = rel_path == "CLAUDE.md"

    try:
        # F-28: errors="replace" sanitizes lone surrogates from double-encoded
        # source files. Without this, json.dump(ensure_ascii=False) downstream
        # crashes with "surrogates not allowed". The data loss (surrogate → U+FFFD)
        # is cosmetic and preferable to a pipeline crash.
        with open(abs_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError as e:
        if is_primary:
            print(f"FATAL: Cannot read primary file {rel_path}: {e}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"WARNING: Skipping {rel_path}: {e}", file=sys.stderr)
            return None

    fm, _ = parse_frontmatter(content)

    # Read scoping field: "paths:" is canonical per Claude Code docs
    # (https://code.claude.com/docs/en/memory#path-specific-rules).
    # "globs:" is accepted as backward-compat fallback. "paths:" takes
    # precedence if both are present.
    # Verification: docs/loading-semantics.md
    paths_raw = fm.get("paths", None)
    globs_raw = fm.get("globs", None)

    if paths_raw:
        # "paths:" — either block-list (already a list) or inline string
        if isinstance(paths_raw, list):
            globs = paths_raw
        elif isinstance(paths_raw, str) and paths_raw:
            if paths_raw.startswith("[") and paths_raw.endswith("]"):
                inner = paths_raw[1:-1]
                globs = [g.strip().strip('"').strip("'") for g in inner.split(",") if g.strip()]
            else:
                globs = [g.strip() for g in paths_raw.split(",") if g.strip()]
        else:
            globs = []
    elif globs_raw is not None and globs_raw:
        # Backward-compat: "globs:" field (not in official docs but used by
        # existing rule files including this plugin's own test fixtures).
        if isinstance(globs_raw, list):
            globs = globs_raw
        elif globs_raw.startswith("[") and globs_raw.endswith("]"):
            inner = globs_raw[1:-1]
            globs = [g.strip().strip('"').strip("'") for g in inner.split(",") if g.strip()]
        else:
            globs = [g.strip() for g in globs_raw.split(",") if g.strip()]
    else:
        globs = []

    # Unscoped .claude/rules/*.md files are always-loaded per Claude Code docs:
    # "Rules without a paths field are loaded unconditionally and apply to all files."
    # CLAUDE.md is always-loaded by its nature.
    # Verification: docs/loading-semantics.md
    if file_info.get("always_loaded", False):
        always_loaded = True
    else:
        always_loaded = not bool(globs)

    glob_match_count = resolve_globs(globs, project_root) if globs else None

    line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

    return {
        "path": rel_path,
        "globs": globs,
        "glob_match_count": glob_match_count,
        "default_category": fm.get("default-category", "mandate"),
        "line_count": line_count,
        "always_loaded": always_loaded,
        "content": content,
    }


def main():
    parser = argparse.ArgumentParser(description="Discover project context for rulesense")
    parser.add_argument("--project-root", required=True, help="Path to project root")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    if not project_root.is_dir():
        print(f"FATAL: Project root does not exist: {project_root}", file=sys.stderr)
        sys.exit(1)

    # Check for primary file (root or .claude/ location)
    has_root_claude = (project_root / "CLAUDE.md").exists()
    has_alt_claude = (project_root / ".claude" / "CLAUDE.md").exists()
    if not has_root_claude and not has_alt_claude:
        # Check .claude/rules/ as fallback
        rules_dir = project_root / ".claude" / "rules"
        if not rules_dir.is_dir() or not any(rules_dir.glob("*.md")):
            print(f"FATAL: No CLAUDE.md, .claude/CLAUDE.md, or .claude/rules/*.md found in {project_root}",
                  file=sys.stderr)
            sys.exit(1)

    # Discover files
    file_infos = find_instruction_files(project_root)

    # Read source files
    source_files = []
    for fi in file_infos:
        sf = read_source_file(fi, project_root)
        if sf is not None:
            source_files.append(sf)

    if not source_files:
        print("FATAL: No instruction files could be read", file=sys.stderr)
        sys.exit(1)

    # Detect stack and tooling
    stack = detect_stack(project_root)
    tooling = detect_tooling(project_root)

    # Load config
    config = load_config(project_root)
    config["ignore_patterns"] = load_ignore_patterns(project_root)

    # Build entity index with known-package awareness (F-14 partial)
    packages = detect_packages(project_root)
    entity_index = build_entity_index(project_root, source_files, packages=packages)

    # Build project context
    always_loaded = [sf["path"] for sf in source_files if sf["always_loaded"]]
    glob_scoped = [
        {"path": sf["path"], "globs": sf["globs"], "glob_match_count": sf["glob_match_count"]}
        for sf in source_files if not sf["always_loaded"]
    ]

    output = {
        "schema_version": "0.1",
        "pipeline_version": "0.1.0",
        "project_root": str(project_root),
        "project_context": {
            "stack": stack,
            "tooling": tooling,
            "always_loaded_files": always_loaded,
            "glob_scoped_files": glob_scoped,
        },
        "config": config,
        "source_files": source_files,
        "entity_index": entity_index,
    }

    _lib.write_json_stdout(output)


if __name__ == "__main__":
    main()
