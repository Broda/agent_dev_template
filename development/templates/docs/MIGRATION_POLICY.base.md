# MIGRATION_POLICY.md — Structured Mode v2

This document defines how persistence schema and data migrations are handled.

Persistence is a long-term commitment.
Migrations must be intentional, deterministic, and reversible when possible.

This policy applies to:
- File-based persistence (JSON/YAML/etc.)
- SQLite / RDBMS persistence
- Any stored format that must evolve over time

---

# 1. When a Migration Is Required

A migration is required when:

## 1.1 File-based persistence (JSON/YAML/etc.)
- The stored data format changes (fields added/removed/renamed).
- Validation rules change in a way that affects stored data.
- Default values must be backfilled.
- Stored data must be transformed to preserve compatibility.
- The storage layout changes (one file -> many files, folder layout changes, etc.).

## 1.2 Database persistence (SQLite/RDBMS)
- A new table is added.
- A column is added, removed, or modified.
- Indexes are added or removed.
- Constraints are modified.
- Data transformation is required.

## 1.3 Always
- Seed data changes that affect application behavior.
- Any persistence change that can break older data.

No schema/format changes may be made without:
- Updating this policy if needed.
- Updating ROADMAP.md.
- Updating ARCHITECTURE.md (if structure changes).
- Creating an ADR if architectural impact exists.

---

# 2. Migration Types

## 2.1 Additive Migration (Safe)

Examples (file-based):
- Add optional field with default behavior.
- Add a new top-level section to stored data.
- Add a new file that does not break reading existing files.

Examples (DB):
- Add nullable column
- Add new table
- Add index
- Add non-breaking constraint

Version bump: MINOR or PATCH (per versioning policy)

Must:
- Preserve backward compatibility.
- Not break existing data.
- Be idempotent if re-run (where possible).

---

## 2.2 Transformative Migration

Examples (file-based):
- Rename fields
- Change a field’s structure (string -> object)
- Split one file into multiple files
- Merge multiple files into one
- Normalize data structures

Examples (DB):
- Rename column
- Convert data format
- Merge/split tables
- Normalize structure

Version bump: MINOR (if compatible) or MAJOR (if breaking)

Must:
- Include a migration script or deterministic migration routine.
- Include validation checks.
- Include rollback plan if possible.
- Include migration notes in CHANGELOG.

---

## 2.3 Breaking Migration

Examples (file-based):
- Remove required fields used by older versions.
- Change format such that older versions cannot read it.
- Change identifiers/keys in a way that breaks references.

Examples (DB):
- Remove column used by prior versions.
- Change column type incompatibly.
- Drop table.
- Change primary keys.

Version bump: MAJOR

Requires:
- ADR
- Explicit migration plan
- Backup strategy
- Upgrade path documentation

Breaking changes must be rare.

---

# 3. Migration Location & File Rules

Choose ONE migration strategy and stick to it (document choice in ARCHITECTURE.md):

## 3.1 File-based migrations
Store migration code/scripts in a dedicated location (example):
- src/persistence/migrations/ (preferred), or
- migrations/

Name migrations in ordered format:
- 0001_initial_format.md (notes) + migration routine in code, or
- 0001_initial_format.ts, 0002_rename_field.ts, etc.

Rules:
- Migrations must be immutable once committed.
- Do not edit old migration files.
- New changes require new migration files.
- Migration history must reflect actual evolution.

## 3.2 Database migrations (SQL)
Store migrations in a dedicated directory (e.g., persistence/migrations).

Name migrations in ordered format:
  0001_initial_schema.sql
  0002_add_user_table.sql
  0003_add_index_to_transactions.sql

Same immutability rules apply.

---

# 4. Migration Execution Rules

- Migrations must run automatically on startup (if applicable) OR via an explicit upgrade command.
- Migration execution must be deterministic.
- Partial migration failure must halt startup/upgrade.
- Application must not continue in a partially migrated state.

If migration fails:
- Surface clear error.
- Do not corrupt existing data.

For file-based persistence:
- Prefer “read old -> transform -> write new” with backups.
- Avoid in-place destructive edits without a backup.

---

# 5. Data Integrity Requirements

Migrations must:
- Preserve existing data unless explicitly removed in MAJOR release.
- Avoid silent truncation.
- Avoid silent type coercion.
- Avoid lossy transformations.

For transformative migrations:
- Validate counts/keys before and after (records, entities, etc.).
- Validate constraints.
- Log transformation summary if appropriate.

---

# 6. Rollback Policy

Rollback capability depends on migration type:

Additive migrations:
- Generally safe to leave as-is.
- Rarely require rollback.

Transformative migrations:
- Prefer reversible operations when feasible.
- Strongly prefer a backup before transformation.

Breaking migrations:
- Must require backup before applying.
- Must document restoration procedure.

Rollback strategy must be documented for MAJOR changes.

---

# 7. Version Alignment

Persistence version must align with application version.

PATCH:
- No breaking format/schema change.
- Additive changes only (if allowed by project policy).

MINOR:
- Additive changes allowed.
- Backward-compatible migrations only.

MAJOR:
- Breaking changes allowed with plan.

Application must verify persistence version at startup (where applicable).

If mismatch:
- Run migrations or fail safely.

File-based recommendation:
- Store a `schemaVersion` (or `formatVersion`) in the persisted data.

---

# 8. Seed Data Policy

If seed data is used:
- Treat seed changes as migrations.
- Do not silently modify seed values.
- Document seed changes in CHANGELOG.

---

# 9. Data Backups

If project is local-first or user-data backed:

Before applying Transformative or Breaking migrations:
- Create backup copy.
- Validate backup success.
- Apply migration.
- Confirm integrity.

Backup strategy must be documented in README if applicable.

File-based recommendation:
- Keep rotating backups (e.g., `.bak`, timestamped backups) during upgrades.

---

# 10. Refactor Constraints

Refactor milestones must:
- Not change persistence schema/format.
- Not alter persistence behavior.
- Not require migration.

If a persistence change is required, it is not a pure refactor milestone.
Update roadmap and version accordingly.

---

# 11. Testing Requirements

Migrations must be tested:

- Fresh bootstrap (new install)
- Upgrade from previous version
- Upgrade from multiple prior versions (if possible)

Migration tests must validate:
- Schema/format shape
- Required constraints
- Data preservation
- Application startup success

No migration may ship untested.

---

# 12. AI Guardrails — Migration Discipline

AI must:
- Not modify existing migration files.
- Not rewrite historical schema/format.
- Not remove fields silently.
- Not change types without migration.
- Not introduce schema/format drift.

If uncertain, ask before generating migration.

---

# 13. Guiding Principle

Data is harder to change than code.

Code can be rewritten.
Persistence evolution must be permanent, deliberate, and versioned.

Migrations are historical artifacts.
Treat them as such.
