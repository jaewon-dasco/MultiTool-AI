# PROJECT

## 저장소

| 항목       | 값                                             |
| ---------- | ---------------------------------------------- |
| GitHub URL | <https://github.com/jaewon-dasco/MultiTool-AI> |
| 브랜치     | `master`                                       |

## 관련 문서

| 문서                                                                            | 내용                                       |
| ------------------------------------------------------------------------------- | ------------------------------------------ |
| [MultiTool_E2E.md](MultiTool_E2E.md)                                            | E2E 자율 학습 시스템 설계서 (현재)         |
| [SCHEDULE.md](SCHEDULE.md)                                                      | 작업 히스토리·진행·남은 항목 (우선순위 표) |
| [skills/e2e_explorer/multitool_e2e.md](../skills/e2e_explorer/multitool_e2e.md) | 운영 지침·알려진 함정·갱신 프로토콜        |

## 진행 상황

| 구성 요소                                      | 상태                                                                                  |
| ---------------------------------------------- | ------------------------------------------------------------------------------------- |
| `docs/exp_patterns/baseline.exp`               | done (참조 자산)                                                                      |
| `docs/versions/8.4/function_map.json`          | done (49개 기능, 참조 자산)                                                           |
| 기존 부분 스킬                                 | 폐기 — E2E로 통합됨                                                                   |
| `skills/e2e_explorer/recipes/`                 | active — 5개 핸들러 (set_field_auto·io_pin·io_var_name·network_property·device_modes) |
| `skills/e2e_explorer/sequences_ui/`            | active — A/B/C/D/E/F 6 카테고리 51 시드                                               |
| `MultiToolProject/E2EProject/*.clean_baseline` | done — Save 노이즈 28→0 정합 baseline                                                 |
| 야간 사이클 (night_ui_run.ps1)                 | 매일 12:52 (변동)·6h Task Scheduler 자동 실행                                         |
| 통계 분석 (night_ui_review.py)                 | active — signal/noise + intent 추출 자동 보고                                         |

### 다음 작업 순서

E2E 마일스톤은 [MultiTool_E2E.md](MultiTool_E2E.md) 참조.

## Clarify

| 항목   | 내용                                                  |
| ------ | ----------------------------------------------------- |
| 대상   | AI_MutiTool — MultiTool E2E 자율 학습 환경            |
| 입력   | 야간 자율 탐색 + 주간 Claude routine 감독             |
| 출력   | `.mtproject` 변경 + 정합 `.exp` 자동 생성             |
| 산출물 | `skills/e2e_explorer/` 단일 통합 스킬 (W1+ 작성 예정) |

## Context Gather

### MultiTool 환경

