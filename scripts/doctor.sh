#!/usr/bin/env bash
set -euo pipefail

passes=0
warnings=0
errors=0

pass() {
  echo "  [OK]   $1"
  passes=$((passes + 1))
}

warn() {
  echo "  [WARN] $1"
  warnings=$((warnings + 1))
}

fail() {
  echo "  [FAIL] $1"
  errors=$((errors + 1))
}

echo "Running doctor checks..."
echo ""

# 1. Git hooks installed
echo "Checking git hooks configuration..."
hooks_path=$(git config core.hooksPath 2>/dev/null || true)
if [ "$hooks_path" = ".hooks" ]; then
  pass "Git hooks path is set to .hooks"
else
  fail "Git hooks path is '${hooks_path:-unset}', expected '.hooks'"
fi

# 2. All hook scripts executable
echo "Checking hook script permissions..."
all_executable=true
for f in .hooks/*; do
  [ -f "$f" ] || continue
  if [ ! -x "$f" ]; then
    fail "$f is not executable"
    all_executable=false
  fi
done
if [ "$all_executable" = true ]; then
  pass "All .hooks/ scripts are executable"
fi

# 3. Claude hook scripts exist
echo "Checking Claude hook script paths..."
claude_hooks_ok=true
if [ -f .claude/settings.json ]; then
  # Extract command strings from settings.json using jq
  commands=$(jq -r '.. | objects | select(.command?) | .command' .claude/settings.json 2>/dev/null || true)
  while IFS= read -r cmd; do
    [ -z "$cmd" ] && continue
    # Resolve $CLAUDE_PROJECT_DIR to . and strip quotes
    resolved=$(echo "$cmd" | sed 's|"\$CLAUDE_PROJECT_DIR"/\?|./|g; s|"||g; s|\$CLAUDE_PROJECT_DIR/\?|./|g')
    # Extract file paths that reference hook scripts
    read -ra tokens <<<"$resolved"
    for token in "${tokens[@]}"; do
      case "$token" in
      ./.claude/hooks/* | ./.hooks/*)
        if [ -f "$token" ]; then
          pass "Hook script exists: $token"
        else
          fail "Hook script missing: $token"
          claude_hooks_ok=false
        fi
        ;;
      esac
    done
  done <<<"$commands"
else
  warn ".claude/settings.json not found"
fi

# 4. Required tools available
echo "Checking required tools..."
required_tools="pnpm prettier commitlint jq gh"
optional_tools="shfmt shellcheck ruff uv"

for tool in $required_tools; do
  # Check node_modules/.bin for Node tools
  if [ -x "node_modules/.bin/$tool" ]; then
    pass "$tool available (node_modules)"
  elif command -v "$tool" >/dev/null 2>&1; then
    pass "$tool available"
  else
    fail "$tool not found"
  fi
done

for tool in $optional_tools; do
  if command -v "$tool" >/dev/null 2>&1; then
    pass "$tool available"
  else
    warn "$tool not found (optional)"
  fi
done

# 5. Node dependencies installed
echo "Checking Node dependencies..."
for dep in lint-staged commitlint; do
  if [ -x "node_modules/.bin/$dep" ]; then
    pass "node_modules/.bin/$dep exists"
  else
    fail "node_modules/.bin/$dep missing — run pnpm install"
  fi
done

# 6. package.json scripts configured
echo "Checking package.json scripts..."
configured=0
for script in test lint check; do
  value=$(jq -r ".scripts[\"$script\"] // empty" package.json 2>/dev/null || true)
  if [ -n "$value" ] && ! echo "$value" | grep -q "ERROR: Configure"; then
    pass "Script '$script' is configured"
    configured=$((configured + 1))
  fi
done
if [ "$configured" -eq 0 ]; then
  warn "None of test/lint/check scripts are configured — stop hook provides no protection"
fi

# 7. Workflow name consistency
echo "Checking workflow name consistency..."
if [ -f .github/workflows/comment-on-failed-checks.yaml ]; then
  # Extract workflow names, stripping inline YAML comments (e.g. - "Name" # path)
  wf_names=$(sed -n '/workflows:/,/types:/{/^[[:space:]]*- /{ /^[[:space:]]*#/!{ s/^[[:space:]]*-[[:space:]]*//; s/"[[:space:]]*#.*$/"/; s/'"'"'[[:space:]]*#.*$/'"'"'/; s/^"//; s/"$//; s/'"'"'//g; p; }}}' .github/workflows/comment-on-failed-checks.yaml)
  while IFS= read -r wf_name; do
    [ -z "$wf_name" ] && continue
    found=false
    for wf_file in .github/workflows/*.yaml .github/workflows/*.yml; do
      [ -f "$wf_file" ] || continue
      file_name=$(grep -m1 '^name:' "$wf_file" 2>/dev/null | sed 's/^name:\s*//; s/^"//; s/"$//; s/^'"'"'//; s/'"'"'$//' || true)
      if [ "$file_name" = "$wf_name" ]; then
        found=true
        break
      fi
    done
    if [ "$found" = true ]; then
      pass "Workflow '$wf_name' found"
    else
      warn "Workflow '$wf_name' listed in comment-on-failed-checks.yaml but not found in any workflow file"
    fi
  done <<<"$wf_names"
else
  warn "comment-on-failed-checks.yaml not found"
fi

# 8. GH_TOKEN set
echo "Checking environment..."
if [ -n "${GH_TOKEN:-}" ]; then
  pass "GH_TOKEN is set"
else
  warn "GH_TOKEN is not set"
fi

# Summary
echo ""
echo "---"
echo "$passes checks passed, $warnings warnings, $errors errors"

if [ "$errors" -gt 0 ]; then
  exit 1
fi
