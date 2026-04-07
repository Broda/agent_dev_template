# Quickstart

Python 3 is required for the `scripts/` automation commands used below.

For a concrete start-to-finish example, see `brainstorming/EXAMPLE_LIFECYCLE.md`.

## 5-Minute Start

1. Start brainstorming naturally in chat (or use the shell commands in the cookbook below).
2. When an idea is worth keeping, say "capture this idea" or run `./scripts/lab capture --idea-id <id> --title "<title>"`.
3. When moving forward, say "make this active" or run `./scripts/lab activate --idea-id <id>`.
4. Check current context and finalize readiness with `./scripts/lab status` or `./scripts/lab doctor`.
5. Record decisions/risks only when useful.
6. When done, say "finalize this repo" or run `./scripts/finalize-project --idea-id <id>`.
7. If you also want an archival summary snapshot, rerun with `./scripts/finalize-project --write-export`.
8. Run audit:

```sh
./scripts/validate-governance
```

## Minimal Finalization Checklist

- [ ] Idea exists in `IDEA_CATALOG.md`
- [ ] At least one session exists in `sessions/`
- [ ] Canonical state is ready to be captured in `state/project-init.json`

## Shell Cookbook

Core flow:

```sh
./scripts/lab capture --idea-id idea-template-hardening --title "Template Hardening"
./scripts/lab activate --idea-id idea-template-hardening
./scripts/lab status
./scripts/lab doctor
./scripts/lab review --idea-id idea-template-hardening --result conditional-pass --summary "Ready after parity checks"
./scripts/finalize-project --idea-id idea-template-hardening
```

Optional summary snapshot:

```sh
./scripts/lab export --idea-id idea-template-hardening
./scripts/finalize-project --idea-id idea-template-hardening --write-export
```

## Optional Add-ons

- ADR for strategic decisions (`brainstorming/docs/adr/template.md`)
- Research notes for gathered info (`notes/`, `NOTES_CATALOG.md`, `./scripts/lab-note`)
- Risk tracking (`brainstorming/templates/risk_template.md`)
- Review gate (`brainstorming/templates/review_gate_template.md`)

## Maintaining Intent Docs

When changing brainstorming NL intent mappings:

```sh
./scripts/render-intent-docs
./scripts/validate-governance
```

Edit `brainstorming/intent_registry.json` first. The intent tables in `brainstorming/CONVERSATIONAL_MODE.md` and `brainstorming/COMMANDS.md` are generated.
