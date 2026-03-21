#!/usr/bin/env bash
set -euo pipefail

STATE_FILE="state/project-init.json"

idea_id=""
date_stamp=""
export_path=""
session_path=""

session_paths=()
idea_files=()
hydrate_files=()
backed_up_paths=()
created_paths=()
BACKUP_DIR=""

usage() {
  cat <<'EOF'
Usage: ./scripts/finalize-project.sh --idea-id <idea-id>
EOF
}

trim() {
  local s="${1:-}"
  s="${s#${s%%[![:space:]]*}}"
  s="${s%${s##*[![:space:]]}}"
  printf '%s' "$s"
}

clean_markdown_path() {
  local path
  path=$(trim "${1:-}")
  path="${path#\`}"
  path="${path%\`}"
  printf '%s' "$path"
}

join_by() {
  local sep="$1"
  shift
  local out=""
  local item
  for item in "$@"; do
    [[ -z "$item" ]] && continue
    if [[ -n "$out" ]]; then
      out+="$sep"
    fi
    out+="$item"
  done
  printf '%s' "$out"
}

replace_line_prefix() {
  local file="$1"
  local prefix="$2"
  local value="$3"
  value=$(printf '%s' "$value" | tr '\n' ' ' | tr '\r' ' ')
  awk -v p="$prefix" -v v="$value" '
    index($0, p) == 1 { print p " " v; next }
    { print }
  ' "$file" > "$file.tmp"
  mv "$file.tmp" "$file"
}

append_unique_session_path() {
  local value="$1"
  local existing
  for existing in "${session_paths[@]:-}"; do
    [[ "$existing" == "$value" ]] && return 0
  done
  session_paths+=("$value")
}

append_unique_idea_file() {
  local value="$1"
  local existing
  for existing in "${idea_files[@]:-}"; do
    [[ "$existing" == "$value" ]] && return 0
  done
  idea_files+=("$value")
}

append_unique_hydrate_file() {
  local value="$1"
  local existing
  for existing in "${hydrate_files[@]:-}"; do
    [[ "$existing" == "$value" ]] && return 0
  done
  hydrate_files+=("$value")
}

append_unique_backup_path() {
  local value="$1"
  local existing
  for existing in "${backed_up_paths[@]:-}"; do
    [[ "$existing" == "$value" ]] && return 0
  done
  backed_up_paths+=("$value")
}

append_unique_created_path() {
  local value="$1"
  local existing
  for existing in "${created_paths[@]:-}"; do
    [[ "$existing" == "$value" ]] && return 0
  done
  created_paths+=("$value")
}

backup_path() {
  local path="$1"
  [[ -z "$path" ]] && return 0

  if [[ -e "$path" ]]; then
    mkdir -p "$BACKUP_DIR/$(dirname "$path")"
    cp -R "$path" "$BACKUP_DIR/$path"
    append_unique_backup_path "$path"
  else
    append_unique_created_path "$path"
  fi
}

restore_backups() {
  local path

  for path in "${created_paths[@]:-}"; do
    rm -rf -- "$path"
  done

  for path in "${backed_up_paths[@]:-}"; do
    mkdir -p "$(dirname "$path")"
    rm -rf -- "$path"
    cp -R "$BACKUP_DIR/$path" "$path"
  done
}

cleanup_backups() {
  if [[ -n "$BACKUP_DIR" && -d "$BACKUP_DIR" ]]; then
    rm -rf -- "$BACKUP_DIR"
  fi
}

rollback_on_error() {
  local exit_code=$?
  trap - ERR INT TERM
  if [[ -n "$BACKUP_DIR" ]]; then
    restore_backups
    cleanup_backups
  fi
  exit "$exit_code"
}

existing_state_value() {
  local path="$1"
  [[ -f "$STATE_FILE" ]] || return 0
  perl -MJSON::PP -e '
    use strict;
    use warnings;
    my $path = shift @ARGV;
    my $file = shift @ARGV;
    open my $fh, "<", $file or exit 0;
    local $/;
    my $data = eval { decode_json(<$fh>) };
    exit 0 if !$data || ref($data) ne "HASH";
    my @parts = split /\./, $path;
    my $cur = $data;
    for my $part (@parts) {
      exit 0 if ref($cur) ne "HASH" || !exists $cur->{$part};
      $cur = $cur->{$part};
    }
    print defined $cur ? $cur : q{};
  ' "$path" "$STATE_FILE"
}

