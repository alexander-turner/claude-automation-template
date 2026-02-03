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

## Customization Checklist

After cloning, update the following:
- [ ] This file (`CLAUDE.md`) - Add project-specific details
- [ ] `package.json` - Configure dev/build/test/lint scripts
- [ ] `.github/workflows/comment-on-failed-checks.yaml` - Add your workflow names
