# E2E 자동화 작업 스케줄

작업 히스토리·진행 상태·남은 항목 추적용. 작업 시작/완료 시 본 파일을 갱신한다.

| 항목          | 값                                                |
| ------------- | ------------------------------------------------- |
| 최근 갱신     | 2026-05-19                                        |
| 현재 단계     | 야간 사이클 3차 (19:50~) — Max 버그 fix 통합 검증 |
| 진행률        | 19/23 (82.6%)                                     |
| 마지막 commit | `e3c962a` diagnostics_recipe Max bug fix          |

## 진행 중

| #   | 시작             | 작업                                                            | 상태   | 비고                                  |
| --- | ---------------- | --------------------------------------------------------------- | ------ | ------------------------------------- |
| 8   | 2026-05-19 19:50 | 야간 3차 — Max bug fix 통합 검증 (C 24/24 회복 + 노이즈 0 확인) | 실행중 | ~22:00 완료 예상, 최종 morning_review |

## 완료 (최근 → 과거)

| 일자       | 작업                                                       | 결과 | Commit    |
| ---------- | ---------------------------------------------------------- | ---- | --------- |
| 2026-05-19 | diagnostics_recipe Max bug fix (sort-by-x)                 | ✓    | `e3c962a` |
| 2026-05-19 | 야간 2차 — C Min 12/24 회복, Max bug 발견, OK 72%          | △    | (실행)    |
| 2026-05-19 | Diagnostics UIA 핸들러 — C 회귀 해결 (24→0 → 0→8 fix)      | ✓    | `013debc` |
| 2026-05-19 | 야간 사이클 검증 — F 0→48 회복, C 24→0 회귀, avg vc 22→0.5 | ✓    | (실행)    |
| 2026-05-19 | GitHub URL 추가 + remote 설정 + push                       | ✓    | `509ec99` |
| 2026-05-19 | io_variable_name 핸들러 — 핀 변수명 변경 (F: +8 시드)      | ✓    | `d9613c7` |
| 2026-05-19 | network_property 핸들러 — NETWORK BitRate 변경 (A: 0→3)    | ✓    | `36913d6` |
| 2026-05-19 | night_ui_review.py + morning_review 2026-05-19 dry 분석    | ✓    | `98bd556` |
| 2026-05-19 | SCHEDULE 남은 작업 표에 예상시간 컬럼 추가                 | ✓    | `bdf7bbb` |
| 2026-05-19 | Baseline 정합화 — Save 노이즈 28→3건 (89%↓, 실 노이즈 0)   | ✓    | `e2d7363` |
| 2026-05-19 | CLAUDE.md 글로벌 중복 제거 + 슬림화                        | ✓    | `af601ae` |
| 2026-05-19 | 디바이스 템플릿 XML 파서 + F_io.json 자동 생성             | ✓    | `dbc5312` |
| 2026-05-19 | io_pin UIA recipe + WPF DataGrid 가이드 문서화             | ✓    | `a8c8250` |
| 2026-05-19 | set_field_auto에 table_column 인자 추가                    | ✓    | `16b2b6c` |
| 2026-05-19 | restart 후 Open Project 자동화 추가                        | ✓    | `f7fcabe` |
| 2026-05-19 | 야간 cycles 5→3 (재시작 페널티 반영)                       | ✓    | `eb42eaa` |
| 2026-05-19 | per-seed MultiTool 재시작으로 baseline 노이즈 제거         | △    | `3cfda60` |
| 2026-05-18 | IO/Network/OD 시드 확장 + 야간 framework 보완              | ✓    | `1313b4a` |
| 2026-05-18 | night-UI framework + API portability                       | ✓    | `23b2001` |
| 2026-05-17 | Phase 3 시드 65건 + marathon_status + morning_review       | ✓    | `71909ba` |
| 2026-05-16 | marathon mode (45h continuous) + Phase 2 시드              | ✓    | `58b87eb` |

결과 표기: `✓` 성공 · `△` 부분 성공 · `✗` 실패·차단 (재시도 항목은 "남은 작업"에 분류=재시도로 추가)

## 남은 작업

우선순위(★★★ 최상 ~ ★ 최하) → 관련도(앞 작업의 결과를 활용하는 흐름) 순으로 정렬.

| 우선 | 분류        | 작업                                                                                | 예상시간 |
| ---- | ----------- | ----------------------------------------------------------------------------------- | -------- |
| ★★   | 핸들러 구현 | `dialog_probe` 실 핸들러 승격 — Pre-defined Index 자동화 (D: od_add_predefined 0→3) | 2h       |
| ★★   | 디버그      | A 카테고리 `toolbar_action_with_dialog` 디버그 (net_add_device/slave 0/3, A: 6→12)  | 2h       |
| ★★   | 디버그      | D 카테고리 OD dialog 처리 (od_remove/store/restore/import/export, D: 9→24)          | 3h       |
| ★    | 디버그      | E 카테고리 PDO 일부 실패 (pdo_remove_tx/rx, E: 9→15)                                | 1h       |
| ★    | 확장        | 다른 디바이스 시드 일반화 (3720, 5050, 6807 — 각 8 시드)                            | 3h       |

## 참조

- 운영 지침·알려진 함정·갱신 프로토콜: [skills/e2e_explorer/multitool_e2e.md](../skills/e2e_explorer/multitool_e2e.md)
- 프로젝트 정의: [docs/PROJECT.md](PROJECT.md)
- 작업 단위 task: [docs/tasks/](tasks/)
