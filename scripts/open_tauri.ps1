$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$binary=Join-Path $projectRoot 'desktop\src-tauri\target\release\autoclip-desktop.exe'
if (!(Test-Path -LiteralPath $binary)) {$binary=Join-Path $projectRoot 'desktop\src-tauri\target\debug\autoclip-desktop.exe'}
if (!(Test-Path -LiteralPath $binary)) {throw 'Compile a versão desktop antes de abrir: npm --prefix desktop run desktop:build:local'}
$env:AUTOCLIP_WORKSPACE=$projectRoot
Start-Process -FilePath $binary -WorkingDirectory $projectRoot -WindowStyle Normal
