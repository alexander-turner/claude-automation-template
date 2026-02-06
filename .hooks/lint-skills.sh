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
# Note: lint-staged only passes top-level .claude/skills/*.md files, but the
# directory check below also handles manual invocation with resource paths.
#
# Usage: lint-skills.sh [files...]

set -euo pipefail

errors=0

for file in "$@"; do
  # Skip if not a top-level skills file (resource files don't need frontmatter)
  [[ "$file" != *".claude/skills/"* ]] && continue
  dirname=$(basename "$(dirname "$file")")
  [[ "$dirname" != "skills" ]] && continue

  # Check for YAML frontmatter
  if ! head -1 "$file" | grep -q '^---$'; then
    echo "ERROR: $file missing YAML frontmatter (must start with ---)" >&2
    errors=$((errors + 1))
    continue
  fi

  # Extract frontmatter (between first and second ---), filtering YAML comments
  frontmatter=$(awk '/^---$/{n++; next} n==1' "$file" | grep -v '^#')

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

  # Check description is multi-sentence (at least 2 periods)
  # Extract description from frontmatter only (not body content)
  desc_block=$(awk '/^---$/{n++; next} n==1' "$file" | sed -n '/^description:/,/^[a-z]/p')
  period_count=$(echo "$desc_block" | grep -o '\.' | wc -l)
  if [ "$period_count" -lt 2 ]; then
    echo "ERROR: $file description too short — use 2-3 sentences with specific activation triggers" >&2
    errors=$((errors + 1))
  fi

  # Check body has an Examples section (real examples prevent generic output)
  body=$(awk '/^---$/{n++; next} n>=2' "$file")
  if ! echo "$body" | grep -q '^## Examples'; then
    echo "ERROR: $file missing '## Examples' section — add 2-3 real input/output examples" >&2
    errors=$((errors + 1))
  fi
done

[ "$errors" -gt 0 ] && exit 1 || exit 0
