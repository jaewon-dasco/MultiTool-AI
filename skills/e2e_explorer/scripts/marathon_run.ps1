# E2E Marathon — 45시간 연속 사이클 (2026-05-15 21:00 ~ 2026-05-17 18:00)
# Task Scheduler 'E2E_Marathon_Start' 가 21:00에 1회 호출
$ErrorActionPreference = "Stop"
$ROOT = "D:\4_AIProject\4_CoDeSys\AI_MutiTool"
Set-Location $ROOT

$START = Get-Date "2026-05-15 21:00:00"
$END   = Get-Date "2026-05-17 18:00:00"
$now   = Get-Date
$remainingMin = [Math]::Max(60, [Math]::Round(($END - $now).TotalMinutes))

$DATE = Get-Date -Format "yyyy-MM-dd"
$LOG_DIR = Join-Path $ROOT "logs\e2e\$DATE"
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
$LOG = Join-Path $LOG_DIR "marathon_run.log"

"[$(Get-Date -Format s)] marathon_run start, remaining=$remainingMin min" | Out-File -FilePath $LOG -Append -Encoding utf8

$MULTITOOL = "C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"
$PROJECT   = Join-Path $ROOT "MultiToolProject\E2EProject\DasDemoProject.mtproject"
$running = Get-Process -Name "MultiTool" -ErrorAction SilentlyContinue
if (-not $running) {
    "[$(Get-Date -Format s)] starting MultiTool" | Out-File -FilePath $LOG -Append -Encoding utf8
    Start-Process -FilePath $MULTITOOL -ArgumentList "`"$PROJECT`""
    Start-Sleep -Seconds 30
}

$ORCH = Join-Path $ROOT "skills\e2e_explorer\orchestrator.py"
# max_cycles=999 → 시간이 가장 먼저 도달 (until-minutes)
$CMDLINE = "py `"$ORCH`" --project `"$PROJECT`" --until-minutes $remainingMin --max-cycles 999 1>>`"$LOG`" 2>&1"
"[$(Get-Date -Format s)] launching: $CMDLINE" | Out-File -FilePath $LOG -Append -Encoding utf8

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
cmd /c $CMDLINE

"[$(Get-Date -Format s)] marathon_run end" | Out-File -FilePath $LOG -Append -Encoding utf8
