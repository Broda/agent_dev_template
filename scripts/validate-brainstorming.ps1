param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 "$scriptDir/../.harness/runtime/python/cli.py" validate-brainstorming @Args
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python "$scriptDir/../.harness/runtime/python/cli.py" validate-brainstorming @Args
    exit $LASTEXITCODE
}

throw 'Python 3 is required but was not found.'
