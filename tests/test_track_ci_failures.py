"""Tests for .github/scripts/track_ci_failures.py."""

from __future__ import annotations

import json
import subprocess

import pytest
from track_ci_failures import TRACKER_MARKER, gh_api, main

from tests.helpers import completed

# -----------------------------------------------------------------------
# gh_api
# -----------------------------------------------------------------------


class TestGhApi:
    def test_get_returns_parsed_json(self, mock_subprocess) -> None:
        mock_subprocess["gh api"] = completed(0, stdout='[{"id": 1}]')
        assert gh_api("repos/o/r/issues") == [{"id": 1}]

    def test_post_sends_body(self, mock_subprocess) -> None:
        mock_subprocess["gh api"] = completed(0, stdout='{"id": 99}')
        result = gh_api(
            "repos/o/r/issues/1/comments",
            method="POST",
            body={"body": "hi"},
        )
        assert result == {"id": 99}
        kw = mock_subprocess.calls[0][1]
        assert json.loads(kw["input"]) == {"body": "hi"}

    def test_empty_response_returns_none(self, mock_subprocess) -> None:
        mock_subprocess["gh api"] = completed(0, stdout="  \n  ")
        assert gh_api("repos/o/r/issues") is None

    def test_failure_raises(self, mock_subprocess) -> None:
        mock_subprocess["gh api"] = completed(1, stderr="Not Found")
        with pytest.raises(RuntimeError, match="Not Found"):
            gh_api("repos/o/r/issues")

    def test_no_paginate_flag(self, mock_subprocess) -> None:
        """H1+H3: --paginate was removed to avoid concatenated JSON crash."""
        mock_subprocess["gh api"] = completed(0, stdout="{}")
        gh_api("endpoint")
        args = mock_subprocess.calls[0][0][0]
        assert "--paginate" not in args


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

_API = "gh api repos/owner/repo"


def _tracker_comment(
    failures: dict,
) -> dict:
    """Build a mock tracker comment with embedded failure state."""
    fj = json.dumps(failures)
    return {
        "id": 500,
        "body": f"{TRACKER_MARKER}\n<!-- failures:{fj} -->\ntracked",
    }


def _empty() -> subprocess.CompletedProcess[str]:
    return completed(0, stdout="[]")


def _list(*items: dict) -> subprocess.CompletedProcess[str]:
    return completed(0, stdout=json.dumps(list(items)))


def _ok() -> subprocess.CompletedProcess[str]:
    return completed(0, stdout='{"id": 1}')


def _posted_body(mock_sub, index: int = 1) -> dict:
    """Extract JSON body from the Nth subprocess.run call."""
    kw = mock_sub.calls[index][1]
    return json.loads(kw["input"])


# -----------------------------------------------------------------------
# main() — first failure
# -----------------------------------------------------------------------


class TestFirstFailure:
    def test_creates_comment(self, tracker_env, mock_subprocess, capsys) -> None:
        mock_subprocess[f"{_API}/issues/42/comments -X GET"] = _empty()
        mock_subprocess[f"{_API}/issues/42/comments -X POST"] = _ok()
        main()
        assert "Created tracker comment" in capsys.readouterr().out
        body = _posted_body(mock_subprocess)
        assert TRACKER_MARKER in body["body"]
        assert "attempt 1/2" in body["body"]


# -----------------------------------------------------------------------
# main() — subsequent failure (existing tracker)
# -----------------------------------------------------------------------


class TestSubsequentFailure:
    def test_updates_and_marks_exhausted(
        self, tracker_env, mock_subprocess, capsys
    ) -> None:
        tracker = _tracker_comment(
            {"CI": [{"run": 999, "sha": "old1234", "url": "https://example.com/999"}]}
        )
        mock_subprocess[f"{_API}/issues/42/comments -X GET"] = _list(tracker)
        mock_subprocess[f"{_API}/issues/comments/500 -X PATCH"] = _ok()
        mock_subprocess[f"{_API}/issues/42/labels -X POST"] = _ok()
        main()
        assert "Updated tracker comment" in capsys.readouterr().out
        body = _posted_body(mock_subprocess)
        assert "attempt 2/2" in body["body"]
        assert "giving up" in body["body"]


# -----------------------------------------------------------------------
# main() — dedup
# -----------------------------------------------------------------------


