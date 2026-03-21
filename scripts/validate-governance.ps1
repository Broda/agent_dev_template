Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$modeLine = Select-String -LiteralPath 'MODE.md' -Pattern '^Current mode:\s*(.+)$' | Select-Object -First 1
if (-not $modeLine) {
    Write-Error 'Could not determine repository mode from MODE.md.'
}

$mode = $modeLine.Matches[0].Groups[1].Value.Trim()

switch ($mode) {
    'brainstorming' {
        & "$PSScriptRoot/validate-brainstorming.sh"
        exit $LASTEXITCODE
    }
    'development' {
        & "$PSScriptRoot/validate-development.sh"
        exit $LASTEXITCODE
    }
    default {
        Write-Error "Unknown mode in MODE.md: $mode"
    }
}
