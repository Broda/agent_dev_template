# Template External Idea Import API Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Add a clean, public-safe automation API for creating a new brainstorming project from an external idea source without callers editing template internals or depending on current working directory quirks.

**Architecture:** The template should own its own idea/catalog/session representation. External systems should pass a sanitized idea payload or CLI flags to stable commands, and the harness should create/activate the canonical idea, create a session, optionally add provenance metadata, initialize Git, and return machine-readable JSON. The public template must use generic names, placeholders, and source labels only; no personal hostnames, usernames, machine paths, private repository names, or environment-specific assumptions should be committed.

**Tech Stack:** Python 3 standard library, existing `scripts/project-harness` / `scripts/lab` launchers, existing `.harness/runtime/python/template_cli/*` modules, pytest-based harness tests, shell scripts already present in `scripts/`.

---

## Public-safety constraints

Apply these constraints to every task in this plan:

- Do **not** commit personal names, private hostnames, private machine names, absolute home paths, Tailnet names, Discord IDs, repository names from private infrastructure, or any user-specific defaults.
- Use generic examples only, such as:
  - `/tmp/example-project`
  - `/workspace/example-project`
  - `external-system`
  - `example-source-id-123`
  - `idea-example-web-app`
- Any provenance fields should support arbitrary external sources without naming any real deployment.
- Tests must use temporary directories and generic payloads.
- Documentation must describe integration patterns generically and should not mention any private infrastructure.

---

## Current context

Relevant existing files:

- `scripts/project-harness` and `scripts/project-harness.sh` invoke the runtime bootstrap commands.
- `scripts/lab` and `scripts/lab.sh` invoke brainstorming lab commands.
- `.harness/runtime/python/cli.py` dispatches top-level harness commands.
- `.harness/runtime/python/template_cli/bootstrap.py` contains `run_project_harness_new(...)`.
- `.harness/runtime/python/template_cli/lab_cli_parsers.py` defines lab subcommands and arguments.
- `.harness/runtime/python/template_cli/lab_cli_dispatch.py` dispatches lab commands.
- `.harness/runtime/python/template_cli/workflow_idea_commands.py` implements `capture`, `activate`, `park`, and `kill`.
- `.harness/runtime/python/template_cli/workflow_sessions.py` creates session files.
- `.harness/runtime/python/template_cli/workflow_catalog.py` owns catalog row updates.
- `.harness/runtime/python/template_cli/workflow_status.py` and related modules report readiness/status.
- `.harness/tests/test_lab_lifecycle.py`, `.harness/tests/test_lab_status.py`, and `.harness/tests/test_project_harness_bootstrap.py` are likely test homes.

Current automation pain points:

1. External callers must run several commands in the right order: `project-harness new`, `lab capture`, `lab activate`, `lab path-note`, then Git commit.
2. Commands are root-sensitive and often require `cd` into either the template root or target project root.
3. There is no single JSON contract for seeding an externally sourced idea.
4. External callers must know too much about catalog/session/bucket conventions.
5. Retry/idempotency behavior is spread across multiple commands.

Target boundary:

```text
External system -> sanitized idea payload -> template command -> generated brainstorming project
```

The external system decides *what* idea to promote. The template decides *how* that idea is represented in the generated project.

---

## Proposed command contract

### New lab command

```bash
./scripts/lab import-idea \
  --idea-id idea-example-web-app \
  --title "Example Web App" \
  --summary "Small web application for demonstration." \
  --source external-system \
  --source-id example-source-id-123 \
  --activate \
  --create-session \
  --path-note "Imported from an external idea source." \
  --no-sync \
  --json
```

Expected JSON output shape:

```json
{
  "ok": true,
  "idea_id": "idea-example-web-app",
  "title": "Example Web App",
  "status": "active",
  "source": "external-system",
  "source_id": "example-source-id-123",
  "session_path": "sessions/2026-06-14_idea-example-web-app.md",
  "changed_files": [
    "IDEA_CATALOG.md",
    "ideas/_active.md",
    "sessions/2026-06-14_idea-example-web-app.md"
  ],
  "readiness": "needs-input"
}
```

### New project-harness command

