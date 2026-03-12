#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Updating apt package index"
sudo apt-get update

echo "[2/4] Installing Python 3 and pip"
sudo apt-get install -y python3 python3-pip python3-venv

echo "[3/4] Verifying installation"
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] Python installation did not succeed"
    exit 1
fi

echo "[4/4] Python installed successfully"
python3 --version
python3 -m pip --version
