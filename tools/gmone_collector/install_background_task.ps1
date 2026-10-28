param([string]$Root = (Join-Path $env:LOCALAPPDATA 'Wayon\GMOne'))
$ErrorActionPreference = 'Stop'
$name = 'Wayon GMOne Collector'
$python = Join-Path $Root 'venv\Scripts\pythonw.exe'
$script = Join-Path $Root 'app\gmone_background.py'
foreach ($file in @($python, $script, (Join-Path $Root 'config\background.json'),
    (Join-Path $Root 'config\gmone.json'), (Join-Path $Root 'app\gmone_collector.py'),
    (Join-Path $Root 'app\gmone_store.py'))) {
  if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw 'Missing background collector dependency' }
}
$existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($existing) {
  if ($existing.State -eq 'Running') { throw 'Stop the old collector after review before replacing its task' }
  $backup = Join-Path $Root ('backups\background-task-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.xml')
  New-Item -ItemType Directory -Path (Split-Path $backup) -Force | Out-Null
  Export-ScheduledTask -TaskName $name | Set-Content -LiteralPath $backup -Encoding UTF8
}
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$action = New-ScheduledTaskAction -Execute $python -Argument ('"' + $script + '" --root "' + $Root + '"') -WorkingDirectory (Join-Path $Root 'app')
$logon = New-ScheduledTaskTrigger -AtLogOn -User $user
$watchdog = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) `
  -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $name -Action $action -Principal $principal -Trigger @($logon, $watchdog) -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $name
Get-ScheduledTask -TaskName $name | Select-Object TaskName, State
