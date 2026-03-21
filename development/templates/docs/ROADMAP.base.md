# ROADMAP.md — Structured Mode v2

This roadmap defines execution.

Rules:

- Organized by milestone.
- Each milestone has a clear goal.
- Tasks grouped by architectural layer.
- Completion criteria required.
- Evidence required before marking tasks complete.
- No flat TODO lists.

---

# Milestone Template

Each milestone must include:

- Goal
- Architecture Impact
- Domain/Core Tasks
- Application Tasks
- Persistence Tasks
- Interface Tasks
- Infrastructure Tasks (if needed)
- Testing & Verification
- Completion Criteria

---

# Milestone 0 – Foundation

## Goal

Establish stable architecture baseline and vertical slice.

## Architecture Impact

- Define layer boundaries.
- Establish documentation discipline.

---

## Domain/Core

- [ ] Define core entities
- [ ] Add validation rules
- [ ] Add unit tests

---

## Application

- [ ] Create orchestration layer

---

## Persistence

- [ ] Define repository interfaces
- [ ] Implement initial storage adapter

---

## Interface

- [ ] Basic interaction surface
- [ ] Validation feedback

---

## Testing & Verification

- [ ] Build succeeds
- [ ] Tests pass
- [ ] Manual smoke test complete

---

## Completion Criteria

- Vertical slice works end-to-end
- Tests validate core logic
- No cross-layer violations

---

# Refactor Milestone Template

Refactor milestones must include:

## Goal

Reduce risk or improve structure without changing behavior.

## Constraints

- No public contract changes.
- No DTO shape changes.
- No API surface drift.
- No domain behavior changes.

## Tasks

- [ ] Extract modules
- [ ] Add missing tests
- [ ] Remove cross-layer leaks
- [ ] Preserve behavior parity

## Verification

- [ ] All tests pass
- [ ] Manual workflow parity verified
- [ ] Public interfaces unchanged

---

# Evidence Format

Every completed task must include:

- Evidence: <commands run> + <results observed>
