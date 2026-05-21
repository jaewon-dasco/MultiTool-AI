---
name: e2e_explorer
description: 야간 자율 탐색·관찰 모드로 MultiTool GUI 컨트롤 트리와 .mtproject 상태 변화를 누적 학습한다. Mac mini Ollama qwen3.5:27b를 의사결정 엔진으로 사용. v0.1 관찰 전용 — GUI 클릭이나 파일 변경 금지. 00:00~05:30 Task Scheduler 자동 실행. 키워드 — E2E, 야간 학습, MultiTool 관찰, Qwen3.5, pywinauto, observer.
---

# e2e_explorer (v0.1 — 관찰 모드)

## Purpose

야간 00:00~05:30 무인 실행으로 MultiTool 컨트롤 트리·`.mtproject` 스냅샷·Qwen3.5 응답을 누적해 4단계 round-trip 학습의 원천 데이터를 생성한다.

## v0.1 범위

| 기능                                 | 상태      |
| ------------------------------------ | --------- |
| MultiTool UI 트리 dump               | ✓         |
| `.mtproject` 스냅샷 캡처             | ✓         |
| Qwen3.5에 관찰 결과 전송 + 응답 누적 | ✓         |
| KB JSONL 적재                        | ✓         |
| 05:30 자동 종료                      | ✓         |
| GUI 클릭·키 입력                     | ✗ (금지)  |
| 파일 변경                            | ✗ (금지)  |
| Round-trip 합성·검증                 | ✗ (W5.5+) |

## 실행

```powershell
# 수동 dry-run (5분만)
py skills\e2e_explorer\orchestrator.py --until-minutes 5 --observation-only

# 야간 정규 실행 (Task Scheduler가 호출)
powershell -File skills\e2e_explorer\scripts\nightly_run.ps1
```

## 출력 경로

- `logs/e2e/<YYYY-MM-DD>/observations/` — 트리 dump, `.mtproject` 스냅샷
- `logs/e2e/<YYYY-MM-DD>/observations.jsonl` — Qwen 응답 + 메타
- `logs/e2e/<YYYY-MM-DD>/summary.md` — 사이클 종료 시 자동 생성

## 의존

- 원격: Mac mini Ollama `qwen3.5:27b` (`https://macmini.tailed5292.ts.net:11434`)
- 로컬: Python 3.10+, pywinauto, lxml, requests, tenacity
- MultiTool 8.4 설치 + `MultiToolProject/E2EProject/DasDemoProject.mtproject` 존재

## 안전

- 본 v0.1은 읽기 전용. GUI에 입력 전송 코드 자체가 없음.
- 파일 시스템은 `logs/e2e/`와 `kb/`에만 쓰기. `MultiToolProject/`는 read-only.

## MultiTool 버전 업데이트 시 재학습 절차

KB의 `verified_against` 필드로 버전 매칭 자동 처리됨 (2026-05-15 적용).

### 1. 버전 시그니처 자동 감지

`scripts/version_detect.py` 사용 — `.mtproject`의 `<Tool>`·`<SystemVersion>` + `MultiTool.exe FileVersion` 조합.

| 마커           | 출처                                | 예시                       |
| -------------- | ----------------------------------- | -------------------------- |
| Tool           | `.mtproject <Tool>`                 | `8.4.9308.1109`            |
| SystemVersion  | `.mtproject <SystemVersion>`        | `1.0.13`                   |
| ExeFileVersion | `MultiTool.exe` Windows VersionInfo | `8.4.9308.1109`            |
| **signature**  | `MT<Tool>_SV<SystemVersion>`        | `MT8.4.9308.1109_SV1.0.13` |

### 2. KB 항목 구조

```jsonl
{"xpath": "...", "verified": true, "verified_against": "MT8.4.9308.1109_SV1.0.13", ...}
```

- 사이클 시작 시 현재 시그니처 자동 산출
- KB의 `verified_against`와 일치하면 → skip (재검증 불필요)
- 불일치 또는 미기록 → **STALE 처리 → 자동 재검증**

### 3. 업데이트 후 명령

| 상황                           | 명령                                 | 효과                                   |
| ------------------------------ | ------------------------------------ | -------------------------------------- |
| 마이너 업데이트 (xpath 그대로) | `orchestrator.py` (옵션 없음)        | 버전 다른 KB만 자동 stale 처리, 재검증 |
| 전체 강제 재검증               | `orchestrator.py --revalidate-all`   | KB verified 무시, 모든 시드 실행       |
| 버전 매칭 무시 (legacy 동작)   | `orchestrator.py --no-skip-verified` | xpath verified 모두 그대로 skip        |

### 4. 깨지는 케이스별 수동 작업

| 변경 유형                          | 영향                           | 대응                                                |
| ---------------------------------- | ------------------------------ | --------------------------------------------------- |
| XML 스키마 변경 (필드 rename·이동) | 시드 xpath 무효                | `sequences/*.json`의 xpath 갱신 (FAIL log에서 식별) |
| UI 레이아웃 변경                   | recipe 좌표·라벨 식별 실패     | `recipes/*.py` 재테스트 (1회 인터랙티브)            |
| 모델 ID 변경                       | `verify_scenario.py` 매핑 무효 | `<Id>` 값 매핑 표 갱신                              |
| .exp 포맷 변경                     | KB `.exp` 패턴 무효            | morning_review에서 delta 발견 → KB 재적재           |

### 5. 빠른 재학습 예상 시간

| 변경 규모             | 시간                                        |
| --------------------- | ------------------------------------------- |
| 마이너 (xpath 그대로) | ~5분 (모든 시드 1회) + 결정성 추가 시 ~30분 |
| xpath 일부 변경       | 시드 갱신 + 5~10분 검증                     |
| UI/recipe 영향        | recipe당 5~15분 인터랙티브 + KB 갱신        |

### 6. 권장 순서 (업데이트 발견 시)

1. `version_detect.py` 실행 → 새 signature 확인
2. `orchestrator.py --no-llm --until-minutes 30` 한 번 돌려 KB stale 자동 검출
3. morning_review.md 또는 stats 출력에서 "FAIL · stale · 신규 패턴" 분석
4. 깨진 시드만 수동 갱신 후 `--revalidate-all` 1회
5. 결과 합격 시 새 signature로 KB 마감
