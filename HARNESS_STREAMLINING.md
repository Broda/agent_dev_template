# Harness Streamlining Backlog

This file is the active list of remaining streamlining work for the project harness template.

As each item is finished, delete it from this file in the same commit as the change. When this file is empty, do one final project survey before declaring the streamlining pass complete.

## Runtime Module Cleanup

- Review `scripts/python/template_cli/validators.py` for any remaining mixed responsibilities. Extract validator families only where the resulting modules match existing validation boundaries.

## Test Suite Cleanup

- Keep Python test files below the governance size limit as new coverage is added. If finalization or lifecycle tests grow again, split by command family rather than adding broad catch-all files.
- Add focused regression coverage around any module split that changes imports or command wiring, even when behavior is intended to stay identical.

## Plugin And Skill Packaging

- Validate the `plugins/project-lifecycle-lab` package in an external install/use path once the local plugin workflow is ready for that test.
- Decide whether plugin skill mirrors should remain copied files or become generated artifacts from `.agents/skills`.
- If plugin mirrors stay copied, keep `./scripts/sync-plugin-skills` and drift validation as the canonical maintenance path.
- If plugin mirrors become generated, update the validator, file map, and maintenance skill so generated status is explicit.

## Bootstrap Helper

- Decide whether the documented bootstrap contract in `BOOTSTRAP_TOOL.md` should become a real `project-harness update` and `project-harness validate` workflow.
- If update support is added, define what can be refreshed safely without overwriting project-specific state, docs, ideas, sessions, notes, or generated development artifacts.
- If validate support is added, keep it focused on harness integrity checks that make sense inside a cloned project.

## Wiki Tooling Follow-Up

- Exercise `wiki-render` and `wiki-check` against a real initialized GitHub Wiki checkout when a suitable test repository is available.
- Decide whether wiki page generation should include any additional canonical user-facing surfaces beyond README, changelog, architecture, roadmap, ADRs, verification, and release notes.

## Final Survey

- Search docs, skills, plugin mirrors, scripts, tests, and generated command docs for stale language from earlier template/plugin framing.
- Re-run the full validation suite after the backlog is empty.
- Confirm `git status --short --branch` is clean and `main` is pushed.
