param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$rootArgs = @()
if ($Args.Count -gt 0 -and $Args[0] -eq '--root') {
    if ($Args.Count -lt 2 -or [string]::IsNullOrWhiteSpace($Args[1])) {
        [Console]::Error.WriteLine('--root requires a path')
        exit 2
    }
    $rootArgs = @('--root', $Args[1])
    if ($Args.Count -gt 2) {
        $Args = $Args[2..($Args.Count - 1)]
    } else {
        $Args = @()
    }
}

$subcommand = ''
if ($Args.Count -gt 0) {
    $subcommand = $Args[0]
}

if (-not $subcommand -or $subcommand -eq '-h' -or $subcommand -eq '--help' -or $subcommand -eq 'help') {
    @'
Usage: ./scripts/lab <command> [args]

Commands:
  status
  doctor [--idea-id <id>]
  capture --idea-id <id> --title "Title"
  import-idea (--payload-file <json> | --idea-id <id> --title "Title")
  activate --idea-id <id>
  decide --idea-id <id> --chosen-option "Decision" --rationale "Reason"
  risk --idea-id <id> --statement "Risk"
  path-note --idea-id <id> --title "Title"
  note --topic "Topic" --summary "Summary"
  review --idea-id <id> --result <result>
  export --idea-id <id>
  handoff [--idea-id <id>] [--check]
  finalize [--idea-id <id>] [--write-export]
  park --idea-id <id> [--reason "Reason"]
  kill --idea-id <id> [--reason "Reason"]
  audit
  evidence --task <task> --command "Command" --result <result>
  adr --title "Title" --decision "Decision"
  wiki-render
  wiki-check
  commit [--message "Message"]
  push
  sync [args]

Run ./scripts/lab <command> --help for command-specific options.
'@
    exit 0
}

$remaining = @()
if ($Args.Count -gt 1) {
    $remaining = $Args[1..($Args.Count - 1)]
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 "$scriptDir/../.harness/runtime/python/cli.py" ("lab-" + $subcommand) @rootArgs @remaining
    exit $LASTEXITCODE
}

if (Get-Command python3 -ErrorAction SilentlyContinue) {
    & python3 "$scriptDir/../.harness/runtime/python/cli.py" ("lab-" + $subcommand) @rootArgs @remaining
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$scriptDir/../.harness/runtime/python/cli.py" ("lab-" + $subcommand) @rootArgs @remaining
    exit $LASTEXITCODE
}

throw 'Python 3 is required but was not found.'
