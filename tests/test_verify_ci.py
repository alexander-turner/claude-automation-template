"""Tests for .claude/hooks/verify_ci.py — the Stop hook."""

from __future__ import annotations

import importlib
import json
import shutil

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
            pytest.param({"scripts": {"test": "jest"}}, "test", True, id="real"),
            pytest.param(
                {"scripts": {"test": "echo 'ERROR: Configure test' && exit 1"}},
                "test",
                False,
                id="placeholder",
            ),
            pytest.param({"scripts": {}}, "test", False, id="empty-scripts"),
            pytest.param({}, "test", False, id="no-scripts-key"),
            pytest.param({"scripts": {"test": ""}}, "test", False, id="empty-str"),
            pytest.param(
                {"scripts": {"lint": "eslint ."}}, "test", False, id="wrong-name"
            ),
        ],
    )
    def test_has_script(self, pkg: dict, name: str, expected: bool) -> None:
        assert _has_script(pkg, name) is expected


# -----------------------------------------------------------------------
# _run_check
# -----------------------------------------------------------------------


class TestRunCheck:
    def test_passing(self, mock_subprocess) -> None:
        mock_subprocess["pnpm test"] = completed(0)
        passed, output = _run_check("tests", "pnpm test")
        assert passed is True
        assert output == ""

    def test_failing(self, mock_subprocess) -> None:
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL src/foo.test.ts")
        passed, output = _run_check("tests", "pnpm test")
        assert passed is False
        assert "=== tests FAILED ===" in output
        assert "FAIL src/foo.test.ts" in output


# -----------------------------------------------------------------------
# main() — approve
# -----------------------------------------------------------------------


