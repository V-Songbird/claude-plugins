"""Instruction parser: extracts discrete rules from markdown instruction files.

Pure JSON-in → JSON-out. Reads project_context.json from stdin (produced by
discover.py), outputs rules.json to stdout.

Implements the 8-step algorithm from instruction-parser.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _lib


# ---------------------------------------------------------------------------
# Step 1: Strip metadata
# ---------------------------------------------------------------------------

# F-23c: Bare reference link pattern — a list item that is ONLY a markdown link
_BARE_LINK_PATTERN = re.compile(r'^\s*[-*]?\s*\[.*?\]\(.*?\)\s*$')


def strip_metadata(content: str) -> tuple[list[dict], dict]:
    """Strip frontmatter, headings, blank lines, horizontal rules,
    fenced code blocks (F-23a), markdown tables (F-23b), and bare
    reference links (F-23c).

    Returns (lines_with_metadata, extracted_annotations).
    Each line dict has: line_num, text, is_content, category_annotation.
    """
    lines = content.split("\n")
    result = []
    annotations = {}  # line_num -> category

    # Strip frontmatter
    in_frontmatter = False
    frontmatter_end = 0
    if lines and lines[0].strip() == "---":
        in_frontmatter = True
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                frontmatter_end = i + 1
                break

    # F-23a: Pre-scan for fenced code block regions
    in_fence = False
    fence_regions = set()  # line indices (0-based) that are inside fences
    for i in range(frontmatter_end, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("```"):
            if not in_fence:
                in_fence = True
                fence_regions.add(i)  # the opening fence line itself
            else:
                in_fence = False
                fence_regions.add(i)  # the closing fence line
        elif in_fence:
            fence_regions.add(i)

    # F-23b: Pre-scan for markdown table regions using state machine with lookahead.
    # A table starts when: line starts with |, AND the next line is a separator (|---|).
    # In table state, consume all contiguous |-prefixed lines.
    # This avoids false-positives on prose containing pipe characters.
    table_regions = set()  # line indices (0-based) inside tables
    i = frontmatter_end
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("|") and i not in fence_regions:
            # Look ahead: is the next line a table separator?
            if i + 1 < len(lines) and re.match(r'^\|[\s:]*-', lines[i + 1].strip()):
                # Enter table state — consume all contiguous |-prefixed lines
                j = i
                while j < len(lines) and lines[j].strip().startswith("|"):
                    table_regions.add(j)
                    j += 1
                i = j
                continue
        i += 1

    for i, line in enumerate(lines):
        line_num = i + 1  # 1-indexed

        # Skip frontmatter
        if i < frontmatter_end:
            continue

        # F-23a: Skip fenced code block content
        if i in fence_regions:
            continue

        # F-23b: Skip markdown table rows
        if i in table_regions:
            continue

        stripped = line.strip()

        # Category annotations
        cat_match = re.match(r'<!--\s*category:\s*(\w+)\s*-->', stripped)
        if cat_match:
            annotations[line_num] = cat_match.group(1)
            continue

        # Skip headings
        if re.match(r'^#{1,6}\s', stripped):
            result.append({"line_num": line_num, "text": "", "is_content": False, "is_blank": False, "is_heading": True, "raw": stripped})
            continue

        # Skip horizontal rules
        if re.match(r'^(?:---+|___+|\*\*\*+)\s*$', stripped):
            continue

        # Blank lines (preserve position as boundary markers)
        if not stripped:
            result.append({"line_num": line_num, "text": "", "is_content": False, "is_blank": True, "is_heading": False, "raw": ""})
            continue

        # F-23c: Skip bare reference links (list items that are only a markdown link)
        if _BARE_LINK_PATTERN.match(stripped):
            continue

        result.append({"line_num": line_num, "text": stripped, "is_content": True, "is_blank": False, "is_heading": False, "raw": line})

    return result, annotations


# ---------------------------------------------------------------------------
# Step 2: Identify chunk boundaries
# ---------------------------------------------------------------------------

def identify_chunks(lines: list[dict]) -> list[dict]:
    """Group lines into chunks based on boundary signals.

    Precedence: bullet > section break > sentence boundary.
    Each chunk is annotated with its parent heading text (section_heading)
    for use in Guide C heading-context merging.
    """
    chunks = []
    current_chunk = None
    current_heading = None       # stripped heading text
    current_heading_line = None  # line number of the heading

    for line in lines:
        if not line["is_content"]:
            # Track heading text for Guide C annotation
            if line.get("is_heading"):
                raw = line.get("raw", "")
                heading_text = re.sub(r'^#{1,6}\s+', '', raw).strip()
                if heading_text:
                    current_heading = heading_text
                    current_heading_line = line["line_num"]
            # Blank line = section break boundary
            if line["is_blank"] and current_chunk is not None:
                chunks.append(current_chunk)
                current_chunk = None
            continue

        text = line["text"]
        raw = line["raw"]

        # Check if this is a bullet/list item
        is_bullet = bool(re.match(r'^(?:[-*]|\d+\.)\s', text))

        # Check if this is an indented continuation
        is_continuation = bool(re.match(r'^(?:\s{2,}|\t)', raw)) and not is_bullet

        if is_bullet:
            # New bullet = new chunk
            if current_chunk is not None:
                chunks.append(current_chunk)
            current_chunk = {
                "lines": [line],
                "line_start": line["line_num"],
                "line_end": line["line_num"],
                "text": re.sub(r'^(?:[-*]|\d+\.)\s+', '', text),
                "is_bullet": True,
                "section_heading": current_heading,
                "section_heading_line": current_heading_line,
            }
        elif is_continuation and current_chunk is not None:
            # Continuation of previous chunk
            current_chunk["lines"].append(line)
            current_chunk["line_end"] = line["line_num"]
            current_chunk["text"] += " " + text
        elif current_chunk is None:
            # Start new prose chunk
            current_chunk = {
                "lines": [line],
                "line_start": line["line_num"],
                "line_end": line["line_num"],
                "text": text,
                "is_bullet": False,
                "section_heading": current_heading,
                "section_heading_line": current_heading_line,
            }
        else:
            # Continue prose chunk (no blank line between)
            current_chunk["lines"].append(line)
            current_chunk["line_end"] = line["line_num"]
            current_chunk["text"] += " " + text

    if current_chunk is not None:
        chunks.append(current_chunk)

    return chunks


# ---------------------------------------------------------------------------
# Step 3: Classify chunks as rule candidates or prose
# ---------------------------------------------------------------------------

# Imperative verbs from the F1 lookup table
_IMPERATIVE_VERBS = _lib.load_data("verbs")
_ALL_VERBS = set()
for tier in _IMPERATIVE_VERBS["patterns"]:
    for v in tier["verbs"]:
        _ALL_VERBS.add(v.lower())

# Pre-compile per-verb patterns at module load. has_imperative_verb runs once
# per rule candidate, and the dynamic pattern build was O(V) regex compiles per
# rule (V ≈ 130). Pre-compiling converts that to O(V) cached-pattern lookups.
_VERB_BOUNDARY_PATTERNS: list["re.Pattern[str]"] = [
    re.compile(r'(?:^|\s|,)' + re.escape(v) + r'(?:\s|$|,|\.)')
    for v in _ALL_VERBS
]

# Pre-compile constraint-keyword patterns too — called on every chunk during
# classification, so paying the compile cost once pays back per chunk.
_CONSTRAINT_KEYWORDS = {"only", "required", "forbidden", "mandatory"}
_CONSTRAINT_PATTERNS: list["re.Pattern[str]"] = [
    re.compile(r'\b' + re.escape(kw) + r'\b') for kw in _CONSTRAINT_KEYWORDS
]
_CONDITIONAL_PATTERN = re.compile(
    r'\b(?:when|if|for)\b.*?,\s*(?:' + '|'.join(re.escape(v) for v in sorted(_ALL_VERBS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE,
)
_PROSE_STARTERS = re.compile(
    # Explanatory openers — prose clauses that describe, not direct.
    r'^(?:this means|this is because|the reason|note that|background:|overview:|for context'
    # Reader-addressing openers (surfaced in 3 dogfood projects as false-
    # extracted "rules" in scoped-file headers, e.g. "These rules load when
    # you're editing X"). They describe the file's loading behavior for a
    # human reader, not a directive for Claude.
    r'|these rules|this rule|this file|these files|this section|the following'
    r'|detailed conventions|scoped rules)',
    re.IGNORECASE,
)
_MECHANISM_PATTERN = re.compile(
    r'^(?:the\s+\w+\s+(?:pipeline|agent|system|layer|service)\s+(?:runs|handles|manages|processes))',
    re.IGNORECASE,
)
_REFERENCE_PATTERN = re.compile(
    r'^see\s+[`"\[].*?\b(?:for|about)\b',
    re.IGNORECASE,
)
# Phase I: description-bullet pattern — **bold term** followed by a separator
# (em-dash, colon, or double-dash) then descriptive text. Matches architecture
# descriptions like "**src/primitives/** — Headless behavior hooks".
_DESCRIPTION_BULLET_PATTERN = re.compile(
    r'^\*\*[^*]+\*\*\s*(?:\u2014|--|:)\s',
)

# Navigation-pointer bullets — false-extraction pattern observed across the
# Dallas-Digital, Axo-folio, and guess-who dogfood projects. When a CLAUDE.md
# points readers at scoped rule files, the pointer bullets look like rules
# (they have nouns and descriptions) but they are documentation, not Claude
# directives. Common shapes:
#   - `.claude/rules/comments.md` — when to write comments
#   - **src/game/**` → [`.claude/rules/game-logic.md`](path) — purity, coupling
#   - [`.claude/rules/testing.md`](path) — test file placement
# The common denominator: the bullet opens with a filename.md reference (in
# backticks, bold, or a markdown link) followed by a description separator.
_NAVIGATION_POINTER_PATTERN = re.compile(
    # Variant A: `file.md` — description
    r'^`[^`]+\.md`\s*(?:\u2014|--|:|\u2192|→)\s'
    # Variant B: **path** → [link.md](...) — description (any separator before the .md)
    r'|^\*\*[^*]+\*\*\s*(?:\u2192|→|\u2014|--)\s*\[?`?[\w./-]*\.md'
    # Variant C: [label](file.md) — description
    r'|^\[[^\]]+\]\([^)]*\.md\)\s*(?:\u2014|--|:|\u2192|→)\s',
)


def has_imperative_verb(text: str) -> bool:
    """Check if text contains any imperative verb from the lookup table."""
    text_lower = text.lower()
    for pattern in _VERB_BOUNDARY_PATTERNS:
        if pattern.search(text_lower):
            return True
    return False


def has_constraint_keyword(text: str) -> bool:
    """Check for constraint keywords."""
    text_lower = text.lower()
    for pattern in _CONSTRAINT_PATTERNS:
        if pattern.search(text_lower):
            return True
    return False


def classify_chunk(chunk: dict) -> str:
    """Classify a chunk as 'rule' or 'prose'."""
    text = chunk["text"]
    # Strip markdown bold for verb detection — **Use X** has "use" hidden
    # from the (?:^|\s|,) boundary pattern in has_imperative_verb because
    # ** is not a recognized boundary character.
    text_plain = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

    # Prose indicators (check first)
    if _PROSE_STARTERS.match(text):
        return "prose"
    if _MECHANISM_PATTERN.match(text):
        return "prose"
    if _REFERENCE_PATTERN.match(text):
        return "prose"

    # Navigation-pointer bullets — CLAUDE.md pointers into scoped rule files
    # are documentation, not directives. Check before the rule-indicator pass
    # because these bullets often contain description words that look like
    # verbs to has_imperative_verb. Only applies to bullets; a paragraph
    # starting with a .md reference is rare enough to leave alone.
    if chunk.get("is_bullet", False) and _NAVIGATION_POINTER_PATTERN.match(text):
        return "prose"

    # Rule indicators (use text_plain so bold-wrapped verbs are detected)
    if has_imperative_verb(text_plain):
        return "rule"
    if has_constraint_keyword(text):
        return "rule"
    if _CONDITIONAL_PATTERN.search(text):
        return "rule"

    # Ambiguous: over-extract per spec guidance
    # Check if it reads like a directive at all
    if chunk.get("is_bullet", False):
        # Phase I: description-bullet filter — verbless bullets matching
        # **bold** —/:/-- description format are context, not directives.
        if _DESCRIPTION_BULLET_PATTERN.match(text):
            return "prose"
        # Bullet items are more likely to be rules
        return "rule"

    return "prose"


# ---------------------------------------------------------------------------
# Step 4: Merge clarification chunks
# ---------------------------------------------------------------------------

_CLARIFICATION_STARTERS = re.compile(
    r'^(?:this means|for example|i\.e\.|e\.g\.|in other words|specifically|that is)',
    re.IGNORECASE,
)


def _is_verbless_bullet(chunk: dict) -> bool:
    """Check if chunk is a bullet with no imperative verb or constraint keyword."""
    return (chunk.get("is_bullet", False)
            and not has_imperative_verb(chunk["text"])
            and not has_constraint_keyword(chunk["text"]))


def merge_clarifications(chunks: list[dict]) -> list[dict]:
    """Merge clarification prose into preceding rule candidates."""
    classified = [(chunk, classify_chunk(chunk)) for chunk in chunks]
    merged = []

    i = 0
    while i < len(classified):
        chunk, cls = classified[i]

        if cls == "rule":
            # Guide C: heading-context merge for orphaned verbless bullets.
            # When a verbless bullet has a section_heading but no preceding
            # paragraph directive to merge into (Phase H), create a synthetic
            # parent from the heading and merge consecutive verbless siblings.
            if (_is_verbless_bullet(chunk)
                    and chunk.get("section_heading")):
                heading = chunk["section_heading"]
                heading_line = chunk.get("section_heading_line", chunk["line_start"])
                # Synthetic parent carries the heading text as directive context
                synthetic = {
                    "lines": [],
                    "line_start": heading_line,
                    "line_end": chunk["line_start"],
                    "text": heading + ":",
                    "is_bullet": False,
                    "section_heading": heading,
                }
                merged_chunk = _merge_two_chunks(synthetic, chunk)
                j = i + 1
                while j < len(classified):
                    next_chunk, next_cls = classified[j]
                    if (next_cls == "rule"
                            and _is_verbless_bullet(next_chunk)
                            and next_chunk.get("section_heading") == heading):
                        merged_chunk = _merge_two_chunks(merged_chunk, next_chunk)
                        j += 1
                    else:
                        break
                merged.append((merged_chunk, "rule"))
                i = j
                continue

            # Look ahead for clarifications and dependent list items
            j = i + 1
            while j < len(classified):
                next_chunk, next_cls = classified[j]
                if next_cls == "prose" and _is_clarification(next_chunk):
                    # Merge prose clarifications into current rule
                    chunk = _merge_two_chunks(chunk, next_chunk)
                    j += 1
                elif (next_cls == "rule"
                      and next_chunk.get("is_bullet", False)
                      and not chunk.get("is_bullet", False)
                      and not has_imperative_verb(next_chunk["text"])
                      and not has_constraint_keyword(next_chunk["text"])):
                    # Phase H: merge verbless bullet items into parent paragraph
                    # directive. The bullet has no verb/constraint of its own —
                    # it's an example or list item of the parent, not standalone.
                    chunk = _merge_two_chunks(chunk, next_chunk)
                    j += 1
                else:
                    break
            merged.append((chunk, "rule"))
            i = j
        else:
            merged.append((chunk, cls))
            i += 1

    return merged


def _is_clarification(chunk: dict) -> bool:
    """Check if a chunk is a clarification of a preceding rule."""
    text = chunk["text"]
    if _CLARIFICATION_STARTERS.match(text):
        return True
    # Code blocks are clarifications
    if text.startswith("```"):
        return True
    return False


def _merge_two_chunks(rule_chunk: dict, clarification: dict) -> dict:
    """Merge a clarification into a rule chunk."""
    return {
        "lines": rule_chunk["lines"] + clarification["lines"],
        "line_start": rule_chunk["line_start"],
        "line_end": clarification["line_end"],
        "text": rule_chunk["text"] + " " + clarification["text"],
        "is_bullet": rule_chunk.get("is_bullet", False),
        "section_heading": rule_chunk.get("section_heading"),
    }


# ---------------------------------------------------------------------------
# Step 5: Split compound rules
# ---------------------------------------------------------------------------

def split_compound_rules(chunks: list[tuple[dict, str]]) -> list[tuple[dict, str]]:
    """Split compound rules with multiple independent directives."""
    result = []
    for chunk, cls in chunks:
        if cls != "rule":
            result.append((chunk, cls))
            continue

        parts = _try_split(chunk)
        for part in parts:
            result.append((part, "rule"))

    return result


def would_fragment(text: str) -> list[str]:
    """Return the parts this text would be split into if extracted as a rule.

    Returns a list of length 1 if the text would NOT fragment, or length >= 2
    if it would. Exposed as a public helper so rewrite_scorer can warn about
    rewrites that would re-fragment once they are applied to source files and
    re-extracted on the next audit pass.

    Wraps `_try_split` with a minimal chunk shape so callers do not need to
    synthesize the full internal chunk dict. The returned parts contain only
    their text; positional fields are not meaningful for fragmentation checks.
    """
    fake_chunk = {
        "text": text,
        "lines": [],
        "line_start": 0,
        "line_end": 0,
        "is_bullet": False,
    }
    parts = _try_split(fake_chunk)
    return [p["text"] for p in parts]


def _try_split(chunk: dict) -> list[dict]:
    """Try to split a compound rule into independent parts.

    Split when comma-separated imperatives with different objects.
    Don't split when 'and' joins steps of one process.
    """
    text = chunk["text"]

    # Check for semicolon-separated directives
    if ";" in text:
        parts = text.split(";")
        if len(parts) >= 2 and all(_has_own_verb(p.strip()) for p in parts if p.strip()):
            return [_make_subchunk(chunk, p.strip()) for p in parts if p.strip()]

    # Check for "and" joining independent directives
    # Only split on ", and " or " and " when both sides have their own verb
    and_parts = re.split(r',\s+and\s+|\s+and\s+', text)
    if len(and_parts) >= 2 and all(_has_own_verb(p.strip()) for p in and_parts):
        # But don't split if they describe steps of one process
        if not _is_single_process(text):
            return [_make_subchunk(chunk, p.strip()) for p in and_parts]

    return [chunk]


def _has_own_verb(text: str) -> bool:
    """Check if text fragment has its own imperative verb."""
    return has_imperative_verb(text)


def _is_single_process(text: str) -> bool:
    """Check if compound text describes steps of a single process."""
    # "Edit X and regenerate" — two steps, one process
    text_lower = text.lower()
    single_process_patterns = [
        r'\b(?:edit|modify|change).*\band\b.*\b(?:regenerate|rebuild|recompile|restart)',
        r'\b(?:save|write).*\band\b.*\b(?:commit|push)',
        r'\b(?:create|add).*\band\b.*\b(?:register|configure|setup)',
    ]
    for pat in single_process_patterns:
        if re.search(pat, text_lower):
            return True
    return False


def _make_subchunk(parent: dict, text: str) -> dict:
    """Create a sub-chunk from a parent chunk with new text."""
    return {
        "lines": parent["lines"],
        "line_start": parent["line_start"],
        "line_end": parent["line_end"],
        "text": text,
        "is_bullet": parent.get("is_bullet", False),
    }


# ---------------------------------------------------------------------------
# Step 6-8: Assign categories, line numbers, output
# ---------------------------------------------------------------------------

def extract_entity_references(text: str, entity_index: dict) -> tuple[list[dict], dict]:
    """Extract entity references from rule text and cross-reference with entity index."""
    entities = []
    missing = []

    # Find backtick-wrapped identifiers
    for m in re.finditer(r'`([^`]+)`', text):
        name = m.group(1)
        # JSX/HTML tag literals (e.g., `<FormattedMessage id="..." />`) contain
        # `/` from `/>` but are not file paths. Exclude them from path classification
        # before the `/`-presence check fires. See design/staleness-gate-fix-plan.md.
        if "<" in name or ">" in name:
            kind = "pattern"
        elif "/" in name or "." in name:
            kind = "path"
        elif name[0].isupper() or "_" in name:
            kind = "api"
        else:
            kind = "pattern"

        exists = None
        if name in entity_index:
            exists = entity_index[name].get("exists")
        elif kind == "path":
            # Check if any entity_index entry is a prefix/match
            for idx_name, idx_info in entity_index.items():
                if name.startswith(idx_name) or idx_name.startswith(name):
                    exists = idx_info.get("exists")
                    break

        # F-14: Path-kind entities not found in entity_index don't exist —
        # but only when the name contains a slash, because entity_index
        # (discover.py build_entity_index) only indexes backtick paths
        # matching `[^`]+/[^`]+`. Slash-less filenames like `Button.tsx`
        # are classified kind="path" by extract but aren't in entity_index
        # by design. Promoting those to exists=False would false-positive
        # every backticked filename in every CLAUDE.md.
        if exists is None and kind == "path" and "/" in name and "<" not in name and ">" not in name:
            exists = False

        entities.append({"name": name, "kind": kind, "exists": exists})
        if exists is False:
            missing.append(name)

    # Find bare file path references
    for m in re.finditer(r'(?:^|\s)((?:src|lib|test|tests|components|pages|api)/[\w/.-]+)', text):
        name = m.group(1)
        if not any(e["name"] == name for e in entities):
            exists = entity_index.get(name, {}).get("exists")
            entities.append({"name": name, "kind": "path", "exists": exists})
            if exists is False:
                missing.append(name)

    staleness = {
        "gated": len(missing) > 0,
        "missing_entities": missing,
    }

    return entities, staleness


def build_rules(project_context: dict) -> list[dict]:
    """Main extraction pipeline: project_context → rule records."""
    source_files = project_context.get("source_files", [])
    config = project_context.get("config", {})
    entity_index = project_context.get("entity_index", {})
    ignore_patterns = config.get("ignore_patterns", [])

    all_rules = []
    rule_counter = 0

    for file_idx, sf in enumerate(source_files):
        content = sf.get("content", "")
        if not content:
            continue

        file_path = sf["path"]

        # Step 1: Strip metadata
        lines, annotations = strip_metadata(content)

        # Step 2: Identify chunks
        chunks = identify_chunks(lines)

        # Step 3 + 4: Classify and merge clarifications
        merged = merge_clarifications(chunks)

        # Step 5: Split compound rules
        split = split_compound_rules(merged)

        # Collect only rule candidates
        for chunk, cls in split:
            if cls != "rule":
                continue

            rule_counter += 1
            rule_id = f"R{rule_counter:03d}"
            rule_text = chunk["text"]

            # Step 6: Assign category
            # Check for per-rule annotation (line before the chunk)
            category = sf.get("default_category", "mandate")
            for line_num in range(chunk["line_start"] - 2, chunk["line_start"]):
                if line_num in annotations:
                    category = annotations[line_num]
                    break

            # Check ignore patterns
            if _should_ignore(file_path, rule_text, ignore_patterns):
                rule_counter -= 1  # Don't count ignored rules
                continue

            # Extract entity references
            entities, staleness = extract_entity_references(rule_text, entity_index)

            all_rules.append({
                "id": rule_id,
                "file_index": file_idx,
                "text": rule_text,
                "line_start": chunk["line_start"],
                "line_end": chunk["line_end"],
                "category": category,
                "referenced_entities": entities,
                "staleness": staleness,
                "factors": {},
            })

    return all_rules


def _should_ignore(file_path: str, rule_text: str, ignore_patterns: list[str]) -> bool:
    """Check if a rule matches any ignore pattern."""
    for pattern in ignore_patterns:
        pattern = pattern.strip()
        if ":" in pattern:
            file_part, _, text_part = pattern.partition(":")
            file_part = file_part.strip()
            text_part = text_part.strip().strip('"').strip("'")
            if file_path == file_part and text_part in rule_text:
                return True
        else:
            if file_path == pattern:
                return True
    return False


def main():
    data = _lib.read_json_stdin()

    rules = build_rules(data)

    # Build output: carry forward project_context, config, source_files (minus content)
    source_files_out = []
    for sf in data.get("source_files", []):
        sf_copy = dict(sf)
        sf_copy.pop("content", None)  # Strip file content from output
        source_files_out.append(sf_copy)

    output = {
        "schema_version": data.get("schema_version", "0.1"),
        "pipeline_version": data.get("pipeline_version", "0.1.0"),
        "project_context": data.get("project_context", {}),
        "config": data.get("config", {}),
        "source_files": source_files_out,
        "rules": rules,
    }

    _lib.write_json_stdout(output)


if __name__ == "__main__":
    main()