```bash
./scripts/project-harness new-from-idea /tmp/example-project \
  --idea-id idea-example-web-app \
  --title "Example Web App" \
  --summary "Small web application for demonstration." \
  --source external-system \
  --source-id example-source-id-123 \
  --activate \
  --commit \
  --json
```

Expected behavior:

1. Create a new brainstorming-mode project from the template.
2. Import the idea using the same internal function as `lab import-idea`.
3. Validate governance.
4. Optionally create a commit containing the imported idea/session changes.
5. Return bounded JSON with target path, idea ID, session path, changed files, validation status, and commit SHA when available.

---

## Task 1: Add data model for external idea imports

**Objective:** Introduce a reusable internal payload/result model for importing externally sourced ideas.

**Files:**

- Create: `.harness/runtime/python/template_cli/external_idea.py`
- Test: `.harness/tests/test_external_idea_import.py`

**Step 1: Write failing tests**

Create `.harness/tests/test_external_idea_import.py` with tests for:

- Payload normalization converts `example-web-app` to `idea-example-web-app`.
- Empty or unsafe `source` values are rejected or normalized to a generic safe value.
- Result serialization emits only relative paths.
- No absolute paths appear in JSON output.

Example test skeleton:

```python
from pathlib import Path

from template_cli.external_idea import ExternalIdeaPayload, ExternalIdeaImportResult


def test_external_idea_payload_normalizes_idea_id():
    payload = ExternalIdeaPayload(
        idea_id="example-web-app",
        title="Example Web App",
        summary="Small web application for demonstration.",
        source="external-system",
        source_id="example-source-id-123",
    )

    assert payload.normalized_idea_id == "idea-example-web-app"


def test_external_idea_result_json_uses_relative_paths():
    result = ExternalIdeaImportResult(
        ok=True,
        idea_id="idea-example-web-app",
        title="Example Web App",
        status="active",
        source="external-system",
        source_id="example-source-id-123",
        session_path="sessions/2026-06-14_idea-example-web-app.md",
        changed_files=["IDEA_CATALOG.md", "ideas/_active.md"],
        readiness="needs-input",
    )

    data = result.to_json_dict()

    assert data["session_path"] == "sessions/2026-06-14_idea-example-web-app.md"
    assert all(not Path(path).is_absolute() for path in data["changed_files"])
```

**Step 2: Run test to verify failure**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_external_idea_import.py -q
```

Expected: FAIL because `template_cli.external_idea` does not exist.

**Step 3: Implement minimal model**

Create `.harness/runtime/python/template_cli/external_idea.py` with:

- `ExternalIdeaPayload` dataclass
- `ExternalIdeaImportResult` dataclass
- `normalized_idea_id` property using existing `normalize_idea_id`
- `to_json_dict()` returning only JSON-safe primitives
- basic source/source_id sanitization helpers that reject newlines and trim excessive length

Implementation notes:

- Keep max text lengths conservative.
- Do not encode any environment-specific source names.
- Do not include absolute paths in result models.

**Step 4: Run test to verify pass**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_external_idea_import.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add .harness/runtime/python/template_cli/external_idea.py .harness/tests/test_external_idea_import.py
git commit -m "feat: add external idea import model"
```

---

## Task 2: Implement reusable `import_external_idea(...)` workflow function

**Objective:** Provide one internal function that performs capture, optional activation, optional session creation, optional path note, and JSON-ready result collection.

**Files:**

- Modify: `.harness/runtime/python/template_cli/workflow_idea_commands.py`
- Modify/Create: `.harness/runtime/python/template_cli/external_idea.py`
- Test: `.harness/tests/test_external_idea_import.py`

**Step 1: Add failing workflow test**

Add a test that creates a temporary copy or minimal harness root and calls the new function directly.

Expected assertions:

- `IDEA_CATALOG.md` has one row for `idea-example-web-app`.
- `ideas/_active.md` contains `idea-example-web-app` when `activate=True`.
- `sessions/<date>_idea-example-web-app.md` exists when `create_session=True`.
- Function returns `changed_files` with relative paths only.
- Running it twice does not duplicate catalog rows or bucket entries.

