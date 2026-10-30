$ErrorActionPreference = 'Stop'
function Get-CreamFileHash {
    param([string]$LiteralPath)
    $stream = [IO.File]::OpenRead($LiteralPath)
    $hash = [Security.Cryptography.SHA256]::Create()
    try { return @{Hash=[BitConverter]::ToString($hash.ComputeHash($stream))} }
    finally { $hash.Dispose(); $stream.Dispose() }
}
function Install-Cream {
    param([string]$SourceRoot, [string]$DocumentsRoot, [string]$LocalDataRoot)
    $source = [IO.Path]::GetFullPath((Join-Path $SourceRoot 'cream'))
    if (-not (Test-Path -LiteralPath (Join-Path $source '__init__.py'))) { throw 'Extract the entire ZIP before running Install.cmd.' }
    if (Get-Process -Name 'Adobe Substance 3D Painter' -ErrorAction SilentlyContinue) { throw 'Save your work and close Substance Painter before installing.' }
    $adobe = [IO.Path]::GetFullPath((Join-Path $DocumentsRoot 'Adobe\Adobe Substance 3D Painter'))
    $plugins = Join-Path $adobe 'python\plugins'
    $target = Join-Path $plugins 'cream'
    $backups = Join-Path $adobe 'cream-backups'
    $data = Join-Path $LocalDataRoot 'CREAM'
    New-Item -ItemType Directory -Path $plugins, $backups, $data -Force | Out-Null
    $previous = @()
    # Recognize CREAM by repository identity, independent of its previous folder name.
    # Read old code as text only. Never execute it or copy its pending updates.
    foreach ($candidate in Get-ChildItem -LiteralPath $plugins -Directory) {
        $versionFile = Join-Path $candidate.FullName 'version.py'
        $isCream = (Test-Path -LiteralPath $versionFile) -and
            ((Get-Content -LiteralPath $versionFile -Raw) -match '(?m)^REPOSITORY\s*=\s*["'']tatauna-doesnt-code/cream["'']') -and
            (Test-Path -LiteralPath (Join-Path $candidate.FullName 'bootstrap.py'))
        if ($candidate.Name -eq 'cream' -and -not $isCream) { throw 'The cream folder exists but is not a recognized CREAM installation. No plugin files were replaced.' }
        if (-not $isCream) { continue }
        if ($candidate.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'The existing installation is a linked folder. Back it up and remove the link before installing.' }
        $previous += $candidate
        $uiFile = Join-Path $candidate.FullName 'ui.py'
        if (-not (Test-Path -LiteralPath $uiFile)) { continue }
        $match = [regex]::Match((Get-Content -LiteralPath $uiFile -Raw), '(?m)^DATA\s*=.* / ["'']([A-Za-z0-9_-]+)["'']\s*$')
        if (-not $match.Success) { continue }
        $oldData = Join-Path $LocalDataRoot $match.Groups[1].Value
        if ($oldData -eq $data -or -not (Test-Path -LiteralPath $oldData)) { continue }
        foreach ($item in Get-ChildItem -LiteralPath $oldData -File) {
            if ($item.Name -ne 'settings.json' -and $item.Name -ne 'cream-github-access.dpapi' -and $item.Name -notlike 'recover-*.json') { continue }
            $destination = Join-Path $data $item.Name
            if (-not (Test-Path -LiteralPath $destination)) { Copy-Item -LiteralPath $item.FullName -Destination $destination }
            elseif ($item.Name -like 'recover-*.json' -and (Get-CreamFileHash -LiteralPath $item.FullName).Hash -ne (Get-CreamFileHash -LiteralPath $destination).Hash) {
                throw 'Conflicting recovery records. Restore the pending preview in the existing CREAM installation before upgrading.'
            }
        }
    }
    $stage = Join-Path $plugins ('.cream-install-' + [guid]::NewGuid().ToString('N'))
    $moves = @()
    try {
        Copy-Item -LiteralPath $source -Destination $stage -Recurse
        foreach ($file in Get-ChildItem -LiteralPath $source -File -Recurse) {
            $relative = $file.FullName.Substring($source.Length).TrimStart('\', '/')
            if ((Get-CreamFileHash -LiteralPath $file.FullName).Hash -ne (Get-CreamFileHash -LiteralPath (Join-Path $stage $relative)).Hash) { throw 'The installation copy failed verification.' }
        }
        $presets = Join-Path $adobe 'assets\export-presets'
        New-Item -ItemType Directory -Path $presets -Force | Out-Null
        $preset = Join-Path $presets 'TM2020.spexp'
        if (-not (Test-Path -LiteralPath $preset)) { Copy-Item -LiteralPath (Join-Path $SourceRoot 'preset\TM2020.spexp') -Destination $preset }
        foreach ($candidate in $previous) {
            $old = [IO.Path]::GetFullPath($candidate.FullName)
            $backup = Join-Path $backups ('cream-' + [guid]::NewGuid().ToString('N'))
            if ([IO.Path]::GetDirectoryName($old) -ne $plugins -or [IO.Path]::GetDirectoryName($backup) -ne $backups) { throw 'Installation paths failed validation.' }
            Move-Item -LiteralPath $old -Destination $backup
            $moves += @{Old=$old; Backup=$backup}
        }
        Move-Item -LiteralPath $stage -Destination $target
    } catch {
        for ($index = $moves.Count - 1; $index -ge 0; $index--) { Move-Item -LiteralPath $moves[$index].Backup -Destination $moves[$index].Old }
        throw
    } finally {
        $resolvedStage = [IO.Path]::GetFullPath($stage)
        if ([IO.Path]::GetDirectoryName($resolvedStage) -eq $plugins -and [IO.Path]::GetFileName($resolvedStage).StartsWith('.cream-install-') -and (Test-Path -LiteralPath $resolvedStage)) {
            Remove-Item -LiteralPath $resolvedStage -Recurse -Force
        }
    }
    Write-Host ('Installed in: ' + $target)
    if ($moves.Count) { Write-Host ('Previous installations backed up to: ' + $backups) }
    Write-Host 'Enable cream in the Python menu, then open Window > CREAM - Skin Exporter.'
    Write-Host 'Settings and any existing TM2020 preset were preserved.'
}
if ($MyInvocation.InvocationName -ne '.') {
    try {
        $documents = [Environment]::GetFolderPath('MyDocuments')
        if (-not $documents) { $documents = Join-Path $env:USERPROFILE 'Documents' }
        Install-Cream -SourceRoot $PSScriptRoot -DocumentsRoot $documents -LocalDataRoot $env:LOCALAPPDATA
    } catch { Write-Host ('Installation failed: ' + $_.Exception.Message) -ForegroundColor Red; exit 1 }
}
