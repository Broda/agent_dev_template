# PROJECT_CONTEXT.md — Structured Mode v2

This document defines how this project evolves.

It exists to keep architecture, roadmap, documentation, and AI-assisted development aligned with long-term intent.

This is a structured, milestone-driven project.

---

# 1. Project Purpose

<Describe what this project is and why it exists.>

Primary goals:

- Correctness
- Maintainability
- Deterministic behavior (if applicable)
- Clean architecture
- Long-term extensibility
- Explicit architectural boundaries

This project is not a scratchpad.
It is intended to evolve intentionally.

---

# 2. Core Architectural Principles

The system follows strict layer separation:

Interface Layer  
→ Application Layer  
→ Domain/Core Logic  
→ Persistence Layer  
→ Infrastructure/Storage

## 2.1 Boundary Rules

- Domain must contain no UI, framework, or infrastructure logic.
- Interface must not contain business rules.
- Persistence must be abstracted behind repository interfaces.
- Infrastructure must not leak into Domain.
- Public interfaces must not change silently.
- Deterministic logic must not rely on uncontrolled runtime behavior.

If unsure, prefer placing logic deeper (Domain/App) rather than higher (Interface).

---

# 3. Development Model

- Local-first development.
- Manual verification required.
- Tests required for core logic.
- No CI/CD required at this stage.
- Milestone-driven execution.

Refactors must be intentional and milestone-scoped.

---

# 4. Documentation Discipline

When a meaningful decision is made:

1. Create or update an ADR in docs/adr/
2. Update ARCHITECTURE.md if structural changes occur.
3. Update ROADMAP.md if milestone scope changes.
4. Update PROJECT_CONTEXT.md if architectural philosophy shifts.

Do not silently introduce structural changes.

---

# 5. ADR Rules

Create an ADR when:

- Multiple viable approaches exist.
- Architectural boundaries change.
- Long-term maintainability is affected.
- Public interfaces change.
- A new major dependency is introduced.
- Storage strategy changes.
- Security model changes.

Naming:

ADR-###-short-description.md

ADRs are historical.
If a decision changes, create a new ADR that supersedes the previous one.

---

# 6. Testing Philosophy

High test coverage is required for:

- Core business logic.
- Deterministic algorithms.
- Edge cases.
- Data transformations.

Application-layer orchestration should be tested with repository mocks where applicable.

Interface-layer tests are secondary to core correctness.

No milestone may be marked complete without passing tests.

---

# 7. Code Quality Expectations

- Strict typing where supported.
- Linting and formatting enforced.
- Clear module ownership.
- No global mutable state without justification.
- No cross-layer imports.
- No “temporary” hacks without roadmap entry.

---

# 8. Definition of Done (Mandatory)

A task may be marked complete only when:

- Project builds successfully.
- Application runs successfully.
- Relevant tests exist and pass.
- Documentation updated if required.
- No architectural boundary violations introduced.
- Evidence commands are recorded under the completed task in ROADMAP.md.

Example evidence:

- Evidence: `npm test` (pass), `npm run build` (success), manual smoke verified.

No exceptions.

---

# 9. .gitignore Governance

The `.gitignore` file must be aligned with the chosen technology stack.

## 9.1 Required Ignored Categories

The following categories must be ignored (when applicable):

### Dependency Artifacts
- node_modules/
- vendor/
- venv/
- .venv/
- package-lock.json (if policy excludes it)
- pnpm-lock.yaml (if policy excludes it)
- Pipfile.lock (if policy excludes it)

### Build Outputs
- dist/
- build/
- out/
- target/
- bin/
- obj/
- coverage/

### Environment & Secrets
- .env
- .env.*
- *.local
- secret files
- key files
- credentials
- API tokens

### IDE / System Artifacts
- .DS_Store
- Thumbs.db
- .idea/
- .vscode/ (unless intentionally versioned)
- .vs/
- *.log

### Runtime Databases (if local-first project)
- *.db
- *.sqlite
- *.sqlite3
- temp runtime data
- exported backups (unless intentionally versioned)

## 9.2 Rules

- Never commit secrets.
- Never commit environment-specific config.
- Never commit local runtime artifacts.
- Never commit dependency caches.
- Never commit compiled artifacts unless required for packaging.

When changing stack or tooling, update `.gitignore` accordingly.

The `.gitignore` file is part of architectural hygiene.

---

# 10. Milestone Discipline

- Only one active milestone at a time.
- All work must align with the active milestone.
- Future features must not be implemented early.
- Refactors must preserve public contracts unless explicitly scoped.

ROADMAP.md is the execution map.
It is not a scratchpad.

---

# 11. Public Contract Stability

Public interfaces include:

- API endpoints
- IPC channels
- DTO structures
- CLI command surfaces
- Library exports

Rules:

- Do not modify public contracts without ADR.
- Refactors must preserve contracts.
- Breaking changes must be versioned or documented.

---

# 12. Dependency Control

Do not introduce:

- Major frameworks
- Heavy runtime dependencies
- Architectural rewrites
- Infrastructure changes

Without:

- Justification
- ADR
- Roadmap alignment

Small utility dependencies may be acceptable if justified.

---

# 13. Security Discipline

- Validate inputs at boundaries.
- Do not trust interface layer input.
- Do not expose infrastructure directly to interface.
- Protect secrets.
- Minimize surface area.
- Preserve secure runtime defaults.

If security-sensitive logic exists, it belongs in lower layers.

---

# 14. No Premature Abstraction

Avoid:

- Abstracting for hypothetical future use.
- Adding factories/interfaces without need.
- Creating over-engineered solutions.
- Introducing unnecessary patterns.

Build for the current milestone.
Refactor when reality demands it.

---

# 15. AI Assistant Guardrails

AI-assisted development must:

- Respect architectural boundaries.
- Follow Definition of Done.
- Update documentation when structure changes.
- Avoid introducing cross-layer logic.
- Avoid adding major dependencies casually.
- Align changes with the active milestone.

If unsure, ask for clarification rather than guessing architecture.

---

# 16. Runtime Verification

Before marking milestones complete:

- Perform manual runtime verification.
- Confirm primary workflows function end-to-end.
- Confirm no console/runtime errors.
- Confirm deterministic behavior (if applicable).

Record verification evidence in ROADMAP.md.

---

# 17. Current Active Milestone

Active Milestone:

<Milestone Name>

Next Priority:

<What comes next>

All development must support the active milestone first.

---

# 18. Guiding Principles

Correctness over convenience.  
Structure over speed.  
Intentional evolution over drift.  
Explicit decisions over implicit behavior.  
Milestones over scattered tasks.  

This is a structured system.
Maintain it accordingly.