| 항목      | 내용                                                                 |
| --------- | -------------------------------------------------------------------- |
| 설치      | `C:\Program Files (x86)\Epec\MultiTool Creator {ver}\` — 8.1/8.2/8.4 |
| 매뉴얼    | `Resources\Manual.chm` (8.4만) — MD5 변경 감지                       |
| API       | 없음 — UI Automation (pywinauto) 전용                                |
| 키 트리거 | `PROJECT > System Export` (Ctrl+Alt+E)                               |

### `.mtproject` 구조

`MultiToolProject/{이름}/` 하위:

| 파일                      | 내용                              |
| ------------------------- | --------------------------------- |
| `{이름}.mtproject`        | XML — 메타·디바이스 구성          |
| `{Device}/{Device}.exp`   | CoDeSys 변수·POU export           |
| `{Device}/{Device}.pro`   | CoDeSys IDE 전용 — 편집 금지      |
| `{Device}/*.HEX/.BIN`     | 펌웨어 빌드 결과                  |
| `Parameters_NETWORK1.csv` | OD 파라미터 — 편집 후 임포트 필요 |
| `NETWORK1.dbc`            | CAN 버스                          |
| `eventconfiguration.csv`  | 이벤트 매핑                       |

### `.exp` 포맷

CoDeSys IEC 61131-3 ST export. `(* @PATH := '...' *)` 메타플래그 + `VAR_GLOBAL [CONSTANT] ... END_VAR` 블록. `(*START - Implicit variables, made by EPEC Parser*)` 마커 이후는 자동 생성. `{Device}_generated.exp` 직접 편집 금지.

### 참조 자산 (E2E 입력)

| 위치                                  | 내용                                    |
| ------------------------------------- | --------------------------------------- |
| `docs/versions/8.4/function_map.json` | 49개 기능 사전 — E2E 탐색 시드          |
| `docs/exp_patterns/baseline.exp`      | `.exp` 골든 — 자기검증 의미적 diff 기준 |
| `docs/exp_patterns/mapping.json`      | 설정값 → `.exp` 변경 라인 매핑          |
| `screencapture/*.png`                 | UI 캡처 참고                            |

### 제약

- `.exp`는 export 시 덮어씌워짐 — 변경은 `.mtproject` 경유
- `.pro`·`_generated.exp` 직접 편집 금지
- CHM은 8.4만 제공 — 하위 버전은 UI 덤프만
- maximized 모드 + fixed offset 좌표 의존

## Plan

### 워크플로

- **야간 자율 (E2E)**: Task Scheduler 00:00 → Qwen3.5 + pywinauto + XML utils → KB 누적 → 자기검증
- **주간 자동 (E2E)**: Claude routine 09:00 → 야간 산출물 검토 → 스킬·지침 개선 + hints 갱신
- **Sunset**: 자율도 지표 충족 시 Claude routine 자기 비활성화 → skill 단독 운영
- 상세 → [MultiTool_E2E.md](MultiTool_E2E.md)

### 단일 스킬 구조

기존 부분 스킬(mtpatch·expscan·multitool)은 모두 폐기. `skills/e2e_explorer/` 단일 통합 스킬로 재구성:

```text
skills/e2e_explorer/
  orchestrator.py     야간 의사결정 루프
  ollama_client.py    Qwen3.5 HTTP
  ui_driver.py        pywinauto GUI
  xml_utils.py        .mtproject read/write/backup
  exp_validator.py    .exp 파싱·골든 diff
  kb_store.py         SQLite/JSONL
```

## Generate

W1 PoC부터 시작. 상세 진입 명령·인터페이스는 [MultiTool_E2E.md](MultiTool_E2E.md) §마일스톤 참조.

## E2E 로그 확인 자동 명령

사용자가 **"로그 확인해줘"**, **"어젯밤 로그 봐줘"**, **"E2E 결과 보여줘"** 같이 야간 사이클 로그 확인을 요청하면 Claude는 즉시 아래 명령을 실행하고 결과를 요약 보고한다.

```powershell
$DATE = Get-Date -Format "yyyy-MM-dd"
$BASE = "D:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e\$DATE"
if (-not (Test-Path $BASE)) {
    $LATEST = Get-ChildItem "D:\4_AIProject\4_CoDeSys\AI_MutiTool\logs\e2e" -Directory | Sort-Object Name -Descending | Select-Object -First 1
    $BASE = $LATEST.FullName
}
Write-Host "== $BASE =="
Get-Content "$BASE\summary.md" -ErrorAction SilentlyContinue
Write-Host "`n== run.log (tail 30) =="
Get-Content "$BASE\run.log" -Tail 30 -ErrorAction SilentlyContinue
Write-Host "`n== observations.jsonl 라인 수 =="
(Get-Content "$BASE\observations.jsonl" -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
Write-Host "`n== Task Scheduler 상태 =="
Get-ScheduledTask -TaskName E2E_Nightly,E2E_Nightly_Kill -ErrorAction SilentlyContinue |
    Select-Object TaskName,State,@{N='LastRun';E={(Get-ScheduledTaskInfo $_).LastRunTime}},@{N='LastResult';E={(Get-ScheduledTaskInfo $_).LastTaskResult}} |
    Format-Table -AutoSize
```

보고 형식:

| 항목       | 내용                                                 |
| ---------- | ---------------------------------------------------- |
| 사이클일자 | `$BASE` 폴더 일자                                    |
| 통계       | summary.md의 steps/trees/snapshots/llm_calls/errors  |
| Task 상태  | LastRun + LastResult (0이면 정상)                    |
| 이상 신호  | `errors > 0` 또는 `LastResult ≠ 0` 또는 폴더 누락 시 |

## Evaluate

| 항목             | 기준                                                |
| ---------------- | --------------------------------------------------- |
| 야간 1사이클     | 00:00~05:30 무중단 + 05:30 클린 복구                |
| 주간 routine     | 09:00 자동 트리거 + auto_approve_policy 분류 commit |
| `.exp` 정합성    | 골든 의미적 diff 0 통과                             |
| 보호 파일 무결성 | `_generated.exp`·`.pro` 변경 0                      |
| Sunset 자율도    | [MultiTool_E2E.md](MultiTool_E2E.md) §자율도 지표   |
