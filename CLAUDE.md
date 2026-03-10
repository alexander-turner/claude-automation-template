# CLAUDE.md

## Commands

```bash
pnpm install    # Install deps + configure git hooks
pnpm format     # Format with Prettier
pnpm dev / pnpm build / pnpm test / pnpm lint  # If configured in package.json
```

Use pnpm (not npm) for all package operations.

## Git Workflow

Commits MUST use [Conventional Commits](https://www.conventionalcommits.org/) (`<type>(<scope>): <desc>`). The `commit-msg` hook enforces this. Types: feat, fix, refactor, docs, test, chore, ci, style, perf, build. Use `!` for breaking changes.

## Pull Requests

Use the `/pr-creation` skill. Include a `## Lessons Learned` section if you discovered generalizable insights — the `phone-home.yaml` workflow propagates these to the template repo on merge.

## Code Style

- Fail loudly: throw errors over logging warnings for critical issues
- Let exceptions propagate — never use try/except unless there is a specific, necessary recovery action. Default to crashing on unexpected input
- Un-nest conditionals; combine related checks
- Smart quotes (U+201C/U+201D/U+2018/U+2019): use Unicode escapes in code, centralize constants, ask user to verify output
- Fail loudly with clear error messages, only remove error reporting if user asks specifically

## CI / GitHub Actions

- Add the `ci:full-tests` label to PRs that modify Playwright tests or interaction behavior, so CI actually runs Playwright on the PR.
- **`paths` filter pitfall**: when a workflow's `push` trigger uses `paths` but its `pull_request` trigger omits `paths`, subsequent PR events (`synchronize`, `labeled`, `reopened`) may silently not trigger the workflow. Always mirror `paths` filters across both `push` and `pull_request` triggers.

## Testing

- Never skip or weaken tests unless asked
- Parametrize for compactness; prefer exact equality assertions
- For interaction features/bugs: add Playwright e2e tests (mobile + desktop, verify visual state)

### Hook Errors

**NEVER disable, bypass, or work around hooks.** If a hook fails, **tell the user** what failed and why, then fix the underlying issue. If any hook fails (SessionStart, PreToolUse, PostToolUse, Stop, or git hooks), you MUST:

1. **Warn prominently** — identify which hook, the error output, and files involved
2. **Propose a fix PR** — check `.claude/hooks/` or `.hooks/` for the source
3. **Assess scope** — repo-specific issues: fix here. General issues: also PR the [template repo](https://github.com/alexander-turner/claude-automation-template)
