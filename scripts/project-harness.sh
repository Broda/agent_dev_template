#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
template_root_arg=()
if [[ "${1:-}" == "--template-root" ]]; then
  if [[ -z "${2:-}" ]]; then
    echo "--template-root requires a path" >&2
    exit 2
  fi
  template_root_arg=("--template-root" "$2")
  shift 2
fi
subcommand="${1:-}"

if [[ -z "$subcommand" || "$subcommand" == "-h" || "$subcommand" == "--help" ]]; then
  cat <<'USAGE'
Usage: ./scripts/project-harness <command> [args]

Commands:
  new <path> [--origin <url>] [--no-git]
  new-from-idea <path> [--payload-file <json> | --idea-id <id> --title <title>] [--json]
  update --dry-run [--source-path <template-checkout> | --source-commit <sha> | --release-version <version>] [--json]
  update --apply --source-path <template-checkout> --yes [--include-mixed]
  update --apply --source-commit <sha> --yes [--include-mixed]
  update --apply --release-version <version> --yes [--include-mixed]
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
  new-from-idea)
    # Delegates to project-harness-new-from-idea.
    cli_command="project-harness-new-from-idea"
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
  exec python3 "$script_dir/../.harness/runtime/python/cli.py" "$cli_command" "${template_root_arg[@]}" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$script_dir/../.harness/runtime/python/cli.py" "$cli_command" "${template_root_arg[@]}" "$@"
fi

echo "Error: Python 3 is required but was not found." >&2
exit 1
