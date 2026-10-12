param([string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot))
$resolvedProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$launcherPath = Join-Path $resolvedProjectRoot 'Abrir AutoClip.vbs'
if (-not (Test-Path -LiteralPath $launcherPath)) { throw 'Launcher AutoClip não encontrado.' }
$shortcutShell = New-Object -ComObject WScript.Shell
$shortcut = $shortcutShell.CreateShortcut((Join-Path $resolvedProjectRoot 'AutoClip.lnk'))
$shortcut.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
$shortcut.Arguments = '"' + $launcherPath + '"'
$shortcut.WorkingDirectory = $resolvedProjectRoot
$shortcut.Description = 'Abrir a biblioteca local de projetos AutoClip'
$shortcut.IconLocation = (Join-Path $resolvedProjectRoot 'desktop\public\autoclip.ico')
$shortcut.Save()