**Step 2: Run test to verify failure**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_external_idea_import.py -q
```

Expected: FAIL because `import_external_idea` does not exist.

**Step 3: Implement workflow function**

Add a function with this shape:

```python
def import_external_idea(
    root: Path,
    payload: ExternalIdeaPayload,
    *,
    activate: bool = True,
    create_session: bool = True,
    path_note: str = "",
    no_sync: bool = False,
) -> ExternalIdeaImportResult:
    ...
```

Implementation guidance:

- Reuse existing internal helpers instead of duplicating catalog logic.
- Prefer extracting common implementation from `run_lab_capture`, `run_lab_activate`, and path-note logic rather than shelling out.
- Preserve idempotency:
  - remove existing bucket entry before adding the current one
  - upsert catalog row
  - reuse existing session when present
- Return changed files even when content was already present.
- Do not auto-commit inside this function; leave commit behavior to CLI/sync layer.

**Step 4: Run direct workflow tests**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_external_idea_import.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add .harness/runtime/python/template_cli/workflow_idea_commands.py .harness/runtime/python/template_cli/external_idea.py .harness/tests/test_external_idea_import.py
git commit -m "feat: import external ideas idempotently"
```

---

## Task 3: Add `lab import-idea` CLI command

**Objective:** Expose the reusable import workflow through the existing lab CLI.

**Files:**

- Modify: `.harness/runtime/python/template_cli/lab_cli_parsers.py`
- Modify: `.harness/runtime/python/template_cli/lab_cli_dispatch.py`
- Modify: `.harness/runtime/python/template_cli/workflow_idea_commands.py`
- Test: `.harness/tests/test_lab_lifecycle.py` or `.harness/tests/test_external_idea_import.py`

**Step 1: Add failing CLI test**

Add a test invoking the CLI with:

```bash
./scripts/lab import-idea \
  --idea-id example-web-app \
  --title "Example Web App" \
  --summary "Small web application for demonstration." \
  --source external-system \
  --source-id example-source-id-123 \
  --activate \
  --create-session \
  --path-note "Imported from an external idea source." \
  --no-sync \
  --json
```

Assert:

- exit code 0
- stdout parses as JSON
- `idea_id == "idea-example-web-app"`
- `session_path` starts with `sessions/`
- no stdout field contains an absolute path
- generated root has no file matching `*devos-idea*` or any source-specific filename convention

**Step 2: Run test to verify failure**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_external_idea_import.py -q
```

Expected: FAIL because parser/dispatcher do not recognize `import-idea`.

**Step 3: Add parser arguments**

In `.harness/runtime/python/template_cli/lab_cli_parsers.py`, add `lab-import-idea` entry with:

- `--idea-id` required, using `idea_arg(required=True)`
- `--title` required
- `--summary` default `""`
- `--source` default `"external"`
- `--source-id` default `""`
- `--activate` action `store_true`
- `--create-session` action `store_true`
- `--path-note` default `""`
- `--no-sync` action `store_true`
- `--json` action `store_true`

Consider defaulting `--activate` and `--create-session` to false at the parser level, then setting friendly defaults in command docs. Or provide explicit `--no-activate` if default activation is preferred. Pick one pattern and document it.

**Step 4: Add dispatcher case**

In `.harness/runtime/python/template_cli/lab_cli_dispatch.py`, dispatch to a wrapper function such as `run_lab_import_idea(...)`.

If `--json` is true, print only JSON to stdout. Human-readable messages should go to stderr or be suppressed in JSON mode.

**Step 5: Run CLI test to verify pass**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_external_idea_import.py -q
```

Expected: PASS.

**Step 6: Commit**

```bash
git add .harness/runtime/python/template_cli/lab_cli_parsers.py .harness/runtime/python/template_cli/lab_cli_dispatch.py .harness/runtime/python/template_cli/workflow_idea_commands.py .harness/tests/test_external_idea_import.py
git commit -m "feat: add lab external idea import command"
```

---

## Task 4: Add explicit root handling to lab commands

**Objective:** Allow automation to call lab commands without relying on `cd` into the target repository.

**Files:**

