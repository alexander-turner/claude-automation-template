---
# prettier-ignore
name: update-pr
description: >
  Updates an existing pull request with new changes, commits, and optionally revises the PR description.
  Activate when the user asks to update, fix, or add to an existing PR.
  Also activate when the user says "update the PR", "fix the PR", "add this to the PR", or any variation of modifying an existing pull request.
---

# Update Pull Request Skill

## When to Use

Activate when the user says:

- "Update the PR"
- "Fix the PR based on feedback"
- "Add this to the PR"
- "Push these changes to the PR"
- "Update the PR description"

Do **NOT** use for:

- Creating a new PR (use `pr-creation` skill)
- Reviewing a PR (`gh pr view`)
- Merging a PR (`gh pr merge`)

## Workflow

### 1. Identify Current PR

```bash
# Get PR for current branch
gh pr view --json number,state,title,url
```

Verify the PR is **open**. If merged or closed, ask the user what to do.

### 2. Make Changes

Implement the requested updates following the user's instructions.

### 3. Commit Changes

Use conventional commits format (activate `/commit` skill if multiple files):

```bash
git add <files>
git commit -m "fix: address review feedback on validation"
```

### 4. Push Updates

```bash
git push
```

### 5. Update PR Description (Optional)

If changes significantly affect the PR scope or the user requests it:

```bash
gh pr edit --body "$(cat <<'EOF'
## Summary
Updated description...

## Changes in this update
- Fixed validation bug
- Added error handling

## Test plan
[...]
EOF
)"
```

### 6. Verify CI

```bash
gh pr checks --watch
```

If checks fail, fix the issues and repeat steps 3-6.

### 7. Report Result

Confirm the PR is updated and provide the URL.

## Examples

**User:** "Fix the type error in the PR"

**Actions:**

1. Run `gh pr view` → PR #42 is open
2. Fix the type error in `src/utils.ts`
3. Commit: `fix: correct return type in parseConfig`
4. Push: `git push`
5. Watch CI: `gh pr checks --watch` → all pass
6. Report: "Updated PR #42 with type fix: https://github.com/org/repo/pull/42"

## Error Handling

- **No PR for branch**: Ask if they want to create one (`/pr-creation`)
- **PR is merged**: Don't modify it; create a new PR if needed
- **Push fails**: Check branch protection rules
- **CI fails**: Fix issues and push again
