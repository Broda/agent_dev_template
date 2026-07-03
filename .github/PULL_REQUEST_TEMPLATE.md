## Summary

- What changed:
- Why:

## Evidence

- Idea catalog link (`IDEA_CATALOG.md`):
- Session evidence (`sessions/...`):
- Export link (`exports/...`) if applicable:
- ADR link (`docs/adr/...`) if applicable:

## Checklist

- [ ] Preserved non-destructive history
- [ ] Updated `IDEA_CATALOG.md` when idea state changed
- [ ] Ran `python3 -m unittest discover -s .harness/tests -v`
- [ ] Ran `./scripts/render-intent-docs` if intent registry or generated intent tables changed
- [ ] Ran `./scripts/sync-plugin-skills` if repo-scoped skills changed
- [ ] Ran `./scripts/validate-governance`
- [ ] Ran the active mode validator (`./scripts/validate-brainstorming` or `./scripts/validate-development`)
- [ ] Updated docs if conversational contract changed
