#!/usr/bin/env bash
set -euo pipefail

topic=""
source_context="recent assistant research context"
idea_id=""
tags=""
summaries=()
no_sync=0

mode=$(awk -F': ' '/^Current mode:/{print $2}' MODE.md 2>/dev/null | tr -d '\r')
if [[ -z "$mode" ]]; then
  mode="brainstorming"
fi

usage() {
  cat <<USAGE
Usage: ./scripts/lab-note.sh --topic <topic> [options]

Options:
  --topic <text>        Required note topic/title seed
  --source <text>       Source context summary
  --idea-id <idea-id>   Related idea id (optional)
  --tags <csv>          Comma-separated tags (optional)
  --summary <text>      Summary bullet (repeatable)
  --no-sync             Skip milestone autosync
USAGE
}

kebab() {
  local s
  s=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  s=$(printf '%s' "$s" | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g')
  printf '%s' "${s:-note}"
}

trim() {
  local s="$1"
  s="${s#${s%%[![:space:]]*}}"
  s="${s%${s##*[![:space:]]}}"
  printf '%s' "$s"
}

while (($# > 0)); do
  case "$1" in
    --topic)
      topic="${2:-}"
      shift 2
      ;;
    --source)
      source_context="${2:-}"
      shift 2
      ;;
    --idea-id)
      idea_id="${2:-}"
      shift 2
      ;;
    --tags)
      tags="${2:-}"
      shift 2
      ;;
    --summary)
      summaries+=("${2:-}")
      shift 2
      ;;
    --no-sync)
      no_sync=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

topic=$(trim "$topic")
if [[ -z "$topic" ]]; then
  echo "--topic is required." >&2
  usage
  exit 1
fi

mkdir -p notes
if [[ ! -f NOTES_CATALOG.md ]]; then
  echo "NOTES_CATALOG.md not found." >&2
  exit 1
fi

max_id=$(grep -Eo '^\|[[:space:]]*note-[0-9]{4}[[:space:]]*\|' NOTES_CATALOG.md | sed -E 's/^\|[[:space:]]*note-([0-9]{4})[[:space:]]*\|/\1/' | sort -n | tail -n1 || true)
if [[ -z "$max_id" ]]; then
  next_num=1
else
  next_num=$((10#$max_id + 1))
fi
id_num=$(printf '%04d' "$next_num")
note_id="note-$id_num"

date_stamp=$(date +%F)
slug=$(kebab "$topic")
note_path="notes/${date_stamp}_${note_id}-${slug}.md"

{
  echo "# Research Note"
  echo
  echo "## Metadata"
  echo
  echo "- Note ID: $note_id"
  echo "- Title: $topic"
  echo "- Date: $date_stamp"
  echo "- Related Idea ID: ${idea_id:-n/a}"
  echo "- Source Context: $source_context"
  echo "- Tags: ${tags:-n/a}"
  echo
  echo "## Captured Information"
  echo
  if (( ${#summaries[@]} > 0 )); then
    for s in "${summaries[@]}"; do
      echo "- $s"
    done
  else
    echo "- Summary pending: fill in captured research details."
  fi
  echo
  echo "## Key Facts / Constraints"
  echo
  echo "- "
  echo
  echo "## Open Questions / Follow-ups"
  echo
  echo "- "
  echo
  echo "## Links"
  echo
  echo "- "
} > "$note_path"

printf '| %s | %s | %s | %s | %s | `%s` | %s |\n' \
  "$note_id" \
  "$topic" \
  "$date_stamp" \
  "${idea_id:-n/a}" \
  "$source_context" \
  "$note_path" \
  "${tags:-n/a}" >> NOTES_CATALOG.md

if (( no_sync == 0 )); then
  ./scripts/lab-sync --quiet --no-warn-push-failure -m "$mode: note $note_id" -- "$note_path" NOTES_CATALOG.md
fi

if (( no_sync == 0 )); then
  echo "Note saved and persisted: $note_path"
else
  echo "Note saved (sync skipped): $note_path"
fi
