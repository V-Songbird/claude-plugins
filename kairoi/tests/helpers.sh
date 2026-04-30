#!/usr/bin/env bash
# Shared test helpers. Sourced by test_*.sh files.
#
# Requires env vars set by run.sh:
#   KAIROI_TEST_PLUGIN_ROOT — path to kairoi/ root
#
# Each test function returns 0 on pass, non-zero on fail. Test scripts exit 1
# on first failure (no suite-level framework).

# --- Assertions -------------------------------------------------------------

# Assert `jq -r <expr> <file>` returns <expected>.
assert_jq() {
  local file="$1"
  local expr="$2"
  local expected="$3"
  local actual
  actual="$(jq -r "$expr" "$file" 2>/dev/null)"
  if [ "$actual" != "$expected" ]; then
    echo "assert_jq FAILED: $file '$expr'"
    echo "  expected: $expected"
    echo "  actual:   $actual"
    return 1
  fi
  return 0
}

# Assert <file> contains <needle> as a literal substring.
assert_contains() {
  local file="$1"
  local needle="$2"
  if [ ! -f "$file" ]; then
    echo "assert_contains FAILED: $file does not exist"
    return 1
  fi
  if ! grep -qF "$needle" "$file" 2>/dev/null; then
    echo "assert_contains FAILED: '$needle' not in $file"
    echo "  file contents:"
    sed 's/^/    /' "$file"
    return 1
  fi
  return 0
}

# Assert <file> exists but is empty (or does not exist).
assert_empty_or_missing() {
  local file="$1"
  if [ -f "$file" ] && [ -s "$file" ]; then
    echo "assert_empty_or_missing FAILED: $file exists and is non-empty"
    sed 's/^/    /' "$file"
    return 1
  fi
  return 0
}

# Assert <file> has exactly <n> non-empty lines.
assert_line_count() {
  local file="$1"
  local expected="$2"
  if [ ! -f "$file" ]; then
    if [ "$expected" = "0" ]; then
      return 0
    fi
    echo "assert_line_count FAILED: $file does not exist (expected $expected lines)"
    return 1
  fi
  local actual
  actual="$(grep -c . "$file" 2>/dev/null || echo 0)"
  if [ "$actual" != "$expected" ]; then
    echo "assert_line_count FAILED: $file"
    echo "  expected: $expected lines"
    echo "  actual:   $actual lines"
    return 1
  fi
  return 0
}

# --- Fixture setup ----------------------------------------------------------

# Create a minimal .kairoi/ state with one module.
# Usage: setup_kairoi_state <module_id> [purpose] [tasks_since_validation]
setup_kairoi_state() {
  local module="${1:-auth}"
  local purpose="${2:-Authentication module}"
  local tsv="${3:-0}"

  mkdir -p .kairoi/model

  jq -n --arg mod "$module" --arg path "src/$module/" '{
    source_dirs: ["src/"],
    modules: { ($mod): { source_paths: [$path] } },
    edges: []
  }' > .kairoi/model/_index.json

  # confidence is NOT persisted — readers derive it from churn_since_validation.
  # Seed churn = tsv (simulates 1 file-touch per historical task, matching
  # buffer_append_raw's default modified_files=[src/module/file.ts]).
  jq -n --arg purpose "$purpose" --argjson tsv "$tsv" --arg ep "src/auth/index.ts" '{
    purpose: $purpose,
    entry_points: [$ep],
    guards: [],
    known_patterns: [],
    negative_invariants: [],
    dependencies: [],
    _meta: {
      last_validated: "2026-04-01",
      tasks_since_validation: $tsv,
      churn_since_validation: $tsv
    }
  }' > ".kairoi/model/$module.json"

  : > .kairoi/buffer.jsonl
  : > .kairoi/receipts.jsonl

  jq -n '{
    kairoi_version: "1.0.0-alpha",
    stack: "test",
    test: "",
    source_dirs: ["src/"],
    test_dirs: [],
    exclude_dirs: [],
    edge_prune_min_weight: 2,
    edge_prune_max_age_days: 30
  }' > .kairoi/build-adapter.json
}

# Add a guard to a module file.
# Usage: add_guard <module> <source_task> <check> <trigger_files_csv>
add_guard() {
  local module="$1"
  local source_task="$2"
  local check="$3"
  local triggers_csv="$4"

  local trigger_json
  trigger_json="$(echo "$triggers_csv" | tr ',' '\n' | jq -R . | jq -s .)"

  local file=".kairoi/model/$module.json"
  local tmp="$file.tmp"
  jq --arg st "$source_task" \
     --arg ck "$check" \
     --argjson tf "$trigger_json" \
     --arg today "$(date -u +%Y-%m-%d)" \
     '.guards += [{
       trigger_files: $tf,
       check: $ck,
       rationale: null,
       source_task: $st,
       created: $today,
       confirmed: 0,
       disputed: 0
     }]' "$file" > "$tmp" && mv "$tmp" "$file"
}

# Initialize a git repo in the current directory with a test identity.
init_git_repo() {
  git init -q 2>/dev/null
  git config user.email "test@kairoi.local"
  git config user.name "kairoi-test"
  git config commit.gpgsign false 2>/dev/null || true
}

# Create a file and commit it. Dependency on init_git_repo having run.
# Usage: commit_file <relative_path> <content> <commit_message>
commit_file() {
  local path="$1"
  local content="$2"
  local msg="$3"
  mkdir -p "$(dirname "$path")" 2>/dev/null || true
  printf '%s\n' "$content" > "$path"
  git add "$path" 2>/dev/null
  git commit -q -m "$msg" 2>/dev/null
}

# Append a task entry to buffer.jsonl directly (skipping buffer-append).
# Usage: buffer_append_raw <task_id> <status> <module> [modified_file]
# Uses jq -c for compact JSONL format — one object per line.
buffer_append_raw() {
  local task_id="$1"
  local status="$2"
  local module="$3"
  local modified="${4:-src/$module/file.ts}"

  jq -n -c --arg task "$task_id" --arg status "$status" --arg mod "$module" \
        --arg mf "$modified" --arg ts "2026-04-01T00:00:00Z" '{
    task_id: $task,
    timestamp: $ts,
    status: $status,
    summary: "test task",
    modules_affected: [$mod],
    modified_files: [$mf],
    test_results: null,
    commit_hash: "abc1234",
    guards_fired: [],
    guards_disputed: [],
    blocked_diagnostics: null
  }' >> .kairoi/buffer.jsonl
}
