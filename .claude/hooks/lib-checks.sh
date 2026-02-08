#!/bin/bash
# Shared helpers for Claude Code hook scripts

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR" || exit 1

exists() { command -v "$1" &>/dev/null; }

has_script() {
  [[ -f package.json ]] &&
    jq -e ".scripts.$1" package.json &>/dev/null &&
    ! jq -r ".scripts.$1" package.json | grep -q "ERROR: Configure"
}

# Portable hash for generating stable file keys from paths.
# Works on both Linux (cksum) and macOS (cksum).
_path_hash() { printf '%s' "$1" | cksum | cut -d' ' -f1; }

# Path to the stop-hook retry counter for this project.
stop_retry_file() { echo "/tmp/claude-stop-attempts-$(_path_hash "$PROJECT_DIR")"; }
