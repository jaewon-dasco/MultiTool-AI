# SessionStart hook 진입점.
# 가장 최근 E2E 사이클 결과 요약을 stdout에 출력 → Claude가 컨텍스트로 받아 자동 보고.
# 이미 리뷰된 사이클은 _reviewed.flag로 skip.

$ErrorActionPreference = "SilentlyContinue"
$ROOT = "D:\4_AIProject\4_CoDeSys\AI_MutiTool"
$LOGBASE = Join-Path $ROOT "logs\e2e"

if (-not (Test-Path $LOGBASE)) { exit 0 }

$LATEST = Get-ChildItem -Path $LOGBASE -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}$' } |
    Sort-Object Name -Descending | Select-Object -First 1

if (-not $LATEST) { exit 0 }

$DIR = $LATEST.FullName
$REVIEWED = Join-Path $DIR "_reviewed.flag"
$SUMMARY = Join-Path $DIR "summary.md"
$OBS = Join-Path $DIR "observations.jsonl"

# 이미 리뷰됨 → 출력 skip (조용히 종료)
if (Test-Path $REVIEWED) { exit 0 }

# summary가 없으면 아직 사이클 미완료 — skip
if (-not (Test-Path $SUMMARY)) { exit 0 }

# 출력
Write-Output "=== E2E_OVERNIGHT_REPORT ==="
Write-Output "cycle_dir: $DIR"
Write-Output ""
Write-Output "--- summary.md ---"
Get-Content $SUMMARY

if (Test-Path $OBS) {
    $count = (Get-Content $OBS | Measure-Object -Line).Lines
    Write-Output ""
    Write-Output "--- observations.jsonl ---"
    Write-Output "lines: $count"
    Write-Output ""
    Write-Output "--- last 3 Gemma observations (truncated) ---"
    Get-Content $OBS -Tail 3 | ForEach-Object {
        try {
            $o = $_ | ConvertFrom-Json
            $c = $o.llm_content
            if (-not $c) { $c = $o.llm.content }
            if ($c) {
                $snippet = $c.Substring(0, [Math]::Min(150, $c.Length))
                Write-Output "[$($o.seq_name)] $snippet..."
            }
        } catch {}
    }
}

# 리뷰 완료 마킹
"" | Out-File -FilePath $REVIEWED -Encoding utf8
Write-Output ""
Write-Output "=== /E2E_OVERNIGHT_REPORT ==="
exit 0
