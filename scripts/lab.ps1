param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
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
  activate --idea-id <id>
  decide --idea-id <id> --chosen-option "Decision" --rationale "Reason"
  risk --idea-id <id> --statement "Risk"
  review --idea-id <id> --result <result>
  handoff [--idea-id <id>] [--check]
  finalize [--idea-id <id>] [--write-export]
  note --topic "Topic" --summary "Summary"
  audit
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
    & py -3 "$scriptDir/python/cli.py" ("lab-" + $subcommand) @remaining
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$scriptDir/python/cli.py" ("lab-" + $subcommand) @remaining
    exit $LASTEXITCODE
}

throw 'Python 3 is required but was not found.'