json_string() {
  perl -MJSON::PP -e 'print encode_json($ARGV[0])' "$1"
}

infer_project_type() {
  local text
  text=$(printf '%s %s' "$project_name" "$objective" | tr '[:upper:]' '[:lower:]')
  if [[ "$text" == *"cli"* || "$text" == *"command line"* ]]; then
    printf '%s' "CLI"
  elif [[ "$text" == *"desktop"* || "$text" == *"electron"* ]]; then
    printf '%s' "Desktop"
  elif [[ "$text" == *"web"* || "$text" == *"frontend"* || "$text" == *"browser"* ]]; then
    printf '%s' "Web App"
  elif [[ "$text" == *"api"* || "$text" == *"service"* || "$text" == *"backend"* ]]; then
    printf '%s' "API"
  elif [[ "$text" == *"library"* || "$text" == *"sdk"* || "$text" == *"package"* ]]; then
    printf '%s' "Library"
  else
    printf '%s' ""
  fi
}

prompt_eof_error() {
  local field="$1"
  echo "Cannot finalize non-interactively without a value for '$field'." >&2
  echo "Populate state/project-init.json first or rerun with stdin/TTY answers." >&2
  exit 1
}

ask_non_empty() {
  local prompt="$1"
  local current="${2:-}"
  local ans

  if [[ -n "$current" ]]; then
    if ! read -r -p "$prompt [$current]: " ans; then
      printf '%s' "$current"
      return
    fi
    ans=$(trim "$ans")
    if [[ -n "$ans" ]]; then
      printf '%s' "$ans"
    else
      printf '%s' "$current"
    fi
    return
  fi

  while true; do
    if ! read -r -p "$prompt: " ans; then
      prompt_eof_error "$prompt"
    fi
    ans=$(trim "$ans")
    if [[ -n "$ans" ]]; then
      printf '%s' "$ans"
      return
    fi
  done
}

choose_project_type() {
  local current="$1"
  local ans

  echo "Project type options:" >&2
  echo "1) CLI" >&2
  echo "2) Desktop" >&2
  echo "3) Web App" >&2
  echo "4) API" >&2
  echo "5) Library" >&2
  if [[ -n "$current" ]]; then
    echo "Detected: $current" >&2
  fi

  while true; do
    if [[ -n "$current" ]]; then
      if ! read -r -p "Select project type [1-5] (current: $current): " ans; then
        printf '%s' "$current"
        return
      fi
      ans=$(trim "$ans")
      if [[ -z "$ans" ]]; then
        printf '%s' "$current"
        return
      fi
    else
      if ! read -r -p "Select project type [1-5]: " ans; then
        prompt_eof_error "project type"
      fi
    fi

    case "$ans" in
      1) printf '%s' "CLI"; return ;;
      2) printf '%s' "Desktop"; return ;;
      3) printf '%s' "Web App"; return ;;
      4) printf '%s' "API"; return ;;
      5) printf '%s' "Library"; return ;;
    esac
  done
}

choose_from_list() {
  local prompt="$1"
  local current="$2"
  shift 2
  local options=("$@")
  local i=1
  local ans
  local upper="${#options[@]}"

  for opt in "${options[@]}"; do
    echo "$i) $opt" >&2
    i=$((i + 1))
  done

  while true; do
    if [[ -n "$current" ]]; then
      if ! read -r -p "$prompt [1-$upper] (current: $current): " ans; then
        printf '%s' "$current"
        return
      fi
      ans=$(trim "$ans")
      if [[ -z "$ans" ]]; then
        printf '%s' "$current"
        return
      fi
    else
      if ! read -r -p "$prompt [1-$upper]: " ans; then
        prompt_eof_error "$prompt"
      fi
    fi

    if [[ "$ans" =~ ^[0-9]+$ ]] && (( ans >= 1 && ans <= upper )); then
      printf '%s' "${options[$((ans - 1))]}"
      return
    fi
  done
}

extract_label_value() {
  local file="$1"
  local label="$2"
  local prefix="- $label:"

  [[ -f "$file" ]] || return 0
  awk -v prefix="$prefix" '
    index($0, prefix) == 1 {
      value = substr($0, length(prefix) + 1)
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      print value
      exit
    }
  ' "$file"
}

