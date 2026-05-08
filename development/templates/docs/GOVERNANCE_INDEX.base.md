# GOVERNANCE_INDEX.md — Structured Mode v2

This document is the authoritative index of all governance, policy,
and structural enforcement documents in this repository.

If there is ever ambiguity, this file defines which document governs what.

All contributors and AI agents must consult this index before major changes.

---

# 1. Core Governance Documents

## 1.1 PROJECT_CONTEXT.md

Defines:

- Project purpose
- Architectural philosophy
- Definition of Done
- .gitignore governance
- Milestone discipline
- AI guardrails

Governs: overall system evolution.

---

## 1.2 ROADMAP.md

Defines:

- Active milestone
- Task structure
- Completion criteria
- Refactor constraints
- Evidence requirements

Governs: execution and delivery.

---

## 1.3 ARCHITECTURE.md

Defines:

- Layer boundaries
- Public contracts
- Runtime structure
- Testing model
- Evolution strategy

Governs: structural integrity.

---

## 1.4 FILE_MAP.md

Defines:

- Directory ownership
- Layer mapping
- AI prompt targeting discipline

Governs: modification targeting and boundary safety.

---

## 1.5 VERSIONING_AND_RELEASE_POLICY.md

Defines:

- Semantic versioning rules
- Breaking change classification
- Release checklist
- Changelog structure
- Refactor release constraints

Governs: stability and public contract protection.

---

## 1.6 MIGRATION_POLICY.md

Defines:

- Schema evolution rules
- Migration types
- Backward compatibility constraints
- Data integrity discipline
- Rollback requirements

Governs: persistence evolution.

Only applicable if persistence exists.

---

## 1.7 SECURITY_POLICY.md

Defines:

- Input validation rules
- Secret handling
- Logging discipline
- Dependency hygiene
- Security testing requirements
- Vulnerability response

Governs: system safety and risk control.

---

## 1.8 RUNTIME_VERIFICATION_REPORT.md

Defines:

- Manual verification process
- Milestone sign-off structure
- Refactor parity verification
- Contract validation checklist
- Packaging validation

Governs: milestone and release confidence.

---

## 1.9 ADR Directory (docs/adr/)

Defines:

- Historical architectural decisions
- Supersession chain of decisions
- Long-term system intent

Governs: decision traceability.

---

## 1.10 Research Notes

Operational research notes are stored in:

- `notes/`
- `NOTES_CATALOG.md`

They govern supporting research capture and continuity, but they do not override ADRs, roadmap commitments, or policy documents.

---

# 2. Governance Hierarchy

If documents conflict, precedence is:

1. PROJECT_CONTEXT.md (core philosophy)
2. SECURITY_POLICY.md (never weaken security)
3. MIGRATION_POLICY.md (never corrupt data)
4. VERSIONING_AND_RELEASE_POLICY.md (never break contracts silently)
5. ARCHITECTURE.md (preserve structure)
6. ROADMAP.md (execution intent)
7. FILE_MAP.md (modification targeting)

Security and data integrity override convenience.

---

# 3. Change Classification Matrix

Before making changes, classify them:

Feature:
- Follow ROADMAP
- Version bump MINOR
- Update CHANGELOG

Refactor:
- Preserve contracts
- PATCH bump
- Verify parity

Bug Fix:
- PATCH bump
- Verify no unintended behavior drift

Breaking Change:
- ADR required
- MAJOR bump
- Migration plan required (if persistence affected)

Security Fix:
- PATCH bump (or MAJOR if breaking)
- Document under Security in CHANGELOG

Migration:
- Follow MIGRATION_POLICY
- Align version bump accordingly

---

# 4. Required Pre-Change Checklist

Before making structural changes:

- [ ] Identify affected layer(s)
- [ ] Confirm milestone alignment
- [ ] Check if public contract changes
- [ ] Check if schema changes
- [ ] Check if security posture changes
- [ ] Determine required version bump
- [ ] Determine if ADR required

Do not proceed without classification.

---

# 5. Required Pre-Release Checklist

Before release:

- [ ] All milestone completion criteria satisfied
- [ ] Definition of Done satisfied
- [ ] Runtime verification report completed
- [ ] CHANGELOG updated
- [ ] Version bump aligned with policy
- [ ] Migration rules satisfied (if applicable)
- [ ] Security baseline verified

---

# 6. AI Guardrails

## Agent Pre-Work Sequence

Before making any meaningful change in this repository:

1. Read this file (`docs/GOVERNANCE_INDEX.md`) to identify which governance docs apply.
2. Read all governance documents listed in the index above.
3. Read the most recent ADRs in `docs/adr/`.
4. Read `CHANGELOG.md`.
5. Identify the active milestone in `docs/ROADMAP.md` and confirm the change is in scope.
6. Classify the change (feature, bug fix, refactor, migration, security fix, docs-only).

If persistence exists in this project, also read `docs/MIGRATION_POLICY.md` before any data-layer change.

## Constraints

AI agents must:

- Not introduce breaking changes silently.
- Not weaken security posture.
- Not modify migrations improperly.
- Not change public contracts without ADR + version bump.
- Not bypass Definition of Done.

When uncertain about scope, architecture, or policy: surface the question to the user before proceeding. Do not guess.

---

# 7. Guiding Principle

Governance exists to prevent silent drift.

Structure protects maintainability.
Versioning protects stability.
Migration discipline protects data.
Security protects users.
Verification protects confidence.

Follow governance deliberately.
