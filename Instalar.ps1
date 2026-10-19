$ErrorActionPreference = 'Stop'
try {
    $kr7Source = Join-Path $PSScriptRoot 'kr7_batch'
    if (-not (Test-Path -LiteralPath (Join-Path $kr7Source '__init__.py'))) {
        throw 'Extraia o ZIP inteiro antes de executar Instalar.cmd.'
    }
    if (Get-Process -Name 'Adobe Substance 3D Painter' -ErrorAction SilentlyContinue) {
        throw 'Salve seu trabalho e feche o Substance Painter antes de instalar. Depois execute Instalar.cmd novamente.'
    }
    $kr7Adobe = Join-Path $env:USERPROFILE 'Documents\Adobe\Adobe Substance 3D Painter'
    if (-not (Test-Path -LiteralPath $kr7Adobe)) {
        $kr7Adobe = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Adobe\Adobe Substance 3D Painter'
    }
    $kr7Plugins = Join-Path $kr7Adobe 'python\plugins'
    $kr7Target = Join-Path $kr7Plugins 'kr7_batch'
    New-Item -ItemType Directory -Path $kr7Plugins -Force | Out-Null
    if (Test-Path -LiteralPath $kr7Target) {
        $kr7BackupRoot = Join-Path $kr7Adobe 'kr7_plugin_backups'
        New-Item -ItemType Directory -Path $kr7BackupRoot -Force | Out-Null
        $kr7Backup = Join-Path $kr7BackupRoot ('kr7_batch_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
        Copy-Item -LiteralPath $kr7Target -Destination $kr7Backup -Recurse
        Write-Host ('Versao anterior copiada para: ' + $kr7Backup)
    }
    New-Item -ItemType Directory -Path $kr7Target -Force | Out-Null
    Get-ChildItem -LiteralPath $kr7Source -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $kr7Target -Recurse -Force
    }
    $kr7Presets = Join-Path $kr7Adobe 'assets\export-presets'
    New-Item -ItemType Directory -Path $kr7Presets -Force | Out-Null
    $kr7PresetTarget = Join-Path $kr7Presets 'TM2020.spexp'
    if (-not (Test-Path -LiteralPath $kr7PresetTarget)) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'preset\TM2020.spexp') -Destination $kr7PresetTarget
    }
    Write-Host ''
    Write-Host ('Instalado em: ' + $kr7Target)
    Write-Host 'Abra o Painter. No menu Python, ative kr7_batch.'
    Write-Host 'Para reabrir a janela: Window > CREAM - Batch Exporter.'
    Write-Host 'O preset TM2020 existente foi preservado.'
} catch {
    Write-Host ('Nao foi possivel instalar: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
