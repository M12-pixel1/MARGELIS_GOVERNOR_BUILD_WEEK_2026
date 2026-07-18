#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ -x .venv/bin/python ]; then
  PYTHON_BIN=.venv/bin/python
fi

"$PYTHON_BIN" -m pytest
"$PYTHON_BIN" scripts/verify_repo.py

