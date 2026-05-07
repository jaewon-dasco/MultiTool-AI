---
name: multitool
description: 자연어 명령으로 EPEC MultiTool Creator GUI를 자동 조작 또는 .mtproject XML을 직접 편집해 산출물을 생성·수정하는 vibecoding 자동화. function_map.json(49개) → Claude tool schema → pywinauto UI 조작 + mtpatch XML 직접 편집(GUI 우회). MultiTool 디바이스 추가·네트워크 설정·OD 편집·System Export·CODESYS 생성, BitRate/Buffering/J1939 변경 등 자연어 명령 시 호출. 키워드 — MultiTool, Epec, .mtproject, .exp, ScanDemo, CU-3606, Bitrate, BitRate, OD index, RPDO, TPDO, System Export, CODESYS, Add Device, Configure CAN, J1939, ISOBUS, Buffering, NodeId, Heartbeat, NETWORK1.dbc, Parameters_NETWORK1.csv.
---

# multitool

## Overview

Epec MultiTool Creator(GUI 전용)를 키보드/마우스 자동화로 조작해 `.mtproject` 산출물을 생성·수정한다. 사용자는 자연어로 명령하고, 본 스킬은 Claude API tool 루프 + pywinauto로 GUI를 직접 클릭한다.

## Trigger 조건

- MultiTool 기능명(Add Device, Configure: CAN, System Export 등) 언급
- `.mtproject` / `.exp` 산출물 생성·변경 의도
- Epec 디바이스 식별자(CU-3606-21 등)·OD 인덱스(0x2300)·Bitrate(250kbps) 등 도메인 키워드
- 사용자가 명시적으로 `/multitool` 슬래시·"MultiTool로 ~" 발화

## 사전 조건 (필수)

| 항목                      | 확인 명령                                                                     |
| ------------------------- | ----------------------------------------------------------------------------- |
| MultiTool 8.4 설치        | `Test-Path "C:\Program Files (x86)\Epec\MultiTool Creator 8.4\MultiTool.exe"` |
| `anthropic` Python 패키지 | `py -3 -c "import anthropic"`                                                 |
| `pywinauto`               | `py -3 -c "import pywinauto"`                                                 |
| `ANTHROPIC_API_KEY`       | `$env:ANTHROPIC_API_KEY -ne $null`                                            |
| `function_map.json`       | `Test-Path docs\versions\8.4\function_map.json`                               |

미충족 시 사용자에게 알리고 작업 보류.

## Workflow

### 1. 명령 분류

자연어 명령을 다음으로 분기:

| 분류          | 예                                      | 진입점                                  |
| ------------- | --------------------------------------- | --------------------------------------- |
| 단일 기능     | "ScanDemo 열어줘", "현재 프로젝트 저장" | `vibe/run.py`                           |
| 다단계 GUI    | "CU-3606-21 새 프로젝트, CAN1 250kbps"  | `vibe/run.py` (LLM이 시퀀스 분해)       |
| GUI 우회 편집 | "CAN1 bitrate 500", "J1939 활성"        | `mtpatch/run.py` 또는 vibe의 xml_* tool |
| 정보 조회     | "현재 디바이스 목록", "OD 인덱스 확인"  | `mtpatch show` 또는 `verify snapshot`   |
| 메타 조작     | "스캔 갱신", "단축키 검증"              | `skills/fnscan/run.py` (별도 스킬)      |
| `.exp` 캡처   | "baseline 캡처", "variant diff"         | `skills/expscan/run.py` (별도 스킬)     |

### 2. 실행 — 단일·다단계 명령

```
py skills\vibe\run.py "<자연어 명령>" [--project <path.mtproject>] [--no-execute] [--before <snap>] [--after <snap>]
```

| 옵션               | 의미                                         |
| ------------------ | -------------------------------------------- |
| (기본)             | MultiTool 시작 → Claude tool 루프 → GUI 조작 |
| `--no-execute`     | dry-run — Claude 판단만 검증, GUI 미조작     |
| `--project <p>`    | 시작 시 해당 `.mtproject` 자동 로드          |
| `--before/--after` | 실행 전후 XML snapshot → diff 자동 출력      |
| `--max-iter N`     | tool 루프 상한 (기본 12)                     |
| `--model <id>`     | Claude 모델 (기본 `claude-opus-4-7`)         |

**위험 조작 가드:** 다음 명령은 사용자에게 사전 확인 받은 후에만 실행 — `Save As`, 신규 프로젝트 생성으로 기존 작업 덮어쓰기, `Remove from Project`, `Export Project Archive` 후 원본 정리, OD/PDO 일괄 삭제. 첫 실행 권장은 `--no-execute` dry-run.

