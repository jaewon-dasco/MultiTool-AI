# Task Scheduler 등록 — E2E_Nightly (매일 00:00 자동 실행)
# 관리자 권한 필요할 수 있음 (사용자 한정 등록은 비관리자 가능).

$ErrorActionPreference = "Stop"
$ROOT = "D:\4_AIProject\4_CoDeSys\AI_MutiTool"
$RUNNER = Join-Path $ROOT "skills\e2e_explorer\scripts\nightly_run.ps1"

if (-not (Test-Path $RUNNER)) {
    Write-Error "nightly_run.ps1 not found: $RUNNER"
    exit 1
}

$taskName = "E2E_Nightly"

# 기존 동일 이름 제거
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "removing existing task: $taskName"
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RUNNER`"" `
    -WorkingDirectory $ROOT

$trigger = New-ScheduledTaskTrigger -Daily -At 00:00

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 6)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "E2E 야간 관찰 학습 사이클 (00:00~05:30)" `
    -RunLevel Limited

Write-Host "registered: $taskName (Daily at 00:00)"
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State, NextRunTime | Format-List

# 추가: 06:00 강제 종료 Task
$killTaskName = "E2E_Nightly_Kill"
$existingKill = Get-ScheduledTask -TaskName $killTaskName -ErrorAction SilentlyContinue
if ($existingKill) {
    Unregister-ScheduledTask -TaskName $killTaskName -Confirm:$false
}

$killAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"Get-Process python,py -ErrorAction SilentlyContinue | Where-Object { `$_.CommandLine -like '*e2e_explorer*' } | Stop-Process -Force`""

$killTrigger = New-ScheduledTaskTrigger -Daily -At 05:30

Register-ScheduledTask `
    -TaskName $killTaskName `
    -Action $killAction `
    -Trigger $killTrigger `
    -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable) `
    -Description "E2E orchestrator 05:30 강제 종료" `
    -RunLevel Limited

Write-Host "registered: $killTaskName (Daily at 05:30)"
