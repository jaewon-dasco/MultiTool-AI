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

# orchestrator 실행 — 05:30까지
# PowerShell 5.1에서 native exe의 *>> 리다이렉트는 NativeCommandError 발생 →
# cmd /c 안에서 리다이렉트 처리하여 PS error stream 우회.
$ORCH_SCRIPT = Join-Path $ROOT "skills\e2e_explorer\orchestrator.py"
$CMDLINE = "py `"$ORCH_SCRIPT`" --project `"$PROJECT`" --until 05:30 --interval 300 1>>`"$LOG`" 2>&1"
"[$(Get-Date -Format s)] launching: $CMDLINE" | Out-File -FilePath $LOG -Append -Encoding utf8

# $env:PYTHONIOENCODING으로 UTF-8 강제 (cp949 인코딩 오류 방지)
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

& cmd /c $CMDLINE
$EXIT = $LASTEXITCODE

"[$(Get-Date -Format s)] nightly_run end (exit=$EXIT)" | Out-File -FilePath $LOG -Append -Encoding utf8
exit $EXIT
