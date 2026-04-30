"""Shared library for rulesense scoring pipeline.

Provides dataclasses for the JSON schema, I/O helpers, and data loading.
No third-party imports — standard library only.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# F-24/F-28: Force UTF-8 on all stdio streams on Windows where the default
# encoding is cp1252. Without this, json.load(sys.stdin) produces surrogates
# from non-ASCII content, and json.dump(sys.stdout) crashes with
# "surrogates not allowed". The hasattr guard handles edge cases where
# streams have been replaced (e.g. tests using capsys).
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Resolve _data/ relative to this file's location
_DATA_DIR = Path(__file__).parent / "_data"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(name: str) -> Any:
    """Load a JSON data file from _data/ by name (with or without .json)."""
    if not name.endswith(".json"):
        name += ".json"
    path = _DATA_DIR / name
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_data_text(name: str) -> str:
    """Load a text file from _data/ (e.g., rubric_F3.md)."""
    path = _DATA_DIR / name
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# JSON I/O helpers
# ---------------------------------------------------------------------------

def read_json_stdin() -> dict:
    """Read JSON from stdin."""
    return json.load(sys.stdin)


def write_json_stdout(data: dict | list) -> None:
    """Write JSON to stdout with consistent formatting."""
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


# ---------------------------------------------------------------------------
# Factor evidence dataclasses (heterogeneous by design)
# ---------------------------------------------------------------------------

@dataclass
class F1Evidence:
    value: float | None
    method: str  # "lookup" | "implicit_imperative_default" | "extraction_failed"
    matched_verb: str | None = None
    matched_score_tier: float | None = None


@dataclass
class F2Evidence:
    value: float
    method: str  # "classify"
    matched_category: str | None = None


@dataclass
class F4Evidence:
    value: float
    method: str  # "glob_match" | "always_universal" | "misaligned" | "keyword_overlap" | "wrong_scope" | "stale" | "dead_glob"
    loading: str | None = None  # "glob-scoped" | "always-loaded"
    trigger_match: str | None = None


@dataclass
class F7Evidence:
    value: float
    method: str  # "count" | "judgment_patch"
    concrete_markers: list[str] = field(default_factory=list)
    abstract_markers: list[str] = field(default_factory=list)
    concrete_count: int = 0
    abstract_count: int = 0


@dataclass
class F3Evidence:
    value: float
    method: str  # "judgment"
    level: int = 0
    reasoning: str = ""


@dataclass
class F8Evidence:
    value: float
    method: str  # "judgment"
    level: int = 0
    reasoning: str = ""


# ---------------------------------------------------------------------------
# Schema dataclasses
# ---------------------------------------------------------------------------

@dataclass
class EntityRef:
    name: str
    kind: str  # "path" | "package" | "api" | "pattern"
    exists: bool | None = None


@dataclass
class StalenessInfo:
    gated: bool = False
    missing_entities: list[str] = field(default_factory=list)


@dataclass
class SourceFile:
    path: str
    globs: list[str] = field(default_factory=list)
    glob_match_count: int | None = None
    default_category: str = "mandate"
    line_count: int = 0
    always_loaded: bool = True
    content: str | None = None  # Present in discover output, stripped by extract


@dataclass
class RuleRecord:
    id: str
    file_index: int
    text: str
    line_start: int
    line_end: int
    category: str = "mandate"
    referenced_entities: list[dict] = field(default_factory=list)
    staleness: dict = field(default_factory=lambda: {"gated": False, "missing_entities": []})
    factors: dict = field(default_factory=dict)
    factor_confidence_low: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def evidence_to_dict(ev: Any) -> dict:
    """Convert a factor evidence dataclass to a plain dict for JSON."""
    if hasattr(ev, "__dataclass_fields__"):
        return asdict(ev)
    return ev


def make_rule_dict(rule: RuleRecord) -> dict:
    """Convert a RuleRecord to a JSON-serializable dict."""
    d = asdict(rule)
    # Only include factor_confidence_low if non-empty
    if not d["factor_confidence_low"]:
        del d["factor_confidence_low"]
    return d
