$ErrorActionPreference = "Stop"

if ($args.Count -lt 1) {
    Write-Error "Usage: ./scripts/lab <command> [args]"
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$subcommand = $args[0]
$remaining = @()
if ($args.Count -gt 1) {
    $remaining = $args[1..($args.Count - 1)]
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$scriptDir/python/cli.py" ("lab-" + $subcommand) @remaining
    exit $LASTEXITCODE
}

Write-Error "Python 3 is required but was not found."
exit 1
