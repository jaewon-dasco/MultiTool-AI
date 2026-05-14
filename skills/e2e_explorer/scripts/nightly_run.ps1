# E2E 야간 진입점. Task Scheduler가 호출.
# 1) MultiTool 자동 시작
# 2) orchestrator.py 실행 (관찰 모드, 06:00까지)
# 3) 로그 일자별 파일

$ErrorActionPreference = "Stop"
$ROOT = "D:\4_AIProject\4_CoDeSys\AI_MutiTool"
Set-Location $ROOT

$DATE = Get-Date -Format "yyyy-MM-dd"
$LOG_DIR = Join-Path $ROOT "logs\e2e\$DATE"
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
$LOG = Join-Path $LOG_DIR "run.log"

"[$(Get-Date -Format s)] nightly_run start" | Out-File -FilePath $LOG -Append -Encoding utf8

# MultiTool 시작 (이미 떠 있으면 ui_driver가 skip)
$MULTITOOL = "C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"
$PROJECT   = Join-Path $ROOT "MultiToolProject\E2EProject\DasDemoProject.mtproject"

$running = Get-Process -Name "MultiTool" -ErrorAction SilentlyContinue
if (-not $running) {
    "[$(Get-Date -Format s)] starting MultiTool" | Out-File -FilePath $LOG -Append -Encoding utf8
    Start-Process -FilePath $MULTITOOL -ArgumentList "`"$PROJECT`""
    Start-Sleep -Seconds 25
} else {
    "[$(Get-Date -Format s)] MultiTool already running" | Out-File -FilePath $LOG -Append -Encoding utf8
}

# orchestrator 실행 — 06:00까지
$PY = "py"
$ARGS = @(
    "skills\e2e_explorer\orchestrator.py",
    "--project", $PROJECT,
    "--until", "05:30",
    "--interval", "300"
)
"[$(Get-Date -Format s)] launching orchestrator $($ARGS -join ' ')" | Out-File -FilePath $LOG -Append -Encoding utf8

& $PY @ARGS *>> $LOG

"[$(Get-Date -Format s)] nightly_run end (exit=$LASTEXITCODE)" | Out-File -FilePath $LOG -Append -Encoding utf8
exit $LASTEXITCODE
