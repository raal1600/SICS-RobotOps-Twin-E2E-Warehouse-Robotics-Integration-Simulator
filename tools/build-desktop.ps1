param([switch]$Install, [switch]$RestoreDependencies)
$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$output = Join-Path $repository 'artifacts\desktop\RobotOps Twin'
$dependencyRoot = Join-Path $repository 'artifacts\desktop\dependencies'
$archive = Join-Path $dependencyRoot 'webview2-1.0.3800.47.zip'
$sdk = Join-Path $dependencyRoot 'webview2-1.0.3800.47'
$expectedHash = '56C9F26BDD07916A2D1949FB58A5C7E434DFA1173577DCA879206050C4E718DB'
$python = Join-Path $repository '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run uv sync --locked --all-groups first.' }
New-Item -ItemType Directory -Path $output,$dependencyRoot -Force | Out-Null
if ($RestoreDependencies -or -not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri 'https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/1.0.3800.47/microsoft.web.webview2.1.0.3800.47.nupkg' -OutFile $archive
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expectedHash) { throw 'WebView2 SDK checksum mismatch.' }
Expand-Archive -LiteralPath $archive -DestinationPath $sdk -Force
foreach ($name in @('Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll')) {
    Copy-Item -LiteralPath (Join-Path $sdk ('lib\net462\'+$name)) -Destination (Join-Path $output $name) -Force
}
Copy-Item -LiteralPath (Join-Path $sdk 'runtimes\win-x64\native\WebView2Loader.dll') -Destination $output -Force
Copy-Item -LiteralPath (Join-Path $sdk 'LICENSE.txt') -Destination (Join-Path $output 'WEBVIEW2-LICENSE.txt') -Force
$notice = Join-Path $sdk 'ThirdPartyNotices.txt'
if (Test-Path -LiteralPath $notice) { Copy-Item -LiteralPath $notice -Destination $output -Force }
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$source = Join-Path $repository 'apps\desktop'
& $compiler /nologo /target:winexe /platform:x64 /optimize+ /warnaserror+ /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll ('/reference:'+(Join-Path $output 'Microsoft.Web.WebView2.Core.dll')) ('/reference:'+(Join-Path $output 'Microsoft.Web.WebView2.WinForms.dll')) ('/out:'+(Join-Path $output 'RobotOps Twin.exe')) (Join-Path $source 'OwnedProcess.cs') (Join-Path $source 'RobotOpsLauncher.cs')
if ($LASTEXITCODE -ne 0) { throw 'Desktop compilation failed.' }
@{ repository=$repository; python=$python } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'launcher.json') -Encoding UTF8
@'
<?xml version="1.0" encoding="utf-8"?>
<configuration><startup><supportedRuntime version="v4.0" sku=".NETFramework,Version=v4.8" /></startup></configuration>
'@ | Set-Content -LiteralPath (Join-Path $output 'RobotOps Twin.exe.config') -Encoding UTF8
$hashes = @{}
Get-ChildItem -LiteralPath $output -File | Where-Object Name -NE 'windows-build.json' | ForEach-Object { $hashes[$_.Name]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
$sources = @{}
foreach ($name in @('apps/desktop/OwnedProcess.cs','apps/desktop/RobotOpsLauncher.cs','apps/desktop/backend.py','tools/build-desktop.ps1')) {
    $sources[$name]=(Get-FileHash -LiteralPath (Join-Path $repository $name) -Algorithm SHA256).Hash.ToLowerInvariant()
}
@{ source_commit=(git -C $repository rev-parse HEAD); source_dirty=[bool](git -C $repository status --porcelain); source_sha256=$sources; sdk_version='1.0.3800.47'; sdk_sha256=$expectedHash.ToLowerInvariant(); files=$hashes } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $output 'windows-build.json') -Encoding UTF8
if ($Install) {
    $installed = Join-Path $env:LOCALAPPDATA 'RobotOpsTwin\App'
    New-Item -ItemType Directory -Path $installed -Force | Out-Null
    Get-ChildItem -LiteralPath $output -File | Copy-Item -Destination $installed -Force
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'RobotOps Twin.lnk'))
    $shortcut.TargetPath = Join-Path $installed 'RobotOps Twin.exe'
    $shortcut.WorkingDirectory = $installed
    $shortcut.Description = 'Open RobotOps Twin; closing the app stops its simulator.'
    $shortcut.IconLocation = $shortcut.TargetPath+',0'
    $shortcut.Save()
    Write-Output ('Installed: '+$shortcut.TargetPath)
}
Write-Output ('Built: '+(Join-Path $output 'RobotOps Twin.exe'))
