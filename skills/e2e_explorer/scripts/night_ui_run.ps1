# Night UI cycle — 33 functions × 5 cycles, UI 채널, .mtproject + .exp 통합 학습
$ErrorActionPreference = "Continue"
$ROOT = "D:\4_AIProject\4_CoDeSys\AI_MutiTool"
Set-Location $ROOT

$DATE = Get-Date -Format "yyyy-MM-dd"
$LOG_DIR = Join-Path $ROOT "logs\e2e\$DATE"
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
$LOG = Join-Path $LOG_DIR "night_ui_run.log"

"[$(Get-Date -Format s)] night_ui_run start" | Out-File -FilePath $LOG -Append -Encoding utf8

# MultiTool 보장 + 프로젝트 로드
$MULTITOOL = "C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"
$PROJECT   = Join-Path $ROOT "MultiToolProject\E2EProject\DasDemoProject.mtproject"
$running = Get-Process -Name "MultiTool" -ErrorAction SilentlyContinue
if (-not $running) {
    "[$(Get-Date -Format s)] starting MultiTool" | Out-File -FilePath $LOG -Append -Encoding utf8
    Start-Process -FilePath $MULTITOOL
    Start-Sleep -Seconds 30
    # Auto-load project via Open Project hyperlink
    py "$ROOT\skills\e2e_explorer\scripts\ui_open_project.py" *>> $LOG
}

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# 순서대로 각 카테고리 5 cycle (PS 5.1 호환 — cmd /c 대신 직접 호출)
$categories = @("B", "C", "A", "D", "E", "F")
$scriptPath = Join-Path $ROOT "skills\e2e_explorer\scripts\run_night_ui.py"
foreach ($cat in $categories) {
    "[$(Get-Date -Format s)] === Category $cat ===" | Out-File -FilePath $LOG -Append -Encoding utf8
    "[$(Get-Date -Format s)] launching: py $scriptPath --category $cat --cycles 5" | Out-File -FilePath $LOG -Append -Encoding utf8
    try {
        & py $scriptPath --category $cat --cycles 5 2>&1 | Out-File -FilePath $LOG -Append -Encoding utf8
        "[$(Get-Date -Format s)] category $cat exit=$LASTEXITCODE" | Out-File -FilePath $LOG -Append -Encoding utf8
    } catch {
        "[$(Get-Date -Format s)] category $cat EXCEPTION: $_" | Out-File -FilePath $LOG -Append -Encoding utf8
    }
}

"[$(Get-Date -Format s)] night_ui_run end" | Out-File -FilePath $LOG -Append -Encoding utf8