class TestMainApprove:
    def test_no_config_files(self, project_dir, mock_subprocess, capsys) -> None:
        main()
        assert parse_json_output(capsys)["decision"] == "approve"

    def test_all_pass(self, project_dir, package_json, mock_subprocess, capsys) -> None:
        package_json({"test": "jest", "lint": "eslint ."})
        mock_subprocess["pnpm test"] = completed(0)
        mock_subprocess["pnpm lint"] = completed(0)
        main()
        assert parse_json_output(capsys)["decision"] == "approve"

    def test_retry_file_cleaned_on_pass(
        self, project_dir, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(0)
        rf = _retry_file(str(project_dir))
        rf.write_text("1")
        main()
        assert not rf.exists()


# -----------------------------------------------------------------------
# main() — block
# -----------------------------------------------------------------------


class TestMainBlock:
    def test_first_failure(
        self, project_dir, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")
        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "block"
        assert "attempt 1/3" in result["reason"]

    def test_increments_counter(
        self, project_dir, package_json, mock_subprocess, capsys
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


# -----------------------------------------------------------------------
# main() — exhaustion
# -----------------------------------------------------------------------


class TestMainExhaustion:
    def test_exhaustion_approves(
        self, project_dir, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")
        _retry_file(str(project_dir)).write_text("2")
        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "approve"
        assert "3 attempts" in result["reason"]
        assert not _retry_file(str(project_dir)).exists()

    def test_custom_max_retries_via_env(
        self,
        project_dir,
        package_json,
        mock_subprocess,
        capsys,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify MAX_STOP_RETRIES env var works end-to-end."""
        monkeypatch.setenv("MAX_STOP_RETRIES", "1")
        import verify_ci

        importlib.reload(verify_ci)
        try:
            package_json({"test": "jest"})
            mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")
            verify_ci.main()
            result = parse_json_output(capsys)
            assert result["decision"] == "approve"
            assert "1 attempt." in result["reason"]
        finally:
            # Restore module state for other tests
            monkeypatch.delenv("MAX_STOP_RETRIES")
            importlib.reload(verify_ci)

    def test_pluralization(
        self, project_dir, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")
        _retry_file(str(project_dir)).write_text("2")
        main()
        # Default MAX_RETRIES=3, so "3 attempts" (plural)
        assert "3 attempts" in parse_json_output(capsys)["reason"]


class TestMainCorruptRetryFile:
    def test_resets_to_one(
        self, project_dir, package_json, mock_subprocess, capsys
    ) -> None:
        package_json({"test": "jest"})
        mock_subprocess["pnpm test"] = completed(1, stderr="FAIL")
        _retry_file(str(project_dir)).write_text("not-a-number")
        main()
        assert "attempt 1/3" in parse_json_output(capsys)["reason"]


# -----------------------------------------------------------------------
# Python checks
# -----------------------------------------------------------------------


class TestPythonChecks:
    def test_pyproject_triggers_ruff(
        self, project_dir, mock_subprocess, capsys, monkeypatch
    ) -> None:
        (project_dir / "pyproject.toml").write_text("[project]\nname='x'")
        monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
        mock_subprocess["ruff check"] = completed(0)
        main()
        assert parse_json_output(capsys)["decision"] == "approve"

    def test_uv_lock_uses_uv_prefix(
        self, project_dir, mock_subprocess, capsys, monkeypatch
    ) -> None:
        (project_dir / "pyproject.toml").write_text("[project]\nname='x'")
        (project_dir / "uv.lock").write_text("")
        (project_dir / "tests").mkdir()
        monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
        # Register "uv run" prefixed commands — without uv prefix they won't match
        mock_subprocess["uv run ruff"] = completed(0)
        mock_subprocess["uv run pytest"] = completed(0)
        main()
        assert parse_json_output(capsys)["decision"] == "approve"
        # Verify all subprocess calls used the uv prefix
        for call in mock_subprocess.calls:
            cmd = call[0][0] if call[0] else call[1].get("args", "")
            # Handle both list (from shlex.split) and string formats
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            assert "uv run" in cmd_str, f"Expected 'uv run' prefix in: {cmd_str}"

    @pytest.mark.parametrize(
        ("failing_cmd", "expected_name"),
        [
            pytest.param("ruff", "ruff", id="ruff-fails"),
            pytest.param("pytest", "pytest", id="pytest-fails"),
        ],
    )
    def test_failure_blocks(
        self,
        project_dir,
        mock_subprocess,
        capsys,
        monkeypatch,
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
        self, project_dir, mock_subprocess, capsys, monkeypatch
    ) -> None:
        (project_dir / "pyproject.toml").write_text("[project]\nname='x'")
        monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
        mock_subprocess["ruff check"] = completed(0)
        main()
        assert parse_json_output(capsys)["decision"] == "approve"
        cmds = [str(c[0][0]) for c in mock_subprocess.calls]
        assert not any("pytest" in c for c in cmds)

    def test_ruff_missing_warns(
        self, project_dir, mock_subprocess, capsys, monkeypatch
    ) -> None:
        """M5: warn when pyproject.toml exists but ruff isn't available."""
        (project_dir / "pyproject.toml").write_text("[project]\nname='x'")
        monkeypatch.setattr(shutil, "which", lambda _cmd: None)
        main()
        captured = capsys.readouterr()
        result = json.loads(captured.out.strip().splitlines()[-1])
        assert result["decision"] == "approve"
        assert "ruff not found" in captured.err


# -----------------------------------------------------------------------
# Combined Node.js + Python
# -----------------------------------------------------------------------


class TestCombinedChecks:
    def test_node_and_python_failures_both_reported(
        self, project_dir, package_json, mock_subprocess, capsys, monkeypatch
    ) -> None:
        """M4: Both ecosystems fail → all failures in output."""
        package_json({"test": "jest"})
        (project_dir / "pyproject.toml").write_text("[project]\nname='x'")
        monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")

        mock_subprocess["pnpm test"] = completed(1, stderr="jest FAIL")
        mock_subprocess["ruff check"] = completed(1, stderr="ruff error")

        main()
        result = parse_json_output(capsys)
        assert result["decision"] == "block"
        assert "tests failed" in result["reason"]
        assert "ruff failed" in result["reason"]