is_placeholder_value() {
  local value
  value=$(trim "${1:-}")

  [[ -z "$value" ]] && return 0
  [[ "$value" == "None" ]] && return 0
  [[ "$value" == "_none_" ]] && return 0
  [[ "$value" == "_n/a_" ]] && return 0
  [[ "$value" == "_none yet_" ]] && return 0
  [[ "$value" == "pass | conditional-pass | fail" ]] && return 0

  return 1
}

first_value_for_label() {
  local label="$1"
  local file
  local value

  for file in "${hydrate_files[@]:-}"; do
    value=$(extract_label_value "$file" "$label")
    value=$(trim "$value")
    if ! is_placeholder_value "$value"; then
      printf '%s' "$value"
      return 0
    fi
  done
  return 1
}

latest_session_path() {
  local latest=""
  local path
  for path in "${session_paths[@]:-}"; do
    if [[ -z "$latest" || "$path" > "$latest" ]]; then
      latest="$path"
    fi
  done
  printf '%s' "$latest"
}

summarize_decisions() {
  local summary=""

  [[ -n "${project_type:-}" ]] && summary+="Project type: $project_type. "
  [[ -n "${persistence:-}" ]] && summary+="Persistence: $persistence. "
  [[ -n "${authentication:-}" ]] && summary+="Authentication: $authentication. "
  [[ -n "${determinism:-}" ]] && summary+="Correctness sensitivity: $determinism. "
  [[ -n "${packaging:-}" ]] && summary+="Packaging: $packaging."

  printf '%s' "$(trim "$summary")"
}

summarize_dependencies() {
  printf 'Language: %s; Runtime: %s; Framework: %s; Tooling: %s' \
    "$language" "$runtime" "${framework:-None}" "${package_tool:-None}"
}

collect_session_paths() {
  local candidate

  while IFS= read -r candidate; do
    candidate=$(trim "$candidate")
    [[ -z "$candidate" ]] && continue
    [[ -f "$candidate" ]] && append_unique_session_path "$candidate"
  done < <(printf '%s\n' "$sessions_col" | grep -oE 'sessions/[^`,[:space:]]+\.md' || true)

  while IFS= read -r candidate; do
    candidate=$(trim "$candidate")
    [[ -z "$candidate" ]] && continue
    [[ -f "$candidate" ]] && append_unique_session_path "$candidate"
  done < <(rg -l --fixed-strings "$idea_id" sessions 2>/dev/null || true)
}

collect_idea_files() {
  local candidate

  while IFS= read -r candidate; do
    candidate=$(trim "$candidate")
    [[ -z "$candidate" ]] && continue
    [[ -f "$candidate" ]] && append_unique_idea_file "$candidate"
  done < <(rg -l --fixed-strings "$idea_id" ideas 2>/dev/null || true)
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --idea-id)
      idea_id="${2:-}"
      shift 2
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

if [[ -z "$idea_id" ]]; then
  echo "--idea-id is required." >&2
  usage
  exit 1
fi

if [[ ! -f "IDEA_CATALOG.md" ]]; then
  echo "IDEA_CATALOG.md not found." >&2
  exit 1
fi

catalog_row=$(grep -E "^\|[[:space:]]*$idea_id[[:space:]]*\|" IDEA_CATALOG.md | head -n 1 || true)
if [[ -z "$catalog_row" ]]; then
  echo "Idea '$idea_id' not found in IDEA_CATALOG.md." >&2
  exit 1
fi

IFS='|' read -r _ c1 c2 c3 c4 c5 c6 c7 _ <<< "$catalog_row"
project_name=$(trim "$c2")
owner=$(trim "$c4")
sessions_col=$(trim "$c5")
existing_export_path=$(clean_markdown_path "$c6")
notes_col=$(trim "$c7")

if [[ -z "$project_name" || "$project_name" == "_none yet_" ]]; then
  project_name="$idea_id"
fi
if [[ -z "$owner" || "$owner" == "unassigned" ]]; then
  owner="$(git config --get user.name 2>/dev/null || echo unassigned)"
fi

collect_idea_files
if [[ -z "${idea_files[0]:-}" ]]; then
  echo "Idea '$idea_id' does not have a recorded idea entry under ideas/." >&2
  echo "Capture or activate the idea before finalizing." >&2
  exit 1
fi

collect_session_paths
if [[ -z "${session_paths[0]:-}" ]]; then
  echo "Idea '$idea_id' does not have a related session under sessions/." >&2
  echo "Create at least one session before finalizing." >&2
  exit 1
