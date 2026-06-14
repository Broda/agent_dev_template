# External Integration

This template exposes stable commands for automation that wants to seed brainstorming projects from an external idea source.

Use these commands instead of editing `IDEA_CATALOG.md`, `ideas/_*.md`, or `sessions/*.md` directly. The template owns its internal idea, catalog, bucket, and session layout.

## Public examples only

This repository is public. Documentation, tests, and fixtures must use placeholders such as:

- `external-system`
- `example-source-id-123`
- `/tmp/example-template`
- `/tmp/example-project`
- `idea-example-web-app`

Do not commit personal machine names, private hostnames, private repository names, account IDs, private network names, credentials, tokens, or user-specific absolute paths.

## Import an idea into an existing brainstorming repo

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

The command normalizes the idea ID to `idea-example-web-app`, updates the catalog and bucket files, optionally creates a session, and returns JSON when `--json` is supplied.

## Prefer payload files for automation

Payload files avoid shell-quoting bugs:

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

`tags` is accepted for forward compatibility and validated as a list of strings. The current template does not persist tags in catalog or session files; callers should treat tags as reserved metadata until a future schema version defines durable tag behavior.

Use the payload with:

```bash
./scripts/lab import-idea \
  --payload-file /tmp/example-idea.json \
  --activate \
  --create-session \
  --json \
  --no-sync
```

## Create a new project from an external idea

```bash
./scripts/project-harness new-from-idea /tmp/example-project \
  --payload-file /tmp/example-idea.json \
  --activate \
  --commit \
  --json
```

This command creates a new brainstorming-mode project, imports and activates the idea, creates a session, validates governance, initializes Git unless `--no-git` is supplied, and returns a JSON summary. `new-from-idea` always activates the imported idea because a newly created project is expected to start with one active brainstorming thread; the `--activate` flag remains accepted for compatibility with older automation.

## Explicit roots for automation

Automation can avoid current-working-directory assumptions:

```bash
./scripts/lab --root /tmp/example-project status --json
```

```bash
./scripts/project-harness --template-root /tmp/example-template new-from-idea /tmp/example-project \
  --payload-file /tmp/example-idea.json \
  --json
```

## JSON result shape

Typical `lab import-idea --json` output:

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
    "ideas/_active.md",
    "IDEA_CATALOG.md",
    "sessions/2026-06-14_idea-example-web-app.md"
  ],
  "readiness": "needs-input"
}
```

`project-harness new-from-idea --json` also includes `target_created`, `target_path`, and `commit` when available.

## JSON failure shape

When validation fails before any template files are written, commands that receive `--json` return a stable machine-readable error object on stdout and exit `1`:

```json
{
  "ok": false,
  "code": "unsupported_schema",
  "error": "unsupported external idea payload schema_version"
}
```

Current error codes include:

- `payload_file_not_found`
- `invalid_json`
- `unsupported_schema`
- `invalid_tags`
- `missing_required_field`
- `invalid_field`
- `invalid_payload`
- `external_idea_error`

For non-JSON mode, the same validation failures are printed as concise stderr messages. Payload validation happens before repository creation in `project-harness new-from-idea`, so invalid payloads do not leave partially created target directories. Later runtime, Git, or validation failures may occur after file writes; callers should inspect the exit code and retry idempotently with the same payload after fixing the environment.

## Idempotency

`lab import-idea` is designed to be retry-safe:

- it normalizes the idea ID;
- it removes stale bucket entries before writing the current bucket entry;
- it upserts the catalog row;
- it reuses the template session machinery;
- it returns relative changed-file paths.

## Exit codes

- `0`: success
- `1`: runtime, validation, or Git failure
- `2`: usage, mode, or registry error

## Do not rely on internals

External callers should not:

- edit `IDEA_CATALOG.md` directly;
- edit `ideas/_inbox.md`, `ideas/_active.md`, `ideas/_parked.md`, or `ideas/_killed.md` directly;
- create files in `sessions/` directly;
- assume exact session filenames beyond the returned `session_path`;
- include private environment details in payloads or docs.
