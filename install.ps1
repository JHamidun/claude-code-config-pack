# Claude Code config installer (Windows / PowerShell)
param([switch]$Force, [switch]$SkipDeps, [switch]$BackupExisting)
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SrcClaude = Join-Path $Here ".claude"
$SrcClaudeMd = Join-Path $Here "CLAUDE.md"
$SrcEnvTemplate = Join-Path $Here ".credentials.template.env"
$DstClaude = Join-Path $env:USERPROFILE ".claude"
$DstClaudeMd = Join-Path $env:USERPROFILE "CLAUDE.md"
$DstEnv = Join-Path $DstClaude ".credentials.master.env"

if (-not (Test-Path $SrcClaude)) {
    Write-Host "ERROR: $SrcClaude not found." -ForegroundColor Red
    exit 1
}

if ($BackupExisting -and (Test-Path $DstClaude)) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    Move-Item $DstClaude "$DstClaude.backup.$stamp"
    Write-Host "Backed up existing ~/.claude to .backup.$stamp"
}
if (-not (Test-Path $DstClaude)) { New-Item -ItemType Directory -Path $DstClaude | Out-Null }

Write-Host "Copying .claude/* ..."
$excludeNames = @(".credentials.master.env", "MEMORY.md", "chats.db", "chats.db-journal",
                  "chats.db-wal", "chats.db-shm", "tg_session.session")
robocopy $SrcClaude $DstClaude /E /XF $excludeNames | Out-Null

Write-Host "Copying CLAUDE.md ..."
if ((Test-Path $DstClaudeMd) -and -not $Force) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    Copy-Item $DstClaudeMd "$DstClaudeMd.backup.$stamp"
}
Copy-Item $SrcClaudeMd $DstClaudeMd -Force

if (-not (Test-Path $DstEnv)) {
    Copy-Item $SrcEnvTemplate $DstEnv -Force
    Write-Host "Created $DstEnv -- fill in your API keys."
} else {
    Write-Host "$DstEnv already exists -- left alone."
}

if (-not $SkipDeps) {
    $req = Join-Path $Here "requirements.txt"
    if (Test-Path $req) {
        $py = Get-Command python -ErrorAction SilentlyContinue
        if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
        if ($py) {
            try {
                & $py.Path -m pip install --user --upgrade pip 2>$null | Out-Null
                & $py.Path -m pip install --user -r $req
            } catch { Write-Host "Python deps install failed (skipping)" -ForegroundColor Yellow }
        } else { Write-Host "Python not found -- skipping deps." -ForegroundColor Yellow }
    }
}

Write-Host ""
Write-Host "DONE." -ForegroundColor Green
Write-Host "Next: edit $DstEnv  ->  edit $DstClaude\rules\user-profile.md  ->  run 'claude'"
