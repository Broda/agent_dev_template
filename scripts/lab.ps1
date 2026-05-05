param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($Args.Count -lt 1) {
    throw 'Usage: ./scripts/lab <command> [args]'
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$subcommand = $Args[0]
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
