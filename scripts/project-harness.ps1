param(
    [Parameter(Position = 0)]
    [string]$Command,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $Command -or $Command -eq '-h' -or $Command -eq '--help') {
    @'
Usage: ./scripts/project-harness <command> [args]

Commands:
  new <path> [--origin <url>] [--initial-commit]
'@
    exit 0
}

switch ($Command) {
    # Delegates to project-harness-new.
    'new' { $cliCommand = 'project-harness-new' }
    default {
        Write-Error "Unknown project-harness command: $Command"
        exit 2
    }
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 "$scriptDir/python/cli.py" $cliCommand @Args
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$scriptDir/python/cli.py" $cliCommand @Args
    exit $LASTEXITCODE
}

throw 'Python 3 is required but was not found.'
