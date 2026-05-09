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
  - Current named-module status is tracked in the Repo Survey Backlog module
    decomposition section below; future work should use that detailed task
    definition rather than adding broad, unsliced refactors here.
  - Acceptance for any remaining split is the same as the survey backlog item:
    compatibility exports or stable imports are preserved, retained inventory is
    updated, and targeted plus full validation stay green.
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

Next-task sequencing:

1. Add the `lab handoff` -> noninteractive finalization golden fixture before
   changing more finalization/render behavior.
2. Add development-doc snapshot coverage and repeated render/finalize
   preservation tests before tightening overwrite semantics.
3. Add CI/platform coverage after the local test fixtures define the expected
   behavior.
4. Resolve plugin mirror and runtime extraction decisions only after the local
   harness behavior is covered well enough to avoid packaging unstable
   contracts.

### Release And Public Template Readiness

- [x] Add a public template release checklist that runs `./scripts/validate-governance`,
      the full unit suite, a fresh `project-harness new --no-git` validation,
      and at least one finalize/render smoke fixture.
- [x] Add a top-level template `CHANGELOG.md` or release notes file for harness
      releases, distinct from generated project `CHANGELOG.md` files.
- [x] Define the release process for bumping `harnessVersion`, plugin version,
      compatibility versions, docs, and tags in one reviewable slice.
- [x] Replace remaining public-template wording that says update tooling is
      "future" where dry-run/apply now exist, including README and file-map
      descriptions.
- [x] Generalize remaining public examples that mention project-specific names
      such as DevOS or personal owner placeholders.
- [x] Align `NOTES_CATALOG.md` tags and metadata with generalized retained note
      wording.
- [x] Review plugin author/contact metadata for public release suitability.

### Update Tooling And Provenance

- [x] Fix the `project-harness update --dry-run` "Next commands" text that still
      says apply mode is not implemented.
- [x] Update `harness_commands/harness_manifest.json` stable wrapper metadata so
      `scripts/project-harness` includes `project-harness-update`.
- [x] Add validation that manifest stable wrapper backend commands match real
      CLI parser subcommands.
- [x] Implement or intentionally remove the advertised `--source-commit` update
      source selector.
- [x] Implement or intentionally remove the advertised `--release-version`
      update source selector.
- [x] Add update apply support for clean harness-owned removals, with explicit
      dry-run visibility and tests.
- [x] Add an update rollback command or automatic rollback path when hooks or
      validation fail after file copies.
- [x] Add tests for `--include-mixed` apply behavior and its review/backup
      output.
- [x] Add tests proving update hooks run when repo skills or the intent registry
      change.
- [x] Add source-dirty provenance handling to update dry-run/apply output so
      users know when the target template checkout has uncommitted changes.

### Manifest, Registry, And Schema Contracts

- [x] Add JSON Schema files for `harness_commands/harness_manifest.json` and
      `harness_commands/intent_registry.json`.
- [x] Replace hand-written manifest/intent shape checks with schema-backed
      validation while preserving precise failure messages.
- [x] Tighten artifact inventory validation so retained harness files are either
      covered by an ownership class or explicitly excluded.
- [x] Decide whether broad manifest entries such as `scripts/` and
      `.agents/skills/` should be expanded into generated inventory snapshots
      for update planning.
- [x] Extend command/capability discovery beyond `/lab` intents to cover
      `project-harness`, rendering, sync, and validation commands.
- [x] Validate parity between wrapper help text, CLI parser arguments, and the
      machine-readable command registry.
- [x] Add note-catalog validation that checks note file metadata tags, title,
      date, and ID against `NOTES_CATALOG.md`.

### Module Decomposition And Code Quality

- [ ] Continue splitting orchestration-heavy modules when cohesive boundaries are
      clear: `bootstrap_update.py`, `finalize.py`, `handoff.py`, `lab_cli.py`,
      `render_governance_templates.py`, `render_templates.py`, `intents.py`,
      `wiki.py`, and `workflow_idea_commands.py`.
  - Next pass: review the largest modules under the 350-line guardrail and split
    only when a cohesive boundary is obvious, such as export/report rendering,
    validation rule families, or source-specific command handlers.
  - Acceptance: every split preserves public imports or adds compatibility
    exports where needed, updates `brainstorming/FILE_MAP.md`, updates retained
    artifact validation if a new module is added, and keeps the full suite green.
