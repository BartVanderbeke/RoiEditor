#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
DESKTOP_DIR="${DESKTOP_DIR:-$HOME/Desktop}"

echo "[1/3] Starting the installation of RoiEditor"
cd "$SCRIPT_DIR"
python3 -m pip install -e .
echo "[1/3] Finished the installation of RoiEditor"

echo "[2/3] Creating RoiEditor launcher on desktop"
mkdir -p "$DESKTOP_DIR"
cat >"$DESKTOP_DIR/RoiEditor.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=RoiEditor
Exec=$SCRIPT_DIR/tools/run_roieditor.sh
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/assets/RoiEditor.ico
Terminal=false
Categories=Science;Graphics;
EOF
chmod +x "$DESKTOP_DIR/RoiEditor.desktop"
echo "[2/3] Created RoiEditor launcher on desktop"

if python3 -m pip show cellpose >/dev/null 2>&1; then
    echo "[3/3] Creating cellpose launcher on desktop"
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
    echo "[3/3] Created cellpose launcher on desktop"
else
    echo "[3/3] [WARNING] cellpose is not yet installed"
fi
