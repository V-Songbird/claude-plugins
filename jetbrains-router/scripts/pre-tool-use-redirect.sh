#!/usr/bin/env bash
# pre-tool-use-redirect — the enforcement side of jetbrains-router.
# Intercepts native Read / Grep / Glob / Edit / Write / Bash PreToolUse
# events; when a JetBrains IDE is running and the native call has a direct
# mcp__<ide>__* equivalent, block the native call (exit 2) with a stderr
# message naming the IDE tool and a pre-translated project-relative path.
# Otherwise allow (exit 0).
#
# Exit protocol:
#   0                → allow native tool (path out of project, unknown Bash
#                       pattern, IDE unreachable, malformed input —
#                       all fail-open cases)
#   2 + stderr msg   → block; stderr is shown to Claude verbatim
#
# Platform: macOS bash 3.2, Linux bash 5+, Windows git-bash. Uses only jq,
# awk, sed, grep, tr, bash builtins.

set -u

# --- Active JetBrains IDE MCP prefix ----------------------------------------
# JetBrains auto-configure produces 'webstorm', 'rider', or 'idea' as the
# mcpServers key — that becomes the mcp__<key>__* tool prefix.
# Override with JETBRAINS_MCP_PREFIX if you renamed your mcp server entry.
JB_PREFIX="${JETBRAINS_MCP_PREFIX:-webstorm}"

# --- Resolve plugin root (works without CLAUDE_PLUGIN_ROOT, e.g. in tests) --
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DETECT="$PLUGIN_ROOT/scripts/jetbrains-detect.sh"

# --- Availability gate: fail open if no IDE is reachable --------------------
if [ -f "$DETECT" ] && ! bash "$DETECT"; then
  exit 0
fi

# --- jq required. Without it, we cannot parse the hook input ----------------
command -v jq >/dev/null 2>&1 || exit 0

INPUT="$(cat)"
TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)"
CWD="$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)"
[ -n "$TOOL_NAME" ] || exit 0

# --- Per-tool bypass --------------------------------------------------------
# JETBRAINS_ROUTER_BYPASS is a comma-separated list of native tool names to
# leave alone this session (e.g. JETBRAINS_ROUTER_BYPASS=Read,Edit). Finer-
# grained than JETBRAINS_ROUTER_DISABLE, which kill-switches every tool.
case ",${JETBRAINS_ROUTER_BYPASS:-}," in
  *",$TOOL_NAME,"*) exit 0 ;;
esac

# --- Worktree guard ---------------------------------------------------------
# In a linked git worktree, the session cwd is almost never what the IDE has
# open — the IDE usually holds the main checkout, and translated paths would
# point to files its MCP server can't see. Bail (fail open) when cwd's
# --git-dir differs from --git-common-dir (the signature of a linked
# worktree). Silent on non-git cwds and on the main checkout.
#
# Anchor both rev-parse calls to --show-toplevel: from a subdirectory git
# returns --git-dir as an absolute path but --git-common-dir as a relative
# one, so a raw string compare flags every subdir-cwd as a worktree. Running
# from the worktree root makes both return the same form (`.git` for the main
# checkout, absolute paths for linked worktrees).
if [ -n "$CWD" ] && command -v git >/dev/null 2>&1; then
  _top="$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null)"
  if [ -n "$_top" ]; then
    _gd="$(git -C "$_top" rev-parse --git-dir 2>/dev/null)"
    _gcd="$(git -C "$_top" rev-parse --git-common-dir 2>/dev/null)"
    if [ -n "$_gd" ] && [ -n "$_gcd" ] && [ "$_gd" != "$_gcd" ]; then
      exit 0
    fi
  fi
fi

# --- Binary-file extensions to leave on native tools -----------------------
# Keep in sync with the "Stay on native tools for" section of the skill.
_is_binary() {
  case "$1" in
    *.png|*.jpg|*.jpeg|*.gif|*.bmp|*.tif|*.tiff|*.ico|*.webp|*.avif \
    |*.pdf|*.zip|*.tar|*.tgz|*.gz|*.bz2|*.xz|*.7z|*.rar \
    |*.exe|*.dll|*.so|*.dylib|*.class|*.jar|*.war|*.wasm \
    |*.mp3|*.mp4|*.mov|*.avi|*.mkv|*.ogg|*.flac|*.wav|*.webm|*.m4a \
    |*.ttf|*.otf|*.woff|*.woff2|*.eot \
    |*.pyc|*.pyo|*.o|*.a|*.lib|*.obj|*.bin|*.iso|*.dmg) return 0 ;;
  esac
  return 1
}

