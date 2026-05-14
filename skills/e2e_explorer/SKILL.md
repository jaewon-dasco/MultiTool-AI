---
name: e2e_explorer
description: 야간 자율 탐색·관찰 모드로 MultiTool GUI 컨트롤 트리와 .mtproject 상태 변화를 누적 학습한다. Mac mini Ollama gemma4:26b를 의사결정 엔진으로 사용. v0.1 관찰 전용 — GUI 클릭이나 파일 변경 금지. 00:00~05:30 Task Scheduler 자동 실행. 키워드 — E2E, 야간 학습, MultiTool 관찰, Gemma4, pywinauto, observer.
---

# e2e_explorer (v0.1 — 관찰 모드)

## Purpose

야간 00:00~05:30 무인 실행으로 MultiTool 컨트롤 트리·`.mtproject` 스냅샷·Gemma4 응답을 누적해 4단계 round-trip 학습의 원천 데이터를 생성한다.

## v0.1 범위

| 기능 | 상태 |
|----|----|
| MultiTool UI 트리 dump | ✓ |
| `.mtproject` 스냅샷 캡처 | ✓ |
| Gemma4에 관찰 결과 전송 + 응답 누적 | ✓ |
| KB JSONL 적재 | ✓ |
| 05:30 자동 종료 | ✓ |
| GUI 클릭·키 입력 | ✗ (금지) |
| 파일 변경 | ✗ (금지) |
| Round-trip 합성·검증 | ✗ (W5.5+) |

## 실행

```powershell
# 수동 dry-run (5분만)
py skills\e2e_explorer\orchestrator.py --until-minutes 5 --observation-only

# 야간 정규 실행 (Task Scheduler가 호출)
powershell -File skills\e2e_explorer\scripts\nightly_run.ps1
```

## 출력 경로

- `logs/e2e/<YYYY-MM-DD>/observations/` — 트리 dump, `.mtproject` 스냅샷
- `logs/e2e/<YYYY-MM-DD>/observations.jsonl` — Gemma 응답 + 메타
- `logs/e2e/<YYYY-MM-DD>/summary.md` — 사이클 종료 시 자동 생성

## 의존

- 원격: Mac mini Ollama `gemma4:26b` (`https://macmini.tailed5292.ts.net:11434`)
- 로컬: Python 3.10+, pywinauto, lxml, requests, tenacity
- MultiTool 8.4 설치 + `MultiToolProject/E2EProject/DasDemoProject.mtproject` 존재

## 안전

- 본 v0.1은 읽기 전용. GUI에 입력 전송 코드 자체가 없음.
- 파일 시스템은 `logs/e2e/`와 `kb/`에만 쓰기. `MultiToolProject/`는 read-only.
