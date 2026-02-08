#!/usr/bin/env python3
"""Track CI failures on claude/ branch PRs and escalate when fixes are exhausted.

Called by the comment-on-failed-checks workflow. Reads context from environment
variables and uses the gh CLI for GitHub API calls.

This is a notification/labeling system only — it does NOT ping @claude to trigger
new fix sessions. The Stop hook in the interactive session is the primary fix
mechanism. This workflow exists to:
  1. Track which workflows have failed and how many times
  2. Leave clear comments for humans to see what's broken
  3. Label the PR `needs-human-review` when automated fixes are exhausted
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

MAX_ATTEMPTS = 2
TRACKER_MARKER = "<!-- claude-failure-tracker -->"


def gh_api(
    endpoint: str, method: str = "GET", body: dict | None = None
) -> dict | list | None:
    """Call the GitHub API via the gh CLI."""
    cmd = ["gh", "api", endpoint, "-X", method]
    if method == "GET":
        cmd.append("--paginate")

    input_data = None
    if body is not None:
        cmd.extend(["--input", "-"])
        input_data = json.dumps(body)

    result = subprocess.run(cmd, capture_output=True, text=True, input=input_data)
    if result.returncode != 0:
        raise RuntimeError(
            f"gh api {method} {endpoint} failed: {result.stderr.strip()}"
        )

    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


def main() -> None:
    # Read context from environment (set by the workflow)
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = os.environ["PR_NUMBER"]
    workflow_name = os.environ["WORKFLOW_NAME"]
    run_url = os.environ["RUN_URL"]
    run_id = int(os.environ["RUN_ID"])
    head_sha = os.environ["HEAD_SHA"][:7]

    # Find existing tracker comment
    comments = gh_api(f"repos/{repo}/issues/{pr_number}/comments") or []

    tracker = None
    failures: dict[str, list[dict]] = {}
    for comment in comments:
        body = comment.get("body") or ""
        if TRACKER_MARKER in body:
            tracker = comment
            match = re.search(r"<!-- failures:(\{.*?\}) -->", body)
            if match:
                try:
                    failures = json.loads(match.group(1))
                except json.JSONDecodeError:
                    print("Failed to parse existing failure state, starting fresh")
            break

    # Dedup: skip if we already tracked this specific run
    if any(f["run"] == run_id for f in failures.get(workflow_name, [])):
        print(f"Already tracked run {run_id} for {workflow_name}, skipping")
        return

    # Skip if workflow has exhausted its attempts
    if len(failures.get(workflow_name, [])) >= MAX_ATTEMPTS:
        print(f"{workflow_name} already at {MAX_ATTEMPTS} attempts, skipping")
        return

    # Record the new failure
    failures.setdefault(workflow_name, []).append(
        {"run": run_id, "sha": head_sha, "url": run_url}
    )

    just_exhausted = len(failures[workflow_name]) >= MAX_ATTEMPTS
    # "all exhausted" means every workflow that has ever failed has hit its limit
    all_exhausted = all(len(runs) >= MAX_ATTEMPTS for runs in failures.values())

    # Build the failure summary lines
    failure_lines = []
    for name, runs in failures.items():
        latest = runs[-1]
        exhausted = len(runs) >= MAX_ATTEMPTS
        status = " (giving up)" if exhausted else ""
        failure_lines.append(
            f"- **{name}** [failed]({latest['url']}) on commit "
            f"{latest['sha']} (attempt {len(runs)}/{MAX_ATTEMPTS}){status}"
        )
    failure_list = "\n".join(failure_lines)

    # Build comment body — no @claude mention (this is notification-only)
    failures_json = json.dumps(failures)

    if all_exhausted:
        body = (
            f"{TRACKER_MARKER}\n"
            f"<!-- failures:{failures_json} -->\n"
            f"**Automated fix attempts exhausted.** The following workflows failed "
            f"repeatedly and could not be fixed automatically:\n\n"
            f"{failure_list}\n\n"
            f"Human review is needed to resolve these failures."
        )
    elif just_exhausted:
        body = (
            f"{TRACKER_MARKER}\n"
            f"<!-- failures:{failures_json} -->\n"
            f"The following workflows have failed:\n\n"
            f"{failure_list}\n\n"
            f"**{workflow_name}** has exhausted its {MAX_ATTEMPTS} fix attempts."
        )
    else:
        body = (
            f"{TRACKER_MARKER}\n"
            f"<!-- failures:{failures_json} -->\n"
            f"The following workflows have failed on this PR:\n\n"
            f"{failure_list}"
        )

    # Create or update the tracker comment
    if tracker:
        gh_api(
            f"repos/{repo}/issues/comments/{tracker['id']}",
            method="PATCH",
            body={"body": body},
        )
        print(f"Updated tracker comment for {workflow_name} failure")
    else:
        gh_api(
            f"repos/{repo}/issues/{pr_number}/comments",
            method="POST",
            body={"body": body},
        )
        print(f"Created tracker comment for {workflow_name} failure")

    # Label when all attempts are exhausted
    if all_exhausted:
        try:
            gh_api(
                f"repos/{repo}/issues/{pr_number}/labels",
                method="POST",
                body={"labels": ["needs-human-review"]},
            )
            print("Added needs-human-review label")
        except RuntimeError as e:
            print(f"Could not add label (may not exist): {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
