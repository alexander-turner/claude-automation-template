#!/bin/bash
# PreToolUse hook: hard-block bash antipatterns that silently swallow errors.
#
# Currently detects `|| true` (and the equivalent `|| :`), which mask failures
# and violate the "fail loudly" principle in CLAUDE.md. Exits 2 so Claude Code
# blocks the tool call and surfaces stderr back to the model.

set -uo pipefail

input=$(cat)

tool_name=$(echo "$input" | jq -r '.tool_name // ""')
[[ "$tool_name" != "Bash" ]] && exit 0

command=$(echo "$input" | jq -r '.tool_input.command // ""')
[[ -z "$command" ]] && exit 0

# Strip single- and double-quoted strings so literal occurrences inside
# arguments (e.g. `grep '|| true' file`) don't trip the check. Shell heredocs
# are not handled; prefer the Write/Edit tools when authoring scripts.
stripped=$(echo "$command" | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")

if echo "$stripped" | grep -qE '\|\|[[:space:]]*(true|:)([[:space:]]|;|\)|\||&|$)'; then
  cat >&2 <<'EOF'
BLOCKED: bash antipattern '|| true' detected.

This silently swallows errors and violates the "fail loudly" rule in CLAUDE.md.
Use one of these instead:

  - Check explicitly:    if ! cmd; then handle; fi
  - Capture exit code:   cmd; rc=$?; ...
  - Remove suppression:  let the error propagate

If suppression is genuinely required, explain it to the user and get
confirmation before running the command.
EOF
  exit 2
fi

exit 0
