# E2E 자동화 작업 스케줄

작업 히스토리·진행 상태·남은 항목 추적용. 작업 시작/완료 시 본 파일을 갱신한다.

| 항목          | 값                                                   |
| ------------- | ---------------------------------------------------- |
| 최근 갱신     | 2026-05-21 23:18                                     |
| 현재 단계     | 야간 10차 OK 100% / 11분 38초 — smoke_batch fix 검증 |
| 진행률        | 38/40 (95%)                                          |
| 마지막 commit | `0588f6d` smoke_batch 누락된 expected_kind 분기 추가 |
| 야간 실행     | 매일 18:00 (Task Scheduler) · Kill 00:00             |

## 진행 중

| #   | 시작 | 작업                            | 상태 | 비고 |
| --- | ---- | ------------------------------- | ---- | ---- |
| —   | —    | (없음 — 사용자 수동 probe 대기) | —    | —    |

## 완료 (최근 → 과거)

| 일자       | 작업                                                     | 결과 | Commit    |
| ---------- | -------------------------------------------------------- | ---- | --------- |
| 2026-05-21 | 야간 10차 OK 100% / 11분 38초 — smoke_batch fix 검증     | ✓    | (실행)    |
| 2026-05-21 | smoke_batch 누락된 expected_kind 분기 (net_bitrate/eds)  | ✓    | `0588f6d` |
| 2026-05-21 | 야간 9차 OK 100% / 15분 — 잔존 9 fails 모두 해소         | ✓    | (실행)    |
| 2026-05-21 | Add Device 3-column 재해석 + variant '3606-21' 매칭 fix  | ✓    | `9e64a4c` |
| 2026-05-21 | Device 컬럼 x 확장 + 양방향 contains 매칭                | ✓    | `4b52075` |
| 2026-05-21 | PDO Add 후 행 검색 ListItem fallback (3 fails → 0)       | ✓    | `a10c15b` |
| 2026-05-21 | Adaptive cycles 개편: Phase 1 batch + Phase 2 isolated   | ✓    | `3b2628b` |
| 2026-05-21 | LLM 영문 마이그레이션 + qwen3.5:27b 코드 적용            | ✓    | `5f8f269` |
| 2026-05-21 | 야간 8차 OK 94.4% (54분, adaptive 효과)                  | ✓    | (실행)    |
| 2026-05-21 | 야간 5~7차 OK 93.6→94.5% (정체) — 동일 9 fails           | △    | (실행)    |
| 2026-05-21 | Slave fam 변수 NameError 회피                            | ✓    | `4895135` |
| 2026-05-21 | Slave func boundary + Device contains fallback           | ✓    | `fe90f0b` |
| 2026-05-21 | Add Device polling + Slave 분기 + pdo 폴링 강화          | △    | `5b245cb` |
| 2026-05-20 | Add Device/Slave 4-column ListMenu recipe + dispatcher   | ✓    | `8d8f7fa` |
| 2026-05-20 | 야간 4차 — OK 94.2% (147/156), diag/disconnect 회복      | ✓    | (실행)    |
| 2026-05-20 | pdo Add 후 행 렌더링 폴링 + 검색 영역 확장 (3 재수정)    | ✓    | `59d3ac6` |
| 2026-05-20 | pdo_recipe 버튼 라벨 매칭 1차 + 위치 fallback            | ✓    | `a82edd0` |
| 2026-05-20 | probe_od_predefined: od_recipe idx 사용 + tree limit 800 | ✓    | `d88f825` |
| 2026-05-20 | device_disconnect — save=False 경로 ok 판정 보정 (3 fix) | ✓    | `f92794c` |
| 2026-05-20 | pdo_remove_rx fallback + diag Cycle time 단일 Edit       | ✓    | `cee0359` |
| 2026-05-20 | 야간 사이클 자율 실행 — F:48/48, 전체 OK 90%             | ✓    | (실행)    |
| 2026-05-20 | OD 핸들러 — 행 선택 동적 toolbar (D 6 시드 회복 가능)    | ✓    | `cac6f43` |
| 2026-05-20 | 야간 18:00 daily 자동 실행 + 00:00 kill 재설정           | ✓    | (PS)      |
| 2026-05-19 | PDO 핸들러 — toolbar 인덱스 + row 선택 (E: +2 시드)      | ✓    | `4dfe3a2` |
| 2026-05-19 | diagnostics_recipe Max bug fix (sort-by-x)               | ✓    | `e3c962a` |
| 2026-05-19 | 야간 3차 — C Min/Max 21/24, Cycle Max edge case          | △    | (실행)    |
| 2026-05-19 | Diagnostics UIA 핸들러 — C 회귀 해결 (24→0 → 0→16)       | ✓    | `013debc` |
| 2026-05-19 | 야간 사이클 검증 — F 0→48 회복, avg vc 22→0.5            | ✓    | (실행)    |
| 2026-05-19 | GitHub URL 추가 + remote 설정 + push                     | ✓    | `509ec99` |
| 2026-05-19 | io_variable_name 핸들러 — 핀 변수명 변경 (F: +8 시드)    | ✓    | `d9613c7` |
| 2026-05-19 | network_property 핸들러 — NETWORK BitRate 변경 (A: 0→3)  | ✓    | `36913d6` |
| 2026-05-19 | night_ui_review.py + morning_review 2026-05-19 dry 분석  | ✓    | `98bd556` |
| 2026-05-19 | SCHEDULE 남은 작업 표에 예상시간 컬럼 추가               | ✓    | `bdf7bbb` |
| 2026-05-19 | Baseline 정합화 — Save 노이즈 28→3건 (89%↓, 실 노이즈 0) | ✓    | `e2d7363` |
| 2026-05-19 | CLAUDE.md 글로벌 중복 제거 + 슬림화                      | ✓    | `af601ae` |
| 2026-05-19 | 디바이스 템플릿 XML 파서 + F_io.json 자동 생성           | ✓    | `dbc5312` |
| 2026-05-19 | io_pin UIA recipe + WPF DataGrid 가이드 문서화           | ✓    | `a8c8250` |
| 2026-05-19 | set_field_auto에 table_column 인자 추가                  | ✓    | `16b2b6c` |
| 2026-05-19 | restart 후 Open Project 자동화 추가                      | ✓    | `f7fcabe` |
| 2026-05-19 | 야간 cycles 5→3 (재시작 페널티 반영)                     | ✓    | `eb42eaa` |
| 2026-05-19 | per-seed MultiTool 재시작으로 baseline 노이즈 제거       | △    | `3cfda60` |
| 2026-05-18 | IO/Network/OD 시드 확장 + 야간 framework 보완            | ✓    | `1313b4a` |
| 2026-05-18 | night-UI framework + API portability                     | ✓    | `23b2001` |
| 2026-05-17 | Phase 3 시드 65건 + marathon_status + morning_review     | ✓    | `71909ba` |
| 2026-05-16 | marathon mode (45h continuous) + Phase 2 시드            | ✓    | `58b87eb` |

