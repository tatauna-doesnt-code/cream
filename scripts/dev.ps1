param([string]$Python, [string]$Target, [switch]$ReplacePending)
$ErrorActionPreference = 'Stop'
if (-not $Python) {
    $creamProcesses = @(Get-Process -Name 'Adobe Substance 3D Painter' -ErrorAction SilentlyContinue)
    if ($creamProcesses.Count -gt 1) { throw 'Close extra Painter instances, or use python scripts/dev.py --painter-pid with the intended instance.' }
    $creamProcess = $creamProcesses | Select-Object -First 1
    if ($creamProcess -and $creamProcess.Path) {
        $Python = Join-Path (Split-Path -Parent $creamProcess.Path) 'resources\pythonsdk\python.exe'
    }
}
if (-not $Python -or -not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw 'Open Painter first so Dev.cmd can find its bundled Python. Alternatively run python scripts/dev.py with Python 3.10+.'
}
$creamArguments = @('-B', (Join-Path $PSScriptRoot 'dev.py'))
if ($Target) { $creamArguments += @('--target', $Target) }
if ($ReplacePending) { $creamArguments += '--replace-pending' }
& $Python @creamArguments
exit $LASTEXITCODE