- [x] Split `bootstrap_update.py` into source resolution, plan classification,
      apply execution, backup/rollback, and output rendering modules.
- [x] Split update apply execution, backup, rollback, hook, and validation
      helpers out of `bootstrap_update.py`.
- [x] Split update dry-run output rendering out of `bootstrap_update.py`.
- [x] Split update plan classification and baseline comparison out of
      `bootstrap_update.py`.
- [x] Split `finalize.py` into value collection, state assembly, artifact
      writing, validation, and user-facing output modules.
- [x] Split existing finalized-state value collection out of `finalize.py`.
- [x] Split hydrated finalization value collection from existing state and
      source files out of `finalize.py`.
- [x] Split finalization project setting prompts and noninteractive choice
      collection out of `finalize.py`.
- [x] Split transactional finalization state writing, rendering, catalog/mode
      updates, session logging, and development validation out of `finalize.py`.
- [x] Split finalization user-facing success output out of `finalize.py`.
- [x] Split finalization artifact setup, backup registration, existing-state
      loading, and session-log writing out of `finalize.py`.
- [x] Split finalized canonical state assembly out of `finalize.py`.
- [x] Split finalization required-value and noninteractive missing-field
      validation out of `finalize.py`.
- [x] Split `handoff.py` into state-defaults/constants, label extraction,
      state-fill operations, implementation-contract fill, and summary rendering.
- [x] Split `lab_cli.py` so parser construction and command dispatch are
      table-driven or otherwise easier to compare against the intent registry.
- [x] Split intent registry loading, schema validation, and command lookup out
      of `intents.py`.
- [x] Split `render_governance_templates.py` into architecture, ADR, and roadmap
      renderer modules.
- [x] Split `render_templates.py` into README and project-context renderer
      modules with compatibility exports preserved.
- [x] Split `wiki.py` into wiki config, git execution, page rendering, and status
      checking modules.
- [x] Split lab idea summary export handling out of
      `workflow_idea_commands.py`.
- [x] Lower the Python code-size validation threshold in stages after the large
      modules above are decomposed.
  - Target: lower the enforced Python file-size threshold to 350 lines as the
    normal template guardrail, then reevaluate whether a stricter 300-line cap
    improves agent reviewability enough to justify the added module splitting.
- [x] Split oversized test modules so the Python file-size guardrail can drop
      to the 350-line target.
- [x] Lower the Python code-size validation threshold from 475 to 350 lines.
- [x] Lower the Python code-size validation threshold from 500 to 475 lines
      after the `finalize.py` decomposition.
- [ ] Reevaluate whether a stricter 300-line Python code-size guardrail is worth
      the extra module splitting after maintainers have worked with the 350-line cap.
  - Review after at least several nontrivial slices under the 350-line cap.
  - Compare the largest remaining files, diff review friction, and import
    navigation cost before changing the enforced threshold.
  - If adopted, lower in one staged slice only after all current files are
    already below 300 lines or after splitting the specific blockers.
- [x] Add import-boundary validation for new workflow helper modules as they are
      split out.
- [ ] Run Ruff formatting/linting in CI once local violations are either fixed
      or intentionally configured.
  - First run `python3 -m ruff check .` and `python3 -m ruff format --check .`
    locally to capture the current violation set.
  - Decide per violation family whether to fix code, ignore via `pyproject.toml`,
    or defer with a narrow documented TODO.
  - Add CI steps only after local checks pass on a clean checkout.
  - Acceptance: CI reports lint/format failures clearly, the local governance
    validation still passes, and formatter/linter behavior is documented in the
    contributor-facing release checklist.

### Rendering And Finalization Hardening

