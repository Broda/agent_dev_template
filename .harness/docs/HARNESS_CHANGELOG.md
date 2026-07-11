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
