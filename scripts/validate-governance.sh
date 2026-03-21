#!/usr/bin/env bash
set -euo pipefail

mode=$(awk -F': ' '/^Current mode:/{print $2}' MODE.md | tr -d '\r')

case "$mode" in
  brainstorming)
    exec "$(dirname "$0")/validate-brainstorming.sh"
    ;;
  development)
    exec "$(dirname "$0")/validate-development.sh"
    ;;
  *)
    echo "Unknown mode in MODE.md: $mode" >&2
    exit 1
    ;;
esac
