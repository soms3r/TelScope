#!/usr/bin/env bash
# TelScope one-click launcher (Linux / macOS)
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] python3 not found. Install Python 3.10+ first."
  exit 1
fi

echo "[*] Setting up local virtual environment..."
if [ ! -d venv ]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate

echo "[*] Ensuring dependencies..."
pip install -r requirements.txt --quiet --disable-pip-version-check

echo "[*] Provisioning pinned tools (first run only, internet needed once)..."
python3 bootstrap.py || echo "[!] bootstrap reported problems — continuing (modules may show unavailable)"

echo "[*] Starting TelScope on http://127.0.0.1:8000 ..."
if command -v xdg-open >/dev/null 2>&1; then
  (sleep 2 && xdg-open http://127.0.0.1:8000 &) || true
elif command -v open >/dev/null 2>&1; then
  (sleep 2 && open http://127.0.0.1:8000 &) || true
fi

exec python3 app.py
