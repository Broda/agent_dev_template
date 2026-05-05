# Example Lifecycle

Concrete end-to-end example of using the repo in brainstorming mode and finalizing it in place.

## Scenario

Idea:
- `idea-template-hardening`

Goal:
- Improve the template so brainstorming, canonical state, and development docs stay aligned.

## 1. Capture the Idea

Conversation cue:
- "capture this idea"

Shell equivalent:

```sh
./scripts/lab capture --idea-id idea-template-hardening --title "Template Hardening"
```

Expected effect:
- Add or update the idea in `ideas/_inbox.md`
- Add or update the row in `IDEA_CATALOG.md`

## 2. Activate the Idea

Conversation cue:
- "make this active"

Shell equivalent:

```sh
./scripts/lab activate --idea-id idea-template-hardening
```

Expected effect:
- Move or update the idea in `ideas/_active.md`
- Create or reuse a session file in `sessions/`
- Link the session in `IDEA_CATALOG.md`

## 3. Check Current Status

Shell:

```sh
./scripts/lab status
```

Typical output shape:

```text
Mode: brainstorming
Ideas tracked: 1 (inbox 0, active 1, parked 0, killed 0, finalized 0)
Canonical state: no bound idea yet
Active ideas:
- idea-template-hardening (Template Hardening)
Finalize target: idea-template-hardening (from single active idea)
Target title: Template Hardening
Target owner: David Green
Related sessions: 1
Summary snapshot: none
Finalize readiness: needs-input
Missing before low-friction finalize: problem statement, MVP scope, build command, run command, test command
```

Use this as the main readiness check before finalize.

## 4. Record a Decision, Risk, and Review

Shell:

```sh
./scripts/lab decide --idea-id idea-template-hardening --chosen-option "State-first finalize" --rationale "Preserve continuity"
./scripts/lab risk --idea-id idea-template-hardening --statement "Docs/runtime drift" --mitigation "Validate and test the full path"
./scripts/lab review --idea-id idea-template-hardening --result conditional-pass --summary "Ready after parity checks"
```

Expected effect:
- Append structured entries under `## Decisions`, `## Risks`, and `## Review Gates` in the session file
- Update review state in `ideas/_active.md`

## 5. Optional Summary Snapshot

Shell:

```sh
./scripts/lab export --idea-id idea-template-hardening
```

Expected effect:
- Create `exports/YYYY-MM-DD_PROJECT_SUMMARY_idea-template-hardening.md`
- Record the snapshot path in `IDEA_CATALOG.md`

This is optional. Finalization does not require it.

## 6. Finalize In Place

Shell:

```sh
./scripts/finalize-project --idea-id idea-template-hardening
```

Finalization is non-interactive by default. If readiness is blocked, the command exits with the exact missing fields; use `./scripts/lab doctor --idea-id idea-template-hardening` for source details or rerun with `--interactive` to fill values from prompts.

Optional archival summary during finalize:

```sh
./scripts/finalize-project --idea-id idea-template-hardening --write-export
```

Expected effect:
- Hydrate and persist canonical state in `state/project-init.json`
- Append a finalization session in `sessions/`
- Optionally create or refresh a summary in `exports/`
- Render development docs from canonical state
- Switch `MODE.md` to `development`

## 7. Validate the Result

Shell:

```sh
./scripts/validate-governance
```

In development mode, you can also run:

```sh
./scripts/validate-development
```

## Artifact Summary

By the end of the flow, the durable project record should live in:
- `ideas/_*.md` for idea history and current state
- `sessions/` for chronological context and milestone history
- `state/project-init.json` for canonical structured project definition
- `exports/` only for optional archival summaries

No critical project decision should depend on `exports/` alone.