- Modify: `.harness/runtime/python/template_cli/lab_cli.py`
- Modify: `.harness/runtime/python/template_cli/lab_cli_parsers.py` if global args live there
- Modify: `.harness/runtime/python/template_cli/lab_cli_dispatch.py` if root resolution lives there
- Test: `.harness/tests/test_lab_launcher.py` or `.harness/tests/test_external_idea_import.py`

**Step 1: Add failing test**

Create a temp generated project, then run from a different cwd:

```bash
/path/to/generated/scripts/lab --root /path/to/generated status --json
```

Assert it returns the same JSON as running:

```bash
cd /path/to/generated && ./scripts/lab status --json
```

Use temporary paths only.

**Step 2: Run test to verify failure**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_lab_launcher.py -q
```

Expected: FAIL if `--root` is not recognized.

**Step 3: Implement `--root`**

Add a global lab flag:

```bash
./scripts/lab --root /tmp/example-project status --json
```

Implementation guidance:

- Resolve root path before dispatch.
- Validate root has expected harness markers, such as `.harness/commands/harness_manifest.json` or `MODE.md`.
- Keep default behavior unchanged when `--root` is omitted.
- Do not print absolute root paths in JSON unless explicitly requested.

**Step 4: Run launcher/root tests**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_lab_launcher.py .harness/tests/test_external_idea_import.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add .harness/runtime/python/template_cli/lab_cli.py .harness/runtime/python/template_cli/lab_cli_parsers.py .harness/runtime/python/template_cli/lab_cli_dispatch.py .harness/tests/test_lab_launcher.py .harness/tests/test_external_idea_import.py
git commit -m "feat: allow explicit lab root for automation"
```

---

## Task 5: Add explicit template-root handling to project harness commands

**Objective:** Allow `project-harness` to create projects from a known template root without relying on current working directory.

**Files:**

- Modify: `.harness/runtime/python/cli.py`
- Modify: `.harness/runtime/python/template_cli/bootstrap.py`
- Test: `.harness/tests/test_project_harness_bootstrap.py`

**Step 1: Add failing test**

Run the project harness from a neutral cwd:

```bash
/path/to/template/scripts/project-harness --template-root /path/to/template new /tmp/example-project
```

Assert:

- generated project exists
- generated project includes template harness files
- generated project does not accidentally copy the caller cwd
- validation passes

**Step 2: Run test to verify failure**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_project_harness_bootstrap.py -q
```

Expected: FAIL if `--template-root` is not supported.

**Step 3: Implement `--template-root`**

Implementation guidance:

- Add an optional global `--template-root` for project-harness commands.
- Default should preserve current behavior.
- `run_project_harness_new(root, target, ...)` already accepts `root`; ensure CLI passes the explicit root when supplied.
- Validate explicit root is a template root, not an arbitrary project root.
- Error messages should be generic and not expose private assumptions.

**Step 4: Run bootstrap tests**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_project_harness_bootstrap.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add .harness/runtime/python/cli.py .harness/runtime/python/template_cli/bootstrap.py .harness/tests/test_project_harness_bootstrap.py
git commit -m "feat: support explicit template root"
```

---

## Task 6: Add `project-harness new-from-idea`

**Objective:** Provide the clean one-command automation API for creating and seeding a new brainstorming project from external idea metadata.

**Files:**

- Modify: `.harness/runtime/python/cli.py`
- Modify: `.harness/runtime/python/template_cli/bootstrap.py`
- Modify/Create: `.harness/runtime/python/template_cli/external_idea.py`
- Test: `.harness/tests/test_project_harness_bootstrap.py`
- Test: `.harness/tests/test_external_idea_import.py`

**Step 1: Add failing integration test**

Run:

```bash
./scripts/project-harness new-from-idea /tmp/example-project \
  --idea-id example-web-app \
  --title "Example Web App" \
  --summary "Small web application for demonstration." \
  --source external-system \
  --source-id example-source-id-123 \
  --activate \
  --commit \
  --json
```

Assert:

