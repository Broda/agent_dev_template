# VERSIONING_AND_RELEASE_POLICY.md — Structured Mode v2

This document defines how versions are incremented, how releases are cut,
and how public contract stability is preserved.

This project does not require CI/CD,
but it does require disciplined versioning.

---

# 1. Versioning Strategy

This project follows Semantic Versioning:

MAJOR.MINOR.PATCH

Example:
1.4.2

---

## 1.1 Version Meaning

MAJOR

- Breaking public contract change
- API/IPC/DTO change
- CLI command change
- Library export change
- Persistent storage schema break
- Security model change

Requires:
- ADR
- Roadmap update
- Migration plan (if applicable)

---

MINOR

- New feature
- New endpoint
- New CLI command
- Backward-compatible schema extension
- New capability

Must:
- Not break existing contracts
- Preserve existing behavior

---

PATCH

- Bug fix
- Refactor with no public contract change
- Internal performance improvement
- Documentation-only update
- Test additions

Must:
- Preserve public interfaces
- Preserve DTO shapes
- Preserve persistence compatibility

---

# 2. What Is a Public Contract?

Public contracts include:

- API endpoints
- IPC channels
- DTO structures
- CLI commands
- Library exports
- Database schema (if used externally)
- File formats
- Configuration file formats

Changing these requires:

- ADR
- Version bump (MINOR or MAJOR depending on compatibility)

---

# 3. Release Trigger Rules

A release may be cut when:

- A milestone reaches completion criteria.
- A critical bug fix is complete.
- A stable feature set is ready for external use.

A milestone does NOT require a release unless:

- It introduces user-visible behavior.
- It changes public contracts.
- It affects persistence or configuration.

---

# 4. Release Checklist

Before tagging a release:

- [ ] Build succeeds
- [ ] Application runs
- [ ] Tests pass
- [ ] Definition of Done satisfied for all included tasks
- [ ] ROADMAP.md updated
- [ ] ARCHITECTURE.md updated (if needed)
- [ ] ADR created (if required)
- [ ] Public contract stability verified
- [ ] Runtime verification completed
- [ ] CHANGELOG updated

Record evidence in ROADMAP.md or release notes.

---

# 5. Refactor Release Rules

Refactor milestones:

- Must NOT change public contracts.
- Must NOT change DTO shapes.
- Must NOT break persistence.
- Must NOT alter runtime semantics.

If behavior changes:
- That is not a refactor.
- That is a feature or breaking change.
- Update roadmap + version accordingly.

Refactor-only releases are PATCH releases.

---

# 6. Changelog Format

Maintain a CHANGELOG.md file.

Format:

## [1.2.0] — YYYY-MM-DD

### Added
- New feature X

### Changed
- Improved performance of Y

### Fixed
- Corrected rounding edge case in Z

### Refactored
- Modularized renderer bootstrap wiring

### Security
- Hardened input validation for X

Each release entry must align with version bump rules.

---

# 7. Pre-Release Versions (Optional)

If needed, use:

1.4.0-alpha.1  
1.4.0-beta.1  
1.4.0-rc.1  

Pre-releases:

- Must not be tagged as stable.
- Must clearly indicate instability.
- Do not require full milestone completion.

---

# 8. Tagging Rules

Tag format:

v1.4.2

After:

- Version updated in project metadata.
- Changelog updated.
- Release checklist satisfied.

Tags must match actual project version.

---

# 9. Persistence Compatibility Rules

If persistence is used:

PATCH:
- No schema change.
- No migration required.

MINOR:
- Additive schema change allowed.
- Backward-compatible migrations only.

MAJOR:
- Breaking schema change allowed.
- Migration plan required.
- Backup strategy documented.

---

# 10. Security Fix Policy

If a security vulnerability is discovered:

- Patch release immediately.
- Document under Security section.
- Avoid bundling unrelated features.

---

# 11. AI Guardrail — Version Discipline

AI must:

- Not bump MAJOR without explicit instruction.
- Not modify public contracts without ADR.
- Not introduce breaking changes silently.
- Not modify version numbers casually.
- Suggest version bump when appropriate.

---

# 12. Guiding Rule

Version numbers communicate stability.

Refactors preserve trust.  
Minor versions expand capability.  
Major versions break expectations — rarely.

Version intentionally.
