"""Tests for .github/scripts/track_ci_failures.py."""

from __future__ import annotations

import json

import pytest
from track_ci_failures import TRACKER_MARKER, gh_api, main

from tests.helpers import completed

# -----------------------------------------------------------------------
# gh_api
# -----------------------------------------------------------------------


class TestGhApi:
    def test_get_paginates(self, mock_subprocess) -> None:
        mock_subprocess["gh api"] = completed(0, stdout='[{"id": 1}]')
        result = gh_api("repos/o/r/issues")
        assert result == [{"id": 1}]
        # Should include --paginate for GET
        args = mock_subprocess.calls[0][0][0]
        assert "--paginate" in args

    def test_post_sends_body(self, mock_subprocess) -> None:
        mock_subprocess["gh api"] = completed(0, stdout='{"id": 99}')
        result = gh_api(
            "repos/o/r/issues/1/comments", method="POST", body={"body": "hi"}
        )
        assert result == {"id": 99}
        # Should include --input - for POST
        args = mock_subprocess.calls[0][0][0]
        assert "--input" in args
        assert "-" in args
        # Body should be passed as input
        kw = mock_subprocess.calls[0][1]
        assert json.loads(kw["input"]) == {"body": "hi"}

    def test_empty_response_returns_none(self, mock_subprocess) -> None:
        mock_subprocess["gh api"] = completed(0, stdout="  \n  ")
        assert gh_api("repos/o/r/issues") is None

    def test_failure_raises(self, mock_subprocess) -> None:
        mock_subprocess["gh api"] = completed(1, stderr="Not Found")
        with pytest.raises(RuntimeError, match="Not Found"):
            gh_api("repos/o/r/issues")

    @pytest.mark.parametrize(
        ("method", "expect_paginate"),
        [
            pytest.param("GET", True, id="GET-paginates"),
            pytest.param("POST", False, id="POST-no-paginate"),
            pytest.param("PATCH", False, id="PATCH-no-paginate"),
        ],
    )
    def test_paginate_only_for_get(
        self, mock_subprocess, method: str, expect_paginate: bool
    ) -> None:
        mock_subprocess["gh api"] = completed(0, stdout="{}")
        gh_api("endpoint", method=method)
        args = mock_subprocess.calls[0][0][0]
        assert ("--paginate" in args) is expect_paginate


# -----------------------------------------------------------------------
# main() — helpers
# -----------------------------------------------------------------------


def _tracker_comment(failures: dict, body_text: str = "tracked") -> dict:
    """Build a mock tracker comment with embedded failure state."""
    failures_json = json.dumps(failures)
    body = f"{TRACKER_MARKER}\n<!-- failures:{failures_json} -->\n{body_text}"
    return {"id": 500, "body": body}


def _no_comments() -> completed:
    """gh api response returning an empty comment list."""
    return completed(0, stdout="[]")


def _comments(*comments: dict) -> completed:
    """gh api response returning a list of comments."""
    return completed(0, stdout=json.dumps(list(comments)))


def _ok_post() -> completed:
    """gh api response for a successful POST/PATCH."""
    return completed(0, stdout='{"id": 1}')


class _CallCapture:
    """Track gh api calls made during main() to assert on them."""

    def __init__(self, mock_sub):
        self._mock = mock_sub

    @property
    def call_bodies(self) -> list[dict | None]:
        """Extract the JSON bodies sent in each subprocess.run call."""
        bodies = []
        for c in self._mock.calls:
            kw = c[1] if len(c) > 1 else {}
            input_data = kw.get("input")
            bodies.append(json.loads(input_data) if input_data else None)
        return bodies

    @property
    def call_commands(self) -> list[list[str]]:
        return [c[0][0] for c in self._mock.calls]


# -----------------------------------------------------------------------
# main() — first failure (no existing tracker)
# -----------------------------------------------------------------------


