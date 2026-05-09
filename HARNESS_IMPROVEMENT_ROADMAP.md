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

- [x] Decide whether the first extracted runtime should stay Python or move to a
      compiled binary later.
- [x] Define how thin generated wrappers find the expected runtime.
- [x] Define compatibility checks between local wrappers, recorded provenance,
      and installed runtime version.
- [x] Keep an inspectable source path for public trust.
- [x] Define how a release artifact would be installed through Cargo, Homebrew,
      GitHub releases, or a plain source checkout.
- [x] Preserve local fallback behavior for users who do not install a global
      runtime.
- [x] Identify which copied `scripts/python/template_cli` modules can stop being
      duplicated once the runtime boundary is stable.
- [x] Write an ADR before committing to binary/runtime extraction.

Exit criteria:

- [x] Runtime extraction has an ADR-backed plan and does not break stable local
      command UX.

## Backlog

- [x] Add a `pyproject.toml` for formatter/linter/import hygiene.
- [x] Split generated CI workflow rendering out of `render.py`.
- [x] Split brainstorming session helpers out of `workflow_data.py`.
- [ ] Continue splitting orchestration-heavy modules when cohesive boundaries are clear:
      `finalize.py`, `handoff.py`, `render.py`,
      `render_governance_templates.py`, and `workflow_data.py`.
- [x] Make `HARNESS_IMPROVEMENT_ROADMAP.md` updates part of template-maintenance
      review when adding new public-template work.
- [x] Promote durable conclusions from `note-0001` into ADR or bootstrap/update
      docs after the manifest/update direction is finalized.
- [x] Review public-template notes for generic wording before publishing a
      release.

## Repo Survey Backlog

These tasks come from a fresh full-template survey after Milestone 9 and the
first cleanup backlog pass. They are intentionally grouped so each future slice
can stay small and reviewable.

### Release And Public Template Readiness

- [ ] Add a public template release checklist that runs `./scripts/validate-governance`,
      the full unit suite, a fresh `project-harness new --no-git` validation,
      and at least one finalize/render smoke fixture.
- [ ] Add a top-level template `CHANGELOG.md` or release notes file for harness
      releases, distinct from generated project `CHANGELOG.md` files.
- [ ] Define the release process for bumping `harnessVersion`, plugin version,
      compatibility versions, docs, and tags in one reviewable slice.
- [x] Replace remaining public-template wording that says update tooling is
      "future" where dry-run/apply now exist, including README and file-map
      descriptions.
- [x] Generalize remaining public examples that mention project-specific names
      such as DevOS or personal owner placeholders.
- [x] Align `NOTES_CATALOG.md` tags and metadata with generalized retained note
      wording.
- [ ] Review plugin author/contact metadata for public release suitability.

### Update Tooling And Provenance

- [x] Fix the `project-harness update --dry-run` "Next commands" text that still
      says apply mode is not implemented.
- [x] Update `harness_commands/harness_manifest.json` stable wrapper metadata so
      `scripts/project-harness` includes `project-harness-update`.
- [x] Add validation that manifest stable wrapper backend commands match real
      CLI parser subcommands.
- [ ] Implement or intentionally remove the advertised `--source-commit` update
      source selector.
- [ ] Implement or intentionally remove the advertised `--release-version`
      update source selector.
- [ ] Add update apply support for clean harness-owned removals, with explicit
      dry-run visibility and tests.
- [ ] Add an update rollback command or automatic rollback path when hooks or
      validation fail after file copies.
- [ ] Add tests for `--include-mixed` apply behavior and its review/backup
      output.
- [ ] Add tests proving update hooks run when repo skills or the intent registry
      change.
- [ ] Add source-dirty provenance handling to update dry-run/apply output so
      users know when the target template checkout has uncommitted changes.

### Manifest, Registry, And Schema Contracts

- [ ] Add JSON Schema files for `harness_commands/harness_manifest.json` and
      `harness_commands/intent_registry.json`.
- [ ] Replace hand-written manifest/intent shape checks with schema-backed
      validation while preserving precise failure messages.
- [ ] Tighten artifact inventory validation so retained harness files are either
      covered by an ownership class or explicitly excluded.
