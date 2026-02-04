#!/bin/bash
# Stop hook: Verifies CI checks pass before allowing Claude to complete
# Returns decision=block with reason to make Claude continue fixing issues

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR" || exit 1

# Track failures with actual error output
FAILURES=""
ERROR_DETAILS=""

# Helper: Check if a script is configured (not a placeholder)
script_configured() {
    local script_name="$1"
    if ! jq -e ".scripts.${script_name}" package.json >/dev/null 2>&1; then
        return 1
    fi
    local script_content
    script_content=$(jq -r ".scripts.${script_name}" package.json)
    [[ "$script_content" != "null" && "$script_content" != *"ERROR: Configure"* ]]
}

# Check if package.json exists and has relevant scripts
if [[ -f "package.json" ]]; then
    # Check for test script
    if script_configured "test"; then
        echo "Running tests..." >&2
        TEST_OUTPUT=$(pnpm test 2>&1) || {
            FAILURES="${FAILURES}Tests failed. "
            # Extract key error lines
            ERROR_DETAILS="${ERROR_DETAILS}TEST ERRORS:\n$(echo "$TEST_OUTPUT" | grep -iE "(FAIL|ERROR|expected|actual|✕)" | head -15)\n\n"
        }
    fi

    # Check for lint script
    if script_configured "lint"; then
        echo "Running linter..." >&2
        LINT_OUTPUT=$(pnpm lint 2>&1) || {
            FAILURES="${FAILURES}Linting failed. "
            ERROR_DETAILS="${ERROR_DETAILS}LINT ERRORS:\n$(echo "$LINT_OUTPUT" | grep -iE "(error|warning|✕)" | head -15)\n\n"
        }
    fi

    # Check for typecheck/check script
    if script_configured "check"; then
        echo "Running type check..." >&2
        CHECK_OUTPUT=$(pnpm check 2>&1) || {
            FAILURES="${FAILURES}Type checking failed. "
            ERROR_DETAILS="${ERROR_DETAILS}TYPE ERRORS:\n$(echo "$CHECK_OUTPUT" | grep -iE "(error|TS[0-9]+)" | head -15)\n\n"
        }
    fi
fi

# Check for Python project
if [[ -f "pyproject.toml" ]] || [[ -f "uv.lock" ]]; then
    # Use uv run if uv.lock exists, otherwise run directly
    RUN_PREFIX=""
    if [[ -f "uv.lock" ]] && command -v uv &>/dev/null; then
        RUN_PREFIX="uv run "
    fi

    # Run ruff if available
    if command -v ruff &>/dev/null || [[ -n "$RUN_PREFIX" ]]; then
        echo "Running ruff..." >&2
        RUFF_OUTPUT=$(${RUN_PREFIX}ruff check . 2>&1) || {
            FAILURES="${FAILURES}Ruff linting failed. "
            ERROR_DETAILS="${ERROR_DETAILS}RUFF ERRORS:\n$(echo "$RUFF_OUTPUT" | head -15)\n\n"
        }
    fi

    # Run pytest if tests directory exists
    if [[ -d "tests" ]] && { command -v pytest &>/dev/null || [[ -n "$RUN_PREFIX" ]]; }; then
        echo "Running pytest..." >&2
        PYTEST_OUTPUT=$(${RUN_PREFIX}pytest 2>&1) || {
            FAILURES="${FAILURES}Pytest failed. "
            ERROR_DETAILS="${ERROR_DETAILS}PYTEST ERRORS:\n$(echo "$PYTEST_OUTPUT" | grep -iE "(FAILED|ERROR|assert)" | head -15)\n\n"
        }
    fi
fi

# Return result using jq for proper JSON escaping
if [[ -n "$FAILURES" ]]; then
    jq -n \
        --arg failures "$FAILURES" \
        --arg details "$ERROR_DETAILS" \
        '{
            decision: "block",
            reason: ("CI checks failed: " + $failures + "\n\nDetails:\n" + $details + "\nFix these issues before completing.")
        }'
    exit 0
fi

# All checks passed
echo '{"decision": "approve"}'
exit 0
