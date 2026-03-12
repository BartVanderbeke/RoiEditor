#!/usr/bin/env bash
set -euo pipefail

DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
DESKTOP_DIR="${DESKTOP_DIR:-$HOME/Desktop}"

echo "[1/4] Searching for python3"
if command -v python3 >/dev/null 2>&1; then
    echo "[1/4] [OK] python3 is already available, no need to install."
else
    echo "[1/4] [WARNING] python3 was not found. Please install python3 and try again."
    exit 1
fi

echo "[2/4] Searching for pip"
if python3 -m pip --version >/dev/null 2>&1; then
    echo "[2/4] [OK] pip is already available, no need to install."
else
    echo "[2/4] [WARNING] pip was not found. Please install python3-pip and try again."
    exit 1
fi

echo "[3/4] Searching for cellpose"
if python3 -m pip show cellpose >/dev/null 2>&1; then
    echo "[3/4] [OK] cellpose has already been installed."
else
    echo "[3/4] [WARNING] cellpose has not yet been installed."
fi

if [[ -f "$DESKTOP_DIR/cellpose.desktop" ]]; then
    echo "[3/4] [OK] Launcher for cellpose found on $DESKTOP_DIR."
else
    echo "[3/4] [WARNING] Launcher not found for cellpose."
fi

echo "[4/4] Searching for RoiEditor"
if python3 -m pip show RoiEditor >/dev/null 2>&1; then
    echo "[4/4] [OK] RoiEditor has already been installed."
else
    echo "[4/4] [WARNING] RoiEditor has not yet been installed."
fi

if [[ -f "$DESKTOP_DIR/RoiEditor.desktop" ]]; then
    echo "[4/4] [OK] Launcher for RoiEditor found on $DESKTOP_DIR."
else
    echo "[4/4] [WARNING] Launcher not found for RoiEditor."
fi
