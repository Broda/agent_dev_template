# Quickstart

Python 3 is required for the `scripts/` automation commands used below.

## 5-Minute Start

1. Start brainstorming naturally in chat.
2. When an idea is worth keeping, say "capture this idea".
3. When moving forward, say "make this active".
4. Check current context and finalize readiness with `./scripts/lab status`.
5. Record decisions/risks only when useful.
6. When done, say "finalize this repo", then run `./scripts/finalize-project`.
7. If you also want an archival summary snapshot, rerun with `./scripts/finalize-project --write-export`.
8. Run audit:

```sh
./scripts/validate-governance
```

## Minimal Finalization Checklist

- [ ] Idea exists in `IDEA_CATALOG.md`
- [ ] At least one session exists in `sessions/`
- [ ] Canonical state is ready to be captured in `state/project-init.json`

## Optional Add-ons

- ADR for strategic decisions (`brainstorming/docs/adr/template.md`)
- Research notes for gathered info (`notes/`, `NOTES_CATALOG.md`, `./scripts/lab-note`)
- Risk tracking (`brainstorming/templates/risk_template.md`)
- Review gate (`brainstorming/templates/review_gate_template.md`)
