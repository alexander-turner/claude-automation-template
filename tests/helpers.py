"""Shared helpers for automation script tests."""

from __future__ import annotations

import json
import subprocess

import pytest


def completed(
    returncode: int = 0, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    """Build a CompletedProcess for use with the mock_subprocess fixture."""
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


def parse_json_output(capsys: pytest.CaptureFixture[str]) -> dict:
    """Parse the JSON that verify_ci.py prints to stdout."""
    captured = capsys.readouterr()
    lines = [line for line in captured.out.strip().splitlines() if line.strip()]
    return json.loads(lines[-1])
