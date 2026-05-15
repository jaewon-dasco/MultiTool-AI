# Marathon 진행 상황 한 줄 보고. 언제든 실행 가능.
$ROOT = "D:\4_AIProject\4_CoDeSys\AI_MutiTool"
$DATE = Get-Date -Format "yyyy-MM-dd"
$LOG = Join-Path $ROOT "logs\e2e\$DATE\marathon_run.log"
$END = Get-Date "2026-05-17 18:00:00"
$now = Get-Date

# MultiTool 상태
$mt = Get-Process MultiTool -ErrorAction SilentlyContinue
$pyOrch = Get-WmiObject Win32_Process -Filter "Name='py.exe' OR Name='python.exe'" 2>$null | Where-Object { $_.CommandLine -like "*orchestrator*" }

# 로그 끝부분
$tail = if (Test-Path $LOG) { (Get-Content $LOG -Tail 5) -join "`n" } else { "(no log yet)" }

# 시드 진행
$obsFile = Join-Path $ROOT "logs\e2e\$DATE\observations.jsonl"
$obsCount = if (Test-Path $obsFile) { (Get-Content $obsFile).Count } else { 0 }
$seqDir = Join-Path $ROOT "logs\e2e\$DATE\sequences"
$seqCount = if (Test-Path $seqDir) { (Get-ChildItem $seqDir -Directory).Count } else { 0 }

$remaining = [Math]::Round(($END - $now).TotalHours, 1)

Write-Host "=== E2E Marathon Status @ $($now.ToString('yyyy-MM-dd HH:mm:ss')) ==="
Write-Host "Time: remaining $remaining h (ends $($END.ToString('MM-dd HH:mm')))"
Write-Host "MultiTool: $(if ($mt) { "running PID=$($mt.Id)" } else { 'NOT RUNNING' })"
Write-Host "orchestrator: $(if ($pyOrch) { "running (PID=$($pyOrch.ProcessId))" } else { 'NOT RUNNING' })"
Write-Host "observations: $obsCount entries"
Write-Host "sequences completed: $seqCount"
Write-Host "--- last log lines ---"
Write-Host $tail
