param(
	[Parameter(Mandatory = $false)]
	[string]$DashboardYamlPath,

	[Parameter(Mandatory = $false)]
	[string]$ViewsDir,

	[Parameter(Mandatory = $false)]
	[string]$OutputDir,

	[Parameter(Mandatory = $false)]
	[string]$OutputFileName = 'dashboard.yaml'
)

$ErrorActionPreference = 'Stop'

if (-not $DashboardYamlPath) {
	$DashboardYamlPath = Join-Path $PSScriptRoot '..\dashboard.yaml'
}

if (-not $ViewsDir) {
	$ViewsDir = Join-Path $PSScriptRoot '..\views'
}

if (-not $OutputDir) {
	$OutputDir = Join-Path $PSScriptRoot '..\flattened'
}

function Get-Utf8NoBomEncoding {
	# PowerShell's Set-Content encoding defaults vary by version.
	return New-Object System.Text.UTF8Encoding($false)
}

function Normalize-Lines {
	param(
		[Parameter(Mandatory = $true)]
		[string]$Text
	)

	# Normalize newlines and strip any leading UTF-8 BOM.
	if ($Text.Length -gt 0 -and [int]$Text[0] -eq 0xFEFF) {
		$Text = $Text.Substring(1)
	}

	$Text = $Text -replace "`r`n", "`n"
	$Text = $Text -replace "`r", "`n"
	return $Text.Split("`n")
}

function Remove-CommentsAndDocMarkers {
	param(
		[Parameter(Mandatory = $false)]
		[string[]]$Lines
	)

	if (-not $Lines) {
		return @()
	}

	$out = @()
	foreach ($line in $Lines) {
		$trim = $line.Trim()

		if ($trim -eq '') {
			$out += ''
			continue
		}

		if ($trim.StartsWith('#')) {
			continue
		}

		if ($trim -eq '---' -or $trim -eq '...') {
			continue
		}

		$out += $line
	}

	# Trim leading/trailing blank lines (after comment removal)
	$start = 0
	while ($start -lt $out.Count -and $out[$start].Trim() -eq '') { $start++ }
	$end = $out.Count - 1
	while ($end -ge $start -and $out[$end].Trim() -eq '') { $end-- }

	if ($end -lt $start) {
		return @()
	}

	return @($out[$start..$end])
}

function Get-CommonLeadingSpaceCount {
	param(
		[Parameter(Mandatory = $false)]
		[string[]]$Lines
	)

	if (-not $Lines) {
		return 0
	}

	$min = $null

	foreach ($line in $Lines) {
		$withoutTrailing = $line.TrimEnd()
		if ($withoutTrailing -eq '') {
			continue
		}

		# If a line starts with a tab, don't attempt to normalize indentation.
		if ($withoutTrailing.StartsWith("`t")) {
			return 0
		}

		$match = [regex]::Match($withoutTrailing, '^( +)')
		$spaces = if ($match.Success) { $match.Groups[1].Value.Length } else { 0 }

		if ($null -eq $min -or $spaces -lt $min) {
			$min = $spaces
		}
	}

	if ($null -eq $min) {
		return 0
	}

	return $min
}

if (-not (Test-Path -LiteralPath $DashboardYamlPath)) {
	throw "Dashboard YAML not found: $DashboardYamlPath"
}

