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

Commits must follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New features
- `fix:` Bug fixes
- `refactor:` Code refactoring
- `docs:` Documentation
- `test:` Test changes
- `chore:` Maintenance

## Pull Request Requirements

Use the `/pr-creation` skill when creating pull requests. It handles self-critique, validation, and CI checks.

## Post-PR Reflection

After completing a pull request, reflect on the conversation and look for generalizable mistakes or patterns that could have been prevented with better guidance in this file.

If you identify improvements:

1. Note specific lessons learned (e.g., "Always check X before Y", "Remember to handle edge case Z")
2. Create a separate PR to the template repository (`alexander-turner/claude-automation-template`) adding these insights to `CLAUDE.md`
3. Keep additions concise and actionable

This continuous improvement loop helps prevent recurring issues across future sessions.

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
- Un-nest conditionals where possible; combine related checks into single blocks
- Create shared helpers when the same logic is needed in multiple places
- In TypeScript, only use template literals if using variable substitution

### Testing

- Write focused, non-duplicative tests
- Parametrize tests for compactness while achieving high coverage
- Prefer exact equality assertions over partial/contains checks—make tests as strict as possible

### Dependencies

- Use pnpm (not npm) for all package operations

## Claude GitHub Integration

This template uses the official [claude-code-action](https://github.com/anthropics/claude-code-action) for GitHub automation:

1. **claude.yaml** - Responds to `@claude` mentions in issues, PRs, and comments
2. **comment-on-failed-checks.yaml** - Detects CI failures on `claude/` branches and tags `@claude` for auto-fix

### Setup Required

To let Claude start fixing your PRs after your CI fails, you need to [install the Claude GitHub app](https://github.com/apps/claude).

The automation will then:

- Respond to `@claude` mentions in issues and PRs
- Automatically fix CI failures on `claude/` branches
- Review code and answer questions about the codebase

## Hook Error Handling

If any hook fails during a session (SessionStart, PreToolUse, PostToolUse, Stop, or git hooks like pre-commit and commit-msg), you MUST:

1. **Warn the user prominently.** Output a clear, highly visible warning that identifies:
   - Which hook failed (e.g., `session-setup.sh`, `pre-push-check.sh`, `pre-commit`)
   - The error output or exit code
   - Which file(s) are involved

2. **Suggest a pull request to fix the problem.** Identify the root cause and propose a fix:
   - For Claude Code hooks: check files in `.claude/hooks/` (e.g., `session-setup.sh`, `pre-push-check.sh`, `verify-ci-on-stop.sh`, `lib-checks.sh`)
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