- [x] Add an end-to-end golden fixture for `lab handoff` followed by noninteractive
      finalization and development validation.
  - Build a temp-repo fixture that starts in brainstorming mode with one active
    idea, one or more sessions, and enough implementation-contract data for
    `./scripts/lab handoff --idea-id <id>` to populate draft state.
  - Run `./scripts/finalize-project --idea-id <id>` without interactive prompts,
    then run `./scripts/validate-development`.
  - Assert final mode, canonical state fields, generated docs, session/export
    artifact references, and catalog transition.
  - Keep the golden expected data small and deterministic; normalize dates or
    derive expected paths from the test date helper instead of hard-coding
    unstable values.
- [ ] Add renderer snapshot tests for every generated development document that
      is currently checked by semantic assertions only.
  - Cover `README.md`, `docs/PROJECT_CONTEXT.md`, `docs/ROADMAP.md`,
    `docs/ARCHITECTURE.md`, `docs/GOVERNANCE_INDEX.md`, policy docs, ADR
    template/initial ADR, `.github/workflows/ci.yml`, and generated
    `CHANGELOG.md` content.
  - Store compact expected snapshots under a test fixture directory or generate
    expected strings through purpose-built helpers when full files are too noisy.
  - Normalize dates, owner names, temp paths, and command ordering where needed.
  - Acceptance: a renderer drift failure points to the exact generated document
    and preserves the existing semantic assertions.
- [ ] Add coverage for finalized projects with generated wiki enabled and
      disabled across render, validate, and status commands.
  - Add one finalized-state fixture with wiki disabled and one with wiki enabled.
  - Assert render no-ops cleanly when disabled and writes/validates expected
    wiki config/status when enabled.
  - Include `./scripts/lab status` expectations for both modes so user-facing
    status output stays aligned with wiki configuration.
- [ ] Add tests for preserving user-edited mixed/generated docs during repeated
      render/finalize flows.
  - Start from a finalized fixture, hand-edit representative mixed/generated
    docs, rerun render/finalize paths, and assert explicitly owned sections are
    refreshed while user-owned sections survive.
  - Cover at least README, project context, roadmap, architecture, ADR, and
    generated CI or policy files if their ownership semantics differ.
  - Acceptance: each preservation assertion maps to an ownership rule documented
    in the finalization overwrite policy task below.
- [ ] Document and validate which generated files are overwritten by finalization
      versus intended to become human-owned after first render.
  - Add a concise ownership table for finalization/render outputs, including
    canonical state, catalog/mode files, session/export artifacts, development
    docs, policy docs, ADR files, generated CI, README, and changelog.
  - Add validation that the table covers every finalization backup/write target
    and every generated development document.
  - Acceptance: future additions to finalization/render outputs fail validation
    until their overwrite/human-owned policy is documented.
- [ ] Add migration-path tests before any future `state/project-init.json`
      schemaVersion change.
  - Define a fixture for the current schema version and a test harness for
    applying future migrations without losing product, governance, command, or
    artifact fields.
  - For now, assert that unknown future versions fail clearly and current
    version fixtures validate unchanged.
  - Acceptance: before any schema bump, a migration test must cover old -> new,
    idempotent re-run, and invalid input failure behavior.

### Cross-Platform And CI Coverage

- [ ] Add Windows PowerShell smoke coverage for `project-harness update --dry-run`
      and `project-harness update --apply --yes`.
  - Add a Windows CI job that creates a generated project from the template,
    mutates a clean harness-owned file in the source checkout, runs dry-run, then
    applies with `--yes`.
  - Assert PowerShell launcher help reaches argparse and that update output
    includes the changed file, validation summary, and backup location.
- [ ] Add PowerShell smoke coverage for `render-intent-docs`,
      `sync-plugin-skills`, and `render-development-docs` launchers.
  - Exercise each `.ps1` launcher on Windows with a clean repo checkout.
  - Include at least one drift/repair scenario for `sync-plugin-skills` and one
    idempotence check for generated intent/development docs.
  - Acceptance: PowerShell launcher failures surface the underlying Python exit
    code and do not hide stderr/stdout needed for diagnosis.
