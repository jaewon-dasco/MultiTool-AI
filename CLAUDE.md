# EPEC CoDeSys Project — Claude Code Guide

## 공통 지침

1. 글로벌 지침(`~/.claude/CLAUDE.md`)과 상호 보완하여 동기화한다. 충돌 시 로컬 우선.
2. **MD 파일 작성·수정 시 토큰 소모량 최소화 필수** — 글로벌 지침의 MD 작성 요령을 기본값으로 적용하고, `md_file_skill.py`로 표 열 정렬을 자동 교정한다.
3. MD 파일 작성 시 `|` 구분자를 세로로 열 정렬한다.
4. Python `.py`, 쉘 스크립트 등 외부 실행 파일은 프로젝트 내 `skills/` 폴더에 생성한다. (글로벌 공용은 `~/.claude/scripts/`)
5. MultiTool 프로젝트 파일(`.mtproject`)은 `ROOT/MultiToolProject/프로젝트명/프로젝트명.mtproject` 구조로 위치한다. Python 스크립트에서 경로 참조 시 `glob("*/*.mtproject")`로 탐색한다.