결과 표기: `✓` 성공 · `△` 부분 성공 · `✗` 실패·차단 (재시도 항목은 "남은 작업"에 분류=재시도로 추가)

## 남은 작업

우선순위(★★★ 최상 ~ ★ 최하) → 관련도(앞 작업의 결과를 활용하는 흐름) 순으로 정렬.

| 우선 | 분류       | 작업                                                                                      | 예상시간 |
| ---- | ---------- | ----------------------------------------------------------------------------------------- | -------- |
| ★★★  | 회복 검증  | 야간 9차 실행 (수동) — Add Device + PDO fix 통합 OK% ~100% 목표                           | 1h       |
| ★★   | 다이얼로그 | OD Pre-defined Index inline panel 선택 자동화 (od_add_predefined 0→3, probe 후 recipe)    | 2h       |
| ★★   | 다이얼로그 | OD Add Index / Import / Export / Store-Restore 다이얼로그 자동화 (D +4 시드)              | 3h       |
| ★★   | 확장       | EDS 파일 등록 + 타사 슬레이브 PDO 통신 자동 설정 (Add Slave Device → EDS → 네트워크 연결) | 4h       |
| ★    | 확장       | 다른 디바이스 시드 일반화 (3720, 5050, 6807 — 각 8 시드)                                  | 3h       |

## 참조

- 운영 지침·알려진 함정·갱신 프로토콜: [skills/e2e_explorer/multitool_e2e.md](../skills/e2e_explorer/multitool_e2e.md)
- 프로젝트 정의: [docs/PROJECT.md](PROJECT.md)
- 작업 단위 task: [docs/tasks/](tasks/)
