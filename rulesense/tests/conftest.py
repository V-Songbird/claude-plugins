"""Shared fixtures and helpers for rulesense tests."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PYTHON = sys.executable


def run_script(name: str, stdin_data: dict | str | None = None, args: list[str] | None = None) -> dict | str:
    """Run a script from the scripts/ directory and return parsed JSON output.

    Args:
        name: Script filename (e.g., "discover.py")
        stdin_data: Dict (JSON-serialized) or string to pipe to stdin
        args: Command-line arguments

    Returns:
        Parsed JSON dict/list from stdout

    Raises:
        subprocess.CalledProcessError: If script exits non-zero
        json.JSONDecodeError: If output is not valid JSON
    """
    cmd = [PYTHON, str(SCRIPTS_DIR / name)]
    if args:
        cmd.extend(args)

    stdin_str = None
    if stdin_data is not None:
        if isinstance(stdin_data, dict) or isinstance(stdin_data, list):
            stdin_str = json.dumps(stdin_data)
        else:
            stdin_str = stdin_data

    result = subprocess.run(
        cmd,
        input=stdin_str,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd, result.stdout, result.stderr
        )

    return json.loads(result.stdout)


def run_script_raw(name: str, stdin_data: dict | str | None = None, args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run a script and return the raw CompletedProcess (for testing failures)."""
    cmd = [PYTHON, str(SCRIPTS_DIR / name)]
    if args:
        cmd.extend(args)

    stdin_str = None
    if stdin_data is not None:
        if isinstance(stdin_data, dict) or isinstance(stdin_data, list):
            stdin_str = json.dumps(stdin_data)
        else:
            stdin_str = stdin_data

    return subprocess.run(
        cmd,
        input=stdin_str,
        capture_output=True,
        text=True,
        timeout=30,
    )


def load_fixture(name: str) -> dict | list | str:
    """Load a fixture file. JSON files are parsed; others returned as string."""
    path = FIXTURES_DIR / name
    with open(path, encoding="utf-8") as f:
        if name.endswith(".json"):
            return json.load(f)
        return f.read()


@pytest.fixture
def sample_project(tmp_path):
    """Create a temporary copy of the sample_project fixture tree.

    Returns the path to the temp project root.
    """
    src = FIXTURES_DIR / "sample_project"
    dst = tmp_path / "sample_project"
    shutil.copytree(src, dst)
    return dst
