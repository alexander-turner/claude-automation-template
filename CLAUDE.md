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

**Pull requests**: Follow `.claude/skills/pr-creation.md` before creating any PR.

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

### Dependencies

- Use pnpm (not npm) for all package operations

## Customization Checklist

After cloning, update the following:

- [ ] This file (`CLAUDE.md`) - Add project-specific details
- [ ] `package.json` - Configure dev/build/test/lint scripts
- [ ] `.github/workflows/comment-on-failed-checks.yaml` - Add your workflow names
