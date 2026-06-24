# Org bootstrap

Provision and keep in sync the things a template **repo** can't carry on its own
— org-level **secrets**, branch-protection **rulesets**, and default **settings**
— across every template-based repo in a GitHub organization.

## Why this exists (and how it fits the other sync paths)

| Path                        | What it moves                                            | Direction                   |
| --------------------------- | -------------------------------------------------------- | --------------------------- |
| `template-sync.yaml`        | **Files** (workflows, hooks, configs)                    | template → downstream repos |
| `phone-home.yaml`           | **Lessons** from PR descriptions                         | downstream repos → template |
| `sync-required-checks.yaml` | A **repo** ruleset, from `# required-check:` annotations | within one repo             |
| **this** (`org-bootstrap/`) | **Secrets, an org ruleset, org/repo settings**           | org → all managed repos     |

Secrets and protection rules are account/org state, not files, so `template-sync`
can never carry them. This closes that gap.

> **Required checks are per-repo, not org-wide.** Different repos run different
> tests, so their required status-check _contexts_ differ. Pinning a fixed set in
> the org ruleset would require contexts some repos never emit — and a required
> check that never reports hangs that repo's PRs at **pending forever**. So the
> org ruleset here carries only **repo-agnostic** rules (block deletion, block
> force-push, optional required-PR); it adds no `required_status_checks` rule
> unless you opt in.
>
> Each repo's actual required checks are owned by its own `sync-required-checks`
> workflow, which derives them from that repo's `# required-check:` annotations —
> so a repo that adds, renames, or drops a test is gated on exactly what it runs.
> Org ruleset and per-repo ruleset compose cleanly: GitHub requires a check if
> _any_ matching ruleset requires it.
>
> `REQUIRED_CHECKS` in the config is an **optional org-wide baseline** — set it
> only to contexts _every_ managed repo reports without exception (rare; e.g. a
> universal secret scan). Default is empty.

## Prerequisites

- [`gh`](https://cli.github.com/) authenticated as an **org owner**, and `jq`.
- Token scopes: classic PAT with **`admin:org`** (org secrets, rulesets, org
  settings) **and `repo`** (per-repo merge settings). Fine-grained equivalent:
  organization **Administration: write** + **Secrets: write**, repository
  **Administration: write**. `gh auth login` or `GH_TOKEN=...` both work.

## Setup

```bash
cd org-bootstrap
cp config.example.sh config.sh      # config.sh is gitignored
$EDITOR config.sh                   # set ORG, MANAGED_TOPIC, checks, settings
```

Tag the repos you want managed with the `MANAGED_TOPIC` topic (default
`template-managed`) so unrelated org repos are never touched. Leave
`MANAGED_TOPIC` empty to manage every non-archived repo.

## Run

```bash
# Secret VALUES are read from the environment, never the config file:
export RULESET_SYNC_TOKEN=ghp_xxx

./bootstrap.sh secrets     # push org Actions secrets (skips names with no env value)
./bootstrap.sh ruleset     # create/update the org branch-protection ruleset
./bootstrap.sh defaults    # org defaults + per-repo merge settings
./bootstrap.sh all         # all three, in order
```

Every subcommand is **idempotent** — re-run after editing `config.sh` to
converge. The ruleset is matched by name (`RULESET_NAME`) and updated in place,
so re-runs never create duplicates. A secret name with no matching environment
variable is skipped with a warning, never blanked.

## What each subcommand does

- **`secrets`** — `gh secret set --org` for each name in `SECRET_NAMES`, at
  `SECRET_VISIBILITY`. This is how `RULESET_SYNC_TOKEN` (and any other shared
  secret) reaches all repos without per-repo copying.
- **`ruleset`** — one org ruleset targeting the default branch of all repos
  (`~ALL` / `~DEFAULT_BRANCH`): blocks deletion and force-push, and optionally
  requires a PR. Adds a `required_status_checks` rule only if you set a non-empty
  `REQUIRED_CHECKS` baseline (default empty — per-repo checks are owned by each
  repo's `sync-required-checks` workflow).
- **`defaults`** — org base permission, repo-creation policy, and default
  `GITHUB_TOKEN` workflow permissions; then per-repo merge hygiene
  (squash-only, delete branch on merge, auto-merge) on each managed repo.

## Automating it

Run it manually after onboarding a repo, or wire it to a schedule. To run it
from Actions, store the admin PAT as an org secret and invoke `./bootstrap.sh
all` on a `schedule`/`workflow_dispatch` trigger — keep it **off** `pull_request`
so it never becomes a required check (same rule the `sync-required-checks`
workflow follows).
