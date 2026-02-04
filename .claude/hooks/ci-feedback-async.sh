#!/bin/bash
# Async CI feedback hook: Runs tests in background after file edits
# Results are delivered on the next conversation turn
# Since this is async, it cannot block - only provide feedback

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

# Read input from stdin
INPUT=$(cat)

# Get the file that was edited
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Skip if not a source file
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Determine what checks to run based on file type
FEEDBACK=""

case "$FILE_PATH" in
    *.ts|*.tsx|*.js|*.jsx)
        # TypeScript/JavaScript - run relevant checks
        if [[ -f "package.json" ]]; then
            # Run typecheck if available
            if jq -e '.scripts.check' package.json >/dev/null 2>&1; then
                CHECK_SCRIPT=$(jq -r '.scripts.check' package.json)
                if [[ "$CHECK_SCRIPT" != "null" && "$CHECK_SCRIPT" != *"configure"* ]]; then
                    CHECK_OUTPUT=$(pnpm check 2>&1) || true
                    if echo "$CHECK_OUTPUT" | grep -qi "error"; then
                        ERRORS=$(echo "$CHECK_OUTPUT" | grep -i "error" | head -10)
                        FEEDBACK="${FEEDBACK}Type errors detected:\n${ERRORS}\n\n"
                    fi
                fi
            fi

            # Run lint if available
            if jq -e '.scripts.lint' package.json >/dev/null 2>&1; then
                LINT_SCRIPT=$(jq -r '.scripts.lint' package.json)
                if [[ "$LINT_SCRIPT" != "null" && "$LINT_SCRIPT" != *"configure"* ]]; then
                    LINT_OUTPUT=$(pnpm lint 2>&1) || true
                    if echo "$LINT_OUTPUT" | grep -qi "error"; then
                        ERRORS=$(echo "$LINT_OUTPUT" | grep -i "error" | head -10)
                        FEEDBACK="${FEEDBACK}Lint errors detected:\n${ERRORS}\n\n"
                    fi
                fi
            fi
        fi
        ;;

    *.py)
        # Python - run ruff if available
        if command -v ruff &>/dev/null; then
            RUFF_OUTPUT=$(ruff check "$FILE_PATH" 2>&1) || true
            if [[ -n "$RUFF_OUTPUT" ]]; then
                FEEDBACK="${FEEDBACK}Ruff issues in ${FILE_PATH}:\n${RUFF_OUTPUT}\n\n"
            fi
        fi
        ;;

    *.sh)
        # Shell scripts - run shellcheck if available
        if command -v shellcheck &>/dev/null; then
            SC_OUTPUT=$(shellcheck "$FILE_PATH" 2>&1) || true
            if [[ -n "$SC_OUTPUT" ]]; then
                FEEDBACK="${FEEDBACK}ShellCheck issues in ${FILE_PATH}:\n${SC_OUTPUT}\n\n"
            fi
        fi
        ;;
esac

# Return feedback if any issues found
if [[ -n "$FEEDBACK" ]]; then
    # Escape for JSON
    ESCAPED_FEEDBACK=$(echo -e "$FEEDBACK" | jq -Rs .)
    cat <<EOF
{
  "additionalContext": ${ESCAPED_FEEDBACK}
}
EOF
fi

exit 0
