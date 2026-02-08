# Conventional Commit Types Reference

This file is a quick reference for choosing the correct commit type. The types below are enforced by commitlint with `@commitlint/config-conventional`.

## Types

### `feat` — New Feature

A new user-facing feature or capability.

```
feat(auth): add OAuth2 login with Google
feat: support CSV export for reports
feat!: replace REST API with GraphQL
```

### `fix` — Bug Fix

A correction to existing broken behavior.

```
fix(cart): prevent duplicate items when clicking fast
fix: resolve crash on empty search query
fix(api): return 404 instead of 500 for missing resources
```

### `refactor` — Code Refactoring

Restructuring code without changing external behavior. No new features, no bug fixes.

```
refactor(db): extract connection pooling into shared module
refactor: simplify conditional logic in price calculator
refactor(auth): replace callback chain with async/await
```

### `docs` — Documentation

Changes only to documentation files or code comments.

```
docs: add API authentication guide
docs(readme): update installation instructions
docs: fix typo in contributing guide
```

### `test` — Tests

Adding new tests or updating existing tests. No production code changes.

```
test(auth): add integration tests for token refresh
test: increase coverage for edge cases in parser
test(e2e): add Playwright tests for checkout flow
```

### `chore` — Maintenance

Routine maintenance, dependency updates, tooling configuration. Does not affect production source code or tests.

```
chore: update eslint to v9
chore(deps): bump axios from 1.6.0 to 1.7.2
chore: add .editorconfig for consistent formatting
```

### `ci` — Continuous Integration

Changes to CI/CD configuration files and scripts.

```
ci: add GitHub Actions workflow for staging deploy
ci: fix flaky test retry in CI pipeline
ci: add caching for node_modules in build workflow
```

### `style` — Formatting

Changes that do not affect the meaning of the code: whitespace, formatting, missing semicolons, etc.

```
style: fix indentation in config files
style: apply prettier formatting to all components
style: remove trailing whitespace
```

### `perf` — Performance

A code change that improves performance.

```
perf(api): add database query caching for user lookups
perf: lazy-load images below the fold
perf(search): switch to binary search for sorted results
```

### `build` — Build System

Changes that affect the build system or external dependencies (not CI).

```
build: migrate from webpack to vite
build: add TypeScript path aliases
build(docker): optimize multi-stage build for smaller image
```

## Scopes

Scopes are optional and should clarify what area of the codebase is affected. Use them when the type alone isn't specific enough.

Good scopes:

- Module or component names: `auth`, `cart`, `api`, `ui`
- Layer names: `db`, `middleware`, `routes`
- Tool names: `eslint`, `docker`, `webpack`

Do not use overly broad scopes like `app` or `code` — they add no value.

## Breaking Changes

Indicate breaking changes by appending `!` after the type (and scope, if present):

```
feat!: remove deprecated v1 endpoints
feat(api)!: change response format to JSON:API
refactor!: rename all exported interfaces to use I prefix
```

For significant breaking changes, also add a `BREAKING CHANGE:` footer in the commit body explaining what breaks and how to migrate.

## Choosing Between Similar Types

| Scenario                                   | Type            | Reasoning                                   |
| ------------------------------------------ | --------------- | ------------------------------------------- |
| Fix a bug and add a test for it            | `fix`           | Primary intent is the fix; test supports it |
| Add a test for existing untested code      | `test`          | No behavior change, purely test addition    |
| Rename a function for clarity              | `refactor`      | Code restructuring, no behavior change      |
| Rename a function and change its behavior  | `feat` or `fix` | Behavior changed — type depends on intent   |
| Update a dependency                        | `chore`         | Routine maintenance                         |
| Update a dependency to fix a vulnerability | `fix`           | Security fix is the intent                  |
| Add a README section                       | `docs`          | Documentation only                          |
| Add JSDoc comments to code                 | `docs`          | Documentation only (no logic change)        |
| Format code with prettier                  | `style`         | No logic change                             |
| Move code to a new file                    | `refactor`      | Structural change, no behavior change       |
