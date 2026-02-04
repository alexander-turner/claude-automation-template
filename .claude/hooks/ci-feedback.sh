#!/bin/bash
# PostToolUse hook: Captures CI feedback from test/lint/build commands
# and injects actionable context back to Claude for autonomous fixing

set -uo pipefail

# Read the hook input (JSON with tool_input and tool_response)
INPUT=$(cat)

# Extract command and output
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
STDOUT=$(echo "$INPUT" | jq -r '.tool_response.stdout // empty')
STDERR=$(echo "$INPUT" | jq -r '.tool_response.stderr // empty')
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0')

# Only process CI-related commands - match at word boundaries or start of command
# Matches: "pnpm test", "npm run lint", "pytest", etc.
# Avoids: "echo test", "cat jest.config.js"
if ! [[ "$COMMAND" =~ ^[[:space:]]*(pnpm|npm|yarn|npx|node|python|pytest|ruff|mypy|tsc|eslint|prettier|jest|vitest)[[:space:]] ]] \
   && ! [[ "$COMMAND" =~ (pnpm|npm|yarn)[[:space:]]+(run[[:space:]]+)?(test|lint|check|build|typecheck) ]]; then
    exit 0
fi

# Combine stdout and stderr for analysis
FULL_OUTPUT="${STDOUT}${STDERR}"

# Check for failures based on exit code
if [[ "$EXIT_CODE" != "0" ]]; then
    # Extract relevant error lines (limit to prevent huge context)
    ERROR_SUMMARY=$(echo "$FULL_OUTPUT" | grep -iE "(FAIL|ERROR|exception|ERR!|ENOENT|TypeError|SyntaxError|expected|actual|at line|:[0-9]+:[0-9]+)" | head -30)

    # Build proper JSON using jq
    jq -n \
        --arg errors "$ERROR_SUMMARY" \
        '{
            hookSpecificOutput: {
                hookEventName: "PostToolUse",
                additionalContext: ("CI command failed. Key issues:\n\n" + $errors + "\n\nFix these issues before continuing.")
            }
        }'
    exit 0
fi

# Success case - only report if output clearly indicates success
if echo "$FULL_OUTPUT" | grep -qE "(passed|PASS|✓|success|succeeded|0 errors|0 failures)"; then
    echo '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"CI check passed."}}'
fi

exit 0
