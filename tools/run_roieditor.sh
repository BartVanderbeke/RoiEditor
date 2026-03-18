#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -n "${WSL_DISTRO_NAME:-}" ] && [ -x "$SCRIPT_DIR/venv-wsl/bin/python" ]; then
    exec "$SCRIPT_DIR/venv-wsl/bin/python" -m RoiEditor "$@"
fi

if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    exec "$SCRIPT_DIR/.venv/bin/python" -m RoiEditor "$@"
fi

exec python3 -m RoiEditor "$@"
