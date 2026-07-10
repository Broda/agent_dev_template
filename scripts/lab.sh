#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root=""
if [[ "${1:-}" == "--root" ]]; then
  if [[ -z "${2:-}" ]]; then
    echo "--root requires a path" >&2
    exit 2
  fi
  root="$2"
  shift 2
fi
subcommand="${1:-}"

if [[ -z "$subcommand" || "$subcommand" == "-h" || "$subcommand" == "--help" || "$subcommand" == "help" ]]; then
  cat <<'USAGE'
Usage: ./scripts/lab <command> [args]

Commands:
  status
  doctor [--idea-id <id>]
  capture --idea-id <id> --title "Title"
  import-idea (--payload-file <json> | --idea-id <id> --title "Title")
  activate --idea-id <id>
  decide --idea-id <id> --chosen-option "Decision" --rationale "Reason"
  risk --idea-id <id> --statement "Risk"
  path-note --idea-id <id> --title "Title"
  note --topic "Topic" --summary "Summary"
  review --idea-id <id> --result <result>
  export --idea-id <id>
  handoff [--idea-id <id>] [--check]
  finalize [--idea-id <id>] [--write-export]
  park --idea-id <id> [--reason "Reason"]
  kill --idea-id <id> [--reason "Reason"]
  audit
  evidence --task <task> --command "Command" --result <result>
  adr --title "Title" --decision "Decision"
  wiki-render
  wiki-check
  commit [--message "Message"]
  push
  sync [args]

Run ./scripts/lab <command> --help for command-specific options.
USAGE
  exit 0
fi

shift

if [[ -n "$root" ]]; then
  set -- "--root" "$root" "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$script_dir/../.harness/runtime/python/cli.py" "lab-$subcommand" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$script_dir/../.harness/runtime/python/cli.py" "lab-$subcommand" "$@"
fi

echo "Error: Python 3 is required but was not found." >&2
exit 1
