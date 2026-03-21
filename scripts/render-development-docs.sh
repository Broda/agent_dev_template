#!/usr/bin/env bash
set -euo pipefail

MILESTONE_NAME="Milestone 0 — Foundation / Spine"
STATE_FILE="state/project-init.json"

trim() {
  local s="$1"
  s="${s#${s%%[![:space:]]*}}"
  s="${s%${s##*[![:space:]]}}"
  printf '%s' "$s"
}

extract_json() {
  local path="$1"
  perl -MJSON::PP -e '
    use strict;
    use warnings;
    my $path = shift @ARGV;
    my $file = shift @ARGV;
    open my $fh, "<", $file or die "open $file: $!";
    local $/;
    my $data = decode_json(<$fh>);
    my @parts = split /\./, $path;
    my $cur = $data;
    for my $part (@parts) {
      if (ref($cur) ne "HASH" || !exists $cur->{$part}) {
        exit 2;
      }
      $cur = $cur->{$part};
    }
    print defined $cur ? $cur : q{};
  ' "$path" "$STATE_FILE"
}

copy_base() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
}

replace_literal() {
  local file="$1"
  local from="$2"
  local to="$3"
  FROM="$from" TO="$to" perl -0777 -i -pe '
    BEGIN {
      $from = $ENV{"FROM"} // q{};
      $to = $ENV{"TO"} // q{};
    }
    s/\Q$from\E/$to/g;
  ' "$file"
}

validate_non_empty() {
  local label="$1"
  local value="$2"
  if [[ -z "$(trim "$value")" ]]; then
    echo "Missing required value in state/project-init.json: $label" >&2
    exit 1
  fi
}

project_name=$(extract_json "projectName")
purpose=$(extract_json "purpose")
project_type=$(extract_json "projectType")
language=$(extract_json "techStack.language")
runtime=$(extract_json "techStack.runtime")
framework=$(extract_json "techStack.framework")
package_tool=$(extract_json "techStack.packageTool")
persistence=$(extract_json "persistence")
build_command=$(extract_json "commands.build")
run_command=$(extract_json "commands.run")
test_command=$(extract_json "commands.test")

validate_non_empty "projectName" "$project_name"
validate_non_empty "purpose" "$purpose"
validate_non_empty "projectType" "$project_type"
validate_non_empty "techStack.language" "$language"
validate_non_empty "techStack.runtime" "$runtime"
validate_non_empty "commands.build" "$build_command"
validate_non_empty "commands.run" "$run_command"
validate_non_empty "commands.test" "$test_command"

copy_base "development/templates/docs/README.base.md" "README.md"
copy_base "development/templates/docs/PROJECT_CONTEXT.base.md" "docs/PROJECT_CONTEXT.md"
copy_base "development/templates/docs/ROADMAP.base.md" "docs/ROADMAP.md"
copy_base "development/templates/docs/ARCHITECTURE.base.md" "docs/ARCHITECTURE.md"
copy_base "development/templates/docs/FILE_MAP.base.md" "docs/FILE_MAP.md"
copy_base "development/templates/docs/GOVERNANCE_INDEX.base.md" "docs/GOVERNANCE_INDEX.md"
copy_base "development/templates/docs/VERSIONING_AND_RELEASE_POLICY.base.md" "docs/VERSIONING_AND_RELEASE_POLICY.md"
copy_base "development/templates/docs/SECURITY_POLICY.base.md" "docs/SECURITY_POLICY.md"
copy_base "development/templates/docs/RUNTIME_VERIFICATION_REPORT.base.md" "docs/RUNTIME_VERIFICATION_REPORT.md"
copy_base "development/templates/docs/adr/ADR-0001-record-architecture-decisions.md" "docs/adr/ADR-0001-record-architecture-decisions.md"
copy_base "development/templates/docs/adr/ADR-TEMPLATE.md" "docs/adr/ADR-TEMPLATE.md"
copy_base "development/templates/docs/CHANGELOG.base.md" "CHANGELOG.md"

