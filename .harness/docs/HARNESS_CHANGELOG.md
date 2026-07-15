# Harness Changelog

This changelog tracks releases of the project harness template itself. Generated
projects receive their own `CHANGELOG.md` during finalization.

## [Unreleased]

- Current planned harness version: `0.1.1`.
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
- Reclassified the compatible state schema as harness-owned so update/apply
  delivers runtime schema evolution automatically while preserving the
  downstream project's `state/project-init.json` byte for byte.
- Unified effective deferred scope across state normalization, rendering, and
  validation so populated out-of-scope or non-goal fields cannot render as
  `None recorded`; structured Finalized Contract JSON and legacy headings
  remain compatible.
