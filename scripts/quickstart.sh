#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_EXAMPLE="${ROOT_DIR}/.env.example"
DRY_RUN=0
RUN_APP=1

usage() {
  cat <<'USAGE'
Usage: ./scripts/quickstart.sh [--dry-run] [--no-run]

Bootstraps LLMTrainingTools with uv, verifies .env.example, installs dependencies,
and starts the local Flask app.

Options:
  --dry-run  Print the actions without changing files or running uv.
  --no-run   Install dependencies but do not start the app.
  --help     Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --no-run)
      RUN_APP=0
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

cd "${ROOT_DIR}"

if [[ ! -f "${ENV_EXAMPLE}" ]]; then
  echo "Missing ${ENV_EXAMPLE}" >&2
  exit 1
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "Would use config from .env.example"
else
  echo "Using config from .env.example"
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "Would run: uv sync"
else
  uv sync
fi

if [[ "${RUN_APP}" -eq 0 ]]; then
  echo "Dependencies are installed. Start later with: uv run llm-training-tools"
  exit 0
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "Would run: uv run llm-training-tools"
  echo "Then open: http://127.0.0.1:5000"
else
  echo "Starting LLMTrainingTools at http://127.0.0.1:5000"
  exec uv run llm-training-tools
fi
