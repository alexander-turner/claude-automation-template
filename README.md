# Claude Automation Template

Pre-configured [Claude Code](https://docs.anthropic.com/en/docs/claude-code) automation with git hooks and GitHub Actions.

## Quick Start

```bash
# 1. Create repo from template (click "Use this template" on GitHub)
# 2. Clone and setup
git clone <your-repo-url> && cd <your-repo> && ./setup.sh
```

## What's Included

| Component            | Purpose                                              |
| -------------------- | ---------------------------------------------------- |
| `.claude/`           | Claude Code session setup + PR creation skill        |
| `.hooks/`            | Pre-commit (lint-staged) + commit message validation |
| `.github/workflows/` | CI, Dependabot auto-merge, failure notifications     |

## Customization

Edit these files when ready:

- `CLAUDE.md` - Project details for Claude
- `package.json` - Configure dev/build/test/lint scripts
- `.github/workflows/comment-on-failed-checks.yaml` - Add your workflow names

CI workflows automatically skip unconfigured scripts, so you won't get failures on first push.

## Automatic Updates

Template updates sync daily at 9am UTC. You can also trigger manually:

1. Go to Actions → "Sync from Template"
2. Click "Run workflow"

A PR will be created with any updates for you to review.

## Requirements

- Node.js 18+
- Git 2.9+