class TestFirstFailure:
    def test_creates_comment(self, tracker_env, mock_subprocess, capsys) -> None:
        mock_subprocess["gh api repos/owner/repo/issues/42/comments -X GET"] = (
            _no_comments()
        )
        mock_subprocess["gh api repos/owner/repo/issues/42/comments -X POST"] = (
            _ok_post()
        )

        main()

        captured = capsys.readouterr()
        assert "Created tracker comment" in captured.out

        cap = _CallCapture(mock_subprocess)
        # Second call should be the POST creating the comment
        post_body = cap.call_bodies[1]
        assert post_body is not None
        assert TRACKER_MARKER in post_body["body"]
        assert "CI" in post_body["body"]
        assert "attempt 1/2" in post_body["body"]


# -----------------------------------------------------------------------
# main() — subsequent failure (existing tracker, same workflow)
# -----------------------------------------------------------------------


class TestSubsequentFailure:
    def test_updates_existing_comment(
        self, tracker_env, mock_subprocess, monkeypatch, capsys
    ) -> None:
        existing_failures = {
            "CI": [{"run": 999, "sha": "old1234", "url": "https://example.com/999"}]
        }
        tracker = _tracker_comment(existing_failures)

        mock_subprocess["gh api repos/owner/repo/issues/42/comments -X GET"] = (
            _comments(tracker)
        )
        mock_subprocess["gh api repos/owner/repo/issues/comments/500 -X PATCH"] = (
            _ok_post()
        )
        # Label POST for exhaustion
        mock_subprocess["gh api repos/owner/repo/issues/42/labels -X POST"] = _ok_post()

        main()

        captured = capsys.readouterr()
        assert "Updated tracker comment" in captured.out

        cap = _CallCapture(mock_subprocess)
        patch_body = cap.call_bodies[1]
        assert patch_body is not None
        assert "attempt 2/2" in patch_body["body"]
        assert "giving up" in patch_body["body"]


# -----------------------------------------------------------------------
# main() — dedup: same run_id
# -----------------------------------------------------------------------


class TestDedup:
    def test_skips_duplicate_run(self, tracker_env, mock_subprocess, capsys) -> None:
        existing_failures = {
            "CI": [{"run": 1001, "sha": "abc1234", "url": "https://example.com/1001"}]
        }
        tracker = _tracker_comment(existing_failures)

        mock_subprocess["gh api repos/owner/repo/issues/42/comments -X GET"] = (
            _comments(tracker)
        )

        main()

        captured = capsys.readouterr()
        assert "Already tracked run 1001" in captured.out

    def test_skips_exhausted_workflow(
        self, tracker_env, mock_subprocess, monkeypatch, capsys
    ) -> None:
        monkeypatch.setenv("RUN_ID", "2000")
        existing_failures = {
            "CI": [
                {"run": 999, "sha": "old1234", "url": "https://example.com/999"},
                {"run": 1000, "sha": "old5678", "url": "https://example.com/1000"},
            ]
        }
        tracker = _tracker_comment(existing_failures)

        mock_subprocess["gh api repos/owner/repo/issues/42/comments -X GET"] = (
            _comments(tracker)
        )

        main()

        captured = capsys.readouterr()
        assert "already at 2 attempts" in captured.out


# -----------------------------------------------------------------------
# main() — all workflows exhausted → label
# -----------------------------------------------------------------------


class TestAllExhausted:
    def test_labels_pr_when_all_exhausted(
        self, tracker_env, mock_subprocess, capsys
    ) -> None:
        existing_failures = {
            "CI": [{"run": 999, "sha": "old1234", "url": "https://example.com/999"}],
        }
        tracker = _tracker_comment(existing_failures)

        mock_subprocess["gh api repos/owner/repo/issues/42/comments -X GET"] = (
            _comments(tracker)
        )
        mock_subprocess["gh api repos/owner/repo/issues/comments/500 -X PATCH"] = (
            _ok_post()
        )
        mock_subprocess["gh api repos/owner/repo/issues/42/labels -X POST"] = _ok_post()

        main()

        captured = capsys.readouterr()
        assert "Added needs-human-review label" in captured.out

        cap = _CallCapture(mock_subprocess)
        label_body = cap.call_bodies[2]
        assert label_body == {"labels": ["needs-human-review"]}


