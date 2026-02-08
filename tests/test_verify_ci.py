"""Tests for .claude/hooks/verify_ci.py — the Stop hook."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from verify_ci import _has_script, _retry_file, _run_check, main

from tests.helpers import completed, parse_json_output

# -----------------------------------------------------------------------
# _retry_file
# -----------------------------------------------------------------------


class TestRetryFile:
    def test_deterministic(self) -> None:
        assert _retry_file("/some/path") == _retry_file("/some/path")

    def test_different_dirs_differ(self) -> None:
        assert _retry_file("/a") != _retry_file("/b")

    def test_lives_in_tmp(self) -> None:
        assert str(_retry_file("/x")).startswith("/tmp/claude-stop-attempts-")


# -----------------------------------------------------------------------
# _has_script
# -----------------------------------------------------------------------


class TestHasScript:
    @pytest.mark.parametrize(
        ("pkg", "name", "expected"),
        [
            pytest.param(
                {"scripts": {"test": "jest"}},
                "test",
                True,
                id="real-script",
            ),
            pytest.param(
                {"scripts": {"test": "echo 'ERROR: Configure test' && exit 1"}},
                "test",
                False,
                id="placeholder-script",
            ),
            pytest.param(
                {"scripts": {}},
                "test",
                False,
                id="empty-scripts",
            ),
            pytest.param(
                {},
                "test",
                False,
                id="no-scripts-key",
            ),
            pytest.param(
                {"scripts": {"test": ""}},
                "test",
                False,
                id="empty-string",
            ),
            pytest.param(
                {"scripts": {"lint": "eslint ."}},
                "test",
                False,
                id="wrong-name",
            ),
        ],
    )
    def test_has_script(self, pkg: dict, name: str, expected: bool) -> None:
        assert _has_script(pkg, name) is expected


# -----------------------------------------------------------------------
# _run_check
# -----------------------------------------------------------------------


class TestRunCheck:
    def test_passing_check(self, mock_subprocess) -> None:
        mock_subprocess["pnpm test"] = completed(0)
        passed, output = _run_check("tests", "pnpm test")
        assert passed is True
        assert output == ""

    def test_failing_check(self, mock_subprocess) -> None:
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL src/foo.test.ts")
        passed, output = _run_check("tests", "pnpm test")
        assert passed is False
        assert "=== tests ===" in output
        assert "FAIL src/foo.test.ts" in output


# -----------------------------------------------------------------------
# main() integration tests
# -----------------------------------------------------------------------


class TestMainApprove:
    """Cases where main() should output {"decision": "approve"}."""

    def test_no_package_json_no_pyproject(
        self, project_dir: Path, mock_subprocess, capsys
    ) -> None:
        """No config files at all → nothing to check → approve."""
        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "approve"

    def test_all_checks_pass(
        self, project_dir: Path, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest", "lint": "eslint ."})
        mock_subprocess["pnpm test"] = completed(0)
        mock_subprocess["pnpm lint"] = completed(0)

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "approve"

    def test_retry_file_cleaned_on_pass(
        self, project_dir: Path, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(0)

        # Pre-seed a retry file
        rf = _retry_file(str(project_dir))
        rf.write_text("1")

        main()
        assert not rf.exists(), "Retry file should be cleaned up after all checks pass"


class TestMainBlock:
    """Cases where main() should output {"decision": "block"}."""

    def test_first_failure(
        self, project_dir: Path, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "block"
        assert "attempt 1/3" in result["reason"]

    def test_increments_retry_counter(
        self, project_dir: Path, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")

        rf = _retry_file(str(project_dir))
        rf.write_text("1")

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "block"
        assert "attempt 2/3" in result["reason"]
        assert rf.read_text() == "2"


class TestMainExhaustion:
    """Cases where retries are exhausted → approve with warning."""

    def test_exhaustion_approves(
        self, project_dir: Path, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")

        rf = _retry_file(str(project_dir))
        rf.write_text("2")  # Next attempt will be 3 = MAX_RETRIES

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "approve"
        assert "3 attempts" in result["reason"]
        assert not rf.exists(), "Retry file should be cleaned up after exhaustion"

    def test_custom_max_retries(
        self,
        project_dir: Path,
        package_json,
        mock_subprocess,
        capsys,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("MAX_STOP_RETRIES", "1")
        # Re-import to pick up the new env var
        import verify_ci

        monkeypatch.setattr(verify_ci, "MAX_RETRIES", 1)

        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "approve"
        assert "1 attempts" in result["reason"]


class TestMainCorruptRetryFile:
    def test_corrupt_file_resets_to_one(
        self, project_dir: Path, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")

        rf = _retry_file(str(project_dir))
        rf.write_text("not-a-number")

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "block"
        assert "attempt 1/3" in result["reason"]


class TestMainPythonChecks:
    """Tests for the Python-specific check paths (ruff, pytest)."""

    def test_pyproject_triggers_ruff(
        self,
        project_dir: Path,
        mock_subprocess,
        capsys,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (project_dir / "pyproject.toml").write_text("[project]\nname='x'")
        monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")

        mock_subprocess["ruff check"] = completed(0)

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "approve"

    def test_uv_lock_uses_uv_prefix(
        self,
        project_dir: Path,
        mock_subprocess,
        capsys,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (project_dir / "pyproject.toml").write_text("[project]\nname='x'")
        (project_dir / "uv.lock").write_text("")
        (project_dir / "tests").mkdir()
        monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")

        mock_subprocess["uv run ruff"] = completed(0)
        mock_subprocess["uv run pytest"] = completed(0)

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "approve"

    @pytest.mark.parametrize(
        ("failing_cmd", "expected_name"),
        [
            pytest.param("ruff", "ruff", id="ruff-fails"),
            pytest.param("pytest", "pytest", id="pytest-fails"),
        ],
    )
    def test_python_check_failure_blocks(
        self,
        project_dir: Path,
        mock_subprocess,
        capsys,
        monkeypatch: pytest.MonkeyPatch,
        failing_cmd: str,
        expected_name: str,
    ) -> None:
        (project_dir / "pyproject.toml").write_text("[project]\nname='x'")
        (project_dir / "tests").mkdir()
        monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")

        mock_subprocess["ruff check"] = completed(
            1 if failing_cmd == "ruff" else 0, stderr="error"
        )
        mock_subprocess["pytest"] = completed(
            1 if failing_cmd == "pytest" else 0, stderr="error"
        )

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "block"
        assert expected_name in result["reason"]

    def test_no_tests_dir_skips_pytest(
        self,
        project_dir: Path,
        mock_subprocess,
        capsys,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (project_dir / "pyproject.toml").write_text("[project]\nname='x'")
        monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")

        mock_subprocess["ruff check"] = completed(0)

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "approve"
        # pytest should not have been called
        calls = [str(c) for c in mock_subprocess.calls]
        assert not any("pytest" in c for c in calls)