# --- Normalize a Windows drive-letter prefix to lowercase (for compare) ----
_drive_norm() {
  case "$1" in
    [A-Za-z]:*)
      local first="${1:0:1}"
      local rest="${1:1}"
      first="$(printf '%s' "$first" | tr 'A-Z' 'a-z')"
      printf '%s%s' "$first" "$rest"
      ;;
    *) printf '%s' "$1" ;;
  esac
}

# --- Path translation: absolute → project-relative --------------------------
# Returns empty string if the path is absolute but outside the project root
# (caller should then fail open — the IDE can't see it). Also returns empty
# when there is no project root and the path is absolute.
path_to_project_relative() {
  local path="$1"
  local root="$2"
  [ -n "$path" ] || { echo ""; return; }
  local p_norm="${path//\\//}"
  # Without a project root, we can only emit already-relative paths.
  if [ -z "$root" ]; then
    case "$p_norm" in
      /*|[A-Za-z]:/*) echo "" ;;
      *)              echo "$p_norm" ;;
    esac
    return
  fi
  local r_norm="${root//\\//}"
  r_norm="${r_norm%/}"
  # Windows drive letters are case-insensitive — normalize both sides.
  local p_cmp; p_cmp="$(_drive_norm "$p_norm")"
  local r_cmp; r_cmp="$(_drive_norm "$r_norm")"
  # Strip the root prefix when present.
  if [ -n "$r_cmp" ] && [ "${p_cmp#${r_cmp}/}" != "$p_cmp" ]; then
    echo "${p_cmp#${r_cmp}/}"
    return
  fi
  # Already relative (no leading / and no Windows drive letter)?
  case "$p_norm" in
    /*|[A-Za-z]:/*) echo "" ;;
    *)              echo "$p_norm" ;;
  esac
}

# --- Resolve a file_path to an absolute path for existence checks ----------
_abs_path() {
  local fp="$1"
  local cwd="$2"
  case "$fp" in
    /*|[A-Za-z]:/*|[A-Za-z]:\\*) printf '%s' "${fp//\\//}" ;;
    *) [ -n "$cwd" ] && printf '%s/%s' "${cwd%/}" "$fp" || printf '%s' "$fp" ;;
  esac
}

# --- Emit block + redirect message ------------------------------------------
block() {
  printf 'jetbrains-router: %s\n' "$1" >&2
  exit 2
}

# --- Dispatch ---------------------------------------------------------------
case "$TOOL_NAME" in
  Read)
    FP="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"
    _is_binary "$FP" && exit 0
    REL="$(path_to_project_relative "$FP" "$CWD")"
    [ -n "$REL" ] || exit 0
    block "retry as mcp__${JB_PREFIX}__read_file with pathInProject=\"$REL\" — this redirect is expected."
    ;;

  Grep)
    PATTERN="$(printf '%s' "$INPUT" | jq -r '.tool_input.pattern // empty' 2>/dev/null)"
    # Claude Code's Grep is always ripgrep-backed (regex). Route to
    # search_regex unconditionally — it handles literals too. The skill
    # documents when search_text is slightly more ergonomic.
    block "retry as mcp__${JB_PREFIX}__search_regex with q=\"$PATTERN\" (or mcp__${JB_PREFIX}__search_text for plain literals) — this redirect is expected."
    ;;

  Glob)
    PATTERN="$(printf '%s' "$INPUT" | jq -r '.tool_input.pattern // empty' 2>/dev/null)"
    block "retry as mcp__${JB_PREFIX}__search_file with q=\"$PATTERN\" — this redirect is expected."
    ;;

  Edit)
    FP="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"
    _is_binary "$FP" && exit 0
    REL="$(path_to_project_relative "$FP" "$CWD")"
    [ -n "$REL" ] || exit 0
    # replace_text_in_file requires the file to exist on disk. If it doesn't,
    # let native Edit emit its own "file not found" error rather than route
    # to a tool that will fail with a less clear message.
    ABS="$(_abs_path "$FP" "$CWD")"
    [ -e "$ABS" ] || exit 0
    block "retry as mcp__${JB_PREFIX}__replace_text_in_file with pathInProject=\"$REL\" — this redirect is expected."
    ;;

  Write)
    FP="$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)"
    _is_binary "$FP" && exit 0
    REL="$(path_to_project_relative "$FP" "$CWD")"
    [ -n "$REL" ] || exit 0
    # create_new_file refuses to overwrite. If the target already exists,
    # Write wants overwrite semantics — let native Write handle it.
    ABS="$(_abs_path "$FP" "$CWD")"
    [ -e "$ABS" ] && exit 0
    block "retry as mcp__${JB_PREFIX}__create_new_file with pathInProject=\"$REL\" — this redirect is expected."
    ;;

  Bash)
    CMD="$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)"
    [ -n "$CMD" ] || exit 0

    # Strip leading whitespace for pattern matching.
    CMD_STRIPPED="$(printf '%s' "$CMD" | sed -E 's/^[[:space:]]+//')"

    # Hands-off: pipes, heredocs, here-strings, input/output redirection,
    # command chains. These imply composition that
    # mcp__<ide>__execute_terminal_command's 2000-line output cap and
    # user-confirmation prompt can't faithfully replace, and the individual
    # IDE tools don't compose. Let native Bash handle it.
    #
    # The '<' pattern catches '<', '<<', and '<<<'; the '>' pattern catches
    # '>', '>>', '>&', and '2>'. Over-bailing here is preferred over
    # routing a composed command by accident.
    case "$CMD_STRIPPED" in
      *'|'*|*'<'*|*'>'*|*'&&'*|*'||'*|*';'*|*'&'*)
        exit 0
        ;;
    esac

    # Bail on quoted arguments: we cannot safely extract file/dir operands
    # with awk $NF when the command contains quoted tokens. Let native Bash
    # handle those (rare for the redirectable patterns below).
    case "$CMD_STRIPPED" in
      *\'*|*\"*|*\`*)
        exit 0
        ;;
    esac

    # --- Anti-bypass: normalize leading env-var prefixes ------------------
    # Without this, an agent can sneak past every dispatch pattern by
    # prefixing the command with a no-op env assignment (`FOO=1 cat foo`
    # doesn't match `'cat '*`, so the case falls through and the hook fails
    # open). Setting env vars in the command does NOT actually disable the
    # router — the hook reads its own process env, not the inner command's
    # env — so the bypass is purely a pattern-match miss.
    #
    # Two behaviors:
    #   1. Block outright if the prefix tries to set JETBRAINS_ROUTER_*.
    #      Those vars are the user's session-level controls; the agent must
    #      not set them via command prefix.
    #   2. Otherwise strip leading `env`, `env -i`, and `KEY=VAL` tokens to
    #      produce CMD_DISPATCH, then run the same case-statement against
    #      the normalized form.
    CMD_DISPATCH="$CMD_STRIPPED"

    # Strip a leading `env` (with the most common no-arg flags). We do NOT
    # try to handle `env -u VAR` or other valued flags — those are rare from
    # agents and falling through to fail-open is acceptable for them.
    case "$CMD_DISPATCH" in
      'env '*)   CMD_DISPATCH="${CMD_DISPATCH#env }" ;;
    esac
    case "$CMD_DISPATCH" in
      'env -i '*) CMD_DISPATCH="${CMD_DISPATCH#env -i }" ;;
    esac

    # Peel off leading KEY=VAL tokens. Each peeled token is checked for
    # JETBRAINS_ROUTER_* and the loop refuses to run more than 16 iterations
    # so a malformed command can't spin forever.
    _peel_count=0
    while [ "$_peel_count" -lt 16 ]; do
      _peel_count=$((_peel_count + 1))
      _first="${CMD_DISPATCH%% *}"
      # Stop if there's no space (single-token leftover) or first token
      # isn't an assignment.
      [ "$_first" = "$CMD_DISPATCH" ] && break
      case "$_first" in
        [A-Za-z_]*=*)
          case "$_first" in
            JETBRAINS_ROUTER_*=*)
              block "do not set JETBRAINS_ROUTER_* env vars as a command prefix. Those are the user's session controls (kill switch, force-on, per-tool bypass list) — not an agent escape hatch. The redirect was emitted because the IDE tool is the right call here; setting these vars in the command does not actually disable the hook. If a redirect is genuinely wrong (e.g. binary file, exotic flag combo), surface it to the user instead of working around it."
              ;;
          esac
          CMD_DISPATCH="${CMD_DISPATCH#"$_first" }"
          ;;
        *) break ;;
      esac
    done

    # Redirectable patterns — ordered most-specific first.
    case "$CMD_DISPATCH" in
      'npm run build'*|'yarn build'*|'pnpm build'*|'tsc'|'tsc '*|'yarn tsc'*|'npm run tsc'*|'pnpm tsc'*)
        block "retry as mcp__${JB_PREFIX}__build_project — this redirect is expected."
        ;;

      'npm test'*|'npm run test'*|'yarn test'*|'pnpm test'*|'jest'|'jest '*|'vitest'|'vitest '*)
        block "retry as mcp__${JB_PREFIX}__execute_run_configuration (call mcp__${JB_PREFIX}__get_run_configurations first to list configs) — this redirect is expected."
        ;;

      'cat '*|'head '*|'tail '*)
        # tail -f / head -f is a follow, not a snapshot — no IDE equivalent.
        case "$CMD_DISPATCH" in
          *' -f '*|*' -f'|*' --follow '*|*' --follow') exit 0 ;;
        esac
        FILE_ARG="$(printf '%s' "$CMD_DISPATCH" | awk '{print $NF}')"
        # Skip when the trailing token is a flag (e.g. `cat -n -- file` with the
        # file in the middle; not worth parsing). Let native Bash handle it.
        case "$FILE_ARG" in -*) exit 0 ;; esac
        _is_binary "$FILE_ARG" && exit 0
        REL="$(path_to_project_relative "$FILE_ARG" "$CWD")"
        [ -n "$REL" ] || exit 0
        block "retry as mcp__${JB_PREFIX}__read_file with pathInProject=\"$REL\" — this redirect is expected."
        ;;

      'ls'|'ls '*)
        # Parse args left-to-right for the first non-flag token.
        ARG="."
        _skip_next=0
        set -- $CMD_DISPATCH
        shift  # drop 'ls' (CMD_DISPATCH already has any env-var prefix peeled)
        for token in "$@"; do
          if [ "$_skip_next" = "1" ]; then
            _skip_next=0
            continue
          fi
          case "$token" in
            --) continue ;;
            # Flags that take a value (rare for ls, but safe to list).
            --color|--format|--time|--sort) _skip_next=1; continue ;;
            -*) continue ;;
            *) ARG="$token"; break ;;
          esac
        done
        REL="$(path_to_project_relative "$ARG" "$CWD")"
        [ -n "$REL" ] || exit 0
        block "retry as mcp__${JB_PREFIX}__list_directory_tree with directoryPath=\"$REL\" — this redirect is expected."
        ;;

      'grep '*|'rg '*|'egrep '*|'fgrep '*)
        block "retry as mcp__${JB_PREFIX}__search_text (literal) or mcp__${JB_PREFIX}__search_regex (regex) — this redirect is expected."
        ;;

      'find '*)
        # Only redirect when the expression is a simple name lookup with no
        # other predicates. Anything richer (type/time/or/exec/etc.) stays
        # on native find — WebStorm's find_files_by_name_keyword can't model
        # those semantics.
        case "$CMD_DISPATCH" in
          *' -name '*|*' -iname '*)
            case "$CMD_DISPATCH" in
              *' -exec '*|*' -execdir '*|*' -delete'*|*' -prune'*|*' -not '*| \
              *' -type '*|*' -mtime '*|*' -atime '*|*' -ctime '*| \
              *' -or '*|*' -o '*|*' -and '*|*' -a '*| \
              *' -mindepth '*|*' -maxdepth '*|*' -path '*|*' -ipath '*| \
              *' -newer '*|*' -size '*|*' -empty'*| \
              *' -regex '*|*' -iregex '*| \
              *' -user '*|*' -group '*|*' -uid '*|*' -gid '*|*' -perm '*| \
              *' -print0'*|*' -fprint '*)
                exit 0
                ;;
              *)
                block "retry as mcp__${JB_PREFIX}__find_files_by_name_keyword or mcp__${JB_PREFIX}__find_files_by_glob — this redirect is expected."
                ;;
            esac
            ;;
          *)
            exit 0
            ;;
        esac
        ;;

      *)
        exit 0
        ;;
    esac
    ;;

  *)
    exit 0
    ;;
esac