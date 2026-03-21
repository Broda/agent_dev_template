# BOOTSTRAP.md — Structured Mode Installer (v2)

This file defines the temporary rules for initializing a new Structured Mode project.

Follow this procedure exactly.

---

# 1) Read Manifest

Read:
- project_init_templates/manifest.md

Review:
- project_init_templates/docs/*.base.md
- project_init_templates/docs/adr/*
- project_init_templates/gitignore/*.gitignore

Do not generate anything yet.

---

# 2) Ask Initialization Questions

Ask the initialization questions in manifest.md in the exact order listed.

Do not skip questions.
Do not assume defaults.
Collect all answers before generation.

---

# 3) Determine Required Files

From manifest rules:

Always generate:
- README.md
- docs/PROJECT_CONTEXT.md
- docs/ROADMAP.md
- docs/ARCHITECTURE.md
- docs/FILE_MAP.md
- docs/GOVERNANCE_INDEX.md
- docs/VERSIONING_AND_RELEASE_POLICY.md
- docs/SECURITY_POLICY.md
- docs/RUNTIME_VERIFICATION_REPORT.md
- docs/adr/ADR-0001-record-architecture-decisions.md
- docs/adr/ADR-TEMPLATE.md
- CHANGELOG.md
- .gitignore (stack-aligned)

Conditionally generate:
- docs/MIGRATION_POLICY.md (if persistence exists: file-based, SQLite, or RDBMS)

Note:
- If persistence is file-based, MIGRATION_POLICY.md still applies and must be written in “data format / schema” terms, not only SQL/table terms.
- If persistence is None, do not generate MIGRATION_POLICY.md.

---

# 4) Generate Files

For each required file:

- Copy from the corresponding `.base.md` template.
- Replace all `<...>` placeholders.
- If a placeholder cannot be inferred, ask a targeted follow-up question.
- Do not leave unresolved placeholders.

Ensure:
- README includes stack-aligned build/run/test commands.
- ROADMAP contains "Milestone 0 — Foundation / Spine".
- GOVERNANCE_INDEX lists all governance docs that exist.
- ADR template is generated into docs/adr/ADR-TEMPLATE.md (not only inside templates).
- .gitignore is selected from stack templates and adjusted if necessary.

Persistence-specific requirements:

If persistence is file-based:
- Plan for a stored `schemaVersion` (or `formatVersion`) in persisted data.
- Plan for deterministic migration routines (read old -> transform -> write new).
- Prefer backups during upgrades (e.g., `.bak`, timestamped backups).
- Define where migrations live (recommended): `src/persistence/migrations/` (document in ARCHITECTURE.md once code exists).

If persistence is SQLite/RDBMS:
- Use ordered migration files and immutable history.
- Define where migrations live (root `migrations/` or `src/persistence/migrations/`) and document in ARCHITECTURE.md.

---

# 5) Milestone 0 Requirements

ROADMAP.md must include Milestone 0 tasks for:

- Repo + docs scaffold confirmation
- Minimal vertical slice ("hello feature")
- Test harness + one real test
- Build / Run / Test commands documented
- Persistence baseline (if persistence exists)

Persistence baseline definition:

File-based:
- Establish initial data format + schemaVersion
- Add at least one migration path stub (even if no-op) and tests covering upgrade

SQLite/RDBMS:
- Establish initial schema and baseline migration
- Add migration runner + tests covering upgrade

---

# 6) ADR Initialization

Generate:

- ADR-0001-record-architecture-decisions.md
- ADR-TEMPLATE.md

Ensure ADR numbering starts at 0001.

---

# 7) Final Validation Before Cleanup

Confirm ALL of the following:

## 7.1 Presence & Completeness
- All required files exist.
- Governance index lists every governance/policy file that exists.

## 7.2 Placeholders
- No unresolved `<...>` placeholders remain in generated files.

## 7.3 Encoding Sanity
- Replace any malformed characters such as `�` in:
  - README.md
  - docs/PROJECT_CONTEXT.md
  - docs/ROADMAP.md
  - docs/RUNTIME_VERIFICATION_REPORT.md
  - any other generated governance docs

Use a consistent canonical milestone title everywhere:
- "Milestone 0 — Foundation / Spine"

## 7.4 Fidelity to Answers
- Project name and description match the user’s initialization answers.
- Selected commands match the approved package manager and scripts.
- Persistence choice is correctly reflected (including whether MIGRATION_POLICY exists).
- Packaging choice is reflected (e.g., .gitignore packaging artifacts if applicable).

## 7.5 CHANGELOG
- CHANGELOG includes the initialization entry under [Unreleased].

If ANY validation fails:
- Fix the issue before cleanup.
- Do not delete templates until validations pass.
- Fail if any generated file contains the template repo name.

---

# 8) Cleanup

Delete the entire `project_init_templates/` folder.

After deletion:

- Do NOT reference templates again.
- Do NOT regenerate governance files.
- Switch to permanent governance rules in AGENTS.md.

---

# Completion Statement

After cleanup, confirm:

"The project has been successfully initialized under Structured Mode governance."
