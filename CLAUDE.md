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
- Let exceptions propagate — only catch with a specific recovery action
- Un-nest conditionals; combine related checks
- Smart quotes (U+201C/U+201D/U+2018/U+2019): use Unicode escapes in code, centralize constants, ask user to verify output
- Fail loudly with clear error messages, only remove error reporting if user asks specifically

## Testing

- Never skip or weaken tests unless asked
- Parametrize for compactness; prefer exact equality assertions
- For interaction features/bugs: add Playwright e2e tests (mobile + desktop, verify visual state)

## Hooks

**NEVER disable, bypass, or work around hooks.** This includes:

- `chmod -x` on hook scripts
- `--no-verify` on git commands
- `git config --unset core.hooksPath` or redirecting it
- Temporarily renaming, moving, or emptying hook files
- Any other technique that prevents a hook from running

If a hook fails, **tell the user** what failed and why, then fix the underlying issue. The hook is doing its job — the code needs to satisfy it, not the other way around.

### Hook Errors

If any hook fails (SessionStart, PreToolUse, PostToolUse, Stop, or git hooks), you MUST:

1. **Warn prominently** — identify which hook, the error output, and files involved
2. **Propose a fix PR** — check `.claude/hooks/` or `.hooks/` for the source
3. **Assess scope** — repo-specific issues: fix here. General issues: also PR the [template repo](https://github.com/alexander-turner/claude-automation-template)
