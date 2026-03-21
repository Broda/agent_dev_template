param(
    [string]$Message = "brainstorm: milestone update",
    [string[]]$Files = @(),
    [switch]$NoPush,
    [switch]$Quiet,
    [switch]$NoWarnPushFailure
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info([string]$msg) { Write-Host $msg }
function Write-WarnLine([string]$msg) { Write-Warning $msg }
function Write-InfoMaybe([string]$msg) { if (-not $Quiet) { Write-Info $msg } }

if ($Files.Count -gt 0) {
    & git add -- $Files
} else {
    & git add -A
}

$staged = (& git diff --cached --name-only)
if (-not $staged) {
    Write-InfoMaybe "No staged changes to commit."
    exit 0
}

& git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Error "Commit failed. Push skipped."
    exit 1
}

$commitSha = (& git rev-parse --short HEAD).Trim()
Write-InfoMaybe ("Committed: " + $commitSha)

if ($NoPush) {
    Write-InfoMaybe "Push skipped due to -NoPush."
    exit 0
}

$branch = (& git symbolic-ref --quiet --short HEAD).Trim()
if (-not $branch) {
    Write-WarnLine "Detached HEAD detected. Commit kept locally; push skipped."
    exit 2
}

$hasOrigin = (& git remote) -contains "origin"
if (-not $hasOrigin) {
    Write-WarnLine "Remote 'origin' not configured. Commit kept locally; push skipped."
    exit 2
}

$dirty = & git status --porcelain
if ($dirty) {
    Write-WarnLine "Working tree is not clean after commit. Push skipped by policy."
    Write-WarnLine "Commit kept locally. Resolve local changes, then push manually."
    exit 2
}

& git push origin $branch
if ($LASTEXITCODE -ne 0) {
    if ($NoWarnPushFailure) {
        # Best-effort autosync mode: keep local commit and continue silently.
        exit 0
    }
    Write-WarnLine ("Push failed for origin/" + $branch + ". Commit " + $commitSha + " is local and safe.")
    Write-WarnLine ("Retry: git push origin " + $branch)
    exit 3
}

Write-InfoMaybe ("Pushed: origin/" + $branch + " @ " + $commitSha)
