#!/usr/bin/env bash
# kairoi schema validator.
#
# Rejects malformed JSON before it enters .kairoi/ state. Mechanical gate
# against agent-authored schema drift — receipts with `commit` instead of
# `commit_hash`, `__PENDING__` placeholder hashes, guards with `id`
# instead of `source_task`, etc.
#
# Usage:
#   validate-schema.sh <schema-name> [file-path]
#
# Reads JSON from <file-path> if given, else from stdin. For JSONL files
# (receipts.jsonl, buffer.jsonl), call once per line.
#
# Exit codes:
#   0 — valid
#   1 — invalid (each error on stderr prefixed with "  - ")
#   2 — usage error (unknown schema, jq missing, file unreadable)
#
# Supported schemas:
#   receipt         — one line of receipts.jsonl
#   buffer-entry    — one line of buffer.jsonl
#   reflect-result  — .kairoi/.reflect-result-<mod>.json contents

set -euo pipefail

command -v jq &>/dev/null || { echo "kairoi validate-schema: jq required" >&2; exit 2; }

SCHEMA="${1:-}"
FILE="${2:-/dev/stdin}"

[ -n "$SCHEMA" ] || { echo "usage: validate-schema.sh <schema> [file]" >&2; exit 2; }

if [ "$FILE" = "/dev/stdin" ]; then
  INPUT="$(cat)"
else
  [ -f "$FILE" ] || { echo "kairoi validate-schema: file not found: $FILE" >&2; exit 2; }
  INPUT="$(cat "$FILE")"
fi

# JSON parse-check first. Structural garbage gets rejected immediately.
if ! echo "$INPUT" | jq empty 2>/dev/null; then
  echo "kairoi validate-schema: invalid JSON" >&2
  exit 1
fi

# Each validator returns an array of error strings; empty = valid.
# Schemas intentionally validate what readers actually consume — fields
# the readers don't look at don't gate validation. Keeps this loose enough
# that future field additions don't force simultaneous validator updates.
VALIDATORS='
def err_receipt:
  . as $r |
  [
    (if has("task_id") | not then "missing: task_id" else empty end),
    (if has("timestamp") | not then "missing: timestamp" else empty end),
    (if has("status") | not then "missing: status" else empty end),
    (if has("modules_affected") | not then "missing: modules_affected" else empty end),
    (if has("modified_files") | not then "missing: modified_files" else empty end),
    (if has("commit_hash") | not then "missing: commit_hash" else empty end),
    (if has("guards_fired") | not then "missing: guards_fired" else empty end),
    (if has("guards_disputed") | not then "missing: guards_disputed" else empty end),
    (if has("blocked_diagnostics") | not then "missing: blocked_diagnostics" else empty end),
    (if has("task_id") and (($r.task_id | type) != "string" or $r.task_id == "") then "task_id must be non-empty string" else empty end),
    (if has("timestamp") and ($r.timestamp | type) != "string" then "timestamp must be string" else empty end),
    (if has("status") and ($r.status != "SUCCESS" and $r.status != "BLOCKED") then "status must be SUCCESS or BLOCKED (got: \($r.status))" else empty end),
    (if has("modules_affected") and ($r.modules_affected | type) != "array" then "modules_affected must be array" else empty end),
    (if has("modified_files") and ($r.modified_files | type) != "array" then "modified_files must be array" else empty end),
    (if has("commit_hash") and ($r.commit_hash != null) and ($r.commit_hash | type) != "string" then "commit_hash must be string or null" else empty end),
    (if has("commit_hash") and ($r.commit_hash != null) and ($r.commit_hash | type) == "string" and ($r.commit_hash | test("__PENDING__")) then "commit_hash contains placeholder __PENDING__ (agent failed to resolve hash)" else empty end),
    (if has("guards_fired") and ($r.guards_fired | type) != "array" then "guards_fired must be array" else empty end),
    (if has("guards_disputed") and ($r.guards_disputed | type) != "array" then "guards_disputed must be array" else empty end),
    (if has("blocked_diagnostics") and ($r.blocked_diagnostics != null) and ($r.blocked_diagnostics | type) != "string" then "blocked_diagnostics must be string or null" else empty end),
    (if has("test_results") and ($r.test_results != null) and ($r.test_results | type) != "object" then "test_results must be object or null" else empty end)
  ] | map(select(. != null and type == "string" and length > 0))
;

def err_buffer_entry:
  . as $b |
  [
    (if has("task_id") | not then "missing: task_id" else empty end),
    (if has("timestamp") | not then "missing: timestamp" else empty end),
    (if has("status") | not then "missing: status" else empty end),
    (if has("summary") | not then "missing: summary" else empty end),
    (if has("modules_affected") | not then "missing: modules_affected" else empty end),
    (if has("modified_files") | not then "missing: modified_files" else empty end),
    (if has("commit_hash") | not then "missing: commit_hash" else empty end),
    (if has("guards_fired") | not then "missing: guards_fired" else empty end),
    (if has("guards_disputed") | not then "missing: guards_disputed" else empty end),
    (if has("task_id") and (($b.task_id | type) != "string" or $b.task_id == "") then "task_id must be non-empty string" else empty end),
    (if has("status") and ($b.status != "SUCCESS" and $b.status != "BLOCKED") then "status must be SUCCESS or BLOCKED" else empty end),
    (if has("summary") and ($b.summary | type) != "string" then "summary must be string" else empty end),
    (if has("commit_hash") and (($b.commit_hash | type) != "string" or $b.commit_hash == "") then "commit_hash must be non-empty string" else empty end),
    (if has("commit_hash") and ($b.commit_hash | type) == "string" and ($b.commit_hash | test("__PENDING__")) then "commit_hash contains placeholder __PENDING__ (auto-buffer failed to resolve hash)" else empty end),
    (if has("test_results") and ($b.test_results != null) and ($b.test_results | type) != "object" then "test_results must be object or null" else empty end)
  ] | map(select(. != null and type == "string" and length > 0))
;

# Reflect-result is loose by design — what the agent writes beyond the
# basic shape is free-form and consumed by reflection logic that tolerates
# unexpected fields. The validator only asserts types on fields that
# sync-finalize actually reads.
def err_reflect_result:
  . as $r |
  [
    (if has("guards_created") and ($r.guards_created | type) != "array" then "guards_created must be array" else empty end),
    (if has("semantic_edges") and ($r.semantic_edges | type) != "array" then "semantic_edges must be array" else empty end)
  ] | map(select(. != null and type == "string" and length > 0))
;

if $schema == "receipt" then err_receipt
elif $schema == "buffer-entry" then err_buffer_entry
elif $schema == "reflect-result" then err_reflect_result
else null
end
'

RESULT="$(echo "$INPUT" | jq --arg schema "$SCHEMA" "$VALIDATORS" 2>&1)"
JQ_RC=$?

if [ "$JQ_RC" -ne 0 ]; then
  echo "kairoi validate-schema: jq internal error:" >&2
  echo "$RESULT" | sed 's/^/  /' >&2
  exit 2
fi

if [ "$RESULT" = "null" ]; then
  echo "kairoi validate-schema: unknown schema '$SCHEMA'" >&2
  echo "  valid schemas: receipt, buffer-entry, reflect-result" >&2
  exit 2
fi

ERROR_COUNT="$(echo "$RESULT" | jq 'length')"

if [ "$ERROR_COUNT" -gt 0 ]; then
  echo "kairoi: schema validation failed for '$SCHEMA':" >&2
  echo "$RESULT" | jq -r '.[]' | sed 's/^/  - /' >&2
  exit 1
fi

exit 0