- [ ] Add a macOS launcher smoke job if shell-path behavior diverges from Ubuntu.
  - First audit whether current shell launchers depend on GNU-only behavior or
    Linux-specific paths.
  - Add macOS CI only if that audit or user reports identify divergence; keep it
    launcher-focused rather than duplicating the full Ubuntu matrix.
- [ ] Add CI artifact output for failed generated-doc drift so maintainers can
      inspect the exact changed files.
  - On failure after generated-doc checks, upload a patch/diff artifact plus the
    changed generated files.
  - Include intent docs, development docs, plugin skill mirrors, and manifest
    generated outputs.
  - Acceptance: the artifact is produced only on failure and is small enough for
    routine CI use.
- [ ] Add a scheduled or manual release-readiness CI workflow that runs the full
      public-template smoke checklist.
  - Expose a `workflow_dispatch` trigger first; add a schedule only if runtime
    cost stays reasonable.
  - Run governance validation, full unit suite, plugin package smoke,
    `project-harness new --no-git`, render/finalize smoke fixtures, and update
    dry-run/apply smoke coverage.
  - Acceptance: the workflow is nonblocking for normal PRs until it proves stable
    and documents exactly which release checklist items it covers.

### Plugin And Skill Packaging

- [ ] Decide whether plugin mirrors should remain copied files or become
      generated release artifacts before the first public plugin release.
  - Compare copied mirrors, generated-at-release mirrors, and generated-on-install
    mirrors across reviewability, drift risk, marketplace packaging, and local
    development ergonomics.
  - Capture the decision in an ADR or dedicated release note before changing the
    packaging flow.
  - Acceptance: validation and `sync-plugin-skills` behavior match the chosen
    mirror ownership model.
- [x] Add a plugin package smoke script that verifies all four skills and UI
      metadata outside the repo context.
- [x] Validate plugin README examples against the actual plugin manifest and
      marketplace entry.
- [x] Add a version-alignment test covering harness manifest, plugin manifest,
      marketplace metadata, README, and release notes.

### Runtime Extraction Preparation

- [ ] Define the installed Python runtime package interface before extracting
      any local wrapper behavior.
  - Specify the console entrypoint name, version reporting command, expected
    Python package/module layout, supported Python versions, and compatibility
    metadata read by generated wrappers.
  - Define which commands remain repo-local versus callable through an installed
    runtime in the first extraction slice.
  - Acceptance: wrappers can be designed from the interface without referencing
    private implementation details.
- [ ] Add runtime discovery tests for environment override, compatible installed
      runtime, incompatible installed runtime, and local fallback.
  - Cover explicit environment override, installed runtime on `PATH`, installed
    runtime version mismatch, missing installed runtime, and local source
    fallback.
  - Assert read-only commands and mutating commands report compatibility problems
    according to the policy task below.
- [ ] Decide how installed runtime compatibility errors should behave for
      read-only commands versus mutating commands.
  - Decide whether read-only commands may warn and fall back while mutating
    commands fail closed on version mismatch.
  - Document exact stderr/stdout wording and exit-code expectations.
  - Acceptance: tests cover both command classes before wrapper behavior changes.
- [ ] Identify the first read-only validation module to extract behind the
      installed-runtime boundary.
  - Prefer a module with low write risk and stable inputs, such as manifest,
    intent, artifact inventory, or launcher validation.
  - Define an adapter that can run from both repo-local source and installed
    runtime without changing user-facing command names.
  - Acceptance: extraction can be reverted independently and does not change
    generated project behavior.
- [ ] Add an ADR before introducing any compiled binary, Homebrew formula, Cargo
      package, or GitHub release artifact as an official install path.
  - ADR must compare Python package, compiled binary, Homebrew, Cargo, GitHub
    releases, and source checkout installation.
  - Include trust/auditability, upgrade, rollback, compatibility, and public
    template support implications.
  - Acceptance: no official install path is advertised until the ADR is accepted
    and reflected in README/release docs.
