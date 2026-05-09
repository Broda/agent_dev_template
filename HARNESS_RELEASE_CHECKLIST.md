# Harness Release Checklist

Use this checklist before tagging or publishing a public harness template
release. It applies to this template repository, not to generated projects.

## Required Checks

- [ ] `./scripts/validate-governance`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] Fresh copy validates:

```sh
tmpdir="$(mktemp -d)"
./scripts/project-harness new "$tmpdir/harness-smoke" --no-git
"$tmpdir/harness-smoke/scripts/validate-governance"
```

- [ ] Finalize/render smoke fixture passes through development validation:

```sh
python3 -m unittest tests.test_finalization_regression tests.test_development_rendering -v
```

## Version And Metadata

- [ ] `harness_commands/harness_manifest.json` `harnessVersion` is correct.
- [ ] `plugins/project-lifecycle-lab/.codex-plugin/plugin.json` version matches
      the harness version.
- [ ] Compatibility versions are bumped when wrapper, capability, or state-schema
      contracts change.
- [ ] `HARNESS_CHANGELOG.md` has an entry for the release.
- [ ] `HARNESS_IMPROVEMENT_ROADMAP.md` reflects completed and deferred work.

## Generated And Mirrored Files

- [ ] `./scripts/render-intent-docs` produces no uncommitted diff.
- [ ] `./scripts/sync-plugin-skills` produces no uncommitted diff.
- [ ] Generated command docs still match `harness_commands/intent_registry.json`.
- [ ] Plugin mirrors still match `.agents/skills/`.

## Public Template Review

- [ ] Public docs avoid project-specific product names and personal contact
      details.
- [ ] README, bootstrap/update docs, manifest, plugin README, and roadmap use
      current behavior wording.
- [ ] No local caches, generated backups, or temporary smoke directories are
      tracked.

