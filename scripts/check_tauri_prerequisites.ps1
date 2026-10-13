$ErrorActionPreference='Continue'
$rustBin=Join-Path $env:USERPROFILE '.cargo\bin'
foreach($tool in @('cargo','rustc')) {
 $found=Get-Command $tool -ErrorAction SilentlyContinue
 if(!$found -and (Test-Path (Join-Path $rustBin "$tool.exe"))){$found=Get-Item (Join-Path $rustBin "$tool.exe")}
 if($found){$toolPath=if($found.Source){$found.Source}else{$found.FullName};& $toolPath --version}else{"${tool}: ausente"}
}
$vswhere='C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
if(Test-Path $vswhere){& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath}else{'MSVC: vswhere ausente'}
Get-ItemProperty 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\*','HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients\*' -ErrorAction SilentlyContinue | Where-Object name -Match WebView | Select-Object name,pv
