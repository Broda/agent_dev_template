#!/usr/bin/env bash
set -u

failures=()

add_failure() {
  failures+=("$1")
}

path_exists() {
  local path="$1"
  [[ -n "$path" && -e "$path" ]]
}

required=(
  "AGENTS.md"
  "MODE.md"
  "README.md"
  "CHANGELOG.md"
  ".gitignore"
  "NOTES_CATALOG.md"
  "notes/"
  "scripts/lab-note"
  "scripts/lab-note.sh"
  "scripts/lab-note.ps1"
  "docs/PROJECT_CONTEXT.md"
  "docs/ROADMAP.md"
  "docs/ARCHITECTURE.md"
  "docs/FILE_MAP.md"
  "docs/GOVERNANCE_INDEX.md"
  "docs/VERSIONING_AND_RELEASE_POLICY.md"
  "docs/SECURITY_POLICY.md"
  "docs/RUNTIME_VERIFICATION_REPORT.md"
  "docs/adr/ADR-0001-record-architecture-decisions.md"
  "docs/adr/ADR-TEMPLATE.md"
  "state/project-init.json"
)

for artifact in "${required[@]}"; do
  if ! path_exists "$artifact"; then
    add_failure "Missing required artifact: $artifact"
  fi
done

if ! grep -Fq "Current mode: development" MODE.md 2>/dev/null; then
  add_failure "MODE.md must be switched to development."
fi

if grep -R -n -E '<[^>]+>' README.md docs CHANGELOG.md >/dev/null 2>&1; then
  add_failure "Unresolved placeholders detected in generated development docs."
fi

if ! grep -Fq "## [Unreleased]" CHANGELOG.md 2>/dev/null; then
  add_failure "CHANGELOG.md is missing the [Unreleased] section."
fi

if [[ -f state/project-init.json ]]; then
  if ! grep -Fq '"status": "finalized"' state/project-init.json; then
    add_failure "state/project-init.json must be marked finalized."
  fi
  if ! grep -Eq '"ideaId":[[:space:]]*"[^"]+"' state/project-init.json; then
    add_failure "state/project-init.json must include a non-empty ideaId."
  fi
  if ! grep -Eq '"projectType":[[:space:]]*"[^"]+"' state/project-init.json; then
    add_failure "state/project-init.json must include a non-empty projectType."
  fi
fi

notes_catalog_path="NOTES_CATALOG.md"
if [[ -f "$notes_catalog_path" ]]; then
  seen_note_ids="|"
  while IFS= read -r row; do
    IFS='|' read -r _ c1 c2 c3 c4 c5 c6 c7 _ <<< "$row"
    note_id=$(echo "$c1" | xargs)
    note_date=$(echo "$c3" | xargs)
    note_path=$(echo "$c6" | xargs)

    if [[ ! "$note_id" =~ ^note-[0-9]{4}$ ]]; then
      add_failure "Invalid note id format in NOTES_CATALOG.md: $note_id"
      continue
    fi

    if [[ "$seen_note_ids" == *"|$note_id|"* ]]; then
      add_failure "Duplicate note id in NOTES_CATALOG.md: $note_id"
    else
      seen_note_ids="${seen_note_ids}${note_id}|"
    fi

    if [[ ! "$note_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
      add_failure "Invalid note date format for '$note_id': $note_date"
    fi

    clean_note_path=$(echo "$note_path" | sed 's/^`//; s/`$//' | xargs)
    if [[ "$clean_note_path" != notes/* ]]; then
      add_failure "Note path for '$note_id' must be under notes/: $clean_note_path"
    elif ! path_exists "$clean_note_path"; then
      add_failure "Missing note file for '$note_id': $clean_note_path"
    fi
  done < <(grep -E '^\|[[:space:]]*note-[0-9]{4}[[:space:]]*\|' "$notes_catalog_path" || true)
fi

echo "Development validation summary"
echo "- Failures: ${#failures[@]}"

if (( ${#failures[@]} > 0 )); then
  echo
  echo "Failures:"
  for failure in "${failures[@]}"; do
    echo "- $failure"
  done
  exit 1
fi

echo
echo "PASS: development integrity checks completed with no blocking failures."
