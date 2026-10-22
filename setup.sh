#!/usr/bin/env sh
# Creates .venv next to this file (if missing) and installs requirements.txt into it.
# Safe to run repeatedly - with an existing .venv it only installs missing packages.
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
    PY=$(command -v python3 || command -v python || true)
    if [ -z "$PY" ]; then
        echo "Python not found. Install Python 3.10+ and run this script again." >&2
        exit 1
    fi
    echo "Creating .venv ..."
    "$PY" -m venv .venv
fi

echo "Installing requirements.txt ..."
.venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt

echo "Done. Usage: .venv/bin/python hz432.py ~/Music"
