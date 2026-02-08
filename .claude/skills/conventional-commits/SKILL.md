---
# prettier-ignore
name: commit
description: >
  Creates well-structured git commits using Conventional Commits format.
  Activate this skill whenever the user asks to commit changes, make a commit, save progress,
  or says "commit this", "commit my changes", "/commit", or any variation of requesting a git commit.
  Also activate when task instructions say to commit when done.
---

# Conventional Commits Skill

**IMPORTANT: Always follow this skill when creating commits.** Do not skip steps—especially analyzing the diff and choosing the correct commit type.

## When to Use

Activate this skill when the user says any of the following (or similar):

- "Commit this" / "Commit my changes"
- "Make a commit"
- "Save my progress"
- "Commit what we have"
- "/commit"

Also activate when:

- You have completed a task and need to commit before creating a PR
- CLAUDE.md or task instructions say to commit when done

Do **NOT** use this skill for:

- Creating pull requests (use the `pr-creation` skill instead)
- Amending commits (just run `git commit --amend` directly)
- Interactive rebasing or squashing

## Prerequisites

- Changes must exist (staged or unstaged) — do not create empty commits
- The repository must use Conventional Commits (enforced by the `commit-msg` hook via commitlint)

## Workflow

### Step 1: Review Changes

Run these commands in parallel to understand the current state:

1. `git status` — see staged, unstaged, and untracked files
2. `git diff` — see unstaged changes
3. `git diff --cached` — see already-staged changes
4. `git log --oneline -5` — see recent commits for style consistency

### Step 2: Determine the Commit Type

Read [commit-types.md](commit-types.md) for the full reference. Choose the type that best describes the **primary intent** of the changes:

| Type       | When to use                                    |
| ---------- | ---------------------------------------------- |
| `feat`     | Adding new user-facing functionality           |
| `fix`      | Correcting a bug or broken behavior            |
| `refactor` | Restructuring code without changing behavior   |
| `docs`     | Documentation-only changes                     |
| `test`     | Adding or updating tests only                  |
| `chore`    | Maintenance, deps, tooling, config             |
| `ci`       | CI/CD pipeline or workflow changes             |
| `style`    | Formatting only (whitespace, semicolons, etc.) |
| `perf`     | Performance improvements                       |
| `build`    | Build system or external dependency changes    |

**Rules for choosing:**

- If changes span multiple types, use the type that describes the **primary purpose**. A bug fix that also adds a test is `fix`, not `test`.
- If the change introduces a breaking change, append `!` after the type/scope: `feat!: remove legacy auth endpoint`
- Use a scope when it clarifies what area is affected: `fix(auth): handle expired tokens`

### Step 3: Stage the Right Files

- **Never** use `git add -A` or `git add .` — these can accidentally stage secrets or unrelated files.
- Stage only the files relevant to this commit by name.
- If there are unrelated changes, ask the user whether to include them or create separate commits.
- Do not stage files that likely contain secrets (`.env`, `credentials.json`, API keys, tokens).

### Step 4: Write the Commit Message

Format: `<type>(<optional scope>): <description>`

**Message rules:**

1. **Subject line**: Imperative mood, lowercase, no period at the end, under 72 characters
   - Good: `feat(cart): add quantity selector to product page`
   - Bad: `Added quantity selector.`
2. **Body** (optional): Add a body for non-trivial changes. Explain **why**, not **what**. Separate from subject with a blank line.
3. **Breaking changes**: Use `!` in the header AND add a `BREAKING CHANGE:` footer explaining the migration path.

Always pass the commit message via a HEREDOC for correct formatting:

```bash
git commit -m "$(cat <<'EOF'
type(scope): subject line here

Optional body explaining the motivation for the change.
More details if needed.

BREAKING CHANGE: description of what breaks and how to migrate (if applicable)
EOF
)"
```

### Step 5: Verify the Commit

1. The `commit-msg` hook will run commitlint to validate the format. If it rejects the message, fix the format and create a **new** commit (do not amend).
2. Run `git log --oneline -3` to confirm the commit was created.
3. Report the commit hash and message to the user.

## Handling Multiple Logical Changes

If the diff contains changes that belong to different commit types or affect unrelated areas:

1. **Ask the user** if they want a single commit or multiple atomic commits
2. If splitting: stage and commit each logical group separately, following this full workflow for each
3. If combining: use the type that matches the primary purpose

## Examples

### Example 1: Simple Bug Fix

**User says:** "Commit this fix"

**Claude's actions:**

1. Runs `git status` — sees `src/auth/login.ts` modified
2. Runs `git diff` — sees a null check added on line 42
3. Determines type: `fix` (correcting broken behavior)
4. Stages: `git add src/auth/login.ts`
5. Commits:
   ```
   git commit -m "fix(auth): handle null session token during login"
   ```
6. Confirms: "Created commit `a1b2c3d`: `fix(auth): handle null session token during login`"

### Example 2: New Feature with Tests

**User says:** "Commit my changes"

**Claude's actions:**

1. Runs `git status` — sees new file `src/components/ThemeToggle.tsx`, modified `src/App.tsx`, new `tests/ThemeToggle.test.tsx`
2. Runs `git diff` — sees a dark mode toggle component and integration test
3. Determines type: `feat` (primary purpose is new functionality; tests support the feature)
4. Stages: `git add src/components/ThemeToggle.tsx src/App.tsx tests/ThemeToggle.test.tsx`
5. Commits:
   ```
   git commit -m "feat(ui): add dark mode toggle to settings page"
   ```
6. Confirms: "Created commit `d4e5f6a`: `feat(ui): add dark mode toggle to settings page`"

### Example 3: Mixed Changes

**User says:** "Commit everything"

**Claude's actions:**

1. Runs `git status` — sees `src/api/users.ts` (refactored), `README.md` (updated docs), `.env.example` (new var)
2. Asks: "I see three types of changes: a refactor to the users API, a README update, and a new env var. Would you like me to create separate commits for each, or combine them into one?"
3. User says: "Separate them"
4. Creates three commits:
   - `refactor(api): simplify user lookup query`
   - `docs: update README with new env variables`
   - `chore: add CACHE_TTL to .env.example`

### Example 4: Breaking Change

**User says:** "Commit this — it changes the public API"

**Claude's actions:**

1. Runs `git diff --cached` — sees function signature changed in `src/sdk/client.ts`
2. Determines type: `feat!` (new behavior that breaks existing callers)
3. Commits with body:

   ```
   git commit -m "$(cat <<'EOF'
   feat!(sdk): change authenticate() to return Result type

   The authenticate() method now returns Result<Session, AuthError>
   instead of throwing exceptions. Callers must update to handle
   the Result type.

   BREAKING CHANGE: authenticate() no longer throws on failure.
   Use result.ok to check success and result.error for failures.
   EOF
   )"
   ```

## Error Handling

- **commitlint rejects the message**: Fix the format and create a new commit (never amend the previous commit)
- **No changes to commit**: Tell the user there are no staged or unstaged changes
- **Secrets detected**: Warn the user and do not stage those files
- **pre-commit hook fails (formatting)**: The hook auto-formats files — re-stage the formatted files and commit again