class TestDedup:
    def test_skips_duplicate_run(self, tracker_env, mock_subprocess, capsys) -> None:
        tracker = _tracker_comment(
            {"CI": [{"run": 1001, "sha": "abc1234", "url": "https://example.com/1001"}]}
        )
        mock_subprocess[f"{_API}/issues/42/comments -X GET"] = _list(tracker)
        main()
        assert "Already tracked run 1001" in capsys.readouterr().out

    def test_skips_exhausted_workflow(
        self, tracker_env, mock_subprocess, monkeypatch, capsys
    ) -> None:
        monkeypatch.setenv("RUN_ID", "2000")
        tracker = _tracker_comment(
            {
                "CI": [
                    {"run": 999, "sha": "old1", "url": "https://example.com/999"},
                    {"run": 1000, "sha": "old2", "url": "https://example.com/1000"},
                ]
            }
        )
        mock_subprocess[f"{_API}/issues/42/comments -X GET"] = _list(tracker)
        main()
        assert "already at 2 attempts" in capsys.readouterr().out


# -----------------------------------------------------------------------
# main() — exhaustion + labeling
# -----------------------------------------------------------------------


class TestExhaustion:
    def test_labels_when_all_exhausted(
        self, tracker_env, mock_subprocess, capsys
    ) -> None:
        tracker = _tracker_comment(
            {"CI": [{"run": 999, "sha": "old1", "url": "https://example.com/999"}]}
        )
        mock_subprocess[f"{_API}/issues/42/comments -X GET"] = _list(tracker)
        mock_subprocess[f"{_API}/issues/comments/500 -X PATCH"] = _ok()
        mock_subprocess[f"{_API}/issues/42/labels -X POST"] = _ok()
        main()
        out = capsys.readouterr().out
        assert "Added needs-human-review label" in out
        label_body = _posted_body(mock_subprocess, 2)
        assert label_body == {"labels": ["needs-human-review"]}

    def test_no_label_when_partially_exhausted(
        self, tracker_env, mock_subprocess, monkeypatch, capsys
    ) -> None:
        """Two workflows: CI exhausted, Deploy has 1 attempt. No label."""
        monkeypatch.setenv("WORKFLOW_NAME", "Deploy")
        monkeypatch.setenv("RUN_ID", "2000")
        tracker = _tracker_comment(
            {
                "CI": [
                    {"run": 999, "sha": "old1", "url": "https://example.com/999"},
                    {"run": 1000, "sha": "old2", "url": "https://example.com/1000"},
                ]
            }
        )
        mock_subprocess[f"{_API}/issues/42/comments -X GET"] = _list(tracker)
        mock_subprocess[f"{_API}/issues/comments/500 -X PATCH"] = _ok()
        main()
        out = capsys.readouterr().out
        assert "Updated tracker comment" in out
        assert "needs-human-review" not in out

    def test_label_error_non_fatal(self, tracker_env, mock_subprocess, capsys) -> None:
        tracker = _tracker_comment(
            {"CI": [{"run": 999, "sha": "old1", "url": "https://example.com/999"}]}
        )
        mock_subprocess[f"{_API}/issues/42/comments -X GET"] = _list(tracker)
        mock_subprocess[f"{_API}/issues/comments/500 -X PATCH"] = _ok()
        mock_subprocess[f"{_API}/issues/42/labels -X POST"] = completed(
            1, stderr="Label not found"
        )
        main()  # should not raise
        assert "Could not add label" in capsys.readouterr().out


# -----------------------------------------------------------------------
# Comment content
# -----------------------------------------------------------------------


class TestCommentContent:
    @pytest.mark.parametrize(
        ("prior_attempts", "expected_fragments"),
        [
            pytest.param(0, ["attempt 1/2", "failed on this PR"], id="first"),
            pytest.param(1, ["attempt 2/2", "giving up", "exhausted"], id="exhausted"),
        ],
    )
    def test_body_varies_by_attempt(
        self,
        tracker_env,
        mock_subprocess,
        capsys,
        monkeypatch,
        prior_attempts: int,
        expected_fragments: list[str],
    ) -> None:
        existing: dict = {}
        if prior_attempts > 0:
            monkeypatch.setenv("RUN_ID", "2000")
            existing["CI"] = [
                {"run": 999 + i, "sha": f"s{i}", "url": f"https://example.com/{i}"}
                for i in range(prior_attempts)
            ]

        if existing:
            mock_subprocess[f"{_API}/issues/42/comments -X GET"] = _list(
                _tracker_comment(existing)
            )
            mock_subprocess[f"{_API}/issues/comments/500 -X PATCH"] = _ok()
            mock_subprocess[f"{_API}/issues/42/labels -X POST"] = _ok()
        else:
            mock_subprocess[f"{_API}/issues/42/comments -X GET"] = _empty()
            mock_subprocess[f"{_API}/issues/42/comments -X POST"] = _ok()

        main()

        # Find the POST or PATCH body
        bodies = [
            json.loads(c[1]["input"])
            for c in mock_subprocess.calls
            if c[1].get("input")
        ]
        comment_body = next(b["body"] for b in bodies if "body" in b)
        for frag in expected_fragments:
            assert frag in comment_body, f"Missing '{frag}' in:\n{comment_body}"
