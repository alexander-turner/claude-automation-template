"""Shared fixtures for testing automation scripts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from tests.helpers import completed as _completed_fn


@pytest.fixture()
def project_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an empty project directory and chdir into it."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def package_json(project_dir: Path):
    """Factory to write a package.json with given scripts."""

    def _write(scripts: dict[str, str] | None = None) -> Path:
        data: dict[str, Any] = {"name": "test"}
        if scripts is not None:
            data["scripts"] = scripts
        path = project_dir / "package.json"
        path.write_text(json.dumps(data))
        return path

    return _write


@pytest.fixture()
def mock_subprocess(monkeypatch: pytest.MonkeyPatch):
    """Replace subprocess.run with a configurable mock.

    Usage: ``mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")``

    Matching uses startswith on the command string. Commands without a
    registered prefix return success by default.
    """
    results: dict[str, subprocess.CompletedProcess[str]] = {}
    mock = MagicMock(side_effect=lambda *a, **kw: _match(a, kw, results))
    monkeypatch.setattr(subprocess, "run", mock)

    class _Proxy:
        def __setitem__(self, key, value):
            results[key] = value

        @property
        def calls(self):
            return mock.call_args_list

    return _Proxy()


def _match(args, kwargs, results):
    """Match command against registered prefixes (startswith only)."""
    cmd = args[0] if args else kwargs.get("args", "")
    if isinstance(cmd, list):
        cmd = " ".join(cmd)
    # Try longest prefix first for deterministic matching
    for prefix in sorted(results, key=len, reverse=True):
        if cmd.startswith(prefix):
            return results[prefix]
    return _completed_fn()


@pytest.fixture()
def tracker_env(monkeypatch: pytest.MonkeyPatch):
    """Set default env vars for track_ci_failures.main()."""
    env = {
        "GITHUB_REPOSITORY": "owner/repo",
        "PR_NUMBER": "42",
        "WORKFLOW_NAME": "CI",
        "RUN_URL": "https://github.com/owner/repo/actions/runs/1001",
        "RUN_ID": "1001",
        "HEAD_SHA": "abc1234def5678",
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return env
