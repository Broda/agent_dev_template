# Quickstart

## 5-Minute Start

1. Start brainstorming naturally in chat.
2. When an idea is worth keeping, say "capture this idea".
3. When moving forward, say "make this active".
4. Record decisions/risks only when useful.
5. When done, say "finalize/export plan", then run `./scripts/finalize-project --idea-id <idea-id>`.
6. Run audit:

```sh
./scripts/validate-governance
```

## Minimal Finalization Checklist

- [ ] Idea exists in `IDEA_CATALOG.md`
- [ ] At least one session exists in `sessions/`
- [ ] Export exists in `exports/`

## Optional Add-ons

- ADR for strategic decisions (`brainstorming/docs/adr/template.md`)
- Research notes for gathered info (`notes/`, `NOTES_CATALOG.md`, `./scripts/lab-note`)
- Risk tracking (`brainstorming/templates/risk_template.md`)
- Review gate (`brainstorming/templates/review_gate_template.md`)
