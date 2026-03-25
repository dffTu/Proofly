#!/bin/bash
# Run frontend tests
# Usage: ./tests/run.sh
set -e

cd "$(dirname "$0")/.."

if [ ! -d .venv-tests ]; then
  echo "Creating test venv..."
  python3 -m venv .venv-tests
fi

source .venv-tests/bin/activate
pip install -q -r tests/requirements.txt

python -m pytest tests/ -v "$@"
