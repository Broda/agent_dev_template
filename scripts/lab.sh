#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: ./scripts/lab <command> [args]" >&2
  exit 1
fi

subcommand="$1"
shift

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script_dir/python/cli.py" "lab-$subcommand" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$script_dir/python/cli.py" "lab-$subcommand" "$@"
fi

echo "Error: Python 3 is required but was not found." >&2
exit 1
