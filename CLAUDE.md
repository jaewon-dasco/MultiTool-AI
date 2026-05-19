# EPEC CoDeSys Project — Claude Code Guide

글로벌 공통 지침(`~/.claude/CLAUDE.md`) 상속. 충돌 시 본 파일이 우선.

## 환경

| 항목   | 값                                              |
| ------ | ----------------------------------------------- |
| 대상   | MultiTool Creator 8.4 (Epec) E2E 자동화         |
| 채널   | UI Automation (pywinauto) — API 없음            |
| 산출물 | `.mtproject` XML + CoDeSys `.exp` 변수 export   |
| 의존성 | Python 3.13 (pywinauto, winocr, Pillow), Ollama |

## 프로젝트 특화 규칙

- `.py`·쉘 스크립트는 프로젝트 내 `skills/` 폴더에 생성 (글로벌 공용 스크립트는 `~/.claude/scripts/`)
- MultiTool 프로젝트 파일(`.mtproject`)은 `ROOT/MultiToolProject/<이름>/<이름>.mtproject` 구조. Python 경로 참조 시 `glob("*/*.mtproject")`
- E2E UI 자동화 운영 규칙은 [skills/e2e_explorer/multitool_e2e.md](skills/e2e_explorer/multitool_e2e.md) 단일 권위 문서 참조 (Click 메서드 매트릭스·세션 종료 의무·OCR vs UIA 등)

## 참조

- [docs/PROJECT.md](docs/PROJECT.md) — 정의서 (5섹션)
- [docs/SCHEDULE.md](docs/SCHEDULE.md) — 작업 스케줄
- [skills/e2e_explorer/multitool_e2e.md](skills/e2e_explorer/multitool_e2e.md) — E2E 운영 지침
