#!/usr/bin/env bash
# jetbrains-detect — proxy check for whether a JetBrains IDE MCP server is
# reachable from this Claude Code session. Exits 0 if routing SHOULD be
# enforced, non-zero if the hook should fail open and let the native tool run.
#
# Detection strategy (first match wins):
#
#   1. JETBRAINS_ROUTER_DISABLE=1  → fail open (explicit opt-out, highest
#      priority). Use this to kill-switch the plugin without uninstalling.
#
#   2. JETBRAINS_ROUTER_FORCE_INTERNAL=1  → enforce (explicit opt-in, skips
#      probe). PRIVATE knob — used by the test suite and by wrapper
#      launchers that know an IDE is running but get a probe miss
#      (e.g. IDE launched via `java -cp …` shows up as `java`).
#      Deliberately not exposed under a public name: a user-exported
#      `JETBRAINS_ROUTER_FORCE` in a shell rc would force routing across
#      every Claude session, including ones where no IDE is open.
#
#   3. Process probe             → look for a running JetBrains IDE process
#      on the host, matching on the EXECUTABLE NAME only (not the full
#      command line, which would false-match any process whose cwd or args
#      happen to contain "idea", "clion", etc.).
#
#      Platform dispatch:
#      - Windows git-bash / WSL    →  tasklist (preferred) or ps
#      - macOS                     →  pgrep -x (exact process name)
#      - Linux                     →  pgrep -x (exact process name)
#
# Exit codes:
#   0  — enforce routing (a JetBrains IDE appears reachable)
#   1  — fail open (no IDE detected)
#
# A single line to stderr on explicit disable so hook logs can tell
# "kill-switched" apart from "nothing running." No output on success.

set -u

# --- 1. Kill switch ---------------------------------------------------------
if [ "${JETBRAINS_ROUTER_DISABLE:-}" = "1" ]; then
  echo "jetbrains-router: disabled via JETBRAINS_ROUTER_DISABLE=1" >&2
  exit 1
fi

# --- 2. Force-on (tests, manual override) ----------------------------------
if [ "${JETBRAINS_ROUTER_FORCE_INTERNAL:-}" = "1" ]; then
  exit 0
fi

# --- 3. Process probe -------------------------------------------------------
# Process EXECUTABLE names (not full command line) we consider evidence of a
# running JetBrains IDE that bundles the MCP Server plugin. The pattern is
# anchored so `pgrep -x` requires a full name match; similarly tasklist's
# CSV output is scoped to the IMAGENAME column.
#
# Trade-off: an IDE launched through a `java -cp …` wrapper (uncommon on
# macOS/Windows, common on some Linux setups) will NOT match here and the
# hook will fail open. Users in that case should set
# JETBRAINS_ROUTER_FORCE_INTERNAL=1 in a project-scoped `.envrc` (direnv) or
# the wrapper script itself — NOT in their shell rc, where it would force
# every Claude session into routing mode regardless of which IDE is open.
_JETBRAINS_NAMES='webstorm|webstorm64|idea|idea64|pycharm|pycharm64|phpstorm|phpstorm64|rubymine|rubymine64|goland|goland64|rider|rider64|clion|clion64|datagrip|datagrip64|rustrover|rustrover64|aqua|aqua64|writerside|writerside64|fleet'

# Windows tasklist — IMAGENAME in the first CSV column, typically
# "webstorm64.exe". Anchor the match to the quoted first column.
# Note: use //NH //FO (double slash) not /NH /FO — git-bash MSYS path
# mangling rewrites single-slash Windows flags to absolute paths.
if command -v tasklist >/dev/null 2>&1; then
  if tasklist //NH //FO CSV 2>/dev/null \
      | grep -Eqi "^\"($_JETBRAINS_NAMES)(\.exe)?\","; then
    exit 0
  fi
fi

# pgrep -x: match the process NAME exactly, case-insensitive (-i).
# macOS and most Linuxes support this. Note: we deliberately do NOT pass -f
# because matching the full command line causes false positives on e.g.
# editor windows open in paths named "ideas/" or scripts called "pycharm.py".
if command -v pgrep >/dev/null 2>&1; then
  if pgrep -xi "$_JETBRAINS_NAMES" >/dev/null 2>&1; then
    exit 0
  fi
fi

# Last-resort ps scan. Works everywhere that has ps, including busybox. We
# pull the last token of each line (CMD on most ps variants) and check for
# an exact match against the JetBrains list.
if command -v ps >/dev/null 2>&1; then
  if ps -A 2>/dev/null \
      | awk '{print $NF}' \
      | grep -Eqi "^($_JETBRAINS_NAMES)(\.exe)?$"; then
    exit 0
  fi
fi

# No evidence of a running JetBrains IDE → fail open.
exit 1