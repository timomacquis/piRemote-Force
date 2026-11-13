param(
    [Parameter(Mandatory=$true)][string]$ForceIP,
    [switch]$ProjectSaved
)
$ErrorActionPreference='Stop'
$ip=$null
if(-not [Net.IPAddress]::TryParse($ForceIP,[ref]$ip) -or $ip.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork){throw 'Invalid Force IPv4 address.'}
if(-not $ProjectSaved){
    $answer=Read-Host 'Activation restarts MPC. Save your project first. Type YES to continue'
    if($answer -cne 'YES'){Write-Host 'Cancelled.';exit 2}
}
$helper=Join-Path $PSScriptRoot 'connect.py'
$root=[IO.Path]::GetPathRoot($helper)
$linux='/mnt/'+$root.Substring(0,1).ToLowerInvariant()+$helper.Substring(2).Replace('\','/')
wsl.exe -d Ubuntu -- python3 $linux activate $ForceIP --project-saved
if($LASTEXITCODE -ne 0){throw 'piRemote activation failed. Check the message above and INSTALL.md.'}
