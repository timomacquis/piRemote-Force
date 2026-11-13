$ErrorActionPreference='Stop'
$out=Join-Path $PSScriptRoot '..\build\windows'
New-Item -ItemType Directory -Path $out -Force | Out-Null
$compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $compiler /nologo /target:winexe /optimize+ /platform:anycpu /r:System.dll /r:System.Core.dll /r:System.Drawing.dll /r:System.Windows.Forms.dll /r:System.Web.Extensions.dll (('/win32manifest:')+(Join-Path $PSScriptRoot 'app.manifest')) (('/win32icon:')+(Join-Path $PSScriptRoot 'piRemote.ico')) (('/out:')+(Join-Path $out 'πRemote.exe')) (Join-Path $PSScriptRoot 'PiRemote.cs')
if($LASTEXITCODE -ne 0){throw 'Compilation failed'}
foreach($f in @('πRemote.exe.config','piRemote.ico','connect.py','Activate-Force.ps1')){Copy-Item -LiteralPath (Join-Path $PSScriptRoot $f) -Destination (Join-Path $out $f) -Force}
[IO.File]::WriteAllText((Join-Path $out 'Force-IP.txt'),'', [Text.UTF8Encoding]::new($false))
$p=Start-Process -FilePath (Join-Path $out 'πRemote.exe') -ArgumentList '--selftest' -Wait -PassThru
if($p.ExitCode -ne 0){throw 'Application self-test failed'}
$inputs=[ordered]@{}
Get-ChildItem -LiteralPath $PSScriptRoot -File | Where-Object {$_.Extension -in @('.cs','.py','.ps1','.config','.ico','.manifest')} | Sort-Object Name | ForEach-Object {$inputs[$_.Name]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
$receipt=[ordered]@{version='0.1.0';target='Windows 10/11, .NET Framework 4.8';exe_sha256=(Get-FileHash -LiteralPath (Join-Path $out 'πRemote.exe') -Algorithm SHA256).Hash.ToLowerInvariant();inputs=$inputs;selftest='passed';device_tested=$false}
$receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $out 'BUILD.json') -Encoding UTF8
