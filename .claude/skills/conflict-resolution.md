# Template Sync Conflict Resolution Skill

**Use this skill when resolving conflicts in template-sync PRs.**

This skill guides Claude through analyzing and resolving conflicts between local customizations and template updates.

## When to Use

Use this skill when:

- A template-sync PR has conflicts (marked with `needs-conflict-resolution` label)
- Someone asks to "resolve conflicts" or "help with template sync"
- You're reviewing a PR from the `template-sync` branch

## Understanding Template Sync Conflicts

Template sync conflicts occur when:

1. The template repository has updates to a file
2. The local repository has customized that same file
3. Both versions have diverged from a common ancestor

**Key principle:** Local customizations should be preserved while incorporating beneficial template updates.

## Resolution Workflow

### Step 1: Identify Conflict Types

For each conflicting file, determine the type:

| File Type          | Common Customizations                    | Template Updates             |
| ------------------ | ---------------------------------------- | ---------------------------- |
| `CLAUDE.md`        | Project description, commands, structure | New sections, best practices |
| `settings.json`    | Project-specific hooks, tools            | New hook types, fixes        |
| `*.sh` scripts     | Custom tool installs, paths              | Bug fixes, new features      |
| `*.yaml` workflows | Project-specific jobs, triggers          | Security fixes, improvements |

### Step 2: Analyze Each Conflict

For each conflicting file:

1. **Read both versions** - Understand what changed in each
2. **Identify customizations** - What project-specific content exists locally?
3. **Identify improvements** - What beneficial changes are in the template?
4. **Check for incompatibilities** - Will merging cause issues?

### Step 3: Generate Merged Content

Follow these merge strategies by file type:

#### Documentation Files (CLAUDE.md, README.md)

```
Strategy: MERGE - Keep local content, add new template sections

1. Keep all project-specific sections intact
2. Add any new sections from template
3. Update shared sections if template has improvements
4. Preserve local examples and customizations
```

#### Configuration Files (settings.json, \*.yaml)

```
Strategy: SELECTIVE MERGE - Preserve settings, adopt fixes

1. Keep project-specific configuration values
2. Adopt structural improvements from template
3. Add new configuration options with sensible defaults
4. Preserve custom hooks/jobs while updating shared ones
```

#### Scripts (\*.sh)

```
Strategy: ADOPT WITH PRESERVATION - Take template, restore customizations

1. Start with template version (usually has bug fixes)
2. Re-add any custom tool installations
3. Re-add any project-specific paths or variables
4. Test that customizations still work with new base
```

### Step 4: Apply Resolution

1. **Edit the file** with merged content
2. **Commit the change** with message: `fix: resolve template sync conflict in <file>`
3. **Update PR description** to note what was preserved vs updated

## Example Resolutions

### Example: CLAUDE.md Conflict

**Local version has:**

```markdown
## Overview

This is my custom project for managing widgets...

## Development Commands

pnpm dev # Start widget server
pnpm test # Run widget tests
```

**Template version has:**

```markdown
## Overview

This project uses the Claude automation template...

## Development Commands

pnpm install # Install dependencies
pnpm format # Format code
```

**Merged resolution:**

```markdown
## Overview

This is my custom project for managing widgets. It uses the Claude automation template with pre-configured git hooks and CI workflows.

## Development Commands

pnpm install # Install dependencies
pnpm dev # Start widget server
pnpm test # Run widget tests
pnpm format # Format code
```

### Example: settings.json Conflict

**Local has custom hooks:**

```json
{
  "hooks": {
    "SessionStart": ["bash .claude/hooks/session-setup.sh"],
    "PreCommit": ["bash scripts/my-custom-check.sh"]
  }
}
```

**Template has new structure:**

```json
{
  "hooks": {
    "SessionStart": {
      "command": "bash .claude/hooks/session-setup.sh",
      "timeout": 60000
    }
  }
}
```

**Merged resolution:**

```json
{
  "hooks": {
    "SessionStart": {
      "command": "bash .claude/hooks/session-setup.sh",
      "timeout": 60000
    },
    "PreCommit": ["bash scripts/my-custom-check.sh"]
  }
}
```

## Post-Resolution Checklist

After resolving conflicts:

- [ ] All project-specific customizations are preserved
- [ ] Template improvements/fixes are incorporated
- [ ] Configuration files are valid (JSON parses, YAML validates)
- [ ] Scripts are executable and syntax-checked
- [ ] PR description updated with resolution summary

## When to Reject Template Updates

Sometimes the template update should NOT be applied:

- Template removes functionality your project needs
- Template changes conflict with project requirements
- Template update is a regression (check template repo issues)

In these cases, document why the update was rejected in the PR.
