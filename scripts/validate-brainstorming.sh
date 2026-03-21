#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script_dir/python/cli.py" validate-brainstorming "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$script_dir/python/cli.py" validate-brainstorming "$@"
fi

echo "Error: Python 3 is required but was not found." >&2
exit 1
