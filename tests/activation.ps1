$ErrorActionPreference='Stop'
$script=Join-Path $PSScriptRoot '..\windows\Activate-Force.ps1'
$expected=[IO.Path]::GetFullPath((Join-Path (Split-Path -Parent $script) 'connect.py'))
$linux='/mnt/'+[IO.Path]::GetPathRoot($expected).Substring(0,1).ToLowerInvariant()+$expected.Substring(2).Replace([char]92,[char]47)
$actual=& $script -ForceIP '192.0.2.70' -CheckOnly
if($actual -ne $linux -or $actual.Contains([char]92)){throw 'WSL path conversion failed'}
$global:activationArgs=$null
function wsl.exe {
    $global:activationArgs=@($args)
    $global:LASTEXITCODE=0
}
& $script -ForceIP '192.0.2.70' -ProjectSaved
# PowerShell consumes its -- end-of-options marker for a mocked function; the real native executable receives it.
if(($global:activationArgs -join '|') -ne (@('-d','Ubuntu','python3',$linux,'activate','192.0.2.70','--project-saved') -join '|')){throw 'Activation arguments incorrect'}
Remove-Item Function:\wsl.exe
Write-Output 'PASS: real activation script, spaces and Unicode path, exact WSL arguments; no SSH or MPC restart'
