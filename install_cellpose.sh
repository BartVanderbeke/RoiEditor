#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
DESKTOP_DIR="${DESKTOP_DIR:-$HOME/Desktop}"

echo "[1/3] Searching for python3"
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] Python3 was not found. Please install Python and try again."
    exit 1
fi
echo "[OK] Python3 found: $(command -v python3)"

echo
echo "[2/3] Installing most recent cellpose 3.x.y"
python3 -m pip install --upgrade pip
python3 -m pip install "cellpose[gui]==3.*"
echo "[OK] cellpose 3.x.y successfully installed."

echo
echo "[3/3] Creating desktop launcher for cellpose 3.x.y"
mkdir -p "$DESKTOP_DIR"
cat >"$DESKTOP_DIR/cellpose.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=cellpose
Exec=python3 -m cellpose
Path=$HOME
Icon=$SCRIPT_DIR/assets/cellpose.ico
Terminal=false
Categories=Science;Graphics;
EOF
chmod +x "$DESKTOP_DIR/cellpose.desktop"

if [[ -f "$DESKTOP_DIR/cellpose.desktop" ]]; then
    echo "[OK] Launcher to cellpose found on $DESKTOP_DIR"
else
    echo "[WARNING] Launcher to cellpose not found on desktop."
fi

echo
echo "[3/3] Done! You can now start Cellpose using the launcher on your desktop"
