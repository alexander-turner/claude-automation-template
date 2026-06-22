# Changelog fragments

User-facing changes are recorded here as **one small file per change**, not by
editing `CHANGELOG.md` directly. Because every fragment is its own uniquely named
file, two PRs can never edit the same lines — the changelog stops being a
merge-conflict hotspot. At release time `.github/scripts/assemble-changelog.mjs`
rolls all pending fragments into a new `## [version]` section in `CHANGELOG.md`
and deletes them.

> **Scope:** this fragment flow + the `release-prep`/`tag-release` workflows are
> for repos published as a **versioned app** (semver `package.json`). A repo that
> is not a versioned release (e.g. a website like TurnTrout.com) should drop the
> release workflows via the template-sync `EXCLUDE_PATHS` list and can ignore
> this directory entirely.

## Adding an entry

Create a file named `<id>.<category>.md`:

- **`<id>`** — anything unique; use your PR number (`592`) so fragments sort in
  merge order and never collide. Multiple categories in one PR → multiple files
  (`592.added.md`, `592.fixed.md`).
- **`<category>`** — one of: `added`, `changed`, `deprecated`, `removed`,
  `fixed`, `security` (the [Keep a Changelog](https://keepachangelog.com/) groups).

The file's contents are the Markdown that will appear under that `### Category`
heading — write it as one or more `- ` bullets, exactly as it should read in the
changelog:

```markdown
- `--foo` flag: does the thing, gated on the other thing.
```

Only add a fragment for a **user-facing** change (new flag/command, changed
default, altered security boundary, fixed bug a user could hit). Internal churn
(test refactors, CI plumbing, comment edits) gets none.

Preview the assembled result with
`node .github/scripts/assemble-changelog.mjs --draft`.
