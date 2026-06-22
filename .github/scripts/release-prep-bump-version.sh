#!/usr/bin/env bash
# Run the base branch's trusted release-prep + changelog assembler on the PR branch.
# A PR cannot alter the bump logic that runs against it: both the assembler and the
# release-prep script come from the PR's base branch (via FETCH_HEAD), staged into
# $RUNNER_TEMP. The in-tree copies are used only to bootstrap the very PR that first
# adds these scripts, when the base branch has no copy yet.
# Env: BASE_REF, RUNNER_TEMP
set -eo pipefail
script=.github/scripts/release-prep.sh
assembler=.github/scripts/assemble-changelog.mjs
git fetch --quiet origin "$BASE_REF"
if git show "FETCH_HEAD:${assembler}" >"${RUNNER_TEMP}/assemble-changelog.mjs" 2>/dev/null; then
  export ASSEMBLE_CHANGELOG="${RUNNER_TEMP}/assemble-changelog.mjs"
else
  echo "::warning::base branch lacks ${assembler}; using the PR's copy (bootstrap only)"
fi
if git show "FETCH_HEAD:${script}" >"${RUNNER_TEMP}/release-prep.sh" 2>/dev/null; then
  bash "${RUNNER_TEMP}/release-prep.sh"
else
  echo "::warning::base branch lacks ${script}; running the PR's copy (bootstrap only)"
  bash "$script"
fi