- exit code 0
- JSON parses successfully
- `target_created == true`
- `idea_id == "idea-example-web-app"`
- `session_path` starts with `sessions/`
- generated project `./scripts/lab status --json` reports one active idea
- generated project contains no source-specific filenames like `external-system-idea-*.md`
- no JSON field contains an absolute path except an explicitly named `target_path` field if retained

**Step 2: Run test to verify failure**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_project_harness_bootstrap.py .harness/tests/test_external_idea_import.py -q
```

Expected: FAIL because `new-from-idea` does not exist.

**Step 3: Implement command**

Add a `run_project_harness_new_from_idea(...)` function that:

1. Calls existing `run_project_harness_new(...)` with `no_git=True` or equivalent if a single final commit is desired.
2. Imports the external idea into the generated project with `import_external_idea(...)`.
3. Initializes Git and creates commits according to flags:
   - `--no-git`: no repo initialization
   - default: initialize Git with normal initial harness commit plus idea commit, or one combined commit if simpler
   - `--commit`: explicitly commit import changes when Git exists
4. Runs governance validation.
5. Returns JSON when `--json` is supplied.

Important design choice:

- Prefer preserving existing `new` behavior for current users.
- `new-from-idea` can have its own commit behavior without changing `new`.

**Step 4: Run integration tests**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_project_harness_bootstrap.py .harness/tests/test_external_idea_import.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add .harness/runtime/python/cli.py .harness/runtime/python/template_cli/bootstrap.py .harness/runtime/python/template_cli/external_idea.py .harness/tests/test_project_harness_bootstrap.py .harness/tests/test_external_idea_import.py
git commit -m "feat: create projects from external ideas"
```

---

## Task 7: Add JSON payload-file support

**Objective:** Avoid shell-quoting bugs by allowing callers to pass a structured JSON file instead of long CLI strings.

**Files:**

- Modify: `.harness/runtime/python/template_cli/external_idea.py`
- Modify: `.harness/runtime/python/template_cli/lab_cli_parsers.py`
- Modify: `.harness/runtime/python/cli.py`
- Test: `.harness/tests/test_external_idea_import.py`

**Step 1: Add failing tests**

Create a temp JSON file:

```json
{
  "schema_version": 1,
  "idea_id": "example-web-app",
  "title": "Example Web App",
  "summary": "Small web application for demonstration.",
  "source": "external-system",
  "source_id": "example-source-id-123",
  "tags": ["web", "demo"]
}
```

Run:

```bash
./scripts/lab import-idea --payload-file /tmp/payload.json --activate --create-session --json --no-sync
```

and:

```bash
./scripts/project-harness new-from-idea /tmp/example-project --payload-file /tmp/payload.json --json
```

Assert both produce the same normalized idea ID.

**Step 2: Run test to verify failure**

Expected: FAIL because `--payload-file` does not exist.

**Step 3: Implement payload loading**

Add helpers:

```python
def load_external_idea_payload(path: Path) -> ExternalIdeaPayload:
    ...
```

Validation rules:

- `schema_version` must be `1`.
- Required fields: `idea_id`, `title`.
- Optional fields: `summary`, `source`, `source_id`, `tags`.
- Reject absolute paths and secret-like fields if introduced later.
- Keep payload schema generic.

**Step 4: Run payload tests**

Expected: PASS.

**Step 5: Commit**

```bash
git add .harness/runtime/python/template_cli/external_idea.py .harness/runtime/python/template_cli/lab_cli_parsers.py .harness/runtime/python/cli.py .harness/tests/test_external_idea_import.py
git commit -m "feat: accept external idea payload files"
```

---

## Task 8: Document the public integration contract

**Objective:** Document stable automation entrypoints without exposing private environment details.

**Files:**

- Create: `docs/EXTERNAL_INTEGRATION.md`
- Modify: `README.md`
- Modify: `.harness/brainstorming/QUICKSTART.md` if appropriate

**Step 1: Draft docs**

`docs/EXTERNAL_INTEGRATION.md` should include:

- Purpose and audience
- Public-safety note: use placeholders; do not include secrets or private machine details
- `lab import-idea` examples
- `project-harness new-from-idea` examples
- JSON payload schema
- JSON output schema
- Idempotency guarantees
- Exit code semantics
- What external callers should not do:
  - do not edit `IDEA_CATALOG.md` directly
  - do not edit bucket files directly
  - do not assume session filename internals beyond returned `session_path`

