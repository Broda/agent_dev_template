# Harness Improvement Roadmap

This roadmap tracks improvements to the public project harness template. It is
not a project idea record; it is maintenance planning for the reusable harness
itself.

## Guiding Direction

- Preserve stable repo-local commands: `./scripts/lab`,
  `./scripts/finalize-project`, and `./scripts/validate-governance`.
- Keep project state, brainstorming history, governance docs, notes, and ADRs in
  generated project repositories.
- Reduce duplicated mutable harness implementation over time by moving toward a
  versioned, inspectable runtime with thin local wrappers.
- Do not depend on a global "latest" harness runtime. Generated projects must
  record the template version, exact source commit, and compatibility contract
  they expect.
- Make update tooling conservative by default: dry-run first, classify files,
  preserve project-owned history, and require explicit confirmation before
  changing downstream repositories.

## Milestone 0 - Public Template Hygiene

Goal: remove small public-template friction before deeper runtime changes.

- [x] Add a top-level `LICENSE` file matching the plugin manifest's MIT license.
- [x] Add `.gitattributes` to normalize text files and prevent accidental
      BOM/line-ending churn in generated docs and wrappers.
- [x] Add `.editorconfig` for indentation, final newline, charset, and line
      ending expectations.
- [x] Normalize existing text files intentionally after the line-ending policy is
      committed.
- [x] Expand `.gitignore` for common Python, test, OS, editor, and temporary
      artifacts while keeping template-owned files visible.
- [x] Fix `./scripts/lab --help` and `./scripts/lab help` so the canonical lab
      launcher prints useful command guidance instead of dispatching
      `lab---help` or `lab-help`.
- [x] Add launcher tests for lab help handling on POSIX.
- [x] Add or update PowerShell launcher tests for equivalent help behavior.
- [x] Decide whether `.github/workflows/governance-audit.yml` should be removed
      or changed to run a distinct warn-only audit that is not already covered
      by blocking CI.
- [x] Update `README.md`, `brainstorming/FILE_MAP.md`, and validation fixtures
      whenever public artifact inventory changes.

Exit criteria:

- [x] `./scripts/validate-governance` passes.
- [x] `python3 -m unittest discover -s tests -v` passes.
- [x] A fresh `./scripts/project-harness new <tmp-path> --no-git` copy validates.

## Milestone 1 - Harness Provenance And Compatibility Manifest

Goal: make every generated project able to identify which harness runtime and
capabilities it expects.

- [x] Define a checked-in harness manifest path, such as
      `harness_commands/harness_manifest.json`.
- [x] Include a manifest schema version.
- [x] Include a human harness release version.
- [x] Include the template source repository URL.
- [x] Include the exact source commit when creating a new harness copy.
- [x] Include a compatibility/capability version for wrapper and runtime checks.
- [x] Include supported modes: `brainstorming` and `development`.
- [x] Include stable wrapper entrypoints and the canonical backend command each
      wrapper invokes.
- [x] Include the current `state/project-init.json` schema version expected by
      finalization/rendering.
- [x] Include a retained artifact inventory grouped by ownership class:
      harness-owned, project-owned, mixed/generated, and archival.
- [x] Add a validator for required manifest fields and supported version values.
- [x] Add tests proving `project-harness new` stamps or preserves provenance
      correctly.
- [x] Document the manifest in `README.md` and `BOOTSTRAP_TOOL.md`.

Exit criteria:

- [x] New project copies record source commit/version provenance.
- [x] Validation fails on missing or malformed manifest fields.
- [x] Manifest ownership classes are sufficient to drive an update dry run.

## Milestone 2 - Machine-Readable Command And Capability Surface

Goal: expose the harness command surface without requiring tools to scrape
Markdown docs.

- [x] Decide whether the capability manifest extends
      `harness_commands/intent_registry.json` or lives as a separate generated
      file.
- [x] Include command name, modes, write behavior, touched files, required
      arguments, optional arguments, and stable wrapper path for each command.