### 3. 검증

| 단계       | 명령                                                                    |
| ---------- | ----------------------------------------------------------------------- |
| 파이프라인 | `py skills\vibe\selftest.py` — 모킹 30케이스, API 비용 0                |
| dry-run    | `py skills\vibe\run.py "..." --no-execute` — 실 Claude 판단·GUI 미조작  |
| diff 검증  | `--before snap_a.json --after snap_b.json` — `.mtproject` XML 변화 확인 |

### 4. 결과 해석

`run.py` 출력 구조:

```
final: <Claude 최종 텍스트>
iter:  N  stop: end_turn|max_iterations|tool_use|...
usage: in=<int> out=<int> cache_read=<int> cache_creation=<int>
session log (M):
  - <기능명> via <method>(<detail>)
```

| 정상 신호                 | 이상 신호                                   |
| ------------------------- | ------------------------------------------- |
| `stop=end_turn`           | `stop=max_iterations` — 루프 미수렴         |
| `iter` 2~5                | `iter` 12 + max_iterations — 명령 분해 실패 |
| 2회차 `cache_read` ≫ 0    | 항상 `cache_read=0` — tools 캐시 무효       |
| log의 `via shortcut(...)` | 모두 `via coords(...)` — 단축키 검증 미반영 |

이상 신호 시 `selftest.py` 재실행 → `function_map.json` 갱신 (`skills\fnscan\run.py --force`) → 재시도.

## 한계

| 항목               | 내용                                                             |
| ------------------ | ---------------------------------------------------------------- |
| 기능 커버리지      | function_map 49개 — Export Parameter CSV·CANdb Export 등 미수집  |
| 단축키 검증율      | 7/12 (58.3%) — 미검증 항목은 좌표/메뉴 폴백                      |
| device_config 입력 | 일부 입력은 name 미지정 (`combobox_1` 등) — LLM이 의도 추론 필요 |
| 동시성             | 단일 MultiTool 인스턴스 — 병렬 실행 불가                         |
| Headless 불가      | GUI 자동화 — 사용자 화면 점유                                    |
| 의도 모호성        | "비례밸브 설정" 같은 추상 명령 → 추가 명세 요청                  |

## GUI 우회 — XML 직접 편집

MultiTool GUI 조작 없이 `.mtproject` XML을 직접 mutate. 단순 필드 변경 시 우선 사용.

```
py skills\mtpatch\run.py show <project>                       # 핵심 필드 조회
py skills\mtpatch\run.py set-bitrate <project> <can#> <kbps>  # CAN BitRate
py skills\mtpatch\run.py set-buffering <project> <can#> true  # Buffering
py skills\mtpatch\run.py set-j1939 <project> <can#> true      # J1939 토글
py skills\mtpatch\run.py set-node-id <project> <can#> <id>    # NodeId
py skills\mtpatch\run.py set-heartbeat <project> <can#> <ms>  # Heartbeat
py skills\mtpatch\run.py backup <project>                     # 명시 백업
py skills\mtpatch\run.py restore <project> <bak>              # 백업 복구
```

각 write 호출 시 sibling `.bak.<timestamp>` 자동 생성. bitrate는 `{10,20,50,100,125,250,500,800,1000}` kbps만 허용 (값 검증).

vibe 에이전트에서는 동일 기능을 `xml_set_bitrate`/`xml_set_buffering`/`xml_set_j1939`/`xml_show` tool로 노출 — LLM이 자연어 명령을 보고 GUI 다이얼로그 대신 자동 선택.

## 관련 산출물

| 경로                                  | 내용                                              |
| ------------------------------------- | ------------------------------------------------- |
| `skills\vibe\`                        | LLM tool 루프 실행 코드 (run/agent/tools/session) |
| `skills\mtpatch\`                     | `.mtproject` XML 직접 패치 (GUI 우회)             |
| `skills\fnscan\`                      | UI scan + function_map 빌드 (사전 의존)           |
| `skills\expscan\`                     | `.exp` capture·diff·mapping·plan·validate         |
| `docs\versions\8.4\function_map.json` | 49개 기능 정의 (tool schema 원천)                 |
| `docs\PROJECT.md`                     | 프로젝트 5섹션 명세                               |
| `docs\MultiToolScan.md`               | UI·exp 통합 스캔 상세                             |
| `docs\MultiToolVibeCoding.md`         | 자연어 → 자동화 설계                              |
