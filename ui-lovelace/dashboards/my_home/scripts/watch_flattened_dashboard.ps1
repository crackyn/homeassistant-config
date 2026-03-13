<#
.SYNOPSIS
  Watches the flattened dashboard.yaml file and automatically splits it when changed.

.DESCRIPTION
  This script monitors the flattened/dashboard.yaml file for changes and
  automatically runs the split_flattened_dashboard.py script to regenerate
  the individual view and template files.

.USAGE
  pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/watch_flattened_dashboard.ps1
  # Run from the my_home dashboard directory.
  # Press Ctrl+C to stop watching.
#>

[CmdletBinding()]
param(
  [string]$FlattenedPath = "flattened/dashboard.yaml",
  [int]$CheckIntervalSeconds = 2
)

$ErrorActionPreference = 'Stop'

# Resolve paths relative to script location
$scriptDir = Split-Path -Parent $PSCommandPath
$dashboardDir = Split-Path -Parent $scriptDir
$flattenedFullPath = Join-Path $dashboardDir $FlattenedPath
$pythonScript = Join-Path $scriptDir "split_flattened_dashboard.py"

if (-not (Test-Path $flattenedFullPath)) {
  Write-Error "Flattened dashboard not found: $flattenedFullPath"
  exit 1
}

if (-not (Test-Path $pythonScript)) {
  Write-Error "Python split script not found: $pythonScript"
  exit 1
}

Write-Host "Watching: $flattenedFullPath" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop watching..." -ForegroundColor Yellow
Write-Host ""

$lastWrite = (Get-Item $flattenedFullPath).LastWriteTime

while ($true) {
  Start-Sleep -Seconds $CheckIntervalSeconds
  
  $currentWrite = (Get-Item $flattenedFullPath).LastWriteTime
  
  if ($currentWrite -gt $lastWrite) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Change detected!" -ForegroundColor Green
    Write-Host "Running split script..." -ForegroundColor Cyan
    
    try {
      # Run the Python script
      python $pythonScript
      
      if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Split completed successfully!" -ForegroundColor Green
      } else {
        Write-Host "✗ Split failed with exit code: $LASTEXITCODE" -ForegroundColor Red
      }
    }
    catch {
      Write-Host "✗ Error running split script: $_" -ForegroundColor Red
    }
    
    $lastWrite = $currentWrite
    Write-Host ""
  }
}