if (-not (Test-Path -LiteralPath $ViewsDir)) {
	throw "Views directory not found: $ViewsDir"
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$outputPath = Join-Path $OutputDir $OutputFileName

# Read dashboard.yaml and replace include directives with flattened content.
$dashboardLines = @(Get-Content -LiteralPath $DashboardYamlPath)

function Find-TopLevelKeyIndex {
	param(
		[Parameter(Mandatory = $false)]
		[string[]]$Lines,
		[Parameter(Mandatory = $true)]
		[string]$KeyName
	)

	if (-not $Lines) {
		return -1
	}

	for ($i = 0; $i -lt $Lines.Count; $i++) {
		if ($Lines[$i] -match ("^\s*" + [regex]::Escape($KeyName) + "\s*:")) {
			return $i
		}
	}
	return -1
}

function Find-TopLevelBlockEndIndex {
	param(
		[Parameter(Mandatory = $false)]
		[string[]]$Lines,
		[Parameter(Mandatory = $true)]
		[int]$StartIndex
	)

	if (-not $Lines) {
		return -1
	}

	if ($StartIndex -lt 0) { return -1 }

	for ($i = $StartIndex + 1; $i -lt $Lines.Count; $i++) {
		$line = $Lines[$i]
		if ($line -match '^\S' -and $line -match '^[^#].*:\s*') {
			return ($i - 1)
		}
	}

	return ($Lines.Count - 1)
}

$buttonStart = Find-TopLevelKeyIndex -Lines $dashboardLines -KeyName 'button_card_templates'
$viewsStart = Find-TopLevelKeyIndex -Lines $dashboardLines -KeyName 'views'

if ($viewsStart -lt 0) {
	throw "Could not find a 'views:' line in $DashboardYamlPath"
}

$buttonEnd = if ($buttonStart -ge 0) { Find-TopLevelBlockEndIndex -Lines $dashboardLines -StartIndex $buttonStart } else { -1 }
$viewsEnd = Find-TopLevelBlockEndIndex -Lines $dashboardLines -StartIndex $viewsStart

function Get-IncludeDirNamedPathFromBlock {
	param(
		[Parameter(Mandatory = $false)]
		[string[]]$Lines,
		[Parameter(Mandatory = $true)]
		[int]$StartIndex,
		[Parameter(Mandatory = $true)]
		[int]$EndIndex
	)

	if (-not $Lines) {
		return $null
	}

	for ($i = $StartIndex; $i -le $EndIndex; $i++) {
		$line = $Lines[$i]
		$match = [regex]::Match($line, '!include_dir_named\s+(.+?)\s*$')
		if ($match.Success) {
			return $match.Groups[1].Value.Trim().Trim('"').Trim("'")
		}
	}

	return $null
}

$prefixLines = @()

if ($buttonStart -ge 0 -and $buttonStart -lt $viewsStart) {
	if ($buttonStart -gt 0) {
		$prefixLines += @($dashboardLines[0..($buttonStart - 1)] | ForEach-Object { $_.TrimEnd() })
	}
} else {
	if ($viewsStart -gt 0) {
		$prefixLines += @($dashboardLines[0..($viewsStart - 1)] | ForEach-Object { $_.TrimEnd() })
	}
}

$betweenLines = @()
if ($buttonStart -ge 0 -and $buttonEnd -ge 0 -and $buttonEnd -lt $viewsStart) {
	if (($buttonEnd + 1) -le ($viewsStart - 1)) {
		$betweenLines += @($dashboardLines[($buttonEnd + 1)..($viewsStart - 1)] | ForEach-Object { $_.TrimEnd() })
	}
}

$postLines = @()
if ($viewsEnd -lt ($dashboardLines.Count - 1)) {
	$postLines += @($dashboardLines[($viewsEnd + 1)..($dashboardLines.Count - 1)] | ForEach-Object { $_.TrimEnd() })
}

# Collect view YAML files, sorted by filename.
$viewFiles = Get-ChildItem -LiteralPath $ViewsDir -File -Filter '*.yaml' | Sort-Object Name
if (-not $viewFiles) {
	throw "No view YAML files found in $ViewsDir"
}

$sb = New-Object System.Text.StringBuilder

foreach ($line in $prefixLines) {
	[void]$sb.AppendLine($line)
}

if ($buttonStart -ge 0) {
	$includeRel = Get-IncludeDirNamedPathFromBlock -Lines $dashboardLines -StartIndex $buttonStart -EndIndex $buttonEnd
	if (-not $includeRel) {
		throw "Could not find '!include_dir_named ...' under button_card_templates in $DashboardYamlPath"
	}

	$dashboardDir = Split-Path -Parent $DashboardYamlPath
	$templatesDir = Join-Path $dashboardDir $includeRel
	$templatesDir = (Resolve-Path -LiteralPath $templatesDir).Path

	if (-not (Test-Path -LiteralPath $templatesDir)) {
		throw "button_card_templates directory not found: $templatesDir"
	}

	[void]$sb.AppendLine('button_card_templates:')

	$templateFiles = Get-ChildItem -LiteralPath $templatesDir -File | Where-Object { $_.Extension -in @('.yaml', '.yml') } | Sort-Object Name
	foreach ($tf in $templateFiles) {
		$key = $tf.BaseName
		$rawT = Get-Content -LiteralPath $tf.FullName -Raw
		$tLines = @(Normalize-Lines -Text $rawT)
		$tLines = @(Remove-CommentsAndDocMarkers -Lines $tLines)

		if (-not $tLines -or $tLines.Count -eq 0) {
			[void]$sb.AppendLine(('  ' + $key + ':'))
			[void]$sb.AppendLine('    {}')
			continue
		}

		# If the file already defines a top-level key matching the filename,
		# unwrap it so button_card_templates is truly flat.
		$firstNonEmptyIndex = -1
		for ($i = 0; $i -lt $tLines.Count; $i++) {
			if ($tLines[$i].Trim() -ne '') {
				$firstNonEmptyIndex = $i
				break
			}
		}

		$templateKey = $key
		$contentLines = $tLines
		if ($firstNonEmptyIndex -ge 0) {
			$m = [regex]::Match($tLines[$firstNonEmptyIndex], '^([A-Za-z0-9_\-]+)\s*:\s*$')
			if ($m.Success) {
				$candidate = $m.Groups[1].Value
				if ($candidate.Equals($key, [System.StringComparison]::OrdinalIgnoreCase)) {
					$templateKey = $candidate
					$contentLines = @()
					if (($firstNonEmptyIndex + 1) -le ($tLines.Count - 1)) {
						$contentLines = @($tLines[($firstNonEmptyIndex + 1)..($tLines.Count - 1)])
					}
				}
			}
		}

		$commonTIndent = Get-CommonLeadingSpaceCount -Lines $contentLines

		[void]$sb.AppendLine(('  ' + $templateKey + ':'))
		if (-not $contentLines -or $contentLines.Count -eq 0) {
			[void]$sb.AppendLine('    {}')
			continue
		}

		foreach ($tl in $contentLines) {
			$normalizedT = $tl
			if ($commonTIndent -gt 0 -and $normalizedT.Length -ge $commonTIndent) {
				if ($normalizedT.Substring(0, $commonTIndent) -match '^[ ]+$') {
					$normalizedT = $normalizedT.Substring($commonTIndent)
				}
			}

			$trimmedT = $normalizedT.TrimEnd()
			if ($trimmedT -eq '') {
				[void]$sb.AppendLine('')
				continue
			}

			[void]$sb.AppendLine(('    ' + $trimmedT))
		}
	}

	foreach ($line in $betweenLines) {
		if ($line -ne '') {
			[void]$sb.AppendLine($line)
		} else {
			[void]$sb.AppendLine('')
		}
	}
} else {
	foreach ($line in $betweenLines) {
		[void]$sb.AppendLine($line)
	}
}

[void]$sb.AppendLine('views:')

foreach ($vf in $viewFiles) {
	$raw = Get-Content -LiteralPath $vf.FullName -Raw
	$lines = @(Normalize-Lines -Text $raw)
	$lines = @(Remove-CommentsAndDocMarkers -Lines $lines)
	$commonIndent = Get-CommonLeadingSpaceCount -Lines $lines

	# First pass: remove common indent from all lines.
	$normalizedLines = @()
	foreach ($l in $lines) {
		$normalized = $l
		if ($commonIndent -gt 0 -and $normalized.Length -ge $commonIndent) {
			if ($normalized.Substring(0, $commonIndent) -match '^[ ]+$') {
				$normalized = $normalized.Substring($commonIndent)
			}
		}
		$normalizedLines += $normalized
	}

	# Some view files may already include a leading list item dash (e.g. "- title: ...").
	# Unwrap that so the flattened views list contains mappings, not nested lists.
	$firstNonEmpty = -1
	for ($i = 0; $i -lt $normalizedLines.Count; $i++) {
		if ($normalizedLines[$i].TrimEnd() -ne '') {
			$firstNonEmpty = $i
			break
		}
	}

	if ($firstNonEmpty -ge 0 -and $normalizedLines[$firstNonEmpty] -match '^\s*-\s+') {
		$normalizedLines[$firstNonEmpty] = ($normalizedLines[$firstNonEmpty] -replace '^\s*-\s+', '')
		for ($j = $firstNonEmpty + 1; $j -lt $normalizedLines.Count; $j++) {
			if ($normalizedLines[$j].StartsWith('  ')) {
				$normalizedLines[$j] = $normalizedLines[$j].Substring(2)
			}
		}
	}

	# Start a new list item and indent the entire file underneath it.
	[void]$sb.AppendLine('  -')

	foreach ($l in $normalizedLines) {
		$trimmed = $l.TrimEnd()

		if ($trimmed -eq '') {
			[void]$sb.AppendLine('')
			continue
		}

		[void]$sb.AppendLine(('    ' + $trimmed))
	}
}

foreach ($line in $postLines) {
	[void]$sb.AppendLine($line)
}

# Ensure trailing newline.
$outText = $sb.ToString()
if (-not $outText.EndsWith("`n")) {
	$outText += "`n"
}

[System.IO.File]::WriteAllText($outputPath, $outText, (Get-Utf8NoBomEncoding))

Write-Host "Wrote flattened dashboard: $outputPath"
Write-Host "Views included (sorted): $($viewFiles.Count)"