class TestPartialExhaustion:
    def test_no_label_when_some_not_exhausted(
        self, tracker_env, mock_subprocess, monkeypatch, capsys
    ) -> None:
        """Two workflows: one exhausted, one still has attempts. No label."""
        monkeypatch.setenv("WORKFLOW_NAME", "Deploy")
        monkeypatch.setenv("RUN_ID", "2000")

        existing_failures = {
            "CI": [
                {"run": 999, "sha": "old1234", "url": "https://example.com/999"},
                {"run": 1000, "sha": "old5678", "url": "https://example.com/1000"},
            ],
        }
        tracker = _tracker_comment(existing_failures)

        mock_subprocess["gh api repos/owner/repo/issues/42/comments -X GET"] = (
            _comments(tracker)
        )
        mock_subprocess["gh api repos/owner/repo/issues/comments/500 -X PATCH"] = (
            _ok_post()
        )

        main()

        captured = capsys.readouterr()
        assert "Updated tracker comment" in captured.out
        assert "needs-human-review" not in captured.out


# -----------------------------------------------------------------------
# main() — comment body content
# -----------------------------------------------------------------------


class TestCommentContent:
    @pytest.mark.parametrize(
        ("prior_attempts", "expected_fragments"),
        [
            pytest.param(
                0,
                ["attempt 1/2", "failed on this PR"],
                id="first-attempt",
            ),
            pytest.param(
                1,
                ["attempt 2/2", "giving up", "exhausted"],
                id="exhaustion",
            ),
        ],
    )
    def test_comment_body_varies_by_attempt(
        self,
        tracker_env,
        mock_subprocess,
        capsys,
        monkeypatch,
        prior_attempts: int,
        expected_fragments: list[str],
    ) -> None:
        # Build existing failures
        existing: dict = {}
        if prior_attempts > 0:
            monkeypatch.setenv("RUN_ID", "2000")
            existing["CI"] = [
                {"run": 999 + i, "sha": f"sha{i}", "url": f"https://example.com/{i}"}
                for i in range(prior_attempts)
            ]

        if existing:
            tracker = _tracker_comment(existing)
            mock_subprocess["gh api repos/owner/repo/issues/42/comments -X GET"] = (
                _comments(tracker)
            )
            mock_subprocess["gh api repos/owner/repo/issues/comments/500 -X PATCH"] = (
                _ok_post()
            )
            mock_subprocess["gh api repos/owner/repo/issues/42/labels -X POST"] = (
                _ok_post()
            )
        else:
            mock_subprocess["gh api repos/owner/repo/issues/42/comments -X GET"] = (
                _no_comments()
            )
            mock_subprocess["gh api repos/owner/repo/issues/42/comments -X POST"] = (
                _ok_post()
            )

        main()

        cap = _CallCapture(mock_subprocess)
        # Find the POST or PATCH body
        bodies = [b for b in cap.call_bodies if b and "body" in b]
        assert bodies, "Expected at least one API call with a body"
        comment_body = bodies[0]["body"]

        for fragment in expected_fragments:
            assert fragment in comment_body, (
                f"Expected '{fragment}' in comment body:\n{comment_body}"
            )


# -----------------------------------------------------------------------
# main() — label failure is non-fatal
# -----------------------------------------------------------------------


class TestLabelFailure:
    def test_label_error_does_not_crash(
        self, tracker_env, mock_subprocess, capsys
    ) -> None:
        existing_failures = {
            "CI": [{"run": 999, "sha": "old1234", "url": "https://example.com/999"}]
        }
        tracker = _tracker_comment(existing_failures)

        mock_subprocess["gh api repos/owner/repo/issues/42/comments -X GET"] = (
            _comments(tracker)
        )
        mock_subprocess["gh api repos/owner/repo/issues/comments/500 -X PATCH"] = (
            _ok_post()
        )
        mock_subprocess["gh api repos/owner/repo/issues/42/labels -X POST"] = completed(
            1, stderr="Label not found"
        )

        # Should not raise
        main()

        captured = capsys.readouterr()
        assert "Could not add label" in captured.out
