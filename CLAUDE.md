# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Overview

This project uses the Claude automation template with pre-configured git hooks and CI workflows. Customize this section with your project's description.

## Development Commands

```bash
pnpm install      # Install dependencies (also configures git hooks)
pnpm format       # Format code with Prettier
```

Configure additional scripts in `package.json` as needed:

- `pnpm dev` - Development server
- `pnpm build` - Production build
- `pnpm test` - Run tests
- `pnpm lint` - Run linter

## Git Workflow

Git hooks are configured automatically after `pnpm install`.

**IMPORTANT: All commits MUST use [Conventional Commits](https://www.conventionalcommits.org/) format.** The `commit-msg` hook enforces this via commitlint. Commits that don't follow this format will be rejected.

Format: `<type>(<optional scope>): <description>`

Allowed types:

- `feat:` New features
- `fix:` Bug fixes
- `refactor:` Code refactoring
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `chore:` Maintenance, dependency updates, tooling
- `ci:` CI/CD configuration changes
- `style:` Formatting changes (no code logic changes)
- `perf:` Performance improvements
- `build:` Build system changes

Use a `!` after the type/scope to indicate a breaking change (e.g., `feat!: remove legacy API`).

## Pull Request Requirements

Use the `/pr-creation` skill when creating pull requests. It handles self-critique, validation, and CI checks.

## Post-PR Reflection (Phone Home)

When creating a PR, include a `## Lessons Learned` section in the PR body if you discovered generalizable insights that could improve the template for all downstream projects. Examples:

- A hook edge case that caused failures
- A missing check that should be in the pre-push or stop hooks
- A CLAUDE.md instruction that would have prevented a mistake

When the PR is merged, the `phone-home.yaml` workflow automatically opens an issue on the template repository with the lessons learned, so they can be reviewed and adopted across all projects. This replaces the previous manual process of creating PRs on the template repo directly.

## Project Structure

```
src/              # Source code (create as needed)
tests/            # Test files (create as needed)
.claude/          # Claude Code configuration
.hooks/           # Git hooks (pre-commit, commit-msg)
.github/          # GitHub Actions workflows
```

## Development Practices

### Before Writing Code

- Ask clarifying questions if uncertain about scope or approach
- Check for existing libraries before rolling custom solutions
- Look for existing patterns in the codebase before creating new ones

### Code Style

- Prefer throwing errors that "fail loudly" over logging warnings for critical issues
- Don't wrap code in try/except unless there's a specific recovery action — let exceptions propagate naturally
- Un-nest conditionals where possible; combine related checks into single blocks
- Create shared helpers when the same logic is needed in multiple places
- Use descriptive variable names; don't shorten for brevity
- In TypeScript, only use template literals if using variable substitution
- Comments should describe what code does and why, never reference deleted code or what "used to be" there (e.g., don't write "Do NOT use X" referring to removed code)

### Smart Quotes vs Normal Quotes

Claude has difficulty distinguishing smart/curly quotes (U+201C, U+201D, U+2018, U+2019) from straight quotes ("). **When working with these characters:**

- Use Unicode escape sequences directly in code: `const quote = '\u201C'` (U+201C for left double quote) or `'\u2018'` (U+2018 for left single quote)
- Centralize quote constants in a shared file or constants object rather than duplicating them throughout the codebase
- If you must include smart quotes in source text (e.g., in comments, strings, or configuration), **ask the user to verify** the output — visually inspect that the correct Unicode character was used
- When in doubt, use straight quotes (`"` and `'`) and let the formatter or output system apply smart quotes if needed

### Testing

- Never skip tests or modify them to be easy to pass, unless directly asked to
- Write focused, non-duplicative tests
- Parametrize tests for compactness while achieving high coverage
- Prefer exact equality assertions over partial/contains checks—make tests as strict as possible
- **Interaction features/bug fixes**: When adding an interaction feature or fixing an interaction bug, add end-to-end tests (e.g., Playwright `*.spec.ts`) following best practices (test both mobile and desktop viewports, verify visual state not just DOM state)

### Dependencies

- Use pnpm (not npm) for all package operations

## Claude GitHub Integration

This template uses the official [claude-code-action](https://github.com/anthropics/claude-code-action) for GitHub automation:

1. **claude.yaml** - Responds to `@claude` mentions in issues, PRs, and comments (with concurrency guard to prevent parallel sessions on the same PR)
2. **comment-on-failed-checks.yaml** - Tracks CI failures on `claude/` branches, labels PR `needs-human-review` after max attempts (notification only — does not trigger new Claude sessions)
3. **phone-home.yaml** - When a merged PR contains a "Lessons Learned" section, automatically opens an issue on the template repo to propagate improvements
4. **template-sync.yaml** - Daily sync from template with version tracking, deletion detection, and conflict resolution via `@claude`

### Retry and Bailout Behavior

The automation has built-in safeguards against infinite token spend:

- **Stop hook** (`verify_ci.py`): Blocks session completion if checks fail, but gives up after 3 attempts (configurable via `MAX_STOP_RETRIES` env var). After exhausting retries, it approves with a warning. This is the **primary fix mechanism** — it runs in the interactive session with full context.
- **CI failure tracking** (`track_ci_failures.py`): Notification-only. Tracks which workflows failed and how many times. After all tracked workflows exhaust their 2 attempts, labels the PR `needs-human-review`. Does not ping `@claude` — spawning context-free sessions to fix CI failures is unreliable.
- **PostToolUse CI watcher**: `gh pr checks --watch` has a 5-minute timeout to prevent indefinite hangs.

### Setup Required

To let Claude start fixing your PRs after your CI fails, you need to [install the Claude GitHub app](https://github.com/apps/claude).

The automation will then:

- Respond to `@claude` mentions in issues and PRs
- Track CI failures on `claude/` branches and label for human review when stuck
- Review code and answer questions about the codebase
- Phone home improvements to the template repo when PRs are merged

## Hook Error Handling

If any hook fails during a session (SessionStart, PreToolUse, PostToolUse, Stop, or git hooks like pre-commit and commit-msg), you MUST:

1. **Warn the user prominently.** Output a clear, highly visible warning that identifies:
   - Which hook failed (e.g., `session-setup.sh`, `pre-push-check.sh`, `pre-commit`)
   - The error output or exit code
   - Which file(s) are involved

2. **Suggest a pull request to fix the problem.** Identify the root cause and propose a fix:
   - For Claude Code hooks: check files in `.claude/hooks/` (e.g., `session-setup.sh`, `pre-push-check.sh`, `verify_ci.py`, `lib-checks.sh`)
   - For git hooks: check files in `.hooks/` (e.g., `pre-commit`, `commit-msg`)
   - For setup issues: check `package.json` postinstall scripts and `.claude/settings.json` hook configuration
   - Create a PR to **this repository** with the fix

3. **Determine if the issue is general or repo-specific.**
   - **Repo-specific** (e.g., a misconfigured script path, a missing project dependency, a project-specific lint rule): fix it in this repository only.
   - **General** (e.g., a bug in the hook scripts themselves, a missing edge case in `session-setup.sh`, a broken pattern in `lib-checks.sh`, or an issue that would affect any repo using this template): tell the user to also open a pull request on the **template repository** ([`alexander-turner/claude-automation-template`](https://github.com/alexander-turner/claude-automation-template)) so all downstream projects benefit from the fix.

## Customization Checklist

After cloning, update the following:

- [ ] This file (`CLAUDE.md`) - Add project-specific details
- [ ] `package.json` - Configure dev/build/test/lint scripts
- [ ] `.github/workflows/comment-on-failed-checks.yaml` - Add your workflow names
