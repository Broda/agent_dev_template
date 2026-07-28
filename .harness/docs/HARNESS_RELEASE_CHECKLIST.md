# Harness Release Checklist

Use this checklist before tagging or publishing a public harness template
release. It applies to this template repository, not to generated projects.

## Required Checks

- [ ] Manual Release Readiness workflow passes in GitHub Actions.
- [ ] `./scripts/harness-release-check`
- [ ] `./scripts/validate-governance`
- [ ] `python3 -m pip install -r requirements-dev.txt`
- [ ] `ruff check .` or `python3 -m ruff check .`
- [ ] `ruff format --check .` or `python3 -m ruff format --check .`
- [ ] `python3 -m unittest discover -s .harness/tests -v`
- [ ] Every path in manifest `posixExecutablePaths` is mode `100755` in the
      working tree, Git index, a fresh generated repository, and its Git archive.
      Build release tar archives with `git -c tar.umask=0022 archive ...`; Git's
      default archive mask may otherwise emit executable entries as `0775`.
- [ ] Fresh copy validates:

```sh
tmpdir="$(mktemp -d)"
./scripts/project-harness new "$tmpdir/harness-smoke" --no-git
"$tmpdir/harness-smoke/scripts/validate-governance"
```

- [ ] Finalize/render smoke fixture passes through development validation:

```sh
python3 -m unittest discover -s .harness/tests -p "test_finalization_regression.py" -v
python3 -m unittest discover -s .harness/tests -p "test_development_rendering.py" -v
```

## Version And Metadata

- [ ] `.harness/commands/harness_manifest.json` `harnessVersion` is correct.
- [ ] `.harness/plugins/project-lifecycle-lab/.codex-plugin/plugin.json` version matches
      the harness version.
- [ ] Compatibility versions are bumped when wrapper, capability, or state-schema
      contracts change.
- [ ] `.harness/docs/HARNESS_CHANGELOG.md` has an entry for the release.
- [ ] `.harness/docs/HARNESS_IMPROVEMENT_ROADMAP.md` reflects completed and deferred work.

## Release Process

1. Pick the release version and update `harnessVersion` in
   `.harness/commands/harness_manifest.json`.
2. Update `.harness/plugins/project-lifecycle-lab/.codex-plugin/plugin.json` to the same
   version.
3. Update `.agents/plugins/marketplace.json` deliberately to the same version;
   `sync-plugin-skills` does not generate marketplace metadata.
4. Bump `compatibility.wrapperRuntimeVersion` when stable wrapper behavior,
   launcher dispatch, or runtime discovery changes.
5. Bump `compatibility.capabilityVersion` when command/capability semantics,
   registry fields, or automation expectations change.
6. Bump `compatibility.stateSchemaVersion` only with a new schema file,
   migration tests, and documentation.
7. Run generated-file maintenance:

```sh
./scripts/render-intent-docs
./scripts/sync-plugin-skills
```

8. Run the required checks above.
9. Update `.harness/docs/HARNESS_CHANGELOG.md` with the release date and summary.
10. Commit the release changes in one reviewable commit.
11. Tag the commit after CI passes.

## Generated And Mirrored Files

- [ ] `./scripts/render-intent-docs` produces no uncommitted diff.
- [ ] `./scripts/sync-plugin-skills` produces no uncommitted diff.
- [ ] Generated command docs still match `.harness/commands/intent_registry.json`.
- [ ] Plugin mirrors still match `.agents/skills/`.
- [ ] Plugin cache/reinstall review confirms the skills-only package does not
      replace repo-local launcher files or their manifest-backed mode contract.

## Public Template Review

- [ ] Public docs avoid project-specific product names and personal contact
      details.
- [ ] README, bootstrap/update docs, manifest, plugin README, and roadmap use
      current behavior wording.
- [ ] No local caches, generated backups, or temporary smoke directories are
      tracked.
