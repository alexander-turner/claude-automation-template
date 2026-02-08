"""Shared fixtures for testing automation scripts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from tests.helpers import completed as _completed_fn

# ---------------------------------------------------------------------------
# Fixtures: temporary project directory
# ---------------------------------------------------------------------------


@pytest.fixture()
def project_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an empty project directory and chdir into it."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def package_json(project_dir: Path):
    """Helper to write a package.json with the given scripts dict."""

    def _write(scripts: dict[str, str] | None = None) -> Path:
        data: dict[str, Any] = {"name": "test"}
        if scripts is not None:
            data["scripts"] = scripts
        path = project_dir / "package.json"
        path.write_text(json.dumps(data))
        return path

    return _write


# ---------------------------------------------------------------------------
# Fixtures: subprocess mocking
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_subprocess(monkeypatch: pytest.MonkeyPatch):
    """Replace subprocess.run with a mock that returns configurable results.

    Returns a dict-backed dispatcher: set ``mock[cmd_prefix] = CompletedProcess``
    to control what each command returns. Unmatched commands succeed by default.
    """
    results: dict[str, subprocess.CompletedProcess[str]] = {}
    mock = MagicMock(side_effect=lambda *a, **kw: _match(a, kw, results))
    monkeypatch.setattr(subprocess, "run", mock)

    class _Proxy:
        """Allows setting results[key] and inspecting calls."""

        def __setitem__(self, key: str, value: subprocess.CompletedProcess[str]):
            results[key] = value

        @property
        def calls(self) -> list:
            return mock.call_args_list

        @property
        def mock(self) -> MagicMock:
            return mock

    return _Proxy()


def _match(
    args: tuple,
    kwargs: dict,
    results: dict[str, subprocess.CompletedProcess[str]],
) -> subprocess.CompletedProcess[str]:
    """Find the first matching result by prefix of the command string."""
    cmd = args[0] if args else kwargs.get("args", "")
    if isinstance(cmd, list):
        cmd = " ".join(cmd)
    for prefix, result in results.items():
        if cmd.startswith(prefix) or prefix in cmd:
            return result
    return _completed_fn()


# ---------------------------------------------------------------------------
# Fixtures: environment helpers for track_ci_failures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tracker_env(monkeypatch: pytest.MonkeyPatch):
    """Set default env vars for track_ci_failures.main()."""
    defaults = {
        "GITHUB_REPOSITORY": "owner/repo",
        "PR_NUMBER": "42",
        "WORKFLOW_NAME": "CI",
        "RUN_URL": "https://github.com/owner/repo/actions/runs/1001",
        "RUN_ID": "1001",
        "HEAD_SHA": "abc1234def5678",
    }
    for k, v in defaults.items():
        monkeypatch.setenv(k, v)
    return defaults
