$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "install-codex.ps1")
Write-Host ""
& (Join-Path $PSScriptRoot "install-claude.ps1")
Write-Host ""
& (Join-Path $PSScriptRoot "install-antigravity.ps1")