- [x] Include whether a command is safe for a read-only adapter to call.
- [x] Include whether a command can mutate git state, project files, external
      wiki checkouts, or only print status.
- [x] Include output/exit-code expectations for automation consumers.
- [x] Validate parity between the capability manifest, argparse/lab parser
      wiring, and generated command docs.
- [x] Render human docs from the same source so
      `harness_commands/COMMANDS.md` and
      `harness_commands/CONVERSATIONAL_MODE.md` stay secondary views.
- [x] Add tests for mode enforcement using the machine-readable command surface.
- [x] Document how external tools should discover commands without executing
      arbitrary repository scripts.

Exit criteria:

- [x] Command docs, intent registry, and capability manifest cannot drift in CI.
- [x] External adapters have an allowlist-ready command/capability contract.

## Milestone 3 - Safe `project-harness update --dry-run`

Goal: let downstream projects inspect harness updates without changing files.

- [x] Extend `./scripts/project-harness` with an `update --dry-run` command.
- [x] Accept an explicit source template path, source commit, or release version.
- [x] Refuse ambiguous update sources.
- [x] Load the current project's recorded harness provenance.
- [x] Compare current project files against the recorded source version and the
      target source version.
- [x] Classify each candidate file as harness-owned, project-owned,
      mixed/generated, missing, added, removed, or conflicted.
- [x] Preserve project-owned paths by default, including `ideas/`, `sessions/`,
      `notes/`, `exports/`, `state/project-init.json`, finalized `docs/`, and
      implementation source files.
- [x] Treat generated docs and wrapper scripts as mixed when local edits exist.
- [x] Print a deterministic dry-run plan with no file writes.
- [x] Include exact next commands for applying or skipping update groups once
      apply mode exists.
- [x] Add regression tests for clean project, locally modified wrapper,
      finalized project, missing file, and conflicted mixed/generated file
      scenarios.
- [x] Document the update boundary in `BOOTSTRAP_TOOL.md`.

Exit criteria:

- [x] Dry run writes no files and exits nonzero only for unsafe/ambiguous input.
- [x] The plan is stable enough to use in tests and PR review.

## Milestone 4 - Safe Harness Update Apply Path

Goal: apply low-risk harness-owned changes while protecting project history.

- [x] Add `project-harness update --apply` after dry-run classification is
      trusted.
- [x] Require an explicit source version or source path.
- [x] Require confirmation unless a `--yes` flag is supplied.
- [x] Apply only harness-owned clean updates by default.
- [x] Require explicit flags for mixed/generated updates.
- [x] Create backups or a pre-update commit before changing files.
- [x] Re-run `./scripts/sync-plugin-skills` when repo-scoped skills change.
- [x] Re-run `./scripts/render-intent-docs` when the intent registry changes.
- [x] Re-run `./scripts/validate-governance`.
- [x] In development mode, also run `./scripts/validate-development`.
- [x] Update recorded harness provenance only after validation passes.
- [x] Print a rollback/review summary with changed paths and validation output.

Exit criteria:

- [x] Clean downstream projects can receive harness-owned updates.
- [x] Locally modified project-owned or mixed files are never overwritten
      silently.

## Milestone 5 - State Schema Contract

Goal: make `state/project-init.json` evolution explicit and testable.

- [x] Add a JSON Schema for `state/project-init.json` schemaVersion 2.
- [x] Validate draft and finalized variants separately where their required
      fields differ.
- [x] Replace hand-written schemaVersion checks with a schema-backed validator
      while preserving precise error messages.
- [x] Add fixture tests for missing required fields, wrong types, unsupported
      schemaVersion, missing artifact references, and valid draft/finalized
      states.
- [x] Document migration expectations for future schemaVersion changes.
- [x] Record state schema compatibility in the harness manifest.

Exit criteria:

- [x] Finalization, handoff, rendering, and development validation all use a
      shared schema contract.
- [x] Future schema changes have an obvious migration/test path.