fi

existing_project_name=$(existing_state_value "projectName")
existing_purpose=$(existing_state_value "purpose")
existing_project_type=$(existing_state_value "projectType")
existing_language=$(existing_state_value "techStack.language")
existing_runtime=$(existing_state_value "techStack.runtime")
existing_framework=$(existing_state_value "techStack.framework")
existing_package_tool=$(existing_state_value "techStack.packageTool")
existing_persistence=$(existing_state_value "persistence")
existing_authentication=$(existing_state_value "authentication")
existing_determinism=$(existing_state_value "determinism")
existing_packaging=$(existing_state_value "packaging")
existing_constraints=$(existing_state_value "constraints")
existing_build_command=$(existing_state_value "commands.build")
existing_run_command=$(existing_state_value "commands.run")
existing_test_command=$(existing_state_value "commands.test")

if [[ -n "$existing_project_name" ]]; then
  project_name="$existing_project_name"
fi

for file in "${idea_files[@]:-}"; do
  append_unique_hydrate_file "$file"
done
for file in "${session_paths[@]:-}"; do
  append_unique_hydrate_file "$file"
done
if [[ -n "$existing_export_path" && -f "$existing_export_path" ]]; then
  append_unique_hydrate_file "$existing_export_path"
fi

objective=""
if [[ -n "$existing_purpose" ]]; then
  objective="$existing_purpose"
fi
if [[ -z "$objective" ]]; then
  objective=$(first_value_for_label "One-sentence objective" || true)
fi
if [[ -z "$objective" ]]; then
  objective=$(first_value_for_label "Problem statement" || true)
fi
if [[ -z "$objective" ]]; then
  objective=$(first_value_for_label "Value hypothesis" || true)
fi
if [[ -z "$objective" ]]; then
  objective=$(first_value_for_label "Summary rationale" || true)
fi
if [[ -z "$objective" ]]; then
  objective=$(first_value_for_label "Situation summary" || true)
fi
objective=$(ask_non_empty "One-sentence objective" "$objective")

problem_statement=$(first_value_for_label "Problem statement" || true)
target_users=$(first_value_for_label "Affected users/personas" || true)
if [[ -z "$target_users" ]]; then
  target_users=$(first_value_for_label "Target users" || true)
fi
why_now=$(first_value_for_label "Why now" || true)
expected_value=$(first_value_for_label "Expected value" || true)
if [[ -z "$expected_value" ]]; then
  expected_value=$(first_value_for_label "Value hypothesis" || true)
fi
solution_summary=$(first_value_for_label "Solution summary" || true)
mvp_scope=$(first_value_for_label "MVP scope" || true)
out_of_scope=$(first_value_for_label "Out of scope" || true)
assumptions=$(first_value_for_label "Assumptions" || true)
non_goals=$(first_value_for_label "Non-goals" || true)
top_risks=$(first_value_for_label "Top risks" || true)
if [[ -z "$top_risks" ]]; then
  top_risks=$(first_value_for_label "Top risks (link to risk entries)" || true)
fi
mitigation_plans=$(first_value_for_label "Mitigation plans" || true)
if [[ -z "$mitigation_plans" ]]; then
  mitigation_plans=$(first_value_for_label "Preventive mitigation" || true)
fi
contingencies=$(first_value_for_label "Contingency plan" || true)
remaining_risks=$(first_value_for_label "Remaining accepted risks" || true)
latest_review_outcome=$(first_value_for_label "Latest review outcome" || true)
if [[ -z "$latest_review_outcome" ]]; then
  latest_review_outcome=$(first_value_for_label "Result" || true)
fi
latest_review_session=$(latest_session_path)

constraints_source="$existing_constraints"
if is_placeholder_value "$constraints_source"; then
  constraints_source=""
fi
if [[ -z "$constraints_source" ]]; then
  constraints_source=$(first_value_for_label "Constraints" || true)
fi

