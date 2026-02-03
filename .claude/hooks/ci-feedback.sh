#!/bin/bash
# PostToolUse hook: Captures CI feedback from test/lint/build commands
# and injects actionable context back to Claude for autonomous fixing

set -euo pipefail

# Read the hook input (JSON with tool_input and tool_response)
INPUT=$(cat)

# Extract command and output
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
STDOUT=$(echo "$INPUT" | jq -r '.tool_response.stdout // empty')
STDERR=$(echo "$INPUT" | jq -r '.tool_response.stderr // empty')
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0')

# Only process CI-related commands (test, lint, check, build, typecheck)
if ! [[ "$COMMAND" =~ (test|lint|check|build|typecheck|tsc|eslint|prettier|jest|vitest|pytest|ruff|mypy) ]]; then
    exit 0
fi

# Combine stdout and stderr for analysis
FULL_OUTPUT="${STDOUT}${STDERR}"

# Check for failures
if [[ "$EXIT_CODE" != "0" ]] || echo "$FULL_OUTPUT" | grep -qiE "(fail|error|exception|ERR!|ENOENT|TypeError|SyntaxError)"; then
    # Extract relevant error lines (limit to prevent huge context)
    ERROR_SUMMARY=$(echo "$FULL_OUTPUT" | grep -iE "(fail|error|exception|ERR!|ENOENT|TypeError|SyntaxError|expected|actual|at line|:[0-9]+:)" | head -30)

    # Escape for JSON
    ERROR_SUMMARY_ESCAPED=$(echo "$ERROR_SUMMARY" | jq -Rs '.')

    # Return feedback to Claude
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "CI command failed or has errors. Here are the key issues to fix:\n\n${ERROR_SUMMARY_ESCAPED}\n\nPlease address these issues before continuing."
  }
}
EOF
    exit 0
fi

# Success case - optionally provide positive confirmation
if echo "$FULL_OUTPUT" | grep -qiE "(passed|success|ok|complete)"; then
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "CI check passed successfully."
  }
}
EOF
fi

exit 0