if [[ "$persistence" != "None" && -n "$persistence" ]]; then
  copy_base "development/templates/docs/MIGRATION_POLICY.base.md" "docs/MIGRATION_POLICY.md"
else
  rm -f "docs/MIGRATION_POLICY.md"
fi

lc_lang=$(printf '%s' "$language" | tr '[:upper:]' '[:lower:]')
if [[ "$lc_lang" == *"python"* ]]; then
  cp "development/templates/gitignore/python.gitignore" ".gitignore"
elif [[ "$lc_lang" == *"node"* || "$lc_lang" == *"javascript"* || "$lc_lang" == *"typescript"* ]]; then
  cp "development/templates/gitignore/node.gitignore" ".gitignore"
elif [[ "$lc_lang" == *"c#"* || "$lc_lang" == *"dotnet"* || "$lc_lang" == *".net"* ]]; then
  cp "development/templates/gitignore/dotnet.gitignore" ".gitignore"
else
  cp "development/templates/gitignore/generic.gitignore" ".gitignore"
fi

if [[ "$persistence" != "None" && -n "$persistence" ]]; then
  cat >> ".gitignore" <<'EOF'
*.db
*.sqlite
*.sqlite3
EOF
fi

printf -v setup_steps 'Language: %s\nRuntime: %s\nFramework: %s\nTooling: %s' \
  "$language" "$runtime" "${framework:-None}" "${package_tool:-None}"

for f in \
  "README.md" \
  "docs/PROJECT_CONTEXT.md" \
  "docs/ROADMAP.md" \
  "docs/ARCHITECTURE.md" \
  "docs/FILE_MAP.md" \
  "docs/GOVERNANCE_INDEX.md" \
  "docs/VERSIONING_AND_RELEASE_POLICY.md" \
  "docs/SECURITY_POLICY.md" \
  "docs/RUNTIME_VERIFICATION_REPORT.md" \
  "docs/adr/ADR-0001-record-architecture-decisions.md" \
  "docs/adr/ADR-TEMPLATE.md"; do
  replace_literal "$f" "<Project Name>" "$project_name"
  replace_literal "$f" "<Milestone Name>" "$MILESTONE_NAME"
  replace_literal "$f" "<Build command>" "$build_command"
  replace_literal "$f" "<Run command>" "$run_command"
  replace_literal "$f" "<Test command>" "$test_command"
done

replace_literal "README.md" "Short description of the project." "$purpose"
replace_literal "README.md" "<Prototype / MVP / Beta>" "MVP"
replace_literal "README.md" "<Stack-specific setup steps>" "$setup_steps"

awk -v b="$build_command" -v r="$run_command" -v t="$test_command" '
  /Build:/ { print; getline; print ""; print "    " b; next }
  /Run:/ { print; getline; print ""; print "    " r; next }
  /Test:/ { print; getline; print ""; print "    " t; next }
  { print }
' "README.md" > "README.md.tmp"
mv "README.md.tmp" "README.md"

replace_literal "docs/PROJECT_CONTEXT.md" "<Describe what this project is and why it exists.>" "$purpose"
replace_literal "docs/PROJECT_CONTEXT.md" "<What comes next>" "Deliver Milestone 0 vertical slice and verification evidence."
replace_literal "docs/ROADMAP.md" "Milestone 0 – Foundation" "$MILESTONE_NAME"
replace_literal "docs/ROADMAP.md" "<commands run> + <results observed>" "$build_command (success), $test_command (pass), $run_command (smoke verified)"
replace_literal "docs/RUNTIME_VERIFICATION_REPORT.md" "<build command>" "$build_command"
replace_literal "docs/RUNTIME_VERIFICATION_REPORT.md" "<test command>" "$test_command"
replace_literal "docs/RUNTIME_VERIFICATION_REPORT.md" "<run command>" "$run_command"

awk '
  /## \[Unreleased\]/ { print; print ""; print "### Added"; print "- Initialized Structured Mode governance baseline from brainstorming finalization."; next }
  { print }
' "CHANGELOG.md" > "CHANGELOG.md.tmp"
mv "CHANGELOG.md.tmp" "CHANGELOG.md"
