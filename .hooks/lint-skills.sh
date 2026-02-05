#!/bin/bash
# Validates Claude Code skills have required structure per best practices.
# Based on analysis of common skills failures:
#   https://cashandcache.substack.com/p/i-analyzed-40-claude-skills-failures
#
# Checks enforced:
#   1. YAML frontmatter present (starts with ---)
#   2. name: field in frontmatter (descriptive identifier)
#   3. description: field in frontmatter (2+ sentences for activation context)
#   4. ## Examples section in body (real input/output pairs prevent generic output)
#
# Usage: lint-skills.sh [files...]

set -euo pipefail

errors=0

for file in "$@"; do
  # Skip if not a top-level skills file (resource files don't need frontmatter)
  [[ "$file" != *".claude/skills/"* ]] && continue
  basename=$(basename "$(dirname "$file")")
  [[ "$basename" != "skills" ]] && continue

  # Check for YAML frontmatter
  if ! head -1 "$file" | grep -q '^---$'; then
    echo "ERROR: $file missing YAML frontmatter (must start with ---)" >&2
    errors=$((errors + 1))
    continue
  fi

  # Extract content between first --- and second ---
  frontmatter=$(sed -n '1,/^---$/{ /^---$/d; p; }' "$file" | sed '1d')

  # Check frontmatter has name field
  if ! echo "$frontmatter" | grep -q '^name:'; then
    echo "ERROR: $file missing 'name:' in frontmatter" >&2
    errors=$((errors + 1))
  fi

  # Check frontmatter has description field
  if ! echo "$frontmatter" | grep -q '^description:'; then
    echo "ERROR: $file missing 'description:' in frontmatter" >&2
    errors=$((errors + 1))
  fi

  # Check description is multi-sentence (at least 2 periods in the description block)
  # Collapse the description value (may span multiple lines with YAML folding)
  desc_lines=$(sed -n '/^description:/,/^[a-z]/p' "$file" | head -20)
  period_count=$(echo "$desc_lines" | grep -o '\.' | wc -l)
  if [ "$period_count" -lt 2 ]; then
    echo "ERROR: $file description too short — use 2-3 sentences with specific activation triggers" >&2
    errors=$((errors + 1))
  fi

  # Check body has an Examples section (Fix 2: real examples prevent generic output)
  body=$(sed -n '/^---$/,$ p' "$file" | tail -n +2)
  if ! echo "$body" | grep -q '^## Examples'; then
    echo "ERROR: $file missing '## Examples' section — add 2-3 real input/output examples" >&2
    errors=$((errors + 1))
  fi
done

exit $errors
