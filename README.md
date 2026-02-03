# Claude Automation Template

Pre-configured [Claude Code](https://docs.anthropic.com/en/docs/claude-code) automation with git hooks and GitHub Actions.

## Quick Start

```bash
# 1. Create repo from template (click "Use this template" on GitHub)

# 2. Clone and install
git clone <your-repo-url>
cd <your-repo>
pnpm install        # or: npm install -g pnpm && pnpm install

# 3. Enable git hooks
git config core.hooksPath .hooks

# 4. Verify setup
git config core.hooksPath   # Should print: .hooks
```

Then customize `CLAUDE.md` with your project details.

## What's Included

| Component | Purpose |
|-----------|---------|
| `.claude/settings.json` | Runs setup script when Claude Code starts |
| `.claude/hooks/session-setup.sh` | Installs tools, configures git, authenticates gh |
| `.claude/skills/pr-creation.md` | PR workflow with mandatory self-critique |
| `.hooks/pre-commit` | Runs lint-staged on commit |
| `.hooks/commit-msg` | Validates conventional commit format |
| `.github/workflows/*` | CI, Dependabot auto-merge, failure notifications |

## Customization

1. **Edit `CLAUDE.md`** - Add your project's commands, architecture, and guidelines
2. **Edit `package.json`** - Configure lint-staged rules for your file types
3. **Edit `.github/workflows/comment-on-failed-checks.yaml`** - Add your workflow names to the trigger list

## Requirements

- Node.js 18+
- pnpm (or npm)
- Git 2.9+
