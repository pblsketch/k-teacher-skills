$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $RepoRoot "skills"
$Target = Join-Path $HOME ".codex\skills"

if (-not (Test-Path $Source)) {
    throw "skills directory not found: $Source"
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null

$installed = @()
Get-ChildItem -Path $Source -Directory | Sort-Object Name | ForEach-Object {
    $destination = Join-Path $Target $_.Name
    Copy-Item -Path $_.FullName -Destination $destination -Recurse -Force
    $installed += $_.Name
}

Write-Host "K-Teacher Skills installed for Codex:"
$installed | ForEach-Object { Write-Host "- $_" }
Write-Host ""
Write-Host "Recommended first prompt:"
Write-Host "k-teacher-workflow-router로 내 요청을 분석하고 적절한 K-Teacher Skills workflow를 시작해줘."
