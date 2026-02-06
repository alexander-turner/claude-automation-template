#!/bin/bash
# Pre-push/PR hook: Runs configured checks before pushing or creating PRs
# Only runs scripts that exist and are properly configured in package.json

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR" || exit 1

FAILED=0

# Helpers
exists() { command -v "$1" &>/dev/null; }

has_script() {
  [[ -f package.json ]] &&
    jq -e ".scripts.$1" package.json &>/dev/null &&
    ! jq -r ".scripts.$1" package.json | grep -q "ERROR: Configure"
}

run_check() {
  local name="$1" cmd="$2"
  echo "=== $name ===" >&2
  if ! $cmd 2>&1; then
    echo "$name FAILED" >&2
    FAILED=1
  fi
}

echo "=== PRE-PR CHECKS ===" >&2

# Node.js checks
has_script build && run_check "build" "pnpm build"
has_script lint && run_check "lint" "pnpm lint"
has_script check && run_check "typecheck" "pnpm check"

# Python checks
if [[ -f pyproject.toml ]] || [[ -f uv.lock ]]; then
  PREFIX=""
  [[ -f uv.lock ]] && exists uv && PREFIX="uv run "

  exists ruff || [[ -n "$PREFIX" ]] && run_check "ruff" "${PREFIX}ruff check ."
fi

exit $FAILED
