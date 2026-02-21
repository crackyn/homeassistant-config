<#
.SYNOPSIS
  Flattens individual streamline-card template files into the single
  streamline_templates.yaml consumed by the streamline-card frontend.

.DESCRIPTION
  Reads every .yaml file in the streamline-cards template directory,
  uses the filename (without extension) as the top-level key, indents
  the file content by 2 spaces, and writes the combined result to the
  streamline-card www folder.

  This replicates what HA's !include_dir_named does at the Python level,
  but for a frontend-loaded YAML file.

.USAGE
  pwsh -NoProfile -ExecutionPolicy Bypass -File build/flatten_streamline_templates.ps1
  # Run from the homeassistant-config root directory.
#>

[CmdletBinding()]
param(
  [string]$TemplatesDir = "ui-lovelace/templates/streamline-cards",
  [string]$OutFile      = "www/community/streamline-card/streamline_templates.yaml"
)

$ErrorActionPreference = 'Stop'

# Resolve paths relative to script location or current dir
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path (Join-Path $repoRoot $TemplatesDir))) {
  $repoRoot = Get-Location
}

$srcDir  = Join-Path $repoRoot $TemplatesDir
$destFile = Join-Path $repoRoot $OutFile

if (-not (Test-Path $srcDir)) {
  Write-Error "Templates directory not found: $srcDir"
  exit 1
}

# Collect all .yaml files (skip dummy.txt etc.)
$templateFiles = Get-ChildItem -Path $srcDir -Filter '*.yaml' -File | Sort-Object Name

if ($templateFiles.Count -eq 0) {
  Write-Warning "No .yaml files found in $srcDir"
  exit 0
}

$output = [System.Text.StringBuilder]::new()

foreach ($file in $templateFiles) {
  $templateName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
  $content = Get-Content -Path $file.FullName -Raw

  # Remove trailing newlines from content
  $content = $content.TrimEnd("`r", "`n")

  # Add the template name as top-level key
  [void]$output.AppendLine("${templateName}:")

  # Indent each line by 2 spaces
  foreach ($line in ($content -split "`r?`n")) {
    if ($line -match '^\s*$') {
      [void]$output.AppendLine('')
    } else {
      [void]$output.AppendLine("  $line")
    }
  }

  # Blank line between templates
  [void]$output.AppendLine('')
}

# Ensure output directory exists
$outDir = Split-Path -Parent $destFile
if (-not (Test-Path $outDir)) {
  New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

# Write with UTF-8 no BOM
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($destFile, $output.ToString().TrimEnd("`r", "`n") + "`n", $utf8NoBom)

Write-Host "Flattened $($templateFiles.Count) template(s) -> $destFile" -ForegroundColor Green
foreach ($f in $templateFiles) {
  Write-Host "  - $($f.Name)" -ForegroundColor DarkGray
}
