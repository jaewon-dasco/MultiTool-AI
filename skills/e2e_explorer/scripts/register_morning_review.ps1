# E2E_Morning_Review Task — 매일 06:00 헤드리스 Claude Code 실행
# /review-last-night 슬래시 커맨드를 통해 어젯밤 사이클 자동 검토.

$ErrorActionPreference = "Stop"
$ROOT = "D:\4_AIProject\4_CoDeSys\AI_MutiTool"
$CLAUDE = "C:\Users\JONE\.local\bin\claude.exe"

if (-not (Test-Path $CLAUDE)) {
    Write-Error "Claude CLI not found at $CLAUDE"
    exit 1
}

$taskName = "E2E_Morning_Review"

# 기존 동일 이름 제거
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Claude headless: -p 슬래시 커맨드 + 권한 모드 acceptEdits
# stdout/stderr → logs/e2e/<date>/morning_review.log
$cmd = @"
`$ErrorActionPreference = 'Continue'
`$DATE = Get-Date -Format 'yyyy-MM-dd'
`$LOG_DIR = Join-Path '$ROOT' "logs\e2e\`$DATE"
New-Item -ItemType Directory -Force -Path `$LOG_DIR | Out-Null
`$LOG = Join-Path `$LOG_DIR 'morning_review.log'
Set-Location '$ROOT'
"[`$(Get-Date -Format s)] morning_review start" | Out-File -FilePath `$LOG -Append -Encoding utf8
`$env:PYTHONIOENCODING = 'utf-8'
& cmd /c '"$CLAUDE" -p "/review-last-night" --permission-mode acceptEdits --output-format text 1>>"' + `$LOG + '" 2>&1'
"[`$(Get-Date -Format s)] morning_review end (exit=`$LASTEXITCODE)" | Out-File -FilePath `$LOG -Append -Encoding utf8
"@

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$cmd`"" `
    -WorkingDirectory $ROOT

$trigger = New-ScheduledTaskTrigger -Daily -At 06:00

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "E2E 야간 사이클 06:00 자동 검토 (Claude CLI headless)" `
    -RunLevel Limited

Write-Host "registered: $taskName (Daily at 06:00)"
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State, @{N='NextRun';E={(Get-ScheduledTaskInfo $_).NextRunTime}} | Format-List
