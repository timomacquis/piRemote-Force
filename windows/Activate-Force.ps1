param(
    [Parameter(Mandatory=$true)][string]$ForceIP,
    [switch]$ProjectSaved,
    [switch]$CheckOnly
)
$ErrorActionPreference='Stop'
$ip=$null
if(-not [Net.IPAddress]::TryParse($ForceIP,[ref]$ip) -or $ip.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork){throw 'Invalid Force IPv4 address.'}
$helper=Join-Path $PSScriptRoot 'connect.py'
if(-not (Test-Path -LiteralPath $helper)){throw 'connect.py is missing beside Activate-Force.ps1.'}
$root=[IO.Path]::GetPathRoot($helper)
$linux='/mnt/'+$root.Substring(0,1).ToLowerInvariant()+$helper.Substring(2).Replace([char]92,[char]47)
if($CheckOnly){Write-Output $linux;return}
if(-not $ProjectSaved){
    $answer=Read-Host 'Activation restarts MPC. Save your project first. Type YES to continue'
    if($answer -cne 'YES'){Write-Host 'Cancelled.';exit 2}
}
wsl.exe -d Ubuntu -- python3 $linux activate $ForceIP --project-saved
if($LASTEXITCODE -ne 0){throw 'piRemote activation failed. Check the message above and INSTALL.md.'}