Use generic examples only.

**Step 2: Add README link**

Add a short section:

```markdown
### External automation

External tools can seed brainstorming projects through the stable import commands documented in `docs/EXTERNAL_INTEGRATION.md`. Prefer these commands over editing catalog, bucket, or session files directly.
```

**Step 3: Run docs/public-safety check manually**

Search changed docs for private patterns before commit:

```bash
git diff -- docs/EXTERNAL_INTEGRATION.md README.md
```

Verify no real hostnames, usernames, home paths, private project names, Discord IDs, Tailnet names, or secrets are present.

**Step 4: Commit**

```bash
git add docs/EXTERNAL_INTEGRATION.md README.md .harness/brainstorming/QUICKSTART.md
git commit -m "docs: describe external idea integration"
```

---

## Task 9: Add public-safety regression checks

**Objective:** Reduce the chance that public docs/tests accidentally include private machine names, paths, or identifiers.

**Files:**

- Create or Modify: `.harness/tests/test_public_safety.py`
- Possibly Modify: `scripts/validate-governance` only if validator dispatch needs to include the new test indirectly

**Step 1: Add failing/guard test**

Create a test that scans documentation and test fixtures for disallowed placeholder patterns.

The test should be conservative and generic. It should not encode real private names. Instead, check for categories:

- absolute home paths like `/home/<name>/` outside examples explicitly using `/tmp/`
- known private-looking long numeric identifiers in docs examples, unless explicitly inside a schema explanation
- remote-shell examples without placeholder hostnames such as `example-host`
- accidental `.env` or credential-like strings

Do **not** add any real private machine names to the denylist.

**Step 2: Run test**

```bash
PYTHONPATH=.harness/runtime/python pytest .harness/tests/test_public_safety.py -q
```

Expected: PASS after docs are clean.

**Step 3: Integrate with validation if appropriate**

If governance validation already runs pytest subsets, add this test to that path. Otherwise document that maintainers should run it before public releases.

**Step 4: Commit**

```bash
git add .harness/tests/test_public_safety.py scripts/validate-governance
git commit -m "test: guard public integration docs"
```

---

## Task 10: Update generated agent guidance

**Objective:** Teach agents to use the stable import APIs instead of editing template internals.

**Files:**

- Modify: `AGENTS.md`
- Modify: `.harness/brainstorming/AGENTS.brainstorming.md`
- Modify: `.agents/skills/brainstorming-lab/SKILL.md`
- Modify: `.harness/plugins/project-lifecycle-lab/skills/brainstorming-lab/SKILL.md`
- Modify: any mirrored skill/docs files that validation expects to stay synchronized

**Step 1: Add concise guidance**

Add text like:

