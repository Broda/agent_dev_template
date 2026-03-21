#!/usr/bin/env bash
set -u

failures=()
warnings=()

add_failure() {
  failures+=("$1")
}

add_warning() {
  warnings+=("$1")
}

path_exists() {
  local path="$1"
  [[ -n "$path" && -e "$path" ]]
}

core_artifacts=(
  "README.md"
  "AGENTS.md"
  "MODE.md"
  "brainstorming/AGENTS.brainstorming.md"
  "brainstorming/CONVERSATIONAL_MODE.md"
  "brainstorming/COMMANDS.md"
  "brainstorming/QUICKSTART.md"
  "brainstorming/FILE_MAP.md"
  "IDEA_CATALOG.md"
  "NOTES_CATALOG.md"
  "ideas/_inbox.md"
  "ideas/_active.md"
  "ideas/_parked.md"
  "ideas/_killed.md"
  "notes/"
  "brainstorming/templates/idea_template.md"
  "brainstorming/templates/decision_template.md"
  "brainstorming/templates/note_template.md"
  "brainstorming/templates/project_plan_packet_template.md"
  "brainstorming/templates/risk_template.md"
  "brainstorming/templates/review_gate_template.md"
  "brainstorming/docs/adr/template.md"
  "brainstorming/docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md"
  "scripts/validate-brainstorming.ps1"
  "scripts/validate-governance.ps1"
  "scripts/lab-sync.ps1"
  "scripts/lab-note.ps1"
  "scripts/finalize-project.sh"
  "scripts/render-development-docs.sh"
  "scripts/validate-development.sh"
  "scripts/validate-brainstorming.sh"
  "scripts/validate-governance.sh"
  "scripts/lab-sync.sh"
  "scripts/lab-note.sh"
  "scripts/finalize-project"
  "scripts/render-development-docs"
  "scripts/validate-development"
  "scripts/validate-brainstorming"
  "scripts/validate-governance"
  "scripts/lab-sync"
  "scripts/lab-note"
  "state/project-init.json"
  ".github/workflows/governance-audit.yml"
  ".github/PULL_REQUEST_TEMPLATE.md"
)

for artifact in "${core_artifacts[@]}"; do
  if ! path_exists "$artifact"; then
    add_failure "Missing required artifact: $artifact"
  fi
done

while IFS= read -r mdfile; do
  while IFS= read -r match; do
    [[ -z "$match" ]] && continue
    if ! path_exists "$match"; then
      add_failure "Missing ADR link target: '$match' referenced in '$mdfile'."
    fi
  done < <(grep -Eo 'docs/adr/ADR-[0-9]{4}-[a-z0-9-]+\.md' "$mdfile" || true)
done < <(
  find . -type f -name '*.md' \
    -not -path './.git/*' \
    -not -path './external/*' \
    -not -path './codex_brainstorming_template/*' \
    -not -path './codex_template/*' \
    -not -path './development/templates/*' \
    -not -path './development/bootstrap/*'
)

catalog_path="IDEA_CATALOG.md"
if ! path_exists "$catalog_path"; then
  add_failure "Missing IDEA_CATALOG.md"
else
  while IFS= read -r row; do
    IFS='|' read -r _ c1 c2 c3 c4 c5 c6 c7 _ <<< "$row"
    idea_id=$(echo "$c1" | xargs)
    status=$(echo "$c3" | xargs)
    sessions=$(echo "$c5" | xargs)
    export_path=$(echo "$c6" | xargs)

    if [[ -z "$idea_id" || -z "$status" ]]; then
      add_failure "Malformed catalog row: $row"
      continue
    fi

    case "$status" in
      inbox) state_file='ideas/_inbox.md' ;;
      active) state_file='ideas/_active.md' ;;
      parked) state_file='ideas/_parked.md' ;;
      killed) state_file='ideas/_killed.md' ;;
      exported) state_file='ideas/_active.md' ;;
      *)
        add_failure "Unknown status '$status' for '$idea_id'."
        continue
        ;;
    esac

    if ! path_exists "$state_file"; then
      add_failure "Required state file '$state_file' missing for status '$status'."
    fi

    sessions_lc=$(echo "$sessions" | tr '[:upper:]' '[:lower:]')
    if [[ "$status" == "active" && "$sessions_lc" =~ (_none_|_none\ yet_|n/a) ]]; then
      add_warning "Active idea '$idea_id' has no session link yet."
    fi

    if [[ "$status" == "exported" ]]; then
      export_lc=$(echo "$export_path" | tr '[:upper:]' '[:lower:]')
      if [[ -z "$export_path" || "$export_lc" =~ (_n/a_|_none_|_none\ yet_) ]]; then
        add_failure "Exported idea '$idea_id' must include export file path."
      else
        clean_export_path=$(echo "$export_path" | sed 's/^`//; s/`$//' | xargs)
        if ! path_exists "$clean_export_path"; then
          add_failure "Catalog export path missing for '$idea_id': $clean_export_path"
        fi
      fi
    fi
  done < <(grep -E '^\|[[:space:]]*idea-[a-z0-9-]+' "$catalog_path" || true)
fi

notes_catalog_path="NOTES_CATALOG.md"
if ! path_exists "$notes_catalog_path"; then
  add_failure "Missing NOTES_CATALOG.md"
else
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

if ! grep -Fq "Current mode: brainstorming" MODE.md 2>/dev/null; then
  add_failure "MODE.md must remain in brainstorming mode while using brainstorming validation."
fi

file_map_path="brainstorming/FILE_MAP.md"
if path_exists "$file_map_path"; then
  fm=$(cat "$file_map_path")
  for artifact in "${core_artifacts[@]}"; do
    token="\`$artifact\`"
    if ! grep -Fq "$token" <<< "$fm"; then
      add_warning "FILE_MAP.md missing registry row for: $artifact"
    fi
  done
fi

echo "Lean validation summary"
echo "- Failures: ${#failures[@]}"
echo "- Warnings: ${#warnings[@]}"

if (( ${#warnings[@]} > 0 )); then
  echo
  echo "Warnings:"
  for warning in "${warnings[@]}"; do
    echo "- $warning"
  done
fi

if (( ${#failures[@]} > 0 )); then
  echo
  echo "Failures:"
  for failure in "${failures[@]}"; do
    echo "- $failure"
  done
  exit 1
fi

echo
echo "PASS: lean integrity checks completed with no blocking failures."
