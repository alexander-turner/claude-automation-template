#!/bin/bash
# Stop hook: Verifies CI checks pass before allowing Claude to complete
# Returns ok=false with reason to make Claude continue fixing issues

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

# Track failures
FAILURES=""

# Check if package.json exists and has relevant scripts
if [[ -f "package.json" ]]; then
    # Check for test script
    if jq -e '.scripts.test' package.json >/dev/null 2>&1; then
        TEST_SCRIPT=$(jq -r '.scripts.test' package.json)
        if [[ "$TEST_SCRIPT" != "null" && "$TEST_SCRIPT" != *"configure"* ]]; then
            echo "Running tests..." >&2
            if ! pnpm test 2>&1; then
                FAILURES="${FAILURES}Tests failed. "
            fi
        fi
    fi

    # Check for lint script
    if jq -e '.scripts.lint' package.json >/dev/null 2>&1; then
        LINT_SCRIPT=$(jq -r '.scripts.lint' package.json)
        if [[ "$LINT_SCRIPT" != "null" && "$LINT_SCRIPT" != *"configure"* ]]; then
            echo "Running linter..." >&2
            if ! pnpm lint 2>&1; then
                FAILURES="${FAILURES}Linting failed. "
            fi
        fi
    fi

    # Check for typecheck/check script
    if jq -e '.scripts.check' package.json >/dev/null 2>&1; then
        CHECK_SCRIPT=$(jq -r '.scripts.check' package.json)
        if [[ "$CHECK_SCRIPT" != "null" && "$CHECK_SCRIPT" != *"configure"* ]]; then
            echo "Running type check..." >&2
            if ! pnpm check 2>&1; then
                FAILURES="${FAILURES}Type checking failed. "
            fi
        fi
    fi
fi

# Check for Python project
if [[ -f "pyproject.toml" ]] || [[ -f "uv.lock" ]]; then
    # Run ruff if available
    if command -v ruff &>/dev/null; then
        echo "Running ruff..." >&2
        if ! ruff check . 2>&1; then
            FAILURES="${FAILURES}Ruff linting failed. "
        fi
    fi

    # Run pytest if available
    if command -v pytest &>/dev/null && [[ -d "tests" ]]; then
        echo "Running pytest..." >&2
        if ! pytest 2>&1; then
            FAILURES="${FAILURES}Pytest failed. "
        fi
    fi
fi

# Return result
if [[ -n "$FAILURES" ]]; then
    cat <<EOF
{
  "decision": "block",
  "reason": "CI checks failed: ${FAILURES}Please fix these issues before completing."
}
EOF
    exit 0
fi

# All checks passed
cat <<EOF
{
  "decision": "approve"
}
EOF
exit 0
