# Harness Changelog

This changelog tracks releases of the project harness template itself. Generated
projects receive their own `CHANGELOG.md` during finalization.

## [Unreleased]

- Current planned harness version: `0.1.1`.
- Added the HM10 CI-efficiency baseline: superseded pull-request runs now
  cancel by pull request while manual and release-readiness runs remain
  independent, all template CI jobs have conservative finite timeouts, and
  failure-only drift artifacts expire after three days.
- Generated development CI now applies the same pull-request cancellation and
  three-day diagnostic retention behavior plus a conservative 60-minute
  timeout to every emitted job.
- Development validation now contract-checks generated CI by workflow, job, and
  upload-step placement without requiring brainstorming-only workflows in
  finalized consumers.
- Clarified that generated GitHub CI is feedback and compatibility evidence by
  default and that authoritative exact-SHA release evidence may come from a
  separately controlled verifier defined by project policy.
- Fixed Bash 3.2 `set -u` failures in `lab.sh` and `project-harness.sh` by
  replacing empty-array argument forwarding with scalar-plus-positional
  argument construction.
- Added a manifest-backed mode `100755` contract for POSIX launchers, including
  generation, Git staging, update/apply repair, validation, and source-archive
  verification. The Git index and release archives require exactly `100755`;
  working-tree validation requires only the owner execute bit so checkouts made
  under any umask still validate.
- Made development status and evidence parsing accept case-insensitive active
  milestone labels and CommonMark `-`, `*`, or `+` checkbox bullets.
- Canonicalized rendered development documents on `Active Milestone:` and `-`
  checkbox bullets.
- Added optional structured `finalizedContract` rendering and semantic
  validation so CLI/data-pipeline finalization preserves reviewed milestones,
  invariants, deferred scope, and capability boundaries without web/API/auth
  template residue.
- Fixed brainstorming-to-development semantic fidelity by compiling repeated
  native decision and risk records plus `Related Idea ID` notes into canonical
  structured state, rendering their full choices/rationales/constraints and
  risk controls into development governance, and blocking handoff/finalization
  with actionable record-level guidance when native semantics are incomplete.
- Extended that canonical contract to retain complete ordered related-note
  bodies and substantive Current Focus / Exploration Path Notes with source
  traceability, render them into authoritative development contract sections,
  and detect generated-document omissions during semantic validation.
- Relocated the canonical compatible state schema to the harness-owned
  `.harness/schemas/` namespace so an old downstream updater installs the
  missing target path on its first apply, while preserving both the downstream
  `state/project-init.json` and legacy project-owned schema byte for byte.
- Ignored marker-only CommonMark bullets when compiling note and session
  sections so empty template placeholders cannot become bogus contract items.
- Added an atomic development-doc compatibility migration to the skill-sync
  update hook. Existing finalized projects with legacy generated contract
  omissions now receive a versioned authoritative contract section and
  corrected deferred-scope fallbacks without changing project state or
  replacing authored docs; validation failure restores the original docs.
- Unified effective deferred scope across state normalization, rendering, and
  validation so populated out-of-scope or non-goal fields cannot render as
  `None recorded`; structured Finalized Contract JSON and legacy headings
  remain compatible.
