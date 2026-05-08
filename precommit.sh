#!/usr/bin/env bash
set -euo pipefail

python_files="$(git ls-files '*.py')"

if [[ -z "${python_files}" ]]; then
  echo "No Python files found."
  exit 0
fi

echo "Running pylint..."
uv run pylint ${python_files}

echo "Running ruff..."
uv run ruff check ${python_files}

echo "All pre-commit checks passed."
