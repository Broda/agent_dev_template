param(
    [Parameter(Mandatory = $true)]
    [string]$Topic,
    [string]$Source = 'recent assistant research context',
    [string]$IdeaId,
    [string]$Tags,
    [string[]]$Summary = @(),
    [switch]$NoSync
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$mode = 'brainstorming'
if (Test-Path -LiteralPath 'MODE.md') {
    $modeLine = Select-String -LiteralPath 'MODE.md' -Pattern '^Current mode:\s*(.+)$' | Select-Object -First 1
    if ($modeLine) {
        $mode = $modeLine.Matches[0].Groups[1].Value.Trim()
    }
}

function To-Kebab([string]$value) {
    $k = $value.ToLowerInvariant() -replace '[^a-z0-9]+','-'
    $k = $k -replace '^-+','' -replace '-+$','' -replace '-+','-'
    if ([string]::IsNullOrWhiteSpace($k)) { return 'note' }
    return $k
}

if (-not (Test-Path -LiteralPath 'NOTES_CATALOG.md')) {
    throw 'NOTES_CATALOG.md not found.'
}

New-Item -ItemType Directory -Path 'notes' -Force | Out-Null

$max = 0
Get-Content -LiteralPath 'NOTES_CATALOG.md' |
    Where-Object { $_ -match '^\|\s*note-[0-9]{4}\s*\|' } |
    ForEach-Object {
        if ($_ -match '^\|\s*note-([0-9]{4})\s*\|') {
            $n = [int]$Matches[1]
            if ($n -gt $max) { $max = $n }
        }
    }

$next = $max + 1
$idNum = '{0:D4}' -f $next
$noteId = "note-$idNum"
$dateStamp = Get-Date -Format 'yyyy-MM-dd'
$slug = To-Kebab $Topic
$notePath = "notes/${dateStamp}_${noteId}-${slug}.md"
$ideaVal = if ($IdeaId) { $IdeaId } else { 'n/a' }
$tagsVal = if ($Tags) { $Tags } else { 'n/a' }

$lines = @()
$lines += '# Research Note'
$lines += ''
$lines += '## Metadata'
$lines += ''
$lines += "- Note ID: $noteId"
$lines += "- Title: $Topic"
$lines += "- Date: $dateStamp"
$lines += "- Related Idea ID: $ideaVal"
$lines += "- Source Context: $Source"
$lines += "- Tags: $tagsVal"
$lines += ''
$lines += '## Captured Information'
$lines += ''
if ($Summary.Count -gt 0) {
    foreach ($item in $Summary) { $lines += "- $item" }
} else {
    $lines += '- Summary pending: fill in captured research details.'
}
$lines += ''
$lines += '## Key Facts / Constraints'
$lines += ''
$lines += '- '
$lines += ''
$lines += '## Open Questions / Follow-ups'
$lines += ''
$lines += '- '
$lines += ''
$lines += '## Links'
$lines += ''
$lines += '- '

Set-Content -LiteralPath $notePath -Value $lines

$row = "| $noteId | $Topic | $dateStamp | $ideaVal | $Source | `$notePath` | $tagsVal |"
Add-Content -LiteralPath 'NOTES_CATALOG.md' -Value $row

if (-not $NoSync) {
    & ./scripts/lab-sync -Quiet -NoWarnPushFailure -Message "$mode: note $noteId" -Files @($notePath, 'NOTES_CATALOG.md')
}

if (-not $NoSync) {
    Write-Host "Note saved and persisted: $notePath"
} else {
    Write-Host "Note saved (sync skipped): $notePath"
}