- [ ] Decide whether broad manifest entries such as `scripts/` and
      `.agents/skills/` should be expanded into generated inventory snapshots
      for update planning.
- [ ] Extend command/capability discovery beyond `/lab` intents to cover
      `project-harness`, rendering, sync, and validation commands.
- [ ] Validate parity between wrapper help text, CLI parser arguments, and the
      machine-readable command registry.
- [ ] Add note-catalog validation that checks note file metadata tags, title,
      date, and ID against `NOTES_CATALOG.md`.

### Module Decomposition And Code Quality

- [ ] Continue splitting orchestration-heavy modules when cohesive boundaries are
      clear: `bootstrap_update.py`, `finalize.py`, `handoff.py`, `lab_cli.py`,
      `render_governance_templates.py`, `render_templates.py`, `intents.py`,
      `wiki.py`, and `workflow_idea_commands.py`.
- [ ] Split `bootstrap_update.py` into source resolution, plan classification,
      apply execution, backup/rollback, and output rendering modules.
- [ ] Split `finalize.py` into value collection, state assembly, artifact
      writing, validation, and user-facing output modules.
- [ ] Split `handoff.py` into state-defaults/constants, label extraction,
      state-fill operations, implementation-contract fill, and summary rendering.
- [ ] Split `lab_cli.py` so parser construction and command dispatch are
      table-driven or otherwise easier to compare against the intent registry.
- [ ] Split `render_governance_templates.py` into architecture, ADR, and roadmap
      renderer modules.
- [ ] Split `wiki.py` into wiki config, git execution, page rendering, and status
      checking modules.
- [ ] Lower the Python code-size validation threshold in stages after the large
      modules above are decomposed.
- [ ] Add import-boundary validation for new workflow helper modules as they are
      split out.
- [ ] Run Ruff formatting/linting in CI once local violations are either fixed
      or intentionally configured.

### Rendering And Finalization Hardening

- [ ] Add an end-to-end golden fixture for `lab handoff` followed by noninteractive
      finalization and development validation.
- [ ] Add renderer snapshot tests for every generated development document that
      is currently checked by semantic assertions only.
- [ ] Add coverage for finalized projects with generated wiki enabled and
      disabled across render, validate, and status commands.
- [ ] Add tests for preserving user-edited mixed/generated docs during repeated
      render/finalize flows.
- [ ] Document and validate which generated files are overwritten by finalization
      versus intended to become human-owned after first render.
- [ ] Add migration-path tests before any future `state/project-init.json`
      schemaVersion change.

### Cross-Platform And CI Coverage

- [ ] Add Windows PowerShell smoke coverage for `project-harness update --dry-run`
      and `project-harness update --apply --yes`.
- [ ] Add PowerShell smoke coverage for `render-intent-docs`,
      `sync-plugin-skills`, and `render-development-docs` launchers.
- [ ] Add a macOS launcher smoke job if shell-path behavior diverges from Ubuntu.
- [ ] Add CI artifact output for failed generated-doc drift so maintainers can
      inspect the exact changed files.
- [ ] Add a scheduled or manual release-readiness CI workflow that runs the full
      public-template smoke checklist.

### Plugin And Skill Packaging

- [ ] Decide whether plugin mirrors should remain copied files or become
      generated release artifacts before the first public plugin release.
- [ ] Add a plugin package smoke script that verifies all four skills and UI
      metadata outside the repo context.
- [ ] Validate plugin README examples against the actual plugin manifest and
      marketplace entry.
- [ ] Add a version-alignment test covering harness manifest, plugin manifest,
      marketplace metadata, README, and release notes.

### Runtime Extraction Preparation

- [ ] Define the installed Python runtime package interface before extracting
      any local wrapper behavior.
- [ ] Add runtime discovery tests for environment override, compatible installed
      runtime, incompatible installed runtime, and local fallback.
- [ ] Decide how installed runtime compatibility errors should behave for
      read-only commands versus mutating commands.
- [ ] Identify the first read-only validation module to extract behind the
      installed-runtime boundary.
- [ ] Add an ADR before introducing any compiled binary, Homebrew formula, Cargo
      package, or GitHub release artifact as an official install path.
