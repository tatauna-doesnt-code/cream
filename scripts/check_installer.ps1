param([string]$SourceRoot, [string]$TestRoot)
$ErrorActionPreference = 'Stop'
. (Join-Path $SourceRoot 'Install.ps1')
function Get-Process { param($Name, $ErrorAction) return $null }
function Assert-True($Condition, $Message) { if (-not $Condition) { throw $Message } }
$documents = Join-Path $TestRoot 'Documents'
$local = Join-Path $TestRoot 'AppData'
$adobe = Join-Path $documents 'Adobe\Adobe Substance 3D Painter'
$plugins = Join-Path $adobe 'python\plugins'
$old = Join-Path $plugins 'previous_exporter'
$unrelated = Join-Path $plugins 'other_plugin'
$oldData = Join-Path $local 'PreviousCreamData'
New-Item -ItemType Directory -Path $old, $unrelated, $oldData -Force | Out-Null
Set-Content -LiteralPath (Join-Path $old 'version.py') -Value 'REPOSITORY = "tatauna-doesnt-code/cream"'
Set-Content -LiteralPath (Join-Path $old 'bootstrap.py') -Value '# Previous loader'
Set-Content -LiteralPath (Join-Path $old 'ui.py') -Value 'DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "PreviousCreamData"'
Set-Content -LiteralPath (Join-Path $unrelated 'keep.txt') -Value 'untouched'
foreach ($name in @('settings.json', 'recover-example.json', 'cream-github-access.dpapi', 'update-old.json')) {
    Set-Content -LiteralPath (Join-Path $oldData $name) -Value 'fixture'
}
$preset = Join-Path $adobe 'assets\export-presets\TM2020.spexp'
New-Item -ItemType Directory -Path (Split-Path $preset) -Force | Out-Null
Set-Content -LiteralPath $preset -Value 'custom preset'
Install-Cream $SourceRoot $documents $local
$target = Join-Path $plugins 'cream'
Assert-True (Test-Path -LiteralPath (Join-Path $target '__init__.py')) 'New package missing'
Assert-True (-not (Test-Path -LiteralPath $old)) 'Old package still discoverable by Painter'
Assert-True (Test-Path -LiteralPath (Join-Path $unrelated 'keep.txt')) 'Unrelated plugin changed'
Assert-True ((Get-Content -LiteralPath $preset -Raw).Trim() -eq 'custom preset') 'Preset replaced'
foreach ($name in @('settings.json', 'recover-example.json', 'cream-github-access.dpapi')) {
    Assert-True (Test-Path -LiteralPath (Join-Path $local ('CREAM\' + $name))) ('State not migrated: ' + $name)
    Assert-True (Test-Path -LiteralPath (Join-Path $oldData $name)) 'Original data removed'
}
Assert-True (-not (Test-Path -LiteralPath (Join-Path $local 'CREAM\update-old.json'))) 'Stale update migrated'
Assert-True (@(Get-ChildItem -LiteralPath (Join-Path $adobe 'cream-backups') -Directory).Count -eq 1) 'Backup missing'
Install-Cream $SourceRoot $documents $local
Assert-True (@(Get-ChildItem -LiteralPath $plugins -Directory).Count -eq 2) 'Reinstallation left duplicate plugins'
# Simulate failure after the old package is moved; verify rollback and stage cleanup.
function Move-Item {
    param($LiteralPath, $Destination)
    if ((Split-Path $LiteralPath -Leaf).StartsWith('.cream-install-')) { throw 'Simulated activation failure' }
    Microsoft.PowerShell.Management\Move-Item -LiteralPath $LiteralPath -Destination $Destination
}
try { Install-Cream $SourceRoot $documents $local; throw 'Expected activation failure' }
catch { Assert-True ($_.Exception.Message -eq 'Simulated activation failure') $_.Exception.Message }
Remove-Item Function:\Move-Item
Assert-True (Test-Path -LiteralPath (Join-Path $target '__init__.py')) 'Rollback lost installed package'
Assert-True (@(Get-ChildItem -LiteralPath $plugins -Directory -Filter '.cream-install-*').Count -eq 0) 'Stage leaked'
# Unrelated content at the target must never be overwritten.
$conflictDocs = Join-Path $TestRoot 'Conflict'
$conflict = Join-Path $conflictDocs 'Adobe\Adobe Substance 3D Painter\python\plugins\cream'
New-Item -ItemType Directory -Path $conflict -Force | Out-Null
Set-Content -LiteralPath (Join-Path $conflict 'keep.txt') -Value 'mine'
try { Install-Cream $SourceRoot $conflictDocs $local; throw 'Expected collision failure' }
catch { Assert-True ($_.Exception.Message -like '*not a recognized CREAM*') $_.Exception.Message }
Assert-True (Test-Path -LiteralPath (Join-Path $conflict 'keep.txt')) 'Collision overwrote unrelated content'
# Fresh installation and running-Painter guard.
$freshDocs = Join-Path $TestRoot 'Fresh'
Install-Cream $SourceRoot $freshDocs $local
function Get-Process { param($Name, $ErrorAction) return @{Id=123} }
try { Install-Cream $SourceRoot $freshDocs $local; throw 'Expected running-Painter guard' }
catch { Assert-True ($_.Exception.Message -like '*close Substance Painter*') $_.Exception.Message }
Write-Host 'Passed: fresh install, migration, state preservation, reinstall, rollback, collision and running-Painter guard.'