```markdown
External idea imports must use `./scripts/lab import-idea` or `./scripts/project-harness new-from-idea`. Do not edit `IDEA_CATALOG.md`, `ideas/_*.md`, or `sessions/*.md` directly unless maintaining the harness implementation itself.
```

**Step 2: Sync mirrored skill files**

Use the repo’s existing sync/validation process rather than hand-editing only one mirror.

Likely commands:

```bash
./scripts/sync-plugin-skills
./scripts/validate-governance
```

**Step 3: Commit**

```bash
git add AGENTS.md .harness/brainstorming/AGENTS.brainstorming.md .agents/skills .harness/plugins/project-lifecycle-lab/skills
git commit -m "docs: guide agents to external idea APIs"
```

---

## Task 11: Update downstream integration after template API lands

**Objective:** Replace multi-command external callers with the new single-command template contract.

**Files:**

- This task applies to downstream systems that call the template, not necessarily this public template repository.
- Example downstream change pattern:
  - replace `project-harness new` + `lab capture` + `lab activate` + `lab path-note`
  - with `project-harness new-from-idea ... --payload-file ... --json`

**Step 1: Update downstream caller tests first**

Add tests asserting the caller emits one stable command:

```bash
project-harness new-from-idea <target> --payload-file <payload> --json
```

Do not hardcode private hostnames or paths in tests.

**Step 2: Update caller implementation**

Generate a temp payload file or pipe JSON safely, then call the template command.

**Step 3: Verify with real temporary repo smoke test**

Use only temp paths:

```bash
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
./scripts/project-harness new-from-idea "$tmp/example-project" \
  --idea-id example-web-app \
  --title "Example Web App" \
  --summary "Small web application for demonstration." \
  --source external-system \
  --source-id example-source-id-123 \
  --json
(cd "$tmp/example-project" && ./scripts/lab status --json)
```

**Step 4: Commit downstream changes separately**

Keep template API and downstream usage in separate commits/repositories.

---

## Validation plan

Run these before final merge:

```bash
PYTHONPATH=.harness/runtime/python pytest \
  .harness/tests/test_external_idea_import.py \
  .harness/tests/test_lab_lifecycle.py \
  .harness/tests/test_lab_launcher.py \
  .harness/tests/test_project_harness_bootstrap.py \
  .harness/tests/test_public_safety.py \
  -q
```

Run existing repository validation:

```bash
./scripts/validate-governance
```

Run a real smoke test with temporary paths only:

```bash
set -euo pipefail
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
./scripts/project-harness new-from-idea "$tmp/example-project" \
  --idea-id example-web-app \
  --title "Example Web App" \
  --summary "Small web application for demonstration." \
  --source external-system \
  --source-id example-source-id-123 \
  --activate \
  --commit \
  --json
(cd "$tmp/example-project" && ./scripts/lab status --json)
```

Public-safety check before push:

```bash
git diff --cached
git grep -nE '(/home/[^ /]+|[0-9]{17,}|ssh [^ ]+@[^ ]+|api[_-]?key|token)' -- \
  README.md docs .harness/brainstorming .agents/skills .harness/plugins || true
```

Manually inspect any matches. Generic examples are acceptable only when clearly placeholders.

---

## Risks and tradeoffs

- **Risk:** Adding `--root` and `--template-root` could complicate parser code.
  - **Mitigation:** Keep flags global and preserve existing default cwd behavior.

- **Risk:** JSON output may accidentally include absolute paths.
  - **Mitigation:** Explicit result model with relative `changed_files`; only include target path in a field named `target_path` if necessary.

- **Risk:** Idempotency is hard if existing catalog rows have partial data.
  - **Mitigation:** Use existing upsert/remove-before-add helpers and add duplicate-prevention tests.

- **Risk:** Documentation may include private examples.
  - **Mitigation:** Use only `external-system`, `example-*`, `/tmp/*`, and `/workspace/*` placeholders; add public-safety tests.

- **Risk:** The new command may overlap with existing `capture`/`activate` semantics.
  - **Mitigation:** Keep `import-idea` as a thin orchestration wrapper using existing functions; do not replace existing commands.

---

## Open questions

1. Should `lab import-idea` default to `--activate --create-session`, or should callers opt in explicitly?
   - Recommendation: default to safe, explicit flags first; add shorthand later only if repeated use justifies it.

2. Should `new-from-idea` create one combined initial commit or two commits?
   - Recommendation: preserve existing initial harness commit, then add a second `brainstorm: import external idea <id>` commit for auditability.

3. Should payload JSON support tags immediately?
   - Recommendation: accept and preserve tags in output/provenance if low-cost, but do not force tag rendering into catalog until there is a clear display location.

4. Should source provenance be stored in the generated project?
   - Recommendation: yes, but generically. Consider `.harness/external/imports/<idea-id>.json` with sanitized fields only, or include provenance in the session/path note. Avoid naming any specific private integration in the template.

---

## Definition of done

- `lab import-idea` exists and is documented.
- `project-harness new-from-idea` exists and is documented.
- Both commands support `--json`.
- Both commands support payload-file input.
- Lab commands support explicit `--root`.
- Project-harness commands support explicit `--template-root`.
- New behavior is idempotent and covered by tests.
- Existing `project-harness new`, `lab capture`, and `lab activate` behavior remains backward compatible.
- Public docs/tests contain no personal information, private hostnames, private paths, or machine names.
- `./scripts/validate-governance` passes.
