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

**MANDATORY: Before creating ANY pull request, you MUST follow `.claude/skills/pr-creation.md`.**

This includes:

1. **Self-critique via subagent** - Launch a general-purpose Task agent to review the diff for bugs, security issues, and bloat
2. **Address critique feedback** - Fix legitimate issues before proceeding
3. **Run validation** - Ensure tests/lint/typecheck pass
4. **Create the PR** - With proper summary and test plan
5. **Wait for CI checks** - Use `gh pr checks --watch` and fix any failures

Do NOT skip the self-critique step or the CI check waiting. PRs should not be considered ready until all checks are green.

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

## Customization Checklist

After cloning, update the following:

- [ ] This file (`CLAUDE.md`) - Add project-specific details
- [ ] `package.json` - Configure dev/build/test/lint scripts
- [ ] `.github/workflows/comment-on-failed-checks.yaml` - Add your workflow names
