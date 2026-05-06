# PROJECT

## 관련 문서

| 문서                                             | 내용                      |
| ------------------------------------------------ | ------------------------- |
| [MultiToolScan.md](MultiToolScan.md)             | UI·exp 통합 스캔 (5섹션)  |
| [MultiToolVibeCoding.md](MultiToolVibeCoding.md) | 자연어 → MultiTool 자동화 |

## Clarify

| 항목   | 내용                                                              |
| ------ | ----------------------------------------------------------------- |
| 대상   | AI_MutiTool — MultiTool 없이 동작하는 vibecoding 자동화 환경      |
| 입력   | 자연어 명령                                                       |
| 출력   | `.mtproject` 변경 + 정합 `.exp` 생성                              |
| 산출물 | `skills/fnscan` (UI) · `skills/expscan` (exp) · `MultiTool` Skill |

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

### Skill 인프라

| 위치                   | 내용                                         |
| ---------------------- | -------------------------------------------- |
| `skills/fnscan/`       | UI scan — version·CHM·UIA·mapper·diff·verify |
| `skills/expscan/`      | `.exp` capture·diff·mapping                  |
| `docs/versions/{ver}/` | 버전별 CHM·UIA 덤프·`function_map.json`      |
| `docs/exp_patterns/`   | baseline·variant `.exp`·`mapping.json`       |

### 제약

- `.exp`는 export 시 덮어씌워짐 — 변경은 `.mtproject` 경유
- `.pro`·`_generated.exp` 직접 편집 금지
- CHM은 8.4만 제공 — 하위 버전은 UI 덤프만
- maximized 모드 + fixed offset 좌표 의존

## Plan

### 워크플로

자연어 → Intent 파싱 → 매핑 lookup → (miss 시) scan 폴백 → `.mtproject`/`.exp` 변경 → diff 검증

### 매핑 소스

| 소스                                    | 제공                           |
| --------------------------------------- | ------------------------------ |
| `docs/versions/{ver}/function_map.json` | 기능 → UI 시퀀스               |
| `docs/exp_patterns/mapping.json`        | 설정값 변형 → `.exp` 변경 라인 |

둘 다 존재해야 변경 가능 — 누락 시 `fnscan`/`expscan` 자동 트리거 후 재시도.

## Generate

상세 스키마·코드 → [MultiToolScan.md](MultiToolScan.md), [MultiToolVibeCoding.md](MultiToolVibeCoding.md).

| 명령                                | 동작                                         |
| ----------------------------------- | -------------------------------------------- |
| `py skills/fnscan/run.py [--force]` | UI scan + System Export + expscan baseline   |
| `py skills/expscan/run.py {sub}`    | capture / diff / mapping / list              |
| MultiTool Skill                     | 자연어 명령 — 매핑 누락 시 위 명령 자동 호출 |

**Skill trigger**: MultiTool 기능명·`.mtproject`/`.exp` 변경 의도·산출물 변경 키워드.

## Evaluate

상세 → [MultiToolScan.md](MultiToolScan.md), [MultiToolVibeCoding.md](MultiToolVibeCoding.md).

| 항목             | 기준                                           |
| ---------------- | ---------------------------------------------- |
| 명령 성공        | tool 시퀀스 완료 + `.mtproject` diff 의도 일치 |
| 매핑 커버리지    | `function_map` lookup hit ≥ 90%                |
| Scan 폴백        | miss → `fnscan`/`expscan` 자동 트리거 → 재시도 |
| `.exp` 정합성    | export 재현 시 diff 일치                       |
| 보호 파일 무결성 | `_generated.exp`·`.pro` 변경 0                 |

**Scan 갱신 트리거**: 신규 버전 / `Manual.chm` MD5 변경 / 매핑 miss / `--force`.
