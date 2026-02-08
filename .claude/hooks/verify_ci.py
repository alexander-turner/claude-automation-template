#!/usr/bin/env python3
"""Stop hook: verifies CI checks pass before allowing Claude to complete.

Outputs JSON to stdout:
  {"decision": "approve"}               — all checks passed (or retries exhausted)
  {"decision": "block", "reason": "…"}  — checks failed, Claude should keep fixing

Tracks retry attempts across Stop invocations within a session. Gives up after
MAX_STOP_RETRIES (default 3) to prevent infinite token burn. The retry counter
is reset on each new session by session-setup.sh.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

# Configurable via environment
MAX_RETRIES = int(os.environ.get("MAX_STOP_RETRIES", "3"))


def _retry_file(project_dir: str) -> Path:
    """Return a stable path for the retry counter, keyed on the project directory."""
    dir_hash = sha256(project_dir.encode()).hexdigest()[:16]
    return Path(f"/tmp/claude-stop-attempts-{dir_hash}")


def _has_script(pkg: dict, name: str) -> bool:
    """Check if a package.json script exists and isn't a placeholder."""
    script = pkg.get("scripts", {}).get(name, "")
    return bool(script) and "ERROR: Configure" not in script


def _run_check(name: str, cmd: str) -> tuple[bool, str]:
    """Run a check command. Returns (passed, output)."""
    print(f"Running {name}...", file=sys.stderr)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return True, ""
    output = result.stdout + result.stderr
    return False, f"=== {name} ===\n{output}\n"


def main() -> None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    os.chdir(project_dir)

    # --- Retry tracking ---
    retry_file = _retry_file(project_dir)
    attempt = 1
    if retry_file.exists():
        try:
            attempt = int(retry_file.read_text().strip()) + 1
        except (ValueError, OSError):
            attempt = 1
    retry_file.write_text(str(attempt))

    # --- Determine which checks to run ---
    failures: list[str] = []
    outputs: list[str] = []

    def check(name: str, cmd: str) -> None:
        passed, output = _run_check(name, cmd)
        if not passed:
            failures.append(name)
            outputs.append(output)

    # Node.js checks
    pkg_path = Path("package.json")
    if pkg_path.exists():
        pkg = json.loads(pkg_path.read_text())
        if _has_script(pkg, "test"):
            check("tests", "pnpm test")
        if _has_script(pkg, "lint"):
            check("lint", "pnpm lint")
        if _has_script(pkg, "check"):
            check("typecheck", "pnpm check")

    # Python checks
    has_pyproject = Path("pyproject.toml").exists()
    has_uvlock = Path("uv.lock").exists()
    if has_pyproject or has_uvlock:
        prefix = "uv run " if has_uvlock and shutil.which("uv") else ""
        if prefix or shutil.which("ruff"):
            check("ruff", f"{prefix}ruff check .")
        if Path("tests").is_dir() and (prefix or shutil.which("pytest")):
            check("pytest", f"{prefix}pytest")

    # --- Produce result ---
    if not failures:
        retry_file.unlink(missing_ok=True)
        print(json.dumps({"decision": "approve"}))
        return

    if attempt >= MAX_RETRIES:
        retry_file.unlink(missing_ok=True)
        failed_str = ", ".join(failures)
        print(
            f"WARNING: Giving up after {attempt} attempts. "
            f"Failures remain: {failed_str}",
            file=sys.stderr,
        )
        print(
            json.dumps(
                {
                    "decision": "approve",
                    "reason": (
                        f"Approved despite failures after {attempt} attempts. "
                        f"Remaining: {failed_str}\nHuman review needed."
                    ),
                }
            )
        )
        return

    output_text = "\n".join(outputs)
    failed_str = ", ".join(f"{f} failed" for f in failures)
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": (
                    f"CI failed (attempt {attempt}/{MAX_RETRIES}): "
                    f"{failed_str}.\n\n{output_text}"
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
