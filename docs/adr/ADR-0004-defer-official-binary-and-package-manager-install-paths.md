# ADR-0004: Defer Official Binary and Package Manager Install Paths

- Status: Accepted
- Date: 2026-05-09
- Deciders: template-maintainers
- Technical Story: Decide whether to advertise compiled binary, Homebrew, Cargo, GitHub release, or source checkout installation before runtime extraction.
- Related Ideas: harness-improvement-roadmap-runtime-extraction
- Supersedes:
- Superseded by:

## Context and Problem Statement

ADR-0002 selects a Python installed runtime as the first possible extraction
direction while preserving repo-local fallback behavior. Before any official
install path is advertised, maintainers need a decision that compares binary
and package-manager distribution against the template's inspectability and
compatibility requirements.

## Decision Drivers

- Preserve public trust by keeping behavior inspectable from a checkout.
- Avoid global "latest" runtime behavior that can silently change generated
  projects.
- Keep rollback simple while runtime discovery, compatibility checks, and
  fallback behavior are still new.
- Avoid supporting multiple package ecosystems before there is a stable runtime
  surface.
- Keep normal template use possible without installing external tools.

## Considered Options

1. Python package or source checkout runtime
- Pros: matches the current implementation language, keeps source inspection
  easy, supports gradual extraction, and can reuse existing tests.
- Cons: requires Python availability and does not provide a single native
  executable.

2. Compiled standalone binary
- Pros: single-file execution, simple PATH story, and easier use where Python is
  not already configured.
- Cons: less transparent than source, adds build/release/signing complexity,
  and increases compatibility risk before the runtime boundary is proven.

3. Homebrew formula
- Pros: familiar install and upgrade path on macOS and Linux for many
  developers.
- Cons: requires formula maintenance, bottle/release discipline, and a stronger
  public support commitment than the template currently needs.

4. Cargo package
- Pros: convenient for Rust-oriented users and can distribute compiled tools.
- Cons: would imply a Rust rewrite or wrapper package before there is evidence
  that the Python runtime is insufficient.

5. GitHub release artifact
- Pros: explicit versioned downloads and a natural place for checksums and
  release notes.
- Cons: artifacts can obscure source-to-runtime mapping unless release
  provenance, verification, and rollback are formalized.

6. Plain source checkout only
- Pros: maximum inspectability, easiest rollback, no external package trust.
- Cons: less convenient than package-manager installation for repeated use.

## Decision Outcome

Do not advertise compiled binary, Homebrew, Cargo, or GitHub release artifact
installation as official paths yet. The only acceptable near-term external
runtime path is an explicit Python source checkout or Python package experiment
that preserves repo-local fallback and manifest-backed compatibility checks.

GitHub releases may publish source archives and release notes, but not an
official runtime artifact, until runtime discovery tests and the first
read-only extraction prove the contract. A future ADR is required before any
compiled binary, Homebrew formula, Cargo package, or official GitHub runtime
artifact is introduced.

## Consequences

### Positive

- Keeps the public template auditable while runtime extraction is still
  reversible.
- Avoids premature package-manager support obligations.
- Keeps compatibility and fallback behavior ahead of distribution convenience.

### Negative

- Users who want a single executable or package-manager install must wait.
- Early runtime extraction remains Python-dependent.

### Neutral

- Existing repo-local wrappers and scripts do not change.
- Release tags and source archives can still be used for explicit-source update
  flows.

## Alternatives Considered But Rejected

- Publish a standalone binary immediately.
- Why rejected: it would force build, signing, verification, and support
  decisions before the runtime boundary is proven.

- Publish Homebrew or Cargo packages as experimental.
- Why rejected: "experimental" package-manager paths still create public
  support expectations and upgrade risk.

- Use GitHub release artifacts as the first runtime distribution.
- Why rejected: release artifacts are useful later, but source-to-runtime
  provenance and rollback rules need to be formalized first.

## Implementation Notes

- Required updates: record this ADR, keep bootstrap/runtime docs clear that
  package-manager and binary paths are deferred, and check off the matching
  roadmap item.
- Affected files: `BOOTSTRAP_TOOL.md`, `HARNESS_IMPROVEMENT_ROADMAP.md`,
  `brainstorming/FILE_MAP.md`.
- Follow-up actions: revisit official install paths only after the
  `validate-python-config` extraction and runtime compatibility behavior pass
  release-readiness checks.
