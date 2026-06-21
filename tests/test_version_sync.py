"""Contract test: tool version pins in session-setup.sh must match .pre-commit-config.yaml.

Versioned tools (ruff, zizmor) are pinned in two places:
  - .claude/hooks/session-setup.sh (uv_install_if_missing calls)
  - .pre-commit-config.yaml (rev: and additional_dependencies:)

A mismatch causes local hooks to format differently from CI.  This test is the
machine-checkable form of the comment in session-setup.sh that says "keep in sync".
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SESSION_SETUP = REPO_ROOT / ".claude" / "hooks" / "session-setup.sh"
PRE_COMMIT_CFG = REPO_ROOT / ".pre-commit-config.yaml"


def _session_setup_pin(tool: str) -> str:
    """Return the pinned version string for *tool* from session-setup.sh."""
    text = SESSION_SETUP.read_text()
    # Matches: uv_install_if_missing ruff "ruff==0.14.5"
    m = re.search(
        rf'uv_install_if_missing\s+{re.escape(tool)}\s+"[^"]*?==([^"]+)"',
        text,
    )
    assert m, f"Could not find uv_install_if_missing {tool} pin in session-setup.sh"
    return m.group(1)


def test_ruff_version_matches_pre_commit() -> None:
    """ruff pin in session-setup.sh must match the ruff-pre-commit rev: in .pre-commit-config.yaml."""
    setup_ver = _session_setup_pin("ruff")

    text = PRE_COMMIT_CFG.read_text()
    # The ruff-pre-commit repo uses a tag like "v0.14.5"
    m = re.search(r"astral-sh/ruff-pre-commit.*?rev:\s+v?(\S+)", text, re.DOTALL)
    assert m, "Could not find astral-sh/ruff-pre-commit rev: in .pre-commit-config.yaml"
    precommit_ver = m.group(1)

    assert setup_ver == precommit_ver, (
        f"ruff version mismatch: session-setup.sh pins {setup_ver!r} "
        f"but .pre-commit-config.yaml uses {precommit_ver!r}. "
        "Update both together."
    )


def test_zizmor_version_matches_pre_commit() -> None:
    """zizmor pin in session-setup.sh must match the additional_dependencies in .pre-commit-config.yaml."""
    setup_ver = _session_setup_pin("zizmor")

    text = PRE_COMMIT_CFG.read_text()
    m = re.search(r"zizmor==(\S+?)\"", text)
    assert m, (
        "Could not find zizmor== pin in .pre-commit-config.yaml additional_dependencies"
    )
    precommit_ver = m.group(1)

    assert setup_ver == precommit_ver, (
        f"zizmor version mismatch: session-setup.sh pins {setup_ver!r} "
        f"but .pre-commit-config.yaml uses {precommit_ver!r}. "
        "Update both together."
    )
