param([string]$Root = "C:\Users\leehy\ParkingVision")
$ErrorActionPreference = "Stop"
$Owner = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
New-Item -ItemType Directory -Force $Root | Out-Null
& icacls.exe $Root /inheritance:r /grant:r "${Owner}:(OI)(CI)F" "SYSTEM:(OI)(CI)F" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "ACL setup failed" }
$Python = (Get-Command python.exe).Source
if (!(Test-Path "$Root\venv\Scripts\python.exe")) {
  & $Python -m venv "$Root\venv"
  if ($LASTEXITCODE -ne 0) { throw "venv failed" }
}
& "$Root\venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "$Root\code\requirements.txt"
if ($LASTEXITCODE -ne 0) { throw "dependencies failed" }
$Codex = Get-ChildItem "$env:APPDATA\npm\node_modules\@openai\codex" -Filter codex.exe -Recurse | Select-Object -First 1 -ExpandProperty FullName
if (!$Codex) { throw "Official Codex CLI not installed" }
& $Codex login status
if ($LASTEXITCODE -ne 0) { throw "Run codex.cmd login --device-auth first" }
if (!(Test-Path "$Root\config.json")) {
  $Bytes = New-Object byte[] 32
  $Rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $Rng.GetBytes($Bytes)
  $Rng.Dispose()
  $Token = [Convert]::ToBase64String($Bytes)
  @{dataDir="$Root\data";codexExe=$Codex;port=18765;token=$Token;maxJobsPerDay=24} | ConvertTo-Json | Set-Content "$Root\config.json" -Encoding UTF8
}
$Config = Get-Content -Raw "$Root\config.json" | ConvertFrom-Json
$Config.codexExe = $Codex
$Config | ConvertTo-Json | Set-Content "$Root\config.json" -Encoding UTF8
& "$Root\venv\Scripts\python.exe" -m unittest discover -s "$Root\code" -p test_service.py -v
if ($LASTEXITCODE -ne 0) { throw "tests failed" }
$Action = New-ScheduledTaskAction -Execute "$Root\venv\Scripts\pythonw.exe" -Argument "`"$Root\code\launcher.py`" --config `"$Root\config.json`"" -WorkingDirectory "$Root\code"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId $Owner -LogonType S4U -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "Parking Vision Codex" -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null
Start-ScheduledTask -TaskName "Parking Vision Codex"
Write-Output "Installed private loopback service; no public firewall rule created."
