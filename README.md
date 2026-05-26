# Claude Automation Template

A GitHub template that makes [Claude Code](https://docs.anthropic.com/en/docs/claude-code) work reliably on your repositories. It wires up git hooks, CI workflows, and Claude session hooks so that Claude can autonomously fix code, create PRs, and respond to `@claude` mentions—with safeguards to prevent broken code from shipping.

## Why Use This

**Without this template**, using Claude Code on a repo requires manually configuring hooks, writing CI workflows, and building guardrails against common failure modes (infinite retry loops, pushing broken code, inconsistent formatting).

**With this template**, you get all of that out of the box:

- **A solid starting CLAUDE.md**—upholds high code quality standards, including a self-critique loop that catches bugs before they leave the editor
- **Pre-push verification**—build, lint, type checks, and tests run automatically before every `git push` or `gh pr create`
- **Skill-driven PR flow**—the `pr-creation` skill runs an iterative compress-critique-fix loop on the diff, then watches CI and fixes failures before reporting back
- **Enforced code quality**—Conventional Commits (via commitlint), Prettier formatting, and lint-staged run on every commit
- **`@claude` GitHub integration**—mention Claude in issues or PR comments and it responds with full repo context
- **Weekly security sweeps**—a scheduled workflow collects Dependabot, code-scanning, secret-scanning, and `pnpm audit` alerts, then hands them to Claude to open a rollup fix PR
- **Automatic template sync**—downstream repos receive improvements daily via PR, with 3-way merge that preserves your customizations
- **Multi-language support**—Node.js (pnpm), Python (uv/ruff/pytest), and shell (shfmt/shellcheck) work out of the box

## Prerequisites

- [Node.js](https://nodejs.org/) (see `.nvmrc` for the pinned version)
- [pnpm](https://pnpm.io/) (`npm install -g pnpm` if you don’t have it—`setup.sh` handles this automatically)
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- (Optional) [uv](https://docs.astral.sh/uv/) for Python projects

## Quick Start

1. **Create your repo**—click **“Use this template”** on GitHub.
2. **Clone and set up:**

   ```bash
   git clone <your-repo-url>
   cd <your-repo>
   ./setup.sh
   ```

   This installs dependencies and configures git hooks. Verify the output ends with `✓ Setup complete!`.

3. **Install the [Claude GitHub App](https://github.com/apps/claude)** to enable `@claude` mentions in issues and PRs.

4. **Customize for your project:**
   - Edit **`CLAUDE.md`**—add project-specific context, architecture notes, and conventions for Claude.
   - Edit **`package.json`**—wire up your `dev`, `build`, `test`, `lint`, and `check` scripts. Unconfigured scripts are detected and skipped gracefully, so nothing breaks on first push.

## What’s Included

### Git Hooks (`.hooks/`)

| Hook          | What it does                                                                                 |
| ------------- | -------------------------------------------------------------------------------------------- |
| `pre-commit`  | Runs lint-staged—auto-formats with Prettier, shfmt, and ruff depending on file type          |
| `commit-msg`  | Validates [Conventional Commits](https://www.conventionalcommits.org/) format via commitlint |
| `lint-skills` | Lint-staged helper—validates skill files have required frontmatter (`name`, `description`)   |

### Claude Session Hooks (`.claude/hooks/`)

These run inside Claude Code sessions (local CLI or cloud), not in CI.

| Hook           | What it does                                                              |
| -------------- | ------------------------------------------------------------------------- |
| `SessionStart` | Installs tools (shfmt, shellcheck), configures git, installs dependencies |
| `PreToolUse`   | Runs build/lint/typecheck/tests before `git push` or `gh pr create`       |

### Claude Skills (`.claude/skills/`)

| Skill                  | What it does                                                                    |
| ---------------------- | ------------------------------------------------------------------------------- |
| `pr-creation`          | Self-critique workflow before PR submission, then watches CI and fixes failures |
| `update-pr`            | Updates an existing PR with new changes and optionally revises the description  |
| `conventional-commits` | Guides Claude through properly formatted commits with secret detection          |
| `markdown-block`       | Outputs content in a fenced code block so users can copy raw markdown           |

### GitHub Actions (`.github/workflows/`)

| Workflow                           | What it does                                                          |
| ---------------------------------- | --------------------------------------------------------------------- |
| `claude.yaml`                      | Responds to `@claude` mentions in issues and PR comments              |
| `template-sync.yaml`               | Daily sync from template repo with 3-way merge and conflict detection |
| `phone-home.yaml`                  | Propagates “Lessons Learned” from merged PRs back to the template     |
| `security-vulnerability-scan.yaml` | Weekly security sweep—collects alerts, opens a rollup fix PR          |
| `node-tests.yaml`                  | Runs `pnpm test` (skips gracefully if unconfigured)                   |
| `lint.yaml`                        | Runs `pnpm lint` and `pnpm check` (skips gracefully if unconfigured)  |
| `format-check.yaml`                | Checks Prettier formatting                                            |
| `pre-commit.yaml`                  | Runs pre-commit hooks in CI                                           |
| `validate-config.yaml`             | Validates `.claude/` and `.hooks/` config on every push               |
| `dependabot-auto-merge.yaml`       | Auto-merges minor/patch Dependabot PRs after CI passes                |

## How the Pieces Fit Together

```
Developer / Claude Code session
        │
        ├── git commit
        │     ├── pre-commit hook  → lint-staged (Prettier, shfmt, ruff)
        │     └── commit-msg hook  → commitlint (Conventional Commits)
        │
        ├── git push / gh pr create
        │     └── PreToolUse hook  → build + lint + typecheck + tests
        │
        └── /pr-creation skill    → self-critique loop → create PR → watch CI
                                                                │
GitHub Actions (CI)                                             ▼
        ├── format-check.yaml     → Prettier
        ├── lint.yaml             → pnpm lint + pnpm check
        ├── node-tests.yaml       → pnpm test
        ├── pre-commit.yaml       → pre-commit hooks
        ├── validate-config.yaml  → .claude/ and .hooks/ validation
        │
        ├── claude.yaml           → @claude mentions in issues/PRs
        ├── template-sync.yaml    → daily template updates (9am UTC)
        ├── phone-home.yaml       → sends Lessons Learned back to template
        ├── security-*.yaml       → weekly vulnerability sweep + fix PR
        └── dependabot-*.yaml     → auto-merge minor/patch dependency bumps
```

## Automatic Updates

Template improvements sync daily at 9am UTC via `template-sync.yaml`. You can also trigger manually from **Actions > Sync from Template**.

Changes arrive as a PR for you to review. The sync uses a 3-way merge that preserves local customizations in synced files—if there’s a conflict, Claude is asked to resolve it while keeping your project-specific changes intact.

### Token Setup

Create a **fine-grained personal access token** with these permissions on your repo:

| Permission      | Access         |
| --------------- | -------------- |
| `contents`      | Read and write |
| `workflows`     | Read and write |
| `pull requests` | Read and write |

Add it as a repository secret named **`TEMPLATE_SYNC_TOKEN`**.

## Project Structure

```
.
├── .claude/
│   ├── hooks/              # Claude session hooks (SessionStart, PreToolUse)
│   ├── skills/             # Claude skills (pr-creation, conventional-commits, ...)
│   └── settings.json       # Claude Code hook configuration
├── .hooks/                 # Git hooks (pre-commit, commit-msg, lint-skills)
├── .github/
│   ├── workflows/          # CI workflows
│   └── dependabot.yml      # Dependabot configuration
├── config/                 # Shared configuration (e.g., JavaScript linting)
├── tests/                  # Python tests for hooks and config validation
├── CLAUDE.md               # Instructions for Claude Code sessions
├── package.json            # Node.js deps + lint-staged config
├── pyproject.toml          # Python project config (ruff, pytest)
└── setup.sh                # One-command setup script
```

## Troubleshooting

**Git hooks not running?**
Check that `core.hooksPath` is set: `git config core.hooksPath`. It should return `.hooks`. If not, run `pnpm install` (the `postinstall` script configures it) or set it manually with `git config core.hooksPath .hooks`.

**Pre-push checks failing on unconfigured scripts?**
The pre-push hook detects placeholder scripts in `package.json` (those that echo `ERROR: Configure...`) and skips them. Replace a placeholder with a real command and the corresponding check will start running.

**Claude session setup failing?**
The `SessionStart` hook installs tools like shfmt and shellcheck. If it fails, check the error output—it usually means a network issue or missing `uv`. You can re-run it manually: `.claude/hooks/session-setup.sh`.

**Template sync PR has conflicts?**
The sync workflow asks Claude to resolve conflicts, preserving your customizations. If it can’t, the PR will contain conflict markers for you to resolve manually. Look for header comments in your customized files like `"IMPORTANT: This file has project-specific customizations"`—the sync respects these.