## Milestone 6 - Rendering Source-Of-Truth Cleanup

Goal: make generated development docs easier to reason about and update.

- [x] Decide which rendered artifacts are template-driven and which are pure
      Python renderer output.
- [x] Avoid copying base templates only to fully overwrite them later.
- [x] Move reusable prose into templates when human editing is expected.
- [x] Keep computed sections in small renderer functions with narrow inputs.
- [x] Make render idempotency tests cover every generated artifact.
- [x] Clarify the relationship between generated CI and rendered governance
      wording that currently says CI/CD is not required.
- [x] Add a state option or policy note for generated CI behavior.
- [x] Document which generated files are safe to edit after finalization and
      which should be regenerated from state.

Exit criteria:

- [x] A maintainer can identify the source of every rendered line.
- [x] Rendered docs no longer contain conflicting CI guidance.

## Milestone 7 - Cross-Platform Validation

Goal: prove public wrappers work on the platforms the template claims to
support.

- [x] Add a Windows CI job for PowerShell launchers.
- [x] Run the PowerShell `project-harness new --no-git` regression on Windows.
- [x] Add PowerShell smoke tests for `lab status --help`, `finalize-project
      --help`, and `validate-governance`.
- [x] Add a macOS CI job only if platform-specific shell behavior appears.
- [x] Keep Ubuntu as the full regression and governance baseline.
- [x] Document any platform requirements, such as `py -3` versus `python`.

Exit criteria:

- [x] POSIX and PowerShell launchers have automated coverage.
- [x] Cross-platform failures are caught before template release.

## Milestone 8 - Plugin And Skill Packaging Maturity

Goal: keep repo-scoped skills and plugin mirrors useful without making plugins
the project runtime.

- [x] Decide when copied plugin mirrors should become generated artifacts.
- [x] If generation is adopted, make `.agents/skills/` the single source of
      truth and regenerate plugin skills deterministically.
- [x] Keep validation for plugin manifest, marketplace entry, mirror drift, and
      harness/plugin boundary wording.
- [x] Add a plugin smoke-check script or documented manual check for external
      installation.
- [x] Version the plugin in step with harness capability changes.
- [x] Document which workflows belong in repo skills versus portable plugin
      skills.

Exit criteria:

- [x] Plugin packaging remains optional and never replaces repo-local runtime
      state or validators.
- [x] Skill drift is either impossible by generation or caught by validation.

## Milestone 9 - Long-Term Runtime Extraction Study

Goal: prepare for a versioned installed runtime without hiding behavior from
public template users.

- [ ] Decide whether the first extracted runtime should stay Python or move to a
      compiled binary later.
- [ ] Define how thin generated wrappers find the expected runtime.
- [ ] Define compatibility checks between local wrappers, recorded provenance,
      and installed runtime version.
- [ ] Keep an inspectable source path for public trust.
- [ ] Define how a release artifact would be installed through Cargo, Homebrew,
      GitHub releases, or a plain source checkout.
- [ ] Preserve local fallback behavior for users who do not install a global
      runtime.
- [ ] Identify which copied `scripts/python/template_cli` modules can stop being
      duplicated once the runtime boundary is stable.
- [ ] Write an ADR before committing to binary/runtime extraction.

Exit criteria:

- [ ] Runtime extraction has an ADR-backed plan and does not break stable local
      command UX.

## Backlog

- [ ] Add a `pyproject.toml` for formatter/linter/import hygiene.
- [ ] Split orchestration-heavy modules when cohesive boundaries are clear:
      `finalize.py`, `handoff.py`, `render.py`,
      `render_governance_templates.py`, and `workflow_data.py`.
- [ ] Make `HARNESS_IMPROVEMENT_ROADMAP.md` updates part of template-maintenance
      review when adding new public-template work.
- [ ] Promote durable conclusions from `note-0001` into ADR or bootstrap/update
      docs after the manifest/update direction is finalized.
- [ ] Review public-template notes for generic wording before publishing a
      release.
