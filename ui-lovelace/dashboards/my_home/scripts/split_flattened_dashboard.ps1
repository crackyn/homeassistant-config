<#
.SYNOPSIS
  Splits the flattened dashboard.yaml back into individual view and template files.

.DESCRIPTION
  Reads the flattened/dashboard.yaml file and extracts:
  - Individual view files to views/ directory
  - Individual button_card_templates to ../../templates/button-cards/ directory

  This allows you to edit the flattened dashboard (e.g., in the UI) and then
  regenerate all the split files.

.PARAMETER DryRun
  Show what would be done without making changes.

.USAGE
  pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/split_flattened_dashboard.ps1
  # Run from the my_home dashboard directory.
#>

[CmdletBinding()]
param(
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $PSCommandPath
$pythonScript = Join-Path $scriptDir "split_flattened_dashboard.py"

if (-not (Test-Path $pythonScript)) {
  Write-Error "Python split script not found: $pythonScript"
  exit 1
}

# Check if Python is available
try {
  $pythonVersion = python --version 2>&1
  Write-Host "Using: $pythonVersion" -ForegroundColor Cyan
}
catch {
  Write-Error "Python is not installed or not in PATH. Please install Python 3.7+ with PyYAML."
  exit 1
}

# Check if PyYAML is installed
$yamlCheck = python -c "import yaml" 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Host "PyYAML is not installed. Installing..." -ForegroundColor Yellow
  python -m pip install pyyaml
  
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install PyYAML. Please run: pip install pyyaml"
    exit 1
  }
}

# Run the Python script
$args = @()
if ($DryRun) {
  $args += '--dry-run'
}

Write-Host "Splitting flattened dashboard..." -ForegroundColor Cyan
Write-Host ""

python $pythonScript @args

if ($LASTEXITCODE -eq 0) {
  Write-Host ""
  Write-Host "✓ Done!" -ForegroundColor Green
} else {
  Write-Host ""
  Write-Host "✗ Failed with exit code: $LASTEXITCODE" -ForegroundColor Red
  exit $LASTEXITCODE
}
