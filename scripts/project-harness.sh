#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
subcommand="${1:-}"

if [[ -z "$subcommand" || "$subcommand" == "-h" || "$subcommand" == "--help" ]]; then
  cat <<'USAGE'
Usage: ./scripts/project-harness <command> [args]

Commands:
  new <path> [--origin <url>] [--no-git]
  update --dry-run [--source-path <template-checkout> | --source-commit <sha> | --release-version <version>]
  update --apply --source-path <template-checkout> --yes [--include-mixed]
  validate
USAGE
  exit 0
fi

shift

case "$subcommand" in
  new)
    # Delegates to project-harness-new.
    cli_command="project-harness-new"
    ;;
  validate)
    # Delegates to project-harness-validate.
    cli_command="project-harness-validate"
    ;;
  update)
    # Delegates to project-harness-update.
    cli_command="project-harness-update"
    ;;
  *)
    echo "Unknown project-harness command: $subcommand" >&2
    exit 2
    ;;
esac

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script_dir/python/cli.py" "$cli_command" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$script_dir/python/cli.py" "$cli_command" "$@"
fi

echo "Error: Python 3 is required but was not found." >&2
exit 1
