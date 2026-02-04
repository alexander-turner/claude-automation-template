#!/bin/bash
# Async CI feedback hook: Runs checks in background after file edits
# Results are delivered on the next conversation turn
# Since this is async, it cannot block - only provide feedback

set -uo pipefail

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

# Collect feedback
FEEDBACK=""

case "$FILE_PATH" in
    *.ts|*.tsx|*.js|*.jsx)
        # TypeScript/JavaScript - run relevant checks
        if [[ -f "package.json" ]]; then
            # Run typecheck if available
            if script_configured "check"; then
                CHECK_OUTPUT=$(pnpm check 2>&1) || {
                    # Only capture actual errors, not "0 errors"
                    ERRORS=$(echo "$CHECK_OUTPUT" | grep -iE "(error TS|: error)" | head -10)
                    if [[ -n "$ERRORS" ]]; then
                        FEEDBACK="${FEEDBACK}Type errors:\n${ERRORS}\n\n"
                    fi
                }
            fi

            # Run lint if available
            if script_configured "lint"; then
                LINT_OUTPUT=$(pnpm lint 2>&1) || {
                    ERRORS=$(echo "$LINT_OUTPUT" | grep -iE "^\s*[0-9]+:[0-9]+\s+error|error:" | head -10)
                    if [[ -n "$ERRORS" ]]; then
                        FEEDBACK="${FEEDBACK}Lint errors:\n${ERRORS}\n\n"
                    fi
                }
            fi
        fi
        ;;

    *.py)
        # Python - run ruff if available
        if command -v ruff &>/dev/null; then
            RUFF_OUTPUT=$(ruff check "$FILE_PATH" 2>&1) || true
            # Ruff outputs nothing on success
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

# Return feedback if any issues found, using jq for proper JSON
if [[ -n "$FEEDBACK" ]]; then
    jq -n --arg feedback "$FEEDBACK" '{ additionalContext: $feedback }'
fi

exit 0
