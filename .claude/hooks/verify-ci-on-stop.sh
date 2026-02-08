#!/bin/bash
# Stop hook: Verifies CI checks pass before allowing Claude to complete
# Returns decision=block with reason to make Claude continue fixing issues
# Tracks retry attempts and gives up after MAX_STOP_RETRIES to prevent infinite token burn

set -uo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib-checks.sh
source "$HOOK_DIR/lib-checks.sh"

#######################################
# Retry tracking
#######################################

MAX_STOP_RETRIES="${MAX_STOP_RETRIES:-3}"

# Session-stable file keyed on the project directory
RETRY_FILE="/tmp/claude-stop-attempts-$(echo "$PROJECT_DIR" | md5sum | cut -d' ' -f1)"

attempt=1
if [[ -f "$RETRY_FILE" ]]; then
  attempt=$(( $(cat "$RETRY_FILE") + 1 ))
fi
echo "$attempt" > "$RETRY_FILE"

#######################################
# Run checks
#######################################

FAILURES=""
OUTPUT=""

run_check() {
  local name="$1" cmd="$2"
  echo "Running $name..." >&2
  local result
  if result=$($cmd 2>&1); then
    return 0
  else
    FAILURES="${FAILURES}$name failed. "
    OUTPUT="${OUTPUT}=== $name ===\n${result}\n\n"
    return 1
  fi
}

# Node.js checks
has_script test && run_check "tests" "pnpm test"
has_script lint && run_check "lint" "pnpm lint"
has_script check && run_check "typecheck" "pnpm check"

# Python checks (use uv run if uv.lock exists)
if [[ -f pyproject.toml ]] || [[ -f uv.lock ]]; then
  PREFIX=""
  [[ -f uv.lock ]] && exists uv && PREFIX="uv run "

  { exists ruff || [[ -n "$PREFIX" ]]; } && run_check "ruff" "${PREFIX}ruff check ."
  [[ -d tests ]] && { exists pytest || [[ -n "$PREFIX" ]]; } && run_check "pytest" "${PREFIX}pytest"
fi

#######################################
# Return result with retry limit
#######################################

if [[ -z "$FAILURES" ]]; then
  # All checks passed — clean up retry tracker
  rm -f "$RETRY_FILE"
  echo '{"decision":"approve"}'
elif [[ "$attempt" -ge "$MAX_STOP_RETRIES" ]]; then
  # Exhausted retries — approve to prevent infinite token burn, but warn
  rm -f "$RETRY_FILE"
  echo "WARNING: Giving up after $attempt attempts. Failures remain: $FAILURES" >&2
  jq -n --arg f "$FAILURES" --arg a "$attempt" \
    '{decision:"approve", reason:("Approved despite failures after "+$a+" attempts. Remaining: "+$f+"\nHuman review needed.")}'
else
  jq -n --arg f "$FAILURES" --arg o "$OUTPUT" --arg a "$attempt" --arg m "$MAX_STOP_RETRIES" \
    '{decision:"block", reason:("CI failed (attempt "+$a+"/"+$m+"): "+$f+"\n\n"+$o)}'
fi