project_type=$(choose_project_type "${existing_project_type:-$(infer_project_type)}")
language=$(ask_non_empty "Language" "$existing_language")
runtime=$(ask_non_empty "Runtime" "$existing_runtime")
framework=$(ask_non_empty "Framework (if any, else 'None')" "${existing_framework:-None}")
package_tool=$(ask_non_empty "Package manager/build tool (if any, else 'None')" "${existing_package_tool:-None}")
persistence=$(choose_from_list "Persistence" "$existing_persistence" "None" "File-based (JSON/YAML/etc.)" "SQLite" "Postgres/MySQL/Other RDBMS")
authentication=$(choose_from_list "Authentication" "$existing_authentication" "None" "Local users" "External auth provider")
determinism=$(choose_from_list "Determinism/correctness sensitivity" "$existing_determinism" "Normal" "High")
packaging=$(choose_from_list "Packaging/distribution planned" "$existing_packaging" "None" "Yes (desktop installers / containers / artifacts)")
constraints=$(ask_non_empty "Constraints (comma-separated; use 'None' if none)" "${constraints_source:-None}")
build_command=$(ask_non_empty "Build command" "$existing_build_command")
run_command=$(ask_non_empty "Run command" "$existing_run_command")
test_command=$(ask_non_empty "Test command" "$existing_test_command")

date_stamp=$(date +%F)
export_path="exports/${date_stamp}_PROJECT_PLAN_PACKET_${idea_id}.md"
session_path="exports/${date_stamp}_FINALIZATION_SESSION_${idea_id}.md"

mkdir -p exports state docs/adr

BACKUP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/finalize-project.XXXXXX")
trap rollback_on_error ERR INT TERM

backup_path "$STATE_FILE"
backup_path "$export_path"
backup_path "README.md"
backup_path "CHANGELOG.md"
backup_path ".gitignore"
backup_path "docs/PROJECT_CONTEXT.md"
backup_path "docs/ROADMAP.md"
backup_path "docs/ARCHITECTURE.md"
backup_path "docs/FILE_MAP.md"
backup_path "docs/GOVERNANCE_INDEX.md"
backup_path "docs/VERSIONING_AND_RELEASE_POLICY.md"
backup_path "docs/SECURITY_POLICY.md"
backup_path "docs/RUNTIME_VERIFICATION_REPORT.md"
backup_path "docs/MIGRATION_POLICY.md"
backup_path "docs/adr/ADR-0001-record-architecture-decisions.md"
backup_path "docs/adr/ADR-TEMPLATE.md"
backup_path "IDEA_CATALOG.md"
backup_path "MODE.md"
backup_path "$session_path"

cat > "$STATE_FILE" <<JSON
{
  "status": "finalized",
  "ideaId": $(json_string "$idea_id"),
  "projectName": $(json_string "$project_name"),
  "purpose": $(json_string "$objective"),
  "projectType": $(json_string "$project_type"),
  "techStack": {
    "language": $(json_string "$language"),
    "runtime": $(json_string "$runtime"),
    "framework": $(json_string "$framework"),
    "packageTool": $(json_string "$package_tool")
  },
  "persistence": $(json_string "$persistence"),
  "authentication": $(json_string "$authentication"),
  "determinism": $(json_string "$determinism"),
  "packaging": $(json_string "$packaging"),
  "constraints": $(json_string "$constraints"),
  "commands": {
    "build": $(json_string "$build_command"),
    "run": $(json_string "$run_command"),
    "test": $(json_string "$test_command")
  }
}
JSON

