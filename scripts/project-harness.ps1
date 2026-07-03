param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$templateRootArgs = @()
if ($Args.Count -gt 0 -and $Args[0] -eq '--template-root') {
    if ($Args.Count -lt 2 -or [string]::IsNullOrWhiteSpace($Args[1])) {
        [Console]::Error.WriteLine('--template-root requires a path')
        exit 2
    }
    $templateRootArgs = @('--template-root', $Args[1])
    if ($Args.Count -gt 2) {
        $Args = $Args[2..($Args.Count - 1)]
    } else {
        $Args = @()
    }
}

$Command = ''
if ($Args.Count -gt 0) {
    $Command = $Args[0]
}

if (-not $Command -or $Command -eq '-h' -or $Command -eq '--help') {
    @'
Usage: ./scripts/project-harness <command> [args]

Commands:
  new <path> [--origin <url>] [--no-git] [--template-root <path>]
  new-from-idea <path> [--payload-file <json> | --idea-id <id> --title <title>] [--json]
  update --dry-run [--source-path <template-checkout> | --source-commit <sha> | --release-version <version>] [--json]
  update --apply --source-path <template-checkout> --yes [--include-mixed]
  update --apply --source-commit <sha> --yes [--include-mixed]
  update --apply --release-version <version> --yes [--include-mixed]
  validate
'@
    exit 0
}

switch ($Command) {
    # Delegates to project-harness-new.
    'new' { $cliCommand = 'project-harness-new' }
    # Delegates to project-harness-new-from-idea.
    'new-from-idea' { $cliCommand = 'project-harness-new-from-idea' }
    # Delegates to project-harness-validate.
    'validate' { $cliCommand = 'project-harness-validate' }
    # Delegates to project-harness-update.
    'update' { $cliCommand = 'project-harness-update' }
    default {
        [Console]::Error.WriteLine("Unknown project-harness command: $Command")
        exit 2
    }
}

$remaining = @()
if ($Args.Count -gt 1) {
    $remaining = $Args[1..($Args.Count - 1)]
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 "$scriptDir/../.harness/runtime/python/cli.py" $cliCommand @templateRootArgs @remaining
    exit $LASTEXITCODE
}

if (Get-Command python3 -ErrorAction SilentlyContinue) {
    & python3 "$scriptDir/../.harness/runtime/python/cli.py" $cliCommand @templateRootArgs @remaining
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$scriptDir/../.harness/runtime/python/cli.py" $cliCommand @templateRootArgs @remaining
    exit $LASTEXITCODE
}

throw 'Python 3 is required but was not found.'
