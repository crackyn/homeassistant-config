#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Generate theme viewer cards from theme_scan.json
#>

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH"
    exit 1
}

# Run the Python script
python generate_theme_cards.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Theme cards generated successfully" -ForegroundColor Green
} else {
    Write-Error "Failed to generate theme cards"
    exit 1
}