cp brainstorming/templates/project_plan_packet_template.md "$export_path"
replace_line_prefix "$export_path" "- Project name:" "$project_name"
replace_line_prefix "$export_path" "- Idea ID:" "$idea_id"
replace_line_prefix "$export_path" "- Owner:" "$owner"
replace_line_prefix "$export_path" "- Date:" "$date_stamp"
replace_line_prefix "$export_path" "- One-sentence objective:" "$objective"
replace_line_prefix "$export_path" "- Problem statement:" "${problem_statement:-$objective}"
replace_line_prefix "$export_path" "- Target users:" "${target_users:-See related sessions}"
replace_line_prefix "$export_path" "- Why now:" "${why_now:-See related sessions}"
replace_line_prefix "$export_path" "- Expected value:" "${expected_value:-$objective}"
replace_line_prefix "$export_path" "- Solution summary:" "${solution_summary:-Deliver the first milestone vertical slice for $project_name.}"
replace_line_prefix "$export_path" "- MVP scope:" "${mvp_scope:-Milestone 0 vertical slice with working build, run, and test commands.}"
replace_line_prefix "$export_path" "- Out of scope:" "${out_of_scope:-See roadmap and follow-up sessions.}"
replace_line_prefix "$export_path" "- Assumptions and constraints:" "$(join_by '; ' "$assumptions" "$constraints")"
replace_line_prefix "$export_path" "- Key decisions:" "$(summarize_decisions)"
replace_line_prefix "$export_path" "- ADR references:" "\`docs/adr/ADR-0001-record-architecture-decisions.md\`"
replace_line_prefix "$export_path" "- Top risks:" "${top_risks:-Capture implementation risks during Milestone 0 execution.}"
replace_line_prefix "$export_path" "- Mitigation plans:" "${mitigation_plans:-Keep scope narrow, validate early, and update governance on change.}"
replace_line_prefix "$export_path" "- Contingencies:" "${contingencies:-Reduce scope and re-baseline roadmap if assumptions fail.}"
replace_line_prefix "$export_path" "- Remaining accepted risks:" "${remaining_risks:-None recorded at finalization time.}"
replace_line_prefix "$export_path" "- Milestone 1:" "Milestone 0 vertical slice implemented and verified."
replace_line_prefix "$export_path" "- Milestone 2:" "Stabilize architecture, tests, and documentation after first delivery."
replace_line_prefix "$export_path" "- Milestone 3:" "Expand scope only after baseline verification remains green."
replace_line_prefix "$export_path" "- Exit criteria per milestone:" "$build_command (success), $test_command (pass), $run_command (smoke verified)."
replace_line_prefix "$export_path" "- Technical dependencies:" "$(summarize_dependencies)"
replace_line_prefix "$export_path" "- External dependencies:" "${notes_col:-None recorded}"
replace_line_prefix "$export_path" "- Team/process dependencies:" "Owner: $owner"
replace_line_prefix "$export_path" "- Latest review session:" "${latest_review_session:-None recorded}"
replace_line_prefix "$export_path" "- Quality gate result: pass | conditional-pass | fail" "${latest_review_outcome:-conditional-pass}"
replace_line_prefix "$export_path" "- Required artifacts:" "\`$STATE_FILE\`, development governance docs, verification evidence, and implementation source."
replace_line_prefix "$export_path" "- Implementation recommendations:" "Start with Milestone 0 and keep changes aligned to $project_type boundaries."
replace_line_prefix "$export_path" "- Sequencing notes:" "Build first, then run, then test, then capture verification evidence."
replace_line_prefix "$export_path" "- Explicit non-goals:" "${non_goals:-Avoid scope expansion before baseline verification is complete.}"
replace_line_prefix "$export_path" "- Idea source link:" "$(join_by ', ' "${idea_files[@]:-}")"
replace_line_prefix "$export_path" "- Session links:" "$(join_by ', ' "${session_paths[@]:-}")"
replace_line_prefix "$export_path" "- ADR links:" "\`docs/adr/ADR-0001-record-architecture-decisions.md\`"
replace_line_prefix "$export_path" "- Risk references:" "${latest_review_session:-See related sessions}"

"$(dirname "$0")/render-development-docs.sh"

awk -F'|' -v id="$idea_id" -v path="\`$export_path\`" '
  function trim(s) {
    sub(/^[[:space:]]+/, "", s)
    sub(/[[:space:]]+$/, "", s)
    return s
  }
  $0 ~ "^\\|[[:space:]]*" id "[[:space:]]*\\|" {
    print "| " trim($2) " | " trim($3) " | exported | " trim($5) " | " trim($6) " | " path " | " trim($8) " |"
    next
  }
  { print }
' IDEA_CATALOG.md > IDEA_CATALOG.md.tmp
mv IDEA_CATALOG.md.tmp IDEA_CATALOG.md

cat > MODE.md <<EOF
# Repository Mode

Current mode: development

Allowed values:

- brainstorming
- development

Switch modes with \`./scripts/finalize-project\`.
EOF

cat > "$session_path" <<EOF
# Finalization Session

- Date: $date_stamp
- Owner: $owner
- Idea ID: $idea_id
- Session: $session_path
- Export: \`$export_path\`
- Canonical state: \`$STATE_FILE\`
- Result: in-place mode switch completed

The repository has been successfully finalized into development mode.
EOF

"$(dirname "$0")/validate-development.sh"

trap - ERR INT TERM
cleanup_backups

echo "Project plan created: $export_path"
echo "Canonical state saved: $STATE_FILE"
echo "Finalization session log: $session_path"
echo "The repository has been successfully finalized into development mode."
