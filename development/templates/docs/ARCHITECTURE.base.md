# ARCHITECTURE.md — Structured Mode v2

This document defines structure and boundaries.

---

# 1. Design Goals

- Clean separation of concerns.
- Replaceable infrastructure.
- Deterministic core logic.
- Stable public contracts.
- Long-term maintainability.

---

# 2. Layer Model

Interface  
→ Application  
→ Domain/Core  
→ Persistence  
→ Infrastructure  

---

# 3. Layer Responsibilities

## Interface Layer

- UI / CLI / API
- Basic input validation
- Presentation logic

Must NOT:
- Contain business rules
- Access storage directly

---

## Application Layer

- Orchestrates use cases
- Coordinates domain + repositories
- Defines transaction boundaries

---

## Domain Layer

- Pure business logic
- Deterministic
- Framework-agnostic
- Unit-testable

No I/O.

---

## Persistence Layer

- Repository interfaces + implementations
- Data mapping
- Storage abstraction

---

## Infrastructure

- Filesystem
- Network
- Runtime environment
- External services

---

# 4. Public Contracts

Public contracts include:

- API endpoints
- IPC channels
- DTO structures
- CLI commands
- Library exports

Changes require ADR.

---

# 5. Data Model

Define:

- Entities
- Value objects
- DTOs
- Storage schema

---

# 6. Testing Model

Domain:
- Heavy unit coverage

Application:
- Repository-mocked tests

Interface:
- Smoke tests only

---

# 7. Evolution Strategy

Refactors must:

- Preserve public contracts
- Preserve behavior
- Maintain test coverage
- Avoid cross-layer leaks
