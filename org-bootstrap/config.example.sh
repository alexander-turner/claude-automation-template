#!/usr/bin/env bash
# shellcheck disable=SC2034
# (every var below is consumed by bootstrap.sh after this file is sourced)
# Non-sensitive configuration for org-bootstrap. Copy to `config.sh` (gitignored)
# and edit. Secret VALUES never live here -- they are read from the environment
# at run time (see README.md).

# GitHub organization that owns the template-based repos.
ORG="your-org"

# Only manage repos carrying this topic. Leave empty to manage every
# non-archived repo in the org. Tag template-spawned repos with this topic so
# unrelated repos are never touched.
MANAGED_TOPIC="template-managed"

# --- Secrets ------------------------------------------------------------------
# Names of org-level Actions secrets to provision. The VALUE of each is read
# from the like-named environment variable at run time, e.g. export
# RULESET_SYNC_TOKEN=ghp_... before running `bootstrap.sh secrets`. A name with
# no value in the environment is skipped (warned), never blanked.
SECRET_NAMES=(
  RULESET_SYNC_TOKEN
)

# "all" exposes secrets to every repo; "private" to private repos only;
# "selected" requires you to wire repo access separately.
SECRET_VISIBILITY="all"

# --- Ruleset (branch protection) ----------------------------------------------
# The org ruleset carries only repo-agnostic rules (block deletion + force-push,
# optional required-PR). It deliberately does NOT pin repo-specific required
# status checks: repos run different tests, and requiring a context a repo never
# emits hangs that repo's PRs at pending forever. Per-repo required checks are
# owned by each repo's sync-required-checks workflow (derived from that repo's
# own `# required-check:` annotations).
RULESET_NAME="template-default-branch-protection"

# OPTIONAL org-wide baseline of required status checks. Leave EMPTY (default)
# unless a context is reported by *every* managed repo without exception -- list
# only those. Anything repo-specific belongs in that repo's workflow, not here.
REQUIRED_CHECKS=()

# PRs required before merge? Reviews required (0 = PR required, no approval gate).
REQUIRE_PULL_REQUEST="true"
REQUIRED_APPROVALS=0

# --- Default repo settings ----------------------------------------------------
# Org-wide defaults applied by `bootstrap.sh defaults`.
DEFAULT_REPO_PERMISSION="read" # base permission members get on all repos
MEMBERS_CAN_CREATE_REPOS="false"
DEFAULT_WORKFLOW_PERMISSIONS="read" # GITHUB_TOKEN default: read | write

# Per-repo merge hygiene applied to every managed repo.
ALLOW_SQUASH_MERGE="true"
ALLOW_MERGE_COMMIT="false"
ALLOW_REBASE_MERGE="false"
DELETE_BRANCH_ON_MERGE="true"
ALLOW_AUTO_MERGE="true"
