param(
    [switch]$VerboseOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Add-Failure([string]$msg) { $script:failures.Add($msg) }
function Add-Warning([string]$msg) { $script:warnings.Add($msg) }
function Test-PathSafe([string]$path) {
    if ([string]::IsNullOrWhiteSpace($path)) { return $false }
    return Test-Path -LiteralPath $path
}

$coreArtifacts = @(
    'README.md',
    'AGENTS.md',
    'CONVERSATIONAL_MODE.md',
    'COMMANDS.md',
    'QUICKSTART.md',
    'FILE_MAP.md',
    'IDEA_CATALOG.md',
    'NOTES_CATALOG.md',
    'ideas/_inbox.md',
    'ideas/_active.md',
    'ideas/_parked.md',
    'ideas/_killed.md',
    'notes',
    'templates/idea_template.md',
    'templates/decision_template.md',
    'templates/note_template.md',
    'templates/project_plan_packet_template.md',
    'templates/risk_template.md',
    'templates/review_gate_template.md',
    'docs/adr/template.md',
    'docs/adr/ADR-0001-adopt-governance-structure-for-idea-lab.md',
    'scripts/validate-governance',
    'scripts/lab-sync',
    'scripts/handoff-init',
    'scripts/validate-governance.ps1',
    'scripts/lab-sync.ps1',
    'scripts/lab-note.ps1',
    'scripts/handoff-init.ps1',
    'scripts/validate-governance.sh',
    'scripts/lab-sync.sh',
    'scripts/lab-note.sh',
    'scripts/handoff-init.sh',
    'scripts/lab-note',
    '.github/workflows/governance-audit.yml',
    '.github/PULL_REQUEST_TEMPLATE.md'
)

foreach ($artifact in $coreArtifacts) {
    if (-not (Test-PathSafe $artifact)) {
        Add-Failure("Missing required artifact: $artifact")
    }
}

$markdownFiles = Get-ChildItem -Recurse -File -Filter *.md | Where-Object { $_.FullName -notmatch '\\.git\\' -and $_.FullName -notmatch '\\external\\' }
$adrRegex = [regex]'docs/adr/ADR-[0-9]{4}-[a-z0-9-]+\.md'
foreach ($file in $markdownFiles) {
    $content = Get-Content -Raw -LiteralPath $file.FullName
    foreach ($m in $adrRegex.Matches($content)) {
        $relative = $m.Value.Replace('/', '\\')
        if (-not (Test-PathSafe $relative)) {
            Add-Failure("Missing ADR link target: '$relative' referenced in '$($file.FullName)'.")
        }
    }
}

$catalogPath = 'IDEA_CATALOG.md'
if (-not (Test-PathSafe $catalogPath)) {
    Add-Failure('Missing IDEA_CATALOG.md')
} else {
    $catalog = Get-Content -Raw -LiteralPath $catalogPath
    $rows = $catalog -split "`n" | Where-Object { $_ -match '^\|\s*idea-[a-z0-9-]+' }

    foreach ($row in $rows) {
        $cols = $row.Split('|') | ForEach-Object { $_.Trim() }
        if ($cols.Count -lt 8) {
            Add-Failure("Malformed catalog row: $row")
            continue
        }

        $ideaId = $cols[1]
        $status = $cols[3]
        $sessions = $cols[5]
        $export = $cols[6]

        switch ($status) {
            'inbox'   { $stateFile = 'ideas/_inbox.md' }
            'active'  { $stateFile = 'ideas/_active.md' }
            'parked'  { $stateFile = 'ideas/_parked.md' }
            'killed'  { $stateFile = 'ideas/_killed.md' }
            'exported'{ $stateFile = 'ideas/_active.md' }
            default {
                Add-Failure("Unknown status '$status' for '$ideaId'.")
                continue
            }
        }

        if (-not (Test-PathSafe $stateFile)) {
            Add-Failure("Required state file '$stateFile' missing for status '$status'.")
        }

        if ($status -eq 'active' -and $sessions -match '_none_|_none yet_|n/a') {
            Add-Warning("Active idea '$ideaId' has no session link yet.")
        }

        if ($status -eq 'exported') {
            if ($export -match '_n/a_|_none_|_none yet_' -or [string]::IsNullOrWhiteSpace($export)) {
                Add-Failure("Exported idea '$ideaId' must include export file path.")
            } else {
                $exportPath = $export.Trim('`', ' ')
                $exportPath = $exportPath.Replace('/', '\\')
                if (-not (Test-PathSafe $exportPath)) {
                    Add-Failure("Catalog export path missing for '$ideaId': $exportPath")
                }
            }
        }
    }
}

$notesCatalogPath = 'NOTES_CATALOG.md'
if (-not (Test-PathSafe $notesCatalogPath)) {
    Add-Failure('Missing NOTES_CATALOG.md')
} else {
    $notesCatalog = Get-Content -Raw -LiteralPath $notesCatalogPath
    $rows = $notesCatalog -split "`n" | Where-Object { $_ -match '^\|\s*note-[0-9]{4}\s*\|' }
    $seenNoteIds = New-Object System.Collections.Generic.HashSet[string]

    foreach ($row in $rows) {
        $cols = $row.Split('|') | ForEach-Object { $_.Trim() }
        if ($cols.Count -lt 8) {
            Add-Failure("Malformed note catalog row: $row")
            continue
        }

        $noteId = $cols[1]
        $noteDate = $cols[3]
        $notePath = $cols[6]

        if ($noteId -notmatch '^note-[0-9]{4}$') {
            Add-Failure("Invalid note id format in NOTES_CATALOG.md: $noteId")
            continue
        }

        if (-not $seenNoteIds.Add($noteId)) {
            Add-Failure("Duplicate note id in NOTES_CATALOG.md: $noteId")
        }

        if ($noteDate -notmatch '^[0-9]{4}-[0-9]{2}-[0-9]{2}$') {
            Add-Failure("Invalid note date format for '$noteId': $noteDate")
        }

        $cleanNotePath = $notePath.Trim('`', ' ')
        if ($cleanNotePath -notmatch '^notes[\\/].+') {
            Add-Failure("Note path for '$noteId' must be under notes/: $cleanNotePath")
        } else {
            $normalized = $cleanNotePath.Replace('/', '\')
            if (-not (Test-PathSafe $normalized)) {
                Add-Failure("Missing note file for '$noteId': $normalized")
            }
        }
    }
}

$fileMapPath = 'FILE_MAP.md'
if (Test-PathSafe $fileMapPath) {
    $fm = Get-Content -Raw -LiteralPath $fileMapPath
    foreach ($artifact in $coreArtifacts) {
        $token = '`' + $artifact + '`'
        if ($fm -notmatch [regex]::Escape($token)) {
            Add-Warning("FILE_MAP.md missing registry row for: $artifact")
        }
    }
}

Write-Host 'Lean validation summary'
Write-Host "- Failures: $($failures.Count)"
Write-Host "- Warnings: $($warnings.Count)"

if ($warnings.Count -gt 0) {
    Write-Host "`nWarnings:"
    $warnings | ForEach-Object { Write-Host "- $_" }
}

if ($failures.Count -gt 0) {
    Write-Host "`nFailures:"
    $failures | ForEach-Object { Write-Host "- $_" }
    exit 1
}

Write-Host "`nPASS: lean integrity checks completed with no blocking failures."

