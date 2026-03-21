# project_init_templates/manifest.md — Structured Mode Bootstrap

This folder is a one-time bootstrap installer.

Goal:
- Ask a small set of initialization questions
- Generate only the governance/docs needed for THIS project
- Populate placeholders using user answers
- Delete `project_init_templates/` after successful initialization

After initialization:
- `docs/` is the single source of truth
- Templates must never be used again
- Do not overwrite root `AGENTS.md` (it is the governing runtime instruction file)

---

## A) Initialization Questions (Ask These In Order)

1. Project name?
2. One-paragraph purpose / product description?
3. Project type? (choose one)
   - CLI
   - Desktop
   - Web App
   - API
   - Library
4. Tech stack summary:
   - Language:
   - Runtime:
   - Framework (if any):
   - Package manager/build tool (if any):
5. Persistence?
   - None
   - File-based (JSON/YAML/etc.)
   - SQLite
   - Postgres/MySQL/Other RDBMS
6. Authentication?
   - None
   - Local users
   - External auth provider
7. Determinism / correctness sensitivity?
   - Normal
   - High (deterministic outputs required; no float drift; stable ordering)
8. Packaging/distribution planned?
   - None
   - Yes (desktop installers / containers / artifacts)
9. Any constraints (freeform):
   - Offline-first
   - Security-sensitive
   - Performance-critical
   - Must run on <OS/Platform>
   - Other

Do not proceed to generation until answers are collected.

---

## B) Files To Generate (Always)

Always generate the following (from templates):

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

Note: CHANGELOG.md must be generated from a template file (add `project_init_templates/docs/CHANGELOG.base.md`).

---

## C) Conditional Files

Generate the following ONLY when relevant:

### MIGRATION_POLICY.md
Include if Persistence != None

- docs/MIGRATION_POLICY.md

If Persistence = None:
- Do NOT create MIGRATION_POLICY.md

---

## D) Placeholder Replacement Rules

Templates may include placeholders like:

- <Project Name>
- <Build command>
- <Run command>
- <Test command>
- <Active milestone>

Rules:

1. Replace all placeholders using collected answers.
2. If a placeholder cannot be inferred, ask a targeted follow-up question.
3. Do not leave unresolved `<...>` placeholders in generated files.
4. Keep content concise but complete.

---

## E) Stack-Specific Inserts

### README.md
Must include:

- Setup section with stack-aligned commands
- Build / Run / Test command placeholders resolved
- “Docs” section linking governance files

### .gitignore
Select the best baseline from `project_init_templates/gitignore/`:

- node.gitignore
- dotnet.gitignore
- python.gitignore
- generic.gitignore

Then optionally append:
- build outputs
- local DB files (if persistence is local-first)
- .env patterns
- IDE artifacts

---

## F) Milestone 0 Creation

Initialize ROADMAP Milestone 0 as:

Milestone 0 — Foundation / Spine

Must include tasks for:

- Repo + docs scaffold
- Minimal vertical slice (“hello feature”)
- Test harness exists + one real test
- Local verification commands documented
- (If persistence) initial schema + migration baseline

---

## G) Completion & Cleanup

Initialization is complete only when:

- All files are generated
- All placeholders are resolved
- ROADMAP has Milestone 0 defined
- GOVERNANCE_INDEX lists all governance docs present

Then:

- Delete `project_init_templates/` folder entirely.

Record in CHANGELOG under [Unreleased]:
- “Initialized Structured Mode governance baseline.”
