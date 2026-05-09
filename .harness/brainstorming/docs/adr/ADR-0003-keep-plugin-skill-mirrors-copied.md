# ADR-0003: Keep Plugin Skill Mirrors Copied

- Status: Accepted
- Date: 2026-05-09
- Deciders: template-maintainers
- Technical Story: Define plugin mirror ownership before the first public plugin release.
- Related Ideas: harness-improvement-roadmap-plugin-packaging
- Supersedes:
- Superseded by:

## Context and Problem Statement

The harness keeps repo-scoped skills under `.agents/skills/` as the canonical
agent workflow instructions. The optional plugin package under
`.harness/plugins/project-lifecycle-lab/` exposes copied skill mirrors for portable
distribution. Before publishing that plugin shape, maintainers need a durable
decision about whether mirrors remain checked-in copies or become generated
release/install artifacts.

## Decision Drivers

- Keep public-template review simple: plugin package contents should be visible
  in normal diffs.
- Prevent drift between repo-scoped skills and plugin mirrors.
- Avoid adding release-time generation until packaging has more operational
  complexity than simple copied files.
- Keep local development ergonomic for agents and maintainers editing skills.
- Preserve the boundary that plugin packaging does not replace repo-local
  scripts, state, validators, or generated docs.

## Considered Options

1. Keep checked-in copied mirrors with sync and drift validation
- Pros: inspectable package contents, straightforward local edits, simple public
  review, existing `sync-plugin-skills` repair path.
- Cons: duplicate files are stored in the repository and must be synced after
  canonical skill edits.

2. Generate plugin mirrors only during release packaging
- Pros: avoids checked-in duplication and guarantees release output comes from
  canonical skills.
- Cons: reviewers cannot inspect the exact packaged skills without running a
  release step, and release automation must become mandatory before there is a
  strong packaging need.

3. Generate plugin mirrors on install
- Pros: keeps the repository lean and could adapt packaging to installer
  context.
- Cons: weakens marketplace reviewability, makes installs depend on generation
  code, and introduces avoidable runtime/package failure modes.

## Decision Outcome

Use option 1: keep plugin skill mirrors as checked-in copied files. The
canonical source remains `.agents/skills/`; `./scripts/sync-plugin-skills`
refreshes the copied mirrors; `./scripts/validate-governance` fails on drift,
missing mirrors, malformed plugin metadata, or README/manifest mismatch.

Generated plugin mirrors remain deferred until the plugin package needs a
release pipeline with stronger guarantees than checked-in copied files can
provide. If that happens, a future ADR must define the generated artifact
contract and update validation before changing the packaging flow.

## Consequences

### Positive

- Maintainers and users can inspect the exact plugin package from a checkout.
- Existing validation catches stale mirrors before release.
- The package stays optional and separate from repo-local runtime behavior.

### Negative

- Skill changes intentionally create duplicate-file diffs after syncing.
- Contributors must remember the sync step, or rely on validation to catch it.

### Neutral

- No command names or wrapper behavior change.
- Public release automation can still add generated packaging later.

## Alternatives Considered But Rejected

- Remove plugin mirrors and point the plugin directly at `.agents/skills/`.
- Why rejected: it would couple the portable plugin package to repo-local
  layout and weaken the package boundary.

- Publish generated-on-install mirrors.
- Why rejected: install-time generation is harder to inspect and debug than
  checked-in package contents.

## Implementation Notes

- Required updates: document this ADR, keep plugin README wording tied to copied
  mirrors, keep sync and drift validation active.
- Affected files: `.harness/plugins/project-lifecycle-lab/README.md`,
  `.harness/runtime/python/template_cli/validator_plugins.py`,
  `.harness/docs/HARNESS_IMPROVEMENT_ROADMAP.md`, `.harness/brainstorming/FILE_MAP.md`.
- Follow-up actions: reconsider generated plugin artifacts only when plugin
  release packaging becomes complex enough to justify a new generation contract.